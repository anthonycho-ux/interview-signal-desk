#!/usr/bin/env python3
"""Render the Karsan radio bulletin to MP3 via the ElevenLabs API.

Loads ELEVENLABS_API_KEY from the environment or ~/.hermes/.env
(Anthony's voice API). Picks a voice from the account (skipping any
cloned/private voice unless ELEVENLABS_VOICE names one). Tries a small
list of model ids so older/newer accounts both work.

Usage: python3 render_radio.py [--out DIR] [--voice VOICE_ID]
Writes radio.mp3 + radio-meta.json next to the script, then copies both
into the web folder serving the radio page.
"""
import argparse
import json
import os
import re
import shutil
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
WEB_DIR = os.path.expanduser("~/web/karsan/radio")
SCRIPT_JSON = os.path.join(HERE, "radio-script.json")
MODEL_CANDIDATES = [
    "eleven_monolingual_v1",
    "eleven_multilingual_v2",
    "eleven_flash_v2_5",
    "eleven_turbo_v2_5",
]
API = "https://api.elevenlabs.io"


def load_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if k:
        return k.strip()
    env = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env):
        with open(env, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"\s*ELEVENLABS_API_KEY\s*=\s*['\"]?([^'\"]+)\s*$", line)
                if m:
                    return m.group(1).strip()
    return None


def api_get(path, key):
    req = urllib.request.Request(API + path, headers={"xi-api-key": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def api_post(path, key, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API + path, data=body,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def pick_voice(key, want):
    if want:
        return want, want
    try:
        voices = api_get("/v1/voices", key).get("voices", [])
    except Exception as e:
        print("voice list failed:", e)
        return "", ""
    for v in voices:
        name = (v.get("name") or "").lower()
        if "clone" not in name and "private" not in name and not v.get("is_legacy"):
            return v["voice_id"], v.get("name") or v["voice_id"]
    return (voices[0]["voice_id"], voices[0].get("name") or voices[0]["voice_id"]) if voices else ("", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default=os.environ.get("ELEVENLABS_VOICE", ""))
    ap.add_argument("--out", default=HERE)
    args = ap.parse_args()

    key = load_key()
    if not key:
        sys.exit("ELEVENLABS_API_KEY not found (env or ~/.hermes/.env)")
    if not os.path.exists(SCRIPT_JSON):
        sys.exit("radio-script.json missing — run radio_script.py first")

    script = json.load(open(SCRIPT_JSON, encoding="utf-8"))
    segs = script["segments"]
    text = " ".join(s["text"] for s in segs)

    voice, voice_name = pick_voice(key, args.voice)
    print("voice:", voice_name or voice or "(default request)")

    mp3 = None
    used_model = None
    for model in MODEL_CANDIDATES:
        try:
            mp3 = api_post(f"/v1/text-to-speech/{voice}", key, {
                "text": text,
                "model_id": model,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.6,
                                   "style": 0.4, "use_speaker_boost": True},
            })
            used_model = model
            print("synthesized with model:", model)
            break
        except urllib.error.HTTPError as e:
            print(f"model {model} failed: {e.code} — {e.read()[:160]}")
        except Exception as e:
            print(f"model {model} failed: {e}")
    if mp3 is None:
        sys.exit("could not synthesize with any model")

    if not mp3.startswith(b"ID3") and not mp3.startswith(b"\xff\xfb"):
        print("warning: response does not look like mp3 (%d bytes)" % len(mp3))

    out_mp3 = os.path.join(args.out, "radio.mp3")
    with open(out_mp3, "wb") as fh:
        fh.write(mp3)
    meta = {
        "renderedAt": script["renderedAt"],
        "renderedNow": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "voice": voice, "voiceName": voice_name,
        "model": used_model,
        "words": len(text.split()),
        "bytes": len(mp3),
        "segments": len(segs),
    }
    with open(os.path.join(args.out, "radio-meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=1)

    # publish to the web folder
    os.makedirs(WEB_DIR, exist_ok=True)
    for fn in ("radio.mp3", "radio-meta.json", "radio-script.json"):
        src = os.path.join(args.out, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(WEB_DIR, fn))

    print(f"wrote {out_mp3}: {len(mp3)} bytes, {meta['words']} words, {len(segs)} segments")
    print(f"published to {WEB_DIR}")


if __name__ == "__main__":
    main()
