# Ví dụ prompt hiệu ứng

Bốn prompt đã dùng cho skill "Hắc Viêm Diệt Ấn" của Darknix, mỗi cái ra một sheet 2 hàng 3 cột (6 khung). Dùng làm mẫu khi viết `pets/<pet>/prompts/<tên>.txt` cho pet khác; đừng chép nguyên cho skill khác.

## fx_seal

Thứ nằm trên mặt đất, tả như nhìn thẳng từ trên xuống. Trong `pet.json`: `mode` `cast`, `align` `center`, `qc` `false` vì ấn cố ý vẽ sát ô.

```
Pixel-art game effect sprite sheet, exactly a 2 rows by 3 columns grid of six equal cells, one animation of a dark fire summoning seal seen exactly from above (a perfect circle), six frames read left to right, top to bottom: frame 1 a thin glowing orange ring only, frame 2 the ring plus a second inner ring and five short claw-like rune strokes, frame 3 the full seal: double ring, a five-pointed jagged star of lava cracks, sharp abstract dragon-claw glyphs between the rings, frame 4 the same full seal burning brighter with small flames licking along the outer ring, frame 5 the same seal at maximum brightness, cracks white-hot, flames taller on the ring, frame 6 the seal breaking into glowing fragments and embers.
The seal is the same size and centred in every cell, filling about 70% of the cell; nothing touches or crosses a cell edge. No characters, no ground, only the seal.
Palette: black, charcoal, deep crimson, bright orange, yellow-white core, with small accents of dark violet. Crisp chunky pixel art, hard edges, no soft glow haze, no blur.
Solid flat magenta #FF00FF background, no gradients, no grid lines, no borders, no text, no letters.
```

## fx_pillar

Thứ mọc từ đất lên, nhìn ngang, gốc ở giữa đáy ô. Trong `pet.json`: `mode` `cast`, `align` `bottom`.

```
Pixel-art game effect sprite sheet, exactly a 2 rows by 3 columns grid of six equal cells, one animation of a pillar of black fire and lava erupting straight up from the ground, side view, six frames read left to right, top to bottom: frame 1 a glowing crack and a few sparks at the bottom centre, frame 2 a short burst of lava shooting up, frame 3 a tall narrow column of black flame with a white-hot orange core reaching most of the cell height, frame 4 the column at full height and widest, crowned with a jagged horned flame shape, rocks and embers flying out sideways, frame 5 the column thinning and tearing into separate black flames, frame 6 thin black smoke and falling embers.
The base of the pillar is at the same bottom-centre point in every cell; the pillar stays inside the central 70% of the cell and nothing touches or crosses a cell edge. No characters, no ground.
Palette: black, charcoal, deep crimson, bright orange, yellow-white core, with small accents of dark violet. Crisp chunky pixel art, hard edges, no soft glow haze, no blur.
Solid flat magenta #FF00FF background, no gradients, no grid lines, no borders, no text, no letters.
```

## fx_nova

Vụ nổ, tâm cố định giữa ô. Trong `pet.json`: `mode` `impact`, `align` `center`.

```
Pixel-art game effect sprite sheet, exactly a 2 rows by 3 columns grid of six equal cells, one animation of a huge black-sun explosion, six frames read left to right, top to bottom: frame 1 a small black sphere with a thin white-hot orange rim, frame 2 the black sphere larger with crimson lightning crawling over it, frame 3 the sphere bursting: a white-hot core with a wide crown of black and crimson flame spikes, frame 4 the largest burst, a jagged ring of black fire around an orange core with a sharp circular shockwave ring and flying debris, frame 5 the ring of fire torn open into separate black flames and crimson arcs, core gone, frame 6 scattered black smoke curls and a few dying embers.
Every frame is centred on the same point and stays inside the central 72% of its cell; nothing touches or crosses a cell edge.
Palette: black, charcoal, deep crimson, bright orange, yellow-white core, with small accents of dark violet. Crisp chunky pixel art, hard edges, no soft glow haze, no blur.
Solid flat magenta #FF00FF background, no gradients, no grid lines, no borders, no text, no letters.
```

## fx_curse

Dấu nhỏ lặp vòng. Lượt đầu model trả nền đen kèm quầng sáng; bản dưới đã thêm câu cấm quầng sáng và nhấn nền hồng. Trong `pet.json`: `mode` `idle`, `align` `center`, `cell` 128.

```
Pixel-art game icon sprite sheet, exactly a 2 rows by 3 columns grid of six equal cells, one looping animation of a small curse mark that floats above an enemy: a horned dragon skull seen from the front, charcoal grey bone with a thick bright orange outline, two glowing crimson eyes, small black-and-orange flames rising from the horns. Six frames read left to right, top to bottom. The skull keeps the same size and position in every cell; only the flames on the horns flicker through six different shapes and the eyes pulse from dim red to bright yellow-red and back.
The skull is centred and fills about 50% of its cell; nothing touches or crosses a cell edge.
Flat colours only: absolutely no glow, no aura, no halo, no soft light, no shadow around the skull. Crisp chunky pixel art with hard edges.
The background of the whole image is one solid flat magenta colour #FF00FF, not black, with no gradients, no grid lines, no borders, no text.
```
