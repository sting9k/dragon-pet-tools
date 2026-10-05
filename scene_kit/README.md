# scene_kit

The few pictures a skill demo needs that are neither pack art nor skill effects. All of them were drawn by
code for the first version of the game; nothing here comes from the asset pack.

| File | Holds |
|---|---|
| `ground.png` | a 256x256 grass tile, repeated to cover the scene |
| `fx.png`, `fx.json` | `shadow` (under pets and enemies), `digits` (0-9 for damage numbers), `scorch` (burn mark on the ground), `puff` (6-frame smoke when an enemy dies), `hit` (4-frame hit spark) |

`scene.py` loads them with `kit()` and `ground()`. Demos need these files; do not delete them.
