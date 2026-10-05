#!/usr/bin/env python3
"""One pet from the pack to a redrawn, rigged pet with skill effects: every step behind one command.

Usage: python3 pet.py <pet> <step> [options]
  <pet>   a folder under pets/, e.g. darknix; its pet.json names the pack model, the description for the
          redraw and the effect sheets of its skill

Steps, in the order they are normally run:
  reference   build the picture the image model is shown, and print the prompt (no API call)
  reskin      redraw the pet with the image model                      needs RESKIN_KEY, RESKIN_API
  rig         cut the redraw onto the pack's own skeleton
  preview     GIFs of the animations the game uses, with the new skin
  fx          cut the effect sheets in pets/<pet>/raw into frames and GIFs
              --draw   first draw every sheet that has a prompt but no raw picture   needs IMAGE_KEY, IMAGE_API
              --redraw NAME   draw that one sheet again, replacing its raw picture   needs IMAGE_KEY, IMAGE_API
  demo        the skill demo GIF, when demo_<pet>.py exists
  all         reskin, rig, preview, fx --draw, demo

Where things go: redraws, rigged skins, previews and demo GIFs under <assets>/generated (they hold pack art,
keep them out of a public repository); effect sheets and their frames under pets/<pet>/ (they are ours).
"""
import json
import os
import subprocess
import sys

from common import GENERATED, TOOLS

FORGE = os.path.join(TOOLS, "sprite-forge/skills/generate2dsprite/scripts")


def run(*args):
    """one of the tools in this folder, stopping the whole run if it fails"""
    done = subprocess.run([sys.executable, *args], cwd=TOOLS)
    if done.returncode:
        sys.exit(done.returncode)


def load(pet):
    folder = os.path.join(TOOLS, "pets", pet)
    path = os.path.join(folder, "pet.json")
    if not os.path.isfile(path):
        have = sorted(d for d in os.listdir(os.path.join(TOOLS, "pets")) if os.path.isfile(os.path.join(TOOLS, "pets", d, "pet.json")))
        sys.exit(f"no pets/{pet}/pet.json; pets here: {', '.join(have) or 'none'}")
    info = json.load(open(path, encoding="utf-8"))
    info["folder"], info["name"] = folder, os.path.basename(info["model"])
    return info


def reference(info):
    run("gen_pet.py", info["model"], info["description"], "--dry")


def reskin(info):
    run("gen_pet.py", info["model"], info["description"])


def rig(info):
    picture = os.path.join(GENERATED, "pets", info["name"] + ".png")
    if not os.path.isfile(picture):
        sys.exit(f"no redraw at {picture}; run the reskin step first")
    run("rig_skin.py", f"{info['model']}/{info['name']}", picture)


def preview(info):
    run("preview_pet.py", f"{info['model']}/{info['name']}", "--skin", os.path.join(GENERATED, "rigged"))


def fx(info, draw=False, redraw=None):
    """each effect sheet of pet.json: drawn if asked, then cut into pets/<pet>/fx/<name>/"""
    if redraw and redraw not in info["fx"]:
        sys.exit(f"{redraw} is not an effect of this pet; it has: {', '.join(info['fx'])}")
    for name, rule in info["fx"].items():
        prompt = os.path.join(info["folder"], "prompts", name + ".txt")
        raw = os.path.join(info["folder"], "raw", name + ".png")
        if name == redraw or (draw and not os.path.isfile(raw)):
            wide = rule["cols"] != rule["rows"]
            run(os.path.join(FORGE, "image_api.py"), "--prompt-file", prompt, "--out", raw, "--aspect", f"{rule['cols']}:{rule['rows']}" if wide else "1:1")
            os.remove(raw + ".prompt.txt")  # the prompt already lives in prompts/
        if not os.path.isfile(raw):
            print(f"{name}: no raw sheet yet, skipped (use --draw)")
            continue
        args = ["process", "--input", raw, "--target", "asset", "--mode", rule["mode"], "--rows", str(rule["rows"]), "--cols", str(rule["cols"]),
                "--cell-size", str(rule["cell"]), "--output-dir", os.path.join(info["folder"], "fx", name),
                "--scale-strategy", "preserve", "--align", rule["align"], "--duration", "110", "--prompt-file", prompt]
        if rule.get("qc", True):
            args.append("--strict-qc")
        run("-W", "ignore", os.path.join(FORGE, "generate2dsprite.py"), *args)


def demo(info):
    script = f"demo_{os.path.basename(info['folder'])}.py"
    if not os.path.isfile(os.path.join(TOOLS, script)):
        sys.exit(f"this pet has no {script} yet")
    run(script)


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    info, step, options = load(args[0]), args[1], args[2:]
    redraw = options[options.index("--redraw") + 1] if "--redraw" in options and options.index("--redraw") + 1 < len(options) else None
    steps = {
        "reference": lambda: reference(info),
        "reskin": lambda: reskin(info),
        "rig": lambda: rig(info),
        "preview": lambda: preview(info),
        "fx": lambda: fx(info, draw="--draw" in options, redraw=redraw),
        "demo": lambda: demo(info),
    }
    if step == "all":
        for name in ("reskin", "rig", "preview"):
            steps[name]()
        fx(info, draw=True)
        demo(info)
    elif step in steps:
        steps[step]()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
