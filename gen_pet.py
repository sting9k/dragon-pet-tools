#!/usr/bin/env python3
"""Redraws one pack pet larger and more detailed with an image model, keeping its shape and pose.

The pet is rendered from its Spine model, enlarged on white, and sent as the reference image with the
prompt below; only the description changes from pet to pet (docs/pet-prompts.md lists the ones used).

Usage:  python3 gen_pet.py <model> "<description>" [--dry]
  <model>        folder of the pet under the pack's spine folder, e.g. DV3/character/dragon/fire_00_adult
  <description>  the pet in one sentence: "same <colour> <kind> dragon, same <pose> pose facing <left|right>,
                 <body colours and markings>, <wings>, <anything it must keep>."
  --dry          only build the reference image and print the prompt, call nothing
Environment:
  RESKIN_KEY    API key of the image service (required unless --dry)
  RESKIN_API    its image-edit endpoint, an OpenAI-style .../v1/images/edits taking a form upload (required unless --dry)
  RESKIN_MODEL  default qwen-image-3.0-pro; the model must keep the shape of the reference, or rigging fails
Put them in .env (see .env.example).

Output: <assets>/generated/pets/<name>.png (2048x2048, white background) and <name>_ref.png beside it.
"""
import json
import os
import sys
import tempfile
import urllib.request

from PIL import Image

from common import GENERATED, curl, render, secret

OUT = os.path.join(GENERATED, "pets")
MODEL = os.environ.get("RESKIN_MODEL", "qwen-image-3.0-pro")
PROMPT = (
    "Redraw this small low-resolution pixel-art dragon as a large, highly detailed pixel-art illustration "
    "of the SAME dragon: {description} "
    "Add rich detail: layered scales, horns, claws, wing bones, armor-like plates, sharp spikes, crisp dark "
    "outlines, hard-edged cel shading with bright highlights. Clean 16-bit JRPG boss sprite style, single "
    "character, plain flat white background, no text."
)
# The reference: the pet in a CELL square, enlarged to PASTE and put at MARGIN of a SIDE square.
# rig_skin.py relies on these numbers to find the pet again in the answer.
CELL, SIDE, MARGIN = 640, 1024, 64
PASTE = SIDE - 2 * MARGIN


def reference(model, name):
    """the pet as the pack draws it, enlarged with hard pixels on a white square"""
    with tempfile.TemporaryDirectory() as tmp:
        sheet = os.path.join(tmp, "sheet.png")
        render("--sheet", sheet, model, "-", str(CELL), "1", "bare")
        pet = Image.open(sheet).convert("RGBA").crop((0, 0, CELL, CELL))
    # hard pixels: a texel is either the pet or the white ground, so dark pets keep every dark pixel
    pet.putalpha(pet.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
    ref = Image.new("RGBA", (SIDE, SIDE), (255, 255, 255, 255))
    ref.alpha_composite(pet.resize((PASTE, PASTE), Image.NEAREST), (MARGIN, MARGIN))
    ref = ref.convert("RGB")
    path = os.path.join(OUT, name + "_ref.png")
    ref.save(path)
    return path


def main():
    args = [a for a in sys.argv[1:] if a != "--dry"]
    if len(args) != 2:
        sys.exit(__doc__)
    model, description = args
    name = os.path.basename(os.path.normpath(model))
    os.makedirs(OUT, exist_ok=True)
    ref = reference(model, name)
    prompt = PROMPT.format(description=description)
    if "--dry" in sys.argv:
        print(f"reference: {ref}\nprompt: {prompt}")
        return
    answer = curl(secret("RESKIN_API"), "-H", f"Authorization: Bearer {secret('RESKIN_KEY')}", "-F", f"model={MODEL}", "-F", f"image=@{ref}",
                  "-F", f"prompt={prompt}", "-F", f"size={SIDE}x{SIDE}", "-F", "n=1", timeout=300)
    try:
        url = json.loads(answer)["data"][0]["url"]
    except (ValueError, KeyError, IndexError):
        sys.exit("the API did not return an image: " + answer[:300])
    target = os.path.join(OUT, name + ".png")
    urllib.request.urlretrieve(url, target)
    print(f"{name}: {target}")


if __name__ == "__main__":
    main()
