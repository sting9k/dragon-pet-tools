# Prompt vẽ lại pet

Công thức đã duyệt ngày 2026-10-05 trên rồng lửa và ba rồng sét (ảnh mẫu trong `assets/generated/pets/samples`).

## Prompt

Chỉ thay phần `{mô tả}`, giữ nguyên phần còn lại. Mô tả của mỗi pet nằm trong `pets/<pet>/pet.json` (trường `description`):

```
Redraw this small low-resolution pixel-art dragon as a large, highly detailed pixel-art illustration of the SAME dragon: {mô tả} Add rich detail: layered scales, horns, claws, wing bones, armor-like plates, sharp spikes, crisp dark outlines, hard-edged cel shading with bright highlights. Clean 16-bit JRPG boss sprite style, single character, plain flat white background, no text.
```

`{mô tả}` là một câu tiếng Anh tả đúng con đó: màu, loài, dáng, hướng mặt, màu thân và hoa văn, cánh, thứ bắt buộc phải giữ.

Các mô tả đã dùng:

| Pet | Mô tả |
|---|---|
| fire_00_adult | same red fire dragon, same side-view pose facing left, cream wing membrane and belly, flames on the head, neck and along the tail. |
| bluethunder_00_adult | same black thunder dragon, same side-view crouching pose facing left, charcoal black body with golden lightning-bolt markings, gold horns, blue eye, and wings of crackling blue-white and yellow lightning on its back. |
| lightning_00_adult | same white and red lightning dragon, same rearing pose facing left, white body, red and orange flame-like mane, horns and markings, large orange-to-yellow wings, long white tail with red ridge. |
| thunderboltdragon_00_adult | same purple thunderbolt dragon, same seated serpent-like pose facing left, deep purple body with thin golden lightning lines, golden-yellow belly plates, pale lavender feathered wings and tail fin, blue gem on the forehead. |
| aquadragon_00_adult | same blue water dragon, same side-view standing pose facing left, bright blue body with lighter blue scale patches, grey-white belly, two dark blue-grey horns, lavender wing membranes with blue wing bones, lavender fin at the tip of the tail, orange eye. |
| phoenix_00_adult | same phoenix dragon made of fire, same upright hovering pose facing left, golden-yellow body with orange and red flame patterns, a tall mane of red and orange flames on the head, wings of yellow-to-red flame feathers, long curling tail of orange fire, white claws. |
| sharkgon_00_adult | same pale aqua shark dragon, same side-view standing pose facing left, light mint-cyan body with teal shading and darker teal legs, white underside, shark-like head with a blue fin crest, pink eye, large shark dorsal fins on the back and a tall fin tail, blue fins on the chest. |
| darknix_00_adult | same dark lava dragon, same side-view standing pose facing left, same proportions, charcoal black and dark grey-brown rocky body with glowing orange-red lava cracks on the chest and belly, two dark wings with crimson and orange membranes and a yellow-orange claw at each wing tip, a glowing lava fist raised in front at the lower left, a second lava fist behind the body, glowing orange eye, orange and yellow striped claws on the feet. |

## Lưu ý

- Cỡ pixel giữa các con chưa đều: cùng prompt nhưng mô hình tự chọn độ mịn. Con nào lệch thì chạy lại.
- Mô tả phải khớp với dáng trên ảnh mẫu (`<tên>_ref.png`); chạy `gen_pet.py ... --dry` để xem ảnh mẫu trước khi viết.
