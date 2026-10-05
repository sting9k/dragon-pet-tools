"""What a skill demo is built from: the scene kit, sprites rendered from the pack, effect frames, drawing.

scene_kit/ holds the only pictures stored with the tools: a ground tile and a small atlas of code-drawn
sprites (shadow, damage digits, scorch mark, smoke puff). Everything that shows pack art (the pet, the
enemies) is rendered from the pack when a demo runs and kept in a cache under <assets>/generated/cache.
"""
import hashlib
import json
import os

import numpy as np
from PIL import Image

from common import GENERATED, TOOLS, render

KIT = os.path.join(TOOLS, "scene_kit")
CACHE = os.path.join(GENERATED, "cache")
MARGIN = 12  # render.mjs leaves this much of a cell empty around the model


def kit():
    """{name: [frames]} of the code-drawn sprites, at the size they are drawn on screen"""
    info = json.load(open(os.path.join(KIT, "fx.json")))
    sheet = Image.open(os.path.join(KIT, info["image"])).convert("RGBA")
    return {name: [sheet.crop((x, y, x + s["w"], y + s["h"])) for x, y in s["frames"]] for name, s in info["sprites"].items()}


def ground(width, height):
    """a canvas of that size covered with the ground tile"""
    tile = Image.open(os.path.join(KIT, "ground.png")).convert("RGBA")
    canvas = Image.new("RGBA", (width, height))
    for x in range(0, width, tile.width):
        for y in range(0, height, tile.height):
            canvas.alpha_composite(tile, (x, y))
    return canvas


def pack_frames(model, anim, count, cell, fit="", skin=None):
    """`count` frames of one animation of a pack model, each `cell` pixels square on transparency.
    `fit` names the animations whose extent sets the scale; `skin` is a folder of rigged redraws"""
    stamp = ""
    if skin:
        picture = os.path.join(skin, model + ".png")
        stamp = str(os.path.getmtime(picture)) if os.path.isfile(picture) else "pack"
    key = hashlib.sha1("|".join([model, anim, str(count), str(cell), fit, stamp]).encode()).hexdigest()[:16]
    strip = os.path.join(CACHE, key + ".png")
    if not os.path.isfile(strip):
        os.makedirs(CACHE, exist_ok=True)
        if skin:
            os.environ["SPINE_OVERLAY"] = os.path.abspath(skin)
        else:
            os.environ.pop("SPINE_OVERLAY", None)
        render("--strip", strip, model, anim, str(count), str(cell), fit)
    sheet = Image.open(strip).convert("RGBA")
    return [sheet.crop((k * cell, 0, (k + 1) * cell, cell)) for k in range(count)]


def pack_sprite(model, anim, count, size):
    """a pack model's animation as small sprites whose longer side is `size` pixels, cropped to the body"""
    cell = 160
    frames = pack_frames(model, anim, count, cell)
    box = None
    for f in frames:
        b = f.getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    shrink = size / (cell - MARGIN)
    target = (max(1, round((box[2] - box[0]) * shrink)), max(1, round((box[3] - box[1]) * shrink)))
    return [f.crop(box).resize(target, Image.LANCZOS) for f in frames]


def effect(pet, name, size):
    """the frames of one processed effect sheet of a pet, scaled to `size` pixels with hard pixels"""
    folder = os.path.join(TOOLS, "pets", pet, "fx", name)
    if not os.path.isdir(folder):
        raise SystemExit(f"no frames for {name}; run: python3 pet.py {pet} fx")
    files = sorted(f for f in os.listdir(folder) if f.endswith(".png") and f[:-4].rsplit("-", 1)[-1].isdigit())
    return [Image.open(os.path.join(folder, f)).convert("RGBA").resize((size, size), Image.NEAREST) for f in files]


def put(canvas, sprite, x, y, ax=0.5, ay=0.5):
    """draws the sprite with its point (ax, ay), in shares of its size, at (x, y)"""
    canvas.alpha_composite(sprite, (round(x - sprite.width * ax), round(y - sprite.height * ay)))


def white(sprite, amount):
    """the sprite flashed toward white, keeping its shape"""
    px = np.asarray(sprite).astype(np.float32)
    px[..., :3] += (255 - px[..., :3]) * amount
    return Image.fromarray(px.astype(np.uint8))


def tinted(sprite, colour):
    px = np.asarray(sprite).astype(np.float32)
    px[..., :3] *= np.asarray(colour, np.float32) / 255
    return Image.fromarray(px.astype(np.uint8))


def faded(sprite, share):
    px = np.asarray(sprite).astype(np.float32)
    px[..., 3] *= share
    return Image.fromarray(px.astype(np.uint8))


def number(digits, value, scale, colour):
    """a damage number drawn with the kit's digits"""
    glyphs = [digits[int(c)] for c in str(value)]
    strip = Image.new("RGBA", (sum(g.width + 1 for g in glyphs), glyphs[0].height))
    x = 0
    for g in glyphs:
        strip.alpha_composite(g, (x, 0))
        x += g.width + 1
    return tinted(strip.resize((strip.width * scale, strip.height * scale), Image.NEAREST), colour)


def save_gif(path, frames, fps):
    """a looping GIF with one palette for the whole clip, taken across the timeline, so colours do not flicker"""
    picks = [frames[i] for i in range(0, len(frames), max(1, len(frames) // 8))]
    width, height = frames[0].size
    strip = Image.new("RGB", (width * len(picks), height))
    for i, f in enumerate(picks):
        strip.paste(f, (i * width, 0))
    palette = strip.quantize(255, method=Image.MEDIANCUT)
    paletted = [f.quantize(palette=palette, dither=Image.NONE) for f in frames]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    paletted[0].save(path, save_all=True, append_images=paletted[1:], duration=1000 // fps, loop=0)
