"""Verify gateway authentication; --generate makes one billable test request."""

import argparse
import base64
import binascii
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request
import zlib


def red_pixel_png() -> str:
    def chunk(name: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + name
            + payload
            + struct.pack(">I", binascii.crc32(name + payload) & 0xFFFFFFFF)
        )

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    image = header + chunk(b"IHDR", ihdr)
    image += chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
    image += chunk(b"IEND", b"")
    return base64.b64encode(image).decode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--image", action="store_true")
    parser.add_argument("--model", help="Configured model to verify")
    args = parser.parse_args()
    import google.auth
    from google.auth.transport.requests import Request

    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(Request())
    except (google.auth.exceptions.GoogleAuthError, OSError, ValueError) as error:
        sys.exit(f"Google authentication failed ({type(error).__name__}).")
    print(json.dumps({"authentication": "valid", "project": project}))
    headers = {"Authorization": "Bearer " + os.environ["LITELLM_MASTER_KEY"]}
    request = urllib.request.Request("http://localhost:4000/v1/models", headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        models = [item["id"] for item in json.load(response)["data"]]
    configured_models = list(
        dict.fromkeys(
            item.strip()
            for item in os.environ.get("VERTEX_MODELS", "").split(",")
            if item.strip()
        )
    ) or [os.environ["VERTEX_MODEL"]]
    missing = [item for item in configured_models if item not in models]
    if missing:
        sys.exit("A configured model is missing from the gateway catalogue.")
    model = args.model or os.environ["VERTEX_MODEL"]
    if model not in configured_models:
        sys.exit("The requested model is not included in VERTEX_MODELS.")
    print(
        json.dumps(
            {
                "gateway_models": configured_models,
                "selected_model": model,
                "inference_verified": False,
            }
        )
    )
    if not args.generate:
        return
    user_content = "Responde únicamente: listo"
    expected = "listo"
    if args.image:
        user_content = [
            {"type": "text", "text": "Responde únicamente con el color de la imagen."},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64," + red_pixel_png()},
            },
        ]
        expected = "rojo"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_content}],
        "max_tokens": 128,
        "stream": False,
    }
    headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        "http://localhost:4000/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers=headers,
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        sys.exit(
            f"Vertex generation failed (HTTP {error.code}); check IAM, API and billing."
        )
    except urllib.error.URLError:
        sys.exit("Gateway unavailable or request timed out.")
    choice = result["choices"][0]
    if (
        choice["finish_reason"] != "stop"
        or expected not in choice["message"]["content"].lower()
    ):
        sys.exit("The response did not satisfy the test.")
    print(
        json.dumps(
            {
                "inference_verified": True,
                "model": result["model"],
                "usage": result.get("usage"),
                "response_time_ms": round((time.monotonic() - started) * 1000),
            }
        )
    )


if __name__ == "__main__":
    main()
