#!/usr/bin/env python3
"""EXAMPLE ONLY: the skill demo of one pet (Darknix, skill level 5, "Hắc Viêm Diệt Ấn"), kept as a reference.

Read this before touching the file
----------------------------------
* This file is NOT a tool and NOT a template to fill in. It is the script one agent wrote for one pet's one
  skill. Everything below the imports (positions, timeline, what hits whom) is specific to that skill.
* Do not import it, do not extend it, do not add a second pet to it, do not rename it for another pet.
  For a new pet, write a new file demo_<pet>.py of your own. Take from here only the WAY it is built:
  the order of the sections, how frames are loaded, how the tick loop is laid out, the layering.
* It cannot run from a fresh clone: its inputs are per-pet content that is not stored in the repository.
  To run it you first make them (README, "Hướng dẫn cho agent"):
      pets/darknix/pet.json + prompts/   the pet's config and effect prompts (written by the agent)
      python3 pet.py darknix reskin      the redrawn body          -> <assets>/generated/pets
      python3 pet.py darknix rig         the body on the skeleton  -> <assets>/generated/rigged
      python3 pet.py darknix fx --draw   the four effect sheets    -> pets/darknix/fx
  Then: python3 pet.py darknix demo   (or: python3 demo_darknix.py [<out.gif>])
  Output: <assets>/generated/demo/darknix_skill_lv5.gif

What a demo script is made of (keep these five parts, in this order, in your own script)
---------------------------------------------------------------------------------------
  1. CONSTANTS   the scene size, where things stand, and the timeline in ticks
  2. THE CAST    which enemies stand where (a seeded random layout, so every run gives the same clip)
  3. LOADING     pet frames, enemy sprites, effect frames, kit sprites: all through scene.py
  4. STATE       what changes over time: enemy positions, who was hit when, who is dead, floating numbers
  5. THE LOOP    one pass per tick: apply the timeline to the state, then draw the layers bottom to top

The skill shown here, as the player should read it
--------------------------------------------------
  a. a seal of black fire burns into the ground under the horde and turns        (fx_seal, on the ground)
  b. five pillars of black fire erupt on its rim, one after another               (fx_pillar, standing)
  c. the horde is dragged to the centre, where a black sun swells and bursts      (fx_nova, in the air)
  d. whatever survives carries a curse mark over its head                         (fx_curse, looping)

Rules a demo must follow (the user rejected clips that broke them)
------------------------------------------------------------------
  * never dim, tint or wash the whole screen during a skill
  * no soft additive glow sprites: they blur and break the pixel look
  * scale pixel art with Image.NEAREST only
  * do not draw creatures or effects by code: bodies come from the pack, effects from the drawn sheets
"""
import math
import os
import random
import sys

from PIL import Image

from common import GENERATED
from scene import effect, faded, ground, kit, number, pack_frames, pack_sprite, put, save_gif, white

# ---------------------------------------------------------------------------------------------------------
# 1. CONSTANTS
# ---------------------------------------------------------------------------------------------------------
PET = "darknix"                                                   # folder under pets/ holding the effect frames
MODEL = "DV3/character/dragon/darknix_00_adult/darknix_00_adult"  # pack path of the pet, without extension
MONSTER = "character/monster/monster_{0}/monster_{0}"             # where the pack keeps its monsters

# The horde: pack monster -> (the animation it walks with, its longer side on screen in pixels).
# Monsters of the pack walk with "run" or, when they have none, "idle"; check with render.mjs --sheet.
FOES = {"pinkslime": ("run", 34), "fairyghost_fire": ("idle", 38), "cymbalist": ("run", 42), "bubblepenguin": ("run", 42),
        "poctopus": ("run", 44), "darkmurderer_dark": ("idle", 80), "treemonster": ("run", 66)}
TOUGH = "treemonster"        # the kind that survives the skill, so the curse mark has someone to sit on

W, H, FPS = 640, 400, 20     # the scene in pixels, and ticks per second
CENTRE = (410, 220)          # middle of the seal, a point on the ground
SEAL = (300, 150)            # the seal as it lies on the ground: a circle seen at a slant, so half as high as wide
DRAGON = (118, 300)          # where the dragon's feet stand
# The pack's own "skill" animation of this dragon carries a wide glyph above its head. The cell must be large
# enough to hold body and glyph at one scale, or the glyph is cut off; 560 gives a body about 170 px tall.
DRAGON_CELL = 560

