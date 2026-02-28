"""Volcengine (Doubao) V3 HTTP TTS quick test (MP3).

Goal: simplest possible script to verify whether a voice_type sounds good.

Usage:
  1) Install dependency:
       python3 -m pip install requests

  2) Export credentials (recommended; don't hardcode secrets in code):
       export VOLC_TTS_APPID="your_appid"
       export VOLC_TTS_ACCESS_TOKEN="your_access_token"

  3) Run:
       python3 test/mars_tts_test/tts_http_mp3.py \
         --voice_type zh_female_cancan_mars_bigtts \
         --text "你好，我是火山引擎的语音合成服务。" \
         --out out.mp3

Notes:
- Authorization header MUST be: "Bearer; <token>" (semicolon, not space).
- HTTP is non-streaming: request.operation must be "query".
"""

import argparse
import base64
import os
import sys
import uuid

import requests


URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
CLUSTER = "volcano_tts"


def synthesize_mp3(*, appid: str, access_token: str, voice_type: str, text: str, out_path: str) -> None:
    headers = {
        # Important: Bearer and token are separated by ';'
        "Authorization": f"Bearer; {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "app": {
            "appid": appid,
            # Per docs: this token has no real auth effect but must be non-empty.
            "token": "fake_token",
            "cluster": CLUSTER,
        },
        "user": {"uid": "uid123"},
        "audio": {
            "voice_type": voice_type,
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "rate": 24000,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "operation": "query",
        },
    }

    r = requests.post(URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    if data.get("code") != 3000:
        raise RuntimeError(f"TTS failed: code={data.get('code')} message={data.get('message')}")

    audio_b64 = data.get("data")
    if not audio_b64:
        raise RuntimeError("TTS response missing 'data' field")

    audio_bytes = base64.b64decode(audio_b64)
    with open(out_path, "wb") as f:
        f.write(audio_bytes)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Volcengine/Doubao V3 HTTP TTS -> MP3")
    p.add_argument("--appid", default=os.getenv("VOLC_TTS_APPID"), help="AppID (or set VOLC_TTS_APPID)")
    p.add_argument(
        "--access_token",
        default=os.getenv("VOLC_TTS_ACCESS_TOKEN"),
        help="Access token (or set VOLC_TTS_ACCESS_TOKEN)",
    )
    p.add_argument("--voice_type", required=True, help="Voice type id")
    p.add_argument("--text", required=True, help="Text to synthesize")
    p.add_argument("--out", default="out.mp3", help="Output mp3 path")

    args = p.parse_args(argv)

    if not args.appid:
        print("Missing appid: pass --appid or set VOLC_TTS_APPID", file=sys.stderr)
        return 2
    if not args.access_token:
        print("Missing access_token: pass --access_token or set VOLC_TTS_ACCESS_TOKEN", file=sys.stderr)
        return 2

    try:
        synthesize_mp3(
            appid=args.appid,
            access_token=args.access_token,
            voice_type=args.voice_type,
            text=args.text,
            out_path=args.out,
        )
    except requests.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Saved: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
