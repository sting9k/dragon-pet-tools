#!/usr/bin/env python3
"""Gives a pack pet a redrawn skin while keeping its Spine skeleton, so every animation still plays.

Input: a picture of the whole pet redrawn in its contact-sheet pose (what gen_pet.py produces).
The pack's own rig is the cutting guide. spine/render.mjs reports where every triangle of every part
lies in that pose and where the same triangle sits on the atlas page; here each atlas texel is
filled with the colour the redrawn picture has at the matching spot. A part of the body that is
covered by another part in the pose has no colour in the picture, so it takes the nearest colour of
its own part instead. The new atlas is the old one SCALE times larger; the .skel is copied as is.

Usage: python3 rig_skin.py <model> <picture.png> [<out dir>]
  <model>  pack path without extension, e.g. DV3/character/dragon/fire_00_adult/fire_00_adult
Output: <out dir>/<model>.{skel,atlas,png} (default <assets>/generated/rigged); spine/render.mjs draws the
new skin instead of the pack's when run with SPINE_OVERLAY=<out dir>
"""
import json
import os
import re
import shutil
import sys
import tempfile

import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion, distance_transform_edt, gaussian_filter, label, map_coordinates

from common import GENERATED, PACK_SPINE, render
from gen_pet import CELL, MARGIN, PASTE, SIDE

SCALE = 8     # new atlas pixels per old one, at most; a large atlas gets less so it stays a legal texture
LIMIT = 4096  # longest side a texture may have
FINE = 2      # the pose is examined at this many samples per cell pixel


def drawn(rgb, ground):
    return np.abs(rgb.astype(int) - np.asarray(ground, int)).sum(-1) > 40


def box(mask):
    ys, xs = np.nonzero(mask)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def inside(px, py, tri):
    """barycentric weights of points in a triangle, and which points are in it"""
    (x0, y0), (x1, y1), (x2, y2) = tri
    det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(det) < 1e-9:
        return None
    a = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / det
    b = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / det
    c = 1 - a - b
    return a, b, c, (a >= -1e-4) & (b >= -1e-4) & (c >= -1e-4)


def triangles(slot):
    at, uv = np.array(slot["at"]).reshape(-1, 2), np.array(slot["uvs"]).reshape(-1, 2)
    for k in range(0, len(slot["tris"]), 3):
        i = slot["tris"][k:k + 3]
        yield at[i], uv[i]


def grid(x0, y0, x1, y1):
    ys, xs = np.mgrid[y0:y1, x0:x1]
    return xs + 0.5, ys + 0.5