# The timeline. One tick is 1/FPS second. Laying it out as named constants keeps the loop readable and
# makes retiming a matter of changing numbers here.
SKILL_AT, SKILL_TICKS = 6, 33                     # the dragon's cast animation: start, and how long it plays
SEAL_AT = 10                                      # the seal starts to draw itself
PILLAR_AT, PILLAR_GAP, PILLAR_TICKS = 26, 3, 12   # first pillar, ticks between pillars, life of one pillar
PULL_AT, SUN_AT, BURST_AT = 42, 44, 54            # the horde is dragged in, the sun appears, the sun bursts
STOP = 3                                          # extra ticks the burst frame is held (hit-stop)
END = 96                                          # length of the clip in shown frames


# ---------------------------------------------------------------------------------------------------------
# 2. THE CAST
# ---------------------------------------------------------------------------------------------------------
def horde(rng):
    """The enemies standing on and around the seal, each as a mutable [kind, x, y, tough].

    The small ones are scattered evenly over a disc a little larger than the seal (sqrt gives an even
    spread over the area). The tough ones are placed by hand so that the survivors end up well apart."""
    kinds = [k for k in FOES if k != TOUGH]
    out = []
    for k in range(22):
        a, r = rng.uniform(0, math.tau), math.sqrt(rng.uniform(0.02, 1)) * 1.15
        out.append([kinds[k % len(kinds)], CENTRE[0] + math.cos(a) * r * SEAL[0] / 2, CENTRE[1] + math.sin(a) * r * SEAL[1] / 2, False])
    for dx, dy in ((-70, 34), (88, -22), (20, 48)):
        out.append([TOUGH, CENTRE[0] + dx, CENTRE[1] + dy, True])
    return out


