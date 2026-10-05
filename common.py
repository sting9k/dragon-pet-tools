"""Paths and helpers shared by the tools in this folder."""
import os
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))


def load_env(path):
    """reads KEY=VALUE lines of a .env file into the environment; what is already set there wins"""
    if not os.path.isfile(path):
        return
    for line in open(path, encoding="utf-8"):
        name, mark, value = line.strip().partition("=")
        if mark and name and not name.startswith("#"):
            os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


load_env(os.path.join(TOOLS, ".env"))  # keys and paths of this machine; the file is git-ignored
ASSETS = os.path.abspath(os.environ.get("ASSETS_DIR") or os.path.join(TOOLS, "../../assets"))
PACK_SPINE = os.path.join(ASSETS, "pack/spine")
GENERATED = os.path.join(ASSETS, "generated")


def render(*args):
    """runs spine/render.mjs; its paths are relative to the pack's spine folder"""
    done = subprocess.run(["node", os.path.join(TOOLS, "spine/render.mjs"), *args], capture_output=True, text=True)
    if done.returncode:
        sys.exit("spine/render.mjs failed: " + (done.stderr.strip() or done.stdout.strip()))


def secret(name):
    """a key or endpoint from the environment or the git-ignored .env; it is never written anywhere else"""
    return os.environ.get(name) or sys.exit(f"set {name} in .env (see .env.example)")


def curl(*args, timeout):
    """the body a curl call answers with; a failure reports curl's own message, never the arguments (they hold the key)"""
    done = subprocess.run(["curl", "-sS", "-m", str(timeout), *args], capture_output=True, text=True)
    if done.returncode:
        sys.exit("the request failed: " + done.stderr.strip())
    return done.stdout
