#!/usr/bin/env python3
"""Renders the animations of one pack model to GIFs, to check a redrawn skin in motion.

Only the animations the game uses are drawn (pet_animations.py), with the frame counts the game would bake.

Usage: python3 preview_pet.py <model> [<out dir>] [--skin <dir>] [--use run|menu] [--all] [--fps 12] [--cell 320]
  <model>   pack path without extension, e.g. DV3/character/dragon/fire_00_adult/fire_00_adult
  --skin    folder of redrawn skins made by rig_skin.py; without it the pack's own skin is drawn
  --use     only the animations of a run (move, skill) or of the menus (idle); default both
  --all     every animation the model has, uncapped, ignoring the game's filter
  --fps     frame rate an animation is sampled at before its frame cap applies; it keeps its own length
  --cell    size of a frame in pixels; all animations share one scale

Output: <out dir>/<animation>.gif and all.gif (the chosen animations in a row), default <assets>/generated/preview/<name>
"""
import argparse
import json
import os
import tempfile

from PIL import Image

from common import GENERATED, render
from pet_animations import USES, frame_count, wanted

GROUND = (38, 41, 54)  # the flat colour behind the model
MAX_FRAMES = 48


def animations(model, tmp):
    """[(name, seconds)] of the model, in the order the pack lists them"""
    sheet = os.path.join(tmp, "sheet.png")
    render("--sheet", sheet, os.path.dirname(model), "^" + os.path.basename(model) + "$", "64", "1")
    info = json.load(open(sheet.replace(".png", ".json")))
    return [(name, seconds) for name, seconds in info[0]["anims"]]


def frames(model, name, count, cell, fit, tmp):
    strip = os.path.join(tmp, name + ".png")
    render("--strip", strip, model, name, str(count), str(cell), fit)
    sheet = Image.open(strip).convert("RGBA")
    out = []
    for k in range(count):
        frame = Image.new("RGBA", (cell, cell), GROUND + (255,))
        frame.alpha_composite(sheet.crop((k * cell, 0, (k + 1) * cell, cell)))
        out.append(frame.convert("RGB"))
    return out


def save(path, pictures, step):
    """a looping GIF showing each picture for `step` milliseconds"""
    pictures[0].save(path, save_all=True, append_images=pictures[1:], duration=step, loop=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("model")
    parser.add_argument("out", nargs="?")
    parser.add_argument("--skin")
    parser.add_argument("--use", choices=USES)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--cell", type=int, default=320)
    args = parser.parse_args()
    out = args.out or os.path.join(GENERATED, "preview", os.path.basename(args.model))
    os.makedirs(out, exist_ok=True)
    if args.skin:
        os.environ["SPINE_OVERLAY"] = os.path.abspath(args.skin)

    tick = round(1000 / args.fps)
    with tempfile.TemporaryDirectory() as tmp:
        lengths = dict(animations(args.model, tmp))
        names = list(lengths) if args.all else wanted(lengths, args.use)
        if not names:
            raise SystemExit(f"{args.model} has none of the animations the game uses; it has: {', '.join(lengths)}")
        left_out = [n for n in lengths if n not in names]
        fit = ",".join(names)  # one scale for the chosen animations, so the pet does not change size between them
        row = []
        for name in names:
            seconds = lengths[name]
            count = max(2, min(MAX_FRAMES, round(seconds * args.fps))) if args.all else frame_count(name, seconds, args.fps)
            pictures = frames(args.model, name, count, args.cell, fit, tmp)
            save(os.path.join(out, name + ".gif"), pictures, round(seconds * 1000 / count))
            # all.gif runs on one clock: each animation is laid out in ticks, holding a frame when it has fewer
            ticks = max(count, round(seconds * args.fps))
            row.append([pictures[k * count // ticks] for k in range(ticks)])
            print(f"{name}: {count} frames, {seconds:.2f}s")
        if left_out:
            print("filtered out: " + ", ".join(left_out))
    # the chosen animations side by side, each looping at its own length
    longest = max(len(p) for p in row)
    together = []
    for k in range(longest):
        frame = Image.new("RGB", (args.cell * len(row), args.cell), GROUND)
        for i, pictures in enumerate(row):
            frame.paste(pictures[k % len(pictures)], (i * args.cell, 0))
        together.append(frame)
    save(os.path.join(out, "all.gif"), together, tick)
    print(out)


if __name__ == "__main__":
    main()
