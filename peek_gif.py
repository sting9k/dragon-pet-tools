#!/usr/bin/env python3
"""Lays chosen moments of a GIF side by side in one PNG, to judge an animation without playing it.

Usage: python3 peek_gif.py <in.gif> <out.png> [<seconds>,<seconds>,...] [--cols 3]
  Without a list of moments, eight evenly spaced ones are taken.
"""
import sys

from PIL import Image


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        sys.exit(__doc__)
    cols = int(sys.argv[sys.argv.index("--cols") + 1]) if "--cols" in sys.argv else 3
    if "--cols" in sys.argv:
        args.remove(str(cols))
    gif = Image.open(args[0])
    starts, clock = [], 0  # when each stored frame begins, in milliseconds
    for k in range(gif.n_frames):
        gif.seek(k)
        starts.append(clock)
        clock += gif.info.get("duration", 50)
    moments = [float(m) for m in args[2].split(",")] if len(args) > 2 else [clock / 1000 * (k + 0.5) / 8 for k in range(8)]
    width, height = gif.size
    sheet = Image.new("RGB", (width * min(cols, len(moments)), height * -(-len(moments) // cols)))
    for k, moment in enumerate(moments):
        gif.seek(max(i for i, start in enumerate(starts) if start <= moment * 1000 or i == 0))
        sheet.paste(gif.convert("RGB"), ((k % cols) * width, (k // cols) * height))
    sheet.save(args[1])
    print(f"{args[1]}: {len(moments)} moments of {clock / 1000:.1f}s ({gif.n_frames} stored frames)")


if __name__ == "__main__":
    main()
