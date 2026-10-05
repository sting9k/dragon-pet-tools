#!/usr/bin/env python3
"""Draws one image with a custom OpenAI-compatible image API and saves it as a PNG.

This replaces the agent's built-in image tool: every raw sheet, base map and reference of these skills
is made by calling this script.

Usage:
  python scripts/image_api.py --prompt-file <prompt.txt> --out <raw.png> [--ref <image.png> ...]
  python scripts/image_api.py --prompt "<text>" --out <raw.png> [--aspect 16:9] [--resolution 2k]

  --ref         a reference image the model must see (repeatable, order is kept). With references the
                edits endpoint is called, without any the generations endpoint.
  --aspect      aspect ratio of the picture, default 1:1
  --resolution  1k, 2k or 4k, default 2k
  --size        WIDTHxHEIGHT for APIs that take a size instead (multipart style), default 1024x1024

Environment:
  IMAGE_KEY           API key (required). From the environment, or from the nearest .env file above this
                      script (KEY=VALUE lines, git-ignored); never put it in any other file.
  IMAGE_API           edits endpoint of the image service, .../v1/images/edits (required)
  IMAGE_API_GENERATE  generations endpoint, default: IMAGE_API with /edits replaced by /generations
  IMAGE_MODEL         default gpt-image-2
  IMAGE_API_STYLE     json (default): JSON body, references inline in "images" as data URIs
                      multipart: form upload with "image" files and "size"

The prompt is saved beside the picture as <out>.prompt.txt. A picture that comes back with its background
already transparent is kept transparent (the postprocessors accept both that and solid magenta).
"""
import argparse
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from PIL import Image

TIMEOUT = 600  # seconds; one picture takes one to two minutes
AGENT = "sprite-forge/1.0"  # the default urllib agent is refused by some gateways
CLEAR, SOLID = 16, 235  # alpha below CLEAR becomes 0, alpha from SOLID up becomes 255


def load_env():
    """reads the nearest .env above this script (KEY=VALUE lines); what is already in the environment wins"""
    for folder in Path(__file__).resolve().parents:
        env = folder / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                name, mark, value = line.strip().partition("=")
                if mark and name and not name.startswith("#"):
                    os.environ.setdefault(name.strip(), value.strip().strip("\"'"))
            return


def settings():
    load_env()
    key = os.environ.get("IMAGE_KEY") or sys.exit("set IMAGE_KEY to the image API key (environment or a .env file)")
    edits = os.environ.get("IMAGE_API") or sys.exit("set IMAGE_API to the image-edit endpoint (environment or a .env file)")
    return {
        "key": key,
        "edits": edits,
        "generate": os.environ.get("IMAGE_API_GENERATE", edits.replace("/edits", "/generations")),
        "model": os.environ.get("IMAGE_MODEL", "gpt-image-2"),
        "style": os.environ.get("IMAGE_API_STYLE", "json"),
    }


def json_body(model, prompt, refs, args):
    body = {"model": model, "prompt": prompt, "resolution": args.resolution, "aspect_ratio": args.aspect}
    if refs:
        body["images"] = ["data:image/png;base64," + base64.b64encode(r.read_bytes()).decode() for r in refs]
    return json.dumps(body).encode(), "application/json"


def multipart_body(model, prompt, refs, args):
    mark = uuid.uuid4().hex
    parts = []
    for name, value in (("model", model), ("prompt", prompt), ("size", args.size), ("n", "1")):
        parts.append(f'--{mark}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for r in refs:
        head = f'--{mark}\r\nContent-Disposition: form-data; name="image"; filename="{r.name}"\r\nContent-Type: image/png\r\n\r\n'
        parts.append(head.encode() + r.read_bytes() + b"\r\n")
    parts.append(f"--{mark}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={mark}"


def fetch(request):
    """the body of the answer; an HTTP error ends the run with the server's own words, never with the key"""
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as answer:
            return answer.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"the image API answered {e.code}: {e.read()[:400].decode(errors='replace')}")
    except (urllib.error.URLError, TimeoutError) as e:
        sys.exit(f"the image API could not be reached: {e}")


def draw(prompt, refs, args):
    cfg = settings()
    body, kind = (multipart_body if cfg["style"] == "multipart" else json_body)(cfg["model"], prompt, refs, args)
    headers = {"Authorization": "Bearer " + cfg["key"], "Content-Type": kind, "User-Agent": AGENT}
    answer = fetch(urllib.request.Request(cfg["edits"] if refs else cfg["generate"], data=body, headers=headers))
    try:
        first = json.loads(answer)["data"][0]
    except (ValueError, KeyError, IndexError, TypeError):
        sys.exit("the image API did not return an image: " + answer[:400].decode(errors="replace"))
    if first.get("b64_json"):
        return base64.b64decode(first["b64_json"])
    if first.get("url"):
        return fetch(urllib.request.Request(first["url"], headers={"User-Agent": AGENT}))
    sys.exit("the image API answer holds neither b64_json nor url")


def tidy(picture):
    """the picture as PNG bytes. Some models key the background out themselves and leave a faint haze over it
    and a body that is almost, but not fully, opaque; both ends are snapped so frames can be cut cleanly"""
    img = Image.open(io.BytesIO(picture))
    if img.mode not in ("RGBA", "LA") and "transparency" not in img.info:
        return picture
    img = img.convert("RGBA")
    alpha = img.getchannel("A").point([0 if a < CLEAR else 255 if a >= SOLID else a for a in range(256)])
    img.putalpha(alpha)
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    text = parser.add_mutually_exclusive_group(required=True)
    text.add_argument("--prompt")
    text.add_argument("--prompt-file", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ref", type=Path, action="append", default=[])
    parser.add_argument("--aspect", default="1:1")
    parser.add_argument("--resolution", default="2k")
    parser.add_argument("--size", default="1024x1024")
    args = parser.parse_args()

    prompt = args.prompt if args.prompt is not None else args.prompt_file.read_text(encoding="utf-8")
    missing = [str(r) for r in args.ref if not r.is_file()]
    if missing:
        sys.exit("reference not found: " + ", ".join(missing))
    picture = draw(prompt.strip(), args.ref, args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(tidy(picture))
    args.out.with_name(args.out.name + ".prompt.txt").write_text(prompt.strip() + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