def main(model, picture, out):
    src = os.path.join(PACK_SPINE, model)
    page = np.asarray(Image.open(src + ".png").convert("RGBA"))
    ph, pw = page.shape[:2]
    scale = max(1, min(SCALE, LIMIT // max(pw, ph)))
    with tempfile.TemporaryDirectory() as tmp:
        render("--rig", os.path.join(tmp, "rig.json"), model, str(CELL))
        render("--sheet", os.path.join(tmp, "pose.png"), os.path.dirname(model), "-", str(CELL), "1", "bare")
        rig = json.load(open(os.path.join(tmp, "rig.json")))
        pose = np.asarray(Image.open(os.path.join(tmp, "pose.png")).convert("RGBA"))[:CELL, :CELL, 3] >= 128
    art = np.asarray(Image.open(picture).convert("RGB")).astype(np.float32)

    # line the picture up with the pose: both show the same pet, so their outlines' boxes correspond
    px0, py0, px1, py1 = box(pose)
    ax0, ay0, ax1, ay1 = box(drawn(art, (255, 255, 255)))
    sx, sy = (ax1 - ax0) / (px1 - px0), (ay1 - ay0) / (py1 - py0)
    # gen_pet.py sends the cell enlarged to PASTE at MARGIN of a SIDE square; the answer is that square, larger
    known = art.shape[0] / SIDE * PASTE / CELL
    if abs(sx / known - 1) > 0.1 or abs(sy / known - 1) > 0.1:
        # the outlines disagree (glows and lightning make poor outlines): trust where the picture was asked to be
        sx = sy = known
        ax0, ay0, px0, py0 = MARGIN * art.shape[1] / SIDE, MARGIN * art.shape[0] / SIDE, 0, 0
    to_art = lambda x, y: (ax0 + (x - px0) * sx, ay0 + (y - py0) * sy)
    # the rim of the picture is where it fades into its white ground: colours are only taken from well inside it
    core = binary_erosion(drawn(art, (255, 255, 255)), iterations=5).astype(np.float32)

    # which part is on top at every point of the pose
    top = np.full((CELL * FINE, CELL * FINE), -1, np.int16)
    for k, slot in enumerate(rig["slots"]):
        for at, uv in triangles(slot):
            x0, y0 = np.floor(at.min(0) * FINE).astype(int).clip(0, CELL * FINE - 1)
            x1, y1 = np.ceil(at.max(0) * FINE).astype(int).clip(1, CELL * FINE)
            if x1 <= x0 or y1 <= y0:
                continue
            gx, gy = grid(x0, y0, x1, y1)
            hit = inside(gx / FINE, gy / FINE, at)
            if hit is None:
                continue
            a, b, c, ok = hit
            u, v = a * uv[0, 0] + b * uv[1, 0] + c * uv[2, 0], a * uv[0, 1] + b * uv[1, 1] + c * uv[2, 1]
            solid = page[np.clip((v * ph).astype(int), 0, ph - 1), np.clip((u * pw).astype(int), 0, pw - 1), 3] > 100
            view = top[y0:y1, x0:x1]
            view[ok & solid] = k

    # fill the new atlas from the picture wherever the part shows in the pose
    W, H = pw * scale, ph * scale
    new = np.asarray(Image.fromarray(page).resize((W, H), Image.NEAREST)).copy()
    filled = np.zeros((H, W), bool)
    posed = np.zeros((H, W), bool)  # texels that belong to a part drawn in the pose
    for k, slot in enumerate(rig["slots"]):
        for at, uv in triangles(slot):
            tex = uv * [W, H]
            x0, y0 = np.floor(tex.min(0)).astype(int).clip(0, [W - 1, H - 1])
            x1, y1 = np.ceil(tex.max(0)).astype(int).clip(1, [W, H])
            if x1 <= x0 or y1 <= y0:
                continue
            gx, gy = grid(x0, y0, x1, y1)
            hit = inside(gx, gy, tex)
            if hit is None:
                continue
            a, b, c, ok = hit
            cx, cy = a * at[0, 0] + b * at[1, 0] + c * at[2, 0], a * at[0, 1] + b * at[1, 1] + c * at[2, 1]
            seen = top[np.clip((cy * FINE).astype(int), 0, CELL * FINE - 1), np.clip((cx * FINE).astype(int), 0, CELL * FINE - 1)] == k
            qx, qy = to_art(cx, cy)
            colour = np.stack([map_coordinates(art[..., ch], [qy - 0.5, qx - 0.5], order=1, mode="nearest") for ch in range(3)], -1)
            use = ok & seen & (map_coordinates(core, [qy - 0.5, qx - 0.5], order=0, mode="constant") > 0.5)
            new[y0:y1, x0:x1, :3][use] = colour[use]
            posed[y0:y1, x0:x1][ok] = True
            filled[y0:y1, x0:x1][use] = True

    # what the pose hid: each part borrows the nearest colour it was given
    enlarge = lambda a: np.repeat(np.repeat(a, scale, 0), scale, 1)
    solid = enlarge(page[..., 3] > 0)
    islands, count = label(solid)
    _, (ny, nx) = distance_transform_edt(~filled, return_indices=True)
    same = islands[ny, nx] == islands
    hidden = solid & ~filled & same & filled[ny, nx]
    new[hidden, :3] = new[ny[hidden], nx[hidden], :3]
    alpha = enlarge(page[..., 3]).astype(np.float32)
    hard = (page[..., 3] == 0) | (page[..., 3] == 255)
    smooth = np.clip((gaussian_filter(alpha, scale * 0.45) - 110) * 4, 0, 255)  # stair-steps of the old outline eased
    new[..., 3] = np.where(enlarge(hard), smooth, alpha).astype(np.uint8)  # glows keep their own soft alpha

    dst = os.path.join(out, model)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    Image.fromarray(new).save(dst + ".png", optimize=True)
    lines = []
    for line in open(src + ".atlas").read().split("\n"):
        m = re.match(r"(size|bounds|offsets):(.*)", line)
        lines.append(f"{m[1]}:{','.join(str(int(v) * scale) for v in m[2].split(','))}" if m else line)
    open(dst + ".atlas", "w").write("\n".join(lines))
    shutil.copy(src + ".skel", dst + ".skel")
    share = filled[solid & posed].mean()
    print(f"{os.path.basename(model)}: atlas {pw}x{ph} -> {W}x{H}; {share:.0%} of the posed parts came from the picture, picture lay at {sx:.2f}x{sy:.2f}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(GENERATED, "rigged"))
