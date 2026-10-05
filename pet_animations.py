"""Which animations of a pack pet the game uses. This is the single place the choice is made.

Decided 2026-10-06: pets cannot be hurt or killed and have no basic attack, they only cast their skill,
and performance comes first. So a pet in a run needs two animations, and one more outside runs.
The pack's models keep all their animations; anything not listed here is filtered out when a pet is
previewed or baked, never deleted from the pack.

  move   in a run: the pet follows the hero
  skill  in a run: the body motion of the skill; the effect itself is a separate sprite sheet
  idle   outside runs only: lobby, dragon camp, collection, pet selection

Left out and what stands in for them:
  attack   no basic attack exists
  hit      pets are immortal
  die      pets are immortal
  holding  the original game's "carried" pose, no such feature here
  touch    petting reaction; add it back here if the dragon camp ever gets that feature
"""

# name -> where it is used and the most frames it may be baked to.
# An animation longer than its cap is sampled evenly across its whole length, so it keeps its duration.
PET_ANIMATIONS = {
    "move": {"use": "run", "max_frames": 10},
    "skill": {"use": "run", "max_frames": 10},
    "idle": {"use": "menu", "max_frames": 14},
}
USES = ("run", "menu")


def wanted(names, use=None):
    """the animations of `names` the game keeps, in the order above; `use` narrows it to run or menu"""
    return [n for n, rule in PET_ANIMATIONS.items() if n in names and use in (None, rule["use"])]


def frame_count(name, seconds, fps):
    """how many frames to bake for one animation: its length at `fps`, at least 2, at most its cap"""
    return max(2, min(PET_ANIMATIONS[name]["max_frames"], round(seconds * fps)))