def main(out):
    rng = random.Random(7)  # a fixed seed: the same clip on every run, so two renders can be compared

    # -----------------------------------------------------------------------------------------------------
    # 3. LOADING
    # -----------------------------------------------------------------------------------------------------
    fx = kit()  # code-drawn sprites of scene_kit: shadow, digits, scorch, puff, hit
    foes = {name: pack_sprite(MONSTER.format(name), anim, 6, size) for name, (anim, size) in FOES.items()}
    # Effect frames, six each, scaled to the size they have on screen. Sizes were found by looking at the
    # clip: the seal must cover the horde, a pillar must tower over an enemy, the sun must fill the seal.
    seal, pillar = effect(PET, "fx_seal", 512), effect(PET, "fx_pillar", 230)
    nova, curse = effect(PET, "fx_nova", 420), effect(PET, "fx_curse", 64)
    # The pet with its redrawn skin. Both animations share one scale ("idle,skill"), so the body does not
    # change size when the cast starts.
    skin = os.path.join(GENERATED, "rigged")
    idle = pack_frames(MODEL, "idle", 8, DRAGON_CELL, "idle,skill", skin)
    skill = pack_frames(MODEL, "skill", 10, DRAGON_CELL, "idle,skill", skin)
    # Where the body stands inside its cell, as shares of the cell: used as the anchor when drawing, so
    # DRAGON is the point under its feet no matter how much empty cell surrounds it.
    left, _, right, bottom = idle[0].getbbox()
    feet = ((left + right) / 2 / DRAGON_CELL, bottom / DRAGON_CELL)
    shadow = fx["shadow"][0].resize((40, 16), Image.NEAREST)

    # -----------------------------------------------------------------------------------------------------
    # 4. STATE
    # -----------------------------------------------------------------------------------------------------
    enemies = horde(rng)
    home = [(e[1], e[2]) for e in enemies]  # where each enemy started; the pull and the throw-back move between home and CENTRE
    hurt = [-99] * len(enemies)             # the tick each enemy was last hit, for the white flash
    dead = [None] * len(enemies)            # the tick it died, for the smoke puff
    texts = []                              # floating damage numbers: [tick born, x, y, picture]
    # The five pillars stand on the rim of the seal, at the points of a pentagon, the first one at the top.
    rim = [(CENTRE[0] + math.cos(math.tau * k / 5 - math.pi / 2) * SEAL[0] * 0.43,
            CENTRE[1] + math.sin(math.tau * k / 5 - math.pi / 2) * SEAL[1] * 0.43) for k in range(5)]

    def strike(tick, k, value, big=False):
        """enemy k takes a hit: it flashes, and a number rises from it"""
        hurt[k] = tick
        x, y = home[k] if big else enemies[k][1:3]  # the burst finds the horde in a heap, so its numbers go where each foe stood
        if big and k % 3 and not enemies[k][3]:
            return  # a number for every foe would bury the burst; every third one is enough to read
        texts.append([tick, x + rng.uniform(-6, 6), y - 34, number(fx["digits"], value, 3 if big else 2, (255, 214, 92) if big else (255, 255, 255))])

    # -----------------------------------------------------------------------------------------------------
    # 5. THE LOOP: one pass per tick. First the timeline changes the state, then the layers are drawn
    #    bottom to top: ground -> marks on the ground -> things standing on it (sorted by y) -> effects in
    #    the air -> marks over heads and damage numbers -> screen shake.
    # -----------------------------------------------------------------------------------------------------
    floor = ground(W, H)
    frames = []
    tick = shown = 0
    while shown < END:
        t = tick
        canvas = floor.copy()

        # --- marks on the ground -------------------------------------------------------------------------
        # The seal: frames 1-3 draw it in (5 ticks each), frames 4-5 alternate while it burns, frame 6 is
        # its break-up after the burst. It is turned a little every tick, then squashed to lie on the ground.
        if SEAL_AT <= t < BURST_AT + 14:
            age = t - SEAL_AT
            k = min(age // 5, 2) if age < 15 else (3 + (t // 3) % 2 if t < BURST_AT else 5)
            turned = seal[k].rotate(-age * 2.2, Image.NEAREST)
            flat = turned.resize((round(SEAL[0] * 1.42), round(SEAL[1] * 1.42)), Image.NEAREST)
            if t >= BURST_AT + 8:  # fade the broken seal out over six ticks
                flat.putalpha(flat.getchannel("A").point(lambda a, f=1 - (t - BURST_AT - 8) / 6: int(a * f)))
            put(canvas, flat, *CENTRE)
        if t >= BURST_AT:  # the burst leaves a burn mark
            put(canvas, fx["scorch"][0].resize((170, 96), Image.NEAREST), CENTRE[0], CENTRE[1] + 4)

        # --- the timeline acts on the horde --------------------------------------------------------------
        # A pillar hurts whoever stands near its foot, four ticks after it starts (when the flame is tall).
        # The reach is wider sideways than in depth, because the ground is seen at a slant.
        for p, (px, py) in enumerate(rim):
            if t == PILLAR_AT + p * PILLAR_GAP + 4:
                for k, e in enumerate(enemies):
                    if dead[k] is None and math.hypot((e[1] - px) / 1.6, e[2] - py) < 46:
                        strike(t, k, rng.randint(840, 990))
        # The pull: every enemy slides from home toward the centre, slowly at first, then fast.
        if PULL_AT <= t < BURST_AT:
            pull = ((t - PULL_AT + 1) / (BURST_AT - PULL_AT)) ** 2 * 0.82
            for k, e in enumerate(enemies):
                e[1], e[2] = home[k][0] + (CENTRE[0] - home[k][0]) * pull, home[k][1] + (CENTRE[1] - home[k][1]) * pull
        # The burst: everyone is hit; all but the tough ones die two ticks later.
        if t == BURST_AT:
            for k, e in enumerate(enemies):
                strike(t, k, rng.randint(4200, 4990), big=True)
                if not e[3]:
                    dead[k] = t + 2
        # After the burst the survivors are thrown back to where they stood.
        if BURST_AT < t <= BURST_AT + 6:
            back = 0.82 * (1 - (t - BURST_AT) / 6)
            for k, e in enumerate(enemies):
                if e[3]:
                    e[1], e[2] = home[k][0] + (CENTRE[0] - home[k][0]) * back, home[k][1] + (CENTRE[1] - home[k][1]) * back

        # --- everything that stands on the ground --------------------------------------------------------
        # Collected with the y of its feet and drawn back to front, so that whatever stands lower on the
        # screen covers what stands behind it. Pillars are in this list too: an enemy in front hides a pillar's foot.
        things = [(DRAGON[1], "dragon", None)]
        things += [(e[2], "enemy", k) for k, e in enumerate(enemies) if dead[k] is None or t < dead[k] + 6]
        things += [(py, "pillar", p) for p, (px, py) in enumerate(rim) if 0 <= t - PILLAR_AT - p * PILLAR_GAP < PILLAR_TICKS]
        for y, kind, k in sorted(things, key=lambda th: th[0]):
            if kind == "dragon":
                put(canvas, fx["shadow"][0].resize((120, 32), Image.NEAREST), DRAGON[0], DRAGON[1] - 4)
                # the cast animation plays once across SKILL_TICKS; before and after it the dragon idles
                casting = SKILL_AT <= t < SKILL_AT + SKILL_TICKS
                frame = skill[(t - SKILL_AT) * len(skill) // SKILL_TICKS] if casting else idle[(t // 3) % len(idle)]
                put(canvas, frame, *DRAGON, *feet)
            elif kind == "enemy":
                e = enemies[k]
                look = foes[e[0]]
                sprite = look[(t // 3 + k) % len(look)]  # "+ k" so the horde does not step in unison
                if dead[k] is not None and t >= dead[k]:  # dead: six ticks of smoke instead of the body
                    put(canvas, fx["puff"][min(t - dead[k], 5)].resize((56, 56), Image.NEAREST), e[1], e[2] - 14)
                    continue
                put(canvas, shadow, e[1], e[2])
                if t - hurt[k] < 3:  # three ticks of white flash after a hit, fading
                    sprite = white(sprite, 0.85 - 0.25 * (t - hurt[k]))
                jolt = rng.uniform(-2, 2) if PULL_AT <= t < BURST_AT else 0  # it trembles while being dragged
                put(canvas, sprite, e[1] + jolt, e[2], 0.5, 0.96)
            else:  # a pillar: its six frames spread over its life, anchored at its foot
                px, py = rim[k]
                put(canvas, pillar[(t - PILLAR_AT - k * PILLAR_GAP) * 6 // PILLAR_TICKS], px, py + 12, 0.5, 0.93)

        # --- effects in the air --------------------------------------------------------------------------
        # The black sun hangs a little above the centre. Frames 1-2 are the sun, grown by scaling as it
        # swells; frames 3-6 are the burst, four ticks each.
        if SUN_AT <= t < BURST_AT:
            grow = (t - SUN_AT) / (BURST_AT - SUN_AT)
            size = round(150 + 190 * grow)
            put(canvas, nova[0 if grow < 0.45 else 1].resize((size, size), Image.NEAREST), CENTRE[0], CENTRE[1] - 46)
        elif BURST_AT <= t < BURST_AT + 16:
            age = t - BURST_AT
            put(canvas, nova[min(2 + age // 4, 5)], CENTRE[0], CENTRE[1] - 46)

        # --- marks over heads, then damage numbers (always on top) ---------------------------------------
        if t >= BURST_AT + 8:
            for k, e in enumerate(enemies):
                if e[3]:  # the curse mark loops and bobs over each survivor
                    put(canvas, curse[(t // 2) % len(curse)], e[1], e[2] - 62 + math.sin(t * 0.4 + k) * 2)
        for born, x, y, picture in texts:  # a number rises for 14 ticks and fades over its last six
            age = t - born
            if 0 <= age < 14:
                put(canvas, picture if age < 9 else faded(picture, 1 - (age - 8) / 6), x, y - age * 2.2)

        # --- impact: screen shake and hit-stop -----------------------------------------------------------
        # The whole picture is shifted a few pixels for eight ticks, less each tick. It is pasted onto a copy
        # of itself so the edge the shift uncovers still shows ground instead of a black bar.
        if BURST_AT <= t < BURST_AT + 8:
            reach = 7 * (1 - (t - BURST_AT) / 8)
            moved = canvas.copy()
            moved.paste(canvas, (round(rng.uniform(-reach, reach)), round(rng.uniform(-reach, reach))))
            canvas = moved
        # Hit-stop: the burst frame is shown STOP extra times while the timeline stands still.
        hold = STOP if t == BURST_AT else 0
        for _ in range(1 + hold):
            frames.append(canvas.convert("RGB"))
            shown += 1
        tick += 1

    save_gif(out, frames, FPS)
    print(f"{out}: {len(frames)} frames, {len(frames) / FPS:.1f}s")
    # Next step for the agent: look at the result, e.g.
    #   python3 peek_gif.py <out.gif> /tmp/peek.png 0.6,1.7,2.1,2.6,2.9,4.5
    # and check each phase before showing it to the user.


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(GENERATED, "demo/darknix_skill_lv5.gif"))
