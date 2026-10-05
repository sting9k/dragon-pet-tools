# Dragon pet tools

Bộ công cụ biến một con pet của asset pack **Dragon Village** thành pet dùng được trong game: vẽ lại ở độ phân giải cao, gắn bộ da mới vào đúng bộ xương cũ, vẽ hiệu ứng skill và dựng GIF demo.

> **Chỉ dùng tốt với asset pack của game này.** Mọi công cụ dựa vào cấu trúc thư mục, tên hoạt ảnh và mô hình Spine 4.1 của pack Dragon Village (xem [Asset pack](#asset-pack)). Với pack khác, phần gọi API và phần cắt sprite sheet vẫn chạy, nhưng dựng mô hình, gắn xương, xem trước và demo sẽ không chạy nếu chưa sửa code.

Repo không chứa asset pack và không chứa ảnh nào lấy từ pack. Bạn phải tự có pack và quyền dùng nó.

**Hai loại nội dung trong repo:**

| Loại | Gồm | Ai viết |
|---|---|---|
| Công cụ cố định | `pet.py`, `gen_pet.py`, `rig_skin.py`, `preview_pet.py`, `scene.py`, `peek_gif.py`, `spine/`, `sprite-forge/`, `scene_kit/` | Viết một lần, dùng cho mọi pet |
| Nội dung riêng từng pet | `pets/<pet>/` (cấu hình, prompt, sheet hiệu ứng) và `demo_<pet>.py` (kịch bản skill) | **Do agent tạo mới cho mỗi con**, theo [Hướng dẫn cho agent](#hướng-dẫn-cho-agent). Không lưu trong repo (bị chặn trong `.gitignore`). Ngoại lệ duy nhất là `demo_darknix.py`, giữ lại làm ví dụ để đọc, không phải để dùng lại |

## Quy trình

```
pack (.skel + .atlas + .png)
   │  gen_pet.py      ảnh mẫu → qwen-image-3.0-pro vẽ lại, giữ nguyên dáng
   │  rig_skin.py     cắt ảnh mới theo lưới bộ phận của mô hình cũ
   ▼
pet da mới, xương cũ  → preview_pet.py  (move, skill, idle)
                                  +
hiệu ứng skill 6 khung ← sprite-forge + gpt-image-2  (pets/<pet>/prompts → raw → fx)
                                  ▼
                        demo_<pet>.py  →  GIF skill
```

Hai quyết định thiết kế nằm sẵn trong code:

- **Thân pet giữ xương của pack**, chỉ thay da. Nhờ vậy hoạt ảnh mượt như bản gốc và không tốn công vẽ từng khung.
- **Pet bất tử và chỉ có skill**, nên game chỉ dùng `move`, `skill` (trong trận) và `idle` (ngoài trận). Danh sách này nằm ở [pet_animations.py](pet_animations.py); các hoạt ảnh khác của pack bị lọc bỏ khi xem trước, không bị xoá khỏi asset gốc.

## Cài đặt

Cần Node, Python 3, và Chrome hoặc Chromium (đã chạy với Node 26, Python 3.9 trên macOS).

```bash
npm install
```

```bash
python3 -m pip install -r requirements.txt
```

## Asset pack

Đặt pack ở `../../assets/pack` tính từ thư mục này, hoặc trỏ `ASSETS_DIR` tới thư mục chứa `pack/`:

```
<ASSETS_DIR>/
  pack/spine/
    DV3/character/dragon/<tên>/<tên>.skel|.atlas|.png     pet (417 con)
    character/monster/monster_<tên>/monster_<tên>.*       quái dùng trong demo
  generated/            mọi thứ công cụ ghi ra (tự tạo)
    pets/               ảnh mẫu <tên>_ref.png và ảnh vẽ lại <tên>.png
    rigged/             bộ da đã gắn xương, cùng đường dẫn như trong pack
    preview/<tên>/      GIF xem trước
    demo/               GIF demo skill
    cache/              ảnh dựng từ pack, xoá đi để dựng lại
```

Những điều công cụ mặc định về pack này:

| Mặc định | Dùng ở đâu |
|---|---|
| Mô hình là Spine 4.1 nhị phân (`.skel`) kèm `.atlas` cùng tên | `spine/render.mjs` |
| Pet DV3 có các hoạt ảnh `idle`, `move`, `skill` | `pet_animations.py`, `preview_pet.py`, demo |
| Tên pet dạng `<tên>_00_adult`, thư mục và file trùng tên | `pet.py`, `gen_pet.py` |
| Pet là pixel art, nhìn ngang, quay mặt sang trái | prompt trong `gen_pet.py` |
| Atlas của pet là một trang PNG | `rig_skin.py` |

Xem pack có những con nào (ví dụ mọi rồng trưởng thành, 8 con một hàng):

```bash
node spine/render.mjs --sheet dragons.png DV3/character/dragon "_adult$" 150 8
```

## Khoá API

Khoá đặt trong file `.env` ở thư mục này. File đó đã nằm trong `.gitignore` nên không lên repo:

```bash
cp .env.example .env
```

Mở `.env` và điền khoá cùng endpoint của dịch vụ ảnh bạn dùng. Repo không gắn với nhà cung cấp nào: dịch vụ chỉ cần có API ảnh kiểu OpenAI (`.../v1/images/edits`). Mọi công cụ Python tự đọc file này khi chạy; biến đã đặt sẵn trong shell được ưu tiên hơn giá trị trong file. Không công cụ nào ghi khoá ra chỗ khác. Đừng đưa khoá vào code, prompt hay commit.

| Biến | Dùng cho | Mặc định |
|---|---|---|
| `RESKIN_KEY` | vẽ lại thân pet (`gen_pet.py`) | bắt buộc |
| `RESKIN_API` | endpoint sửa ảnh, nhận form upload | bắt buộc |
| `RESKIN_MODEL` | model | `qwen-image-3.0-pro` |
| `IMAGE_KEY` | vẽ hiệu ứng (`sprite-forge`) | bắt buộc |
| `IMAGE_API` | endpoint sửa ảnh | bắt buộc |
| `IMAGE_MODEL` | model | `gpt-image-2` |
| `ASSETS_DIR` | thư mục chứa `pack/` | `../../assets` |
| `CHROME` | đường dẫn Chrome | tự tìm |

`spine/render.mjs` khi gọi trực tiếp bằng `node` không đọc `.env`; nó nhận `ASSETS_DIR` và `CHROME` từ shell. Gọi qua các công cụ Python thì các biến trong `.env` được truyền sang.

Vì sao hai model: `qwen-image-3.0-pro` giữ đúng dáng ảnh mẫu nên gắn được vào xương cũ; `gpt-image-2` vẽ đẹp hơn nhưng đổi dáng, chỉ hợp với hiệu ứng.

## Làm một pet từ đầu đến cuối

Mỗi pet là một thư mục `pets/<pet>/` với file `pet.json`. Mọi bước chạy qua [pet.py](pet.py):

```bash
python3 pet.py darknix reference
```

| Bước | Việc | Cần khoá |
|---|---|---|
| `reference` | Dựng ảnh mẫu và in prompt, không gọi API | không |
| `reskin` | Vẽ lại pet bằng qwen | `RESKIN_KEY` |
| `rig` | Gắn ảnh mới vào xương của pack | không |
| `preview` | Xuất GIF `move`, `skill`, `idle` với bộ da mới | không |
| `fx` | Cắt các sheet hiệu ứng trong `raw/` thành khung và GIF | không |
| `fx --draw` | Vẽ trước những sheet có prompt mà chưa có ảnh | `IMAGE_KEY` |
| `fx --redraw <tên>` | Vẽ lại một sheet | `IMAGE_KEY` |
| `demo` | Dựng GIF skill (khi có `demo_<pet>.py`) | không |
| `all` | `reskin` → `rig` → `preview` → `fx --draw` → `demo` | cả hai |

Một lượt vẽ mất một đến vài phút và tính tiền theo API của bạn.

### Thêm pet mới

1. Chọn con trong pack, tạo `pets/<pet>/pet.json`:

```json
{
  "model": "DV3/character/dragon/darknix_00_adult",
  "description": "same dark lava dragon, same side-view standing pose facing left, ...",
  "skill": "Hắc Viêm Diệt Ấn",
  "fx": {
    "fx_seal": {"rows": 2, "cols": 3, "mode": "cast", "align": "center", "cell": 256}
  }
}
```

2. Chạy `reference`, mở ảnh `<tên>_ref.png` rồi viết `description`: một câu tiếng Anh tả đúng con đó (màu, dáng, hướng mặt, cánh, chi tiết phải giữ). Các câu đã dùng nằm ở [docs/pet-prompts.md](docs/pet-prompts.md).
3. Chạy `reskin`, rồi `rig`. Bước `rig` in ra tỉ lệ bộ da lấy được từ ảnh mới; khoảng 70% là bình thường, thấp hơn nhiều nghĩa là ảnh vẽ lại đã lệch dáng, hãy vẽ lại.
4. Chạy `preview` và xem GIF.
5. Với mỗi hiệu ứng của skill, viết prompt vào `pets/<pet>/prompts/<tên>.txt` và khai báo trong `fx` của `pet.json`, rồi chạy `fx --draw`.

Các trường của một hiệu ứng trong `pet.json`:

| Trường | Ý nghĩa |
|---|---|
| `rows`, `cols` | Lưới của sheet. Mặc định dùng 2 hàng 3 cột (6 khung) |
| `mode` | Loại hiệu ứng, đặt tên cho khung: `cast`, `impact`, `projectile`, `idle` |
| `align` | Canh khung: `center`, hoặc `bottom` cho thứ mọc từ đất lên |
| `cell` | Cỡ một khung sau khi cắt, tính bằng pixel |
| `qc` | Đặt `false` để bỏ kiểm tra chạm mép ô, cho hiệu ứng cố ý vẽ sát ô |

### Viết prompt hiệu ứng

Mẫu đã cho kết quả tốt (bốn prompt đầy đủ ở [docs/fx-prompt-examples.md](docs/fx-prompt-examples.md)):

- Nói rõ lưới: `exactly a 2 rows by 3 columns grid of six equal cells`.
- Tả từng khung theo thứ tự, mỗi khung một trạng thái khác nhau rõ rệt.
- Yêu cầu nằm gọn trong 65–70% giữa ô, không chạm mép.
- Giới hạn bảng màu và ghi `crisp chunky pixel art, hard edges, no soft glow haze`.
- Kết bằng `Solid flat magenta #FF00FF background`. Nếu model trả nền đen kèm quầng sáng, thêm `no glow, no aura, no halo` và `not black`.

## Ví dụ

Repo giữ một ví dụ để đọc, không kèm dữ liệu của nó:

- [demo_darknix.py](demo_darknix.py): kịch bản skill "Hắc Viêm Diệt Ấn" cấp 5 của Darknix (ấn chú lửa, năm cột lửa đen, mặt trời đen nổ, dấu nguyền), chú thích từng đoạn.
- [docs/fx-prompt-examples.md](docs/fx-prompt-examples.md): bốn prompt hiệu ứng của skill đó.
- [docs/pet-prompts.md](docs/pet-prompts.md): câu mô tả đã dùng để vẽ lại từng pet.

Muốn chạy lại ví dụ thì phải tạo `pets/darknix/` trước (cấu hình và prompt lấy từ hai file docs trên), rồi `python3 pet.py darknix all`.

## Các file

| File | Việc |
|---|---|
| [pet.py](pet.py) | Lệnh chung cho mọi bước của một pet |
| [gen_pet.py](gen_pet.py) | Dựng ảnh mẫu từ mô hình Spine và gọi qwen vẽ lại |
| [rig_skin.py](rig_skin.py) | Cắt ảnh vẽ lại theo lưới bộ phận của mô hình gốc, ghi atlas mới cạnh bản sao `.skel` |
| [preview_pet.py](preview_pet.py) | Xuất GIF các hoạt ảnh game dùng (`--all` để xem đủ mọi hoạt ảnh của pack) |
| [pet_animations.py](pet_animations.py) | Hoạt ảnh nào của pet được dùng và tối đa bao nhiêu khung |
| [scene.py](scene.py) | Thành phần dựng cảnh demo: nền, quái dựng từ pack, khung hiệu ứng, số sát thương, ghi GIF |
| [demo_darknix.py](demo_darknix.py) | Ví dụ để đọc: kịch bản skill của một pet (Darknix), chú thích từng đoạn. Không dùng lại, không chạy được nếu chưa tạo `pets/darknix` |
| [peek_gif.py](peek_gif.py) | Xếp vài thời điểm của một GIF thành một ảnh PNG để kiểm tra bằng mắt |
| [common.py](common.py) | Đường dẫn, đọc `.env` và hàm dùng chung |
| `.env.example` | Mẫu file khoá; chép thành `.env` rồi điền |
| [spine/render.mjs](spine/render.mjs) | Dựng mô hình Spine bằng Chrome không giao diện; chạy không tham số để xem các chế độ |
| [scene_kit/](scene_kit) | Nền cỏ và 5 sprite vẽ bằng code mà mọi demo cần: bóng đổ, chữ số sát thương, vết cháy, khói, tia trúng đòn |
| [sprite-forge/](sprite-forge/README.md) | Bản sửa của agent-sprite-forge: gọi API ảnh riêng và cắt sprite sheet |
| [pets/](pets/README.md) | Nơi agent đặt nội dung riêng từng pet; không lưu trong repo |
| [docs/fx-prompt-examples.md](docs/fx-prompt-examples.md) | Bốn prompt hiệu ứng đã dùng cho Darknix, làm mẫu |
| [docs/pet-prompts.md](docs/pet-prompts.md) | Prompt vẽ lại pet và các câu mô tả đã dùng |

## Hướng dẫn cho agent

Phần này dành cho một agent lập trình (Claude Code, Codex...) được giao việc "làm pet X" mà chưa biết gì về repo. Làm đúng thứ tự dưới đây. Chạy mọi lệnh từ thư mục chứa README này.

### Luật chung

- **Khoá API** nằm trong file `.env` ở thư mục này (`RESKIN_KEY`, `RESKIN_API`, `IMAGE_KEY`, `IMAGE_API`; mẫu ở `.env.example`). Công cụ tự đọc, agent không cần và **không được** mở, in hay chép nội dung `.env`. Nếu công cụ báo `set RESKIN_KEY ...`, `set IMAGE_API ...` hay tương tự thì file thiếu giá trị đó: dừng lại và nhờ người dùng điền. Không ghi khoá vào file nào khác, prompt, log hay commit, và không `git add -f .env`.
- **Mỗi lượt gọi API tốn tiền và một đến vài phút.** Đọc lại prompt trước khi gọi, xem kết quả trước khi gọi tiếp. Có thể chạy song song lượt vẽ thân với các lượt vẽ hiệu ứng nếu chúng dùng hai dịch vụ khác nhau.
- **Luôn tự mở ảnh ra xem** sau mỗi bước (ảnh mẫu, ảnh vẽ lại, sheet hiệu ứng, khung GIF). Bước nào in "thành công" cũng có thể cho ra ảnh hỏng.
- **Không xoá hay sửa gì trong asset pack.** Muốn bỏ hoạt ảnh thì lọc trong `pet_animations.py`.
- **Không vẽ sinh vật hay hiệu ứng bằng code.** Thân pet đi đường reskin + xương cũ; hiệu ứng đi đường sprite sheet do model vẽ.
- **Đề xuất ý tưởng skill cho người dùng trước khi vẽ hiệu ứng**, trừ khi họ bảo làm thẳng.
- Thứ lấy từ hình của pack (ảnh vẽ lại, bộ da gắn xương, GIF) nằm ở `<ASSETS_DIR>/generated`, không đưa vào repo.

### Bước 1: chọn pet và xem nó

```bash
node spine/render.mjs --sheet /tmp/dragons.png DV3/character/dragon "_adult$" 150 8
```

Ảnh ra là bảng mọi rồng trưởng thành kèm tên và danh sách hoạt ảnh; file `.json` cùng tên có độ dài từng hoạt ảnh. Chọn con có đủ `idle`, `move`, `skill`. Tên thư mục của nó (ví dụ `darknix_00_adult`) là phần cuối của `model`.

### Bước 2: tạo `pets/<pet>/pet.json`

`<pet>` là tên ngắn không dấu (ví dụ `darknix`). Lúc đầu chỉ cần `model`, một `description` tạm và `"fx": {}`. Rồi dựng ảnh mẫu:

```bash
python3 pet.py <pet> reference
```

Mở `<ASSETS_DIR>/generated/pets/<tên>_ref.png` và viết `description` theo đúng thứ nhìn thấy, một câu tiếng Anh theo khuôn:

```
same <màu> <loại> dragon, same <dáng> pose facing left, same proportions, <màu thân và hoa văn>, <cánh>, <chi tiết riêng phải giữ: sừng, nắm đấm, vây, mắt, móng>.
```

Tả càng đủ chi tiết riêng thì model càng ít tự bịa. Xem các câu đã dùng ở [docs/pet-prompts.md](docs/pet-prompts.md) và thêm câu mới vào đó.

### Bước 3: vẽ lại và gắn xương

```bash
python3 pet.py <pet> reskin
```

```bash
python3 pet.py <pet> rig
```

Kiểm tra:

- Mở `<tên>.png` cạnh `<tên>_ref.png`: phải cùng dáng, cùng hướng, cùng vị trí trong khung, nền trắng, đúng một con.
- Dòng `rig` in ra, ví dụ `73% of the posed parts came from the picture, picture lay at 2.87x2.93`. Khoảng 70% là tốt. Dưới khoảng 60%, hoặc hai hệ số tỉ lệ lệch nhau nhiều, nghĩa là ảnh đã đổi dáng: sửa `description` (thêm `same proportions`, tả kỹ phần bị lệch) rồi `reskin` lại.

```bash
python3 pet.py <pet> preview
```

Xem `<ASSETS_DIR>/generated/preview/<tên>/all.gif` bằng `peek_gif.py`. Tìm chỗ da bị rách hoặc lệch màu ở khớp khi pet cử động.

### Bước 4: thiết kế skill

Một skill tốt cho game này: phủ rộng màn hình, có nhiều pha nối nhau (mở màn, đòn chính, kết), đọc được rõ từng pha, hợp với hệ và vai của pet. Skill của Darknix làm mẫu: ấn chú hiện dưới đất, năm cột lửa phun lần lượt, hút quái về tâm rồi nổ, quái sống sót mang dấu nguyền.

Chia skill thành các hiệu ứng rời, mỗi cái một sheet. Thường cần 3 đến 4 sheet:

| Loại | Ví dụ | Góc nhìn khi viết prompt |
|---|---|---|
| Thứ nằm trên mặt đất | ấn chú, vũng, vết nứt | Nhìn thẳng từ trên xuống (hình tròn); cảnh sẽ tự ép dẹp và xoay nó |
| Thứ mọc từ đất lên | cột lửa, gai băng | Nhìn ngang, gốc ở giữa đáy ô, `align: bottom` |
| Vụ nổ, quả cầu | mặt trời đen, vụ nổ | Tâm cố định giữa ô |
| Dấu hiệu nhỏ lặp vòng | dấu nguyền trên đầu quái | Cùng cỡ, cùng chỗ mọi khung, chỉ chi tiết nhấp nháy |

### Bước 5: vẽ hiệu ứng

Mỗi hiệu ứng là một file `pets/<pet>/prompts/<tên>.txt` và một mục trong `fx` của `pet.json`. Khuôn prompt (sửa phần trong ngoặc nhọn, xem bản đầy đủ ở [docs/fx-prompt-examples.md](docs/fx-prompt-examples.md)):

```
Pixel-art game effect sprite sheet, exactly a 2 rows by 3 columns grid of six equal cells, one animation of <hiệu ứng>, <góc nhìn>, six frames read left to right, top to bottom: frame 1 <...>, frame 2 <...>, frame 3 <...>, frame 4 <...>, frame 5 <...>, frame 6 <...>.
<Thứ giữ nguyên qua các khung: tâm, gốc, kích thước>; it stays inside the central 70% of the cell and nothing touches or crosses a cell edge. No characters, no ground.
Palette: <4 đến 6 màu>. Crisp chunky pixel art, hard edges, no soft glow haze, no blur.
Solid flat magenta #FF00FF background, no gradients, no grid lines, no borders, no text, no letters.
```

```bash
python3 pet.py <pet> fx --draw
```

Lệnh này vẽ sheet nào chưa có ảnh trong `raw/`, rồi cắt mọi sheet thành khung trong `pets/<pet>/fx/<tên>/` (từng khung `*-1.png`…`*-6.png`, `sheet-transparent.png`, `animation.gif`). Xem `raw/<tên>.png` của từng sheet. Lỗi hay gặp và cách xử lý:

| Thấy gì | Làm gì |
|---|---|
| `QC failed: raw subjects touch a source-cell edge` | Hiệu ứng vẽ quá to. Nếu khung vẫn nguyên vẹn và cố ý to (ấn chú), đặt `"qc": false`. Nếu bị cắt, hạ tỉ lệ trong prompt (ví dụ 60%) rồi `fx --redraw <tên>` |
| Nền đen kèm quầng sáng thay vì nền hồng | Thêm vào prompt: `Flat colours only: absolutely no glow, no aura, no halo` và `The background ... is one solid flat magenta colour #FF00FF, not black`, rồi vẽ lại |
| Ảnh về nền trong suốt | Bình thường, model tự tách nền; công cụ nhận cả hai |
| Các khung gần như giống nhau | Tả từng khung khác nhau rõ hơn, thêm `The poses must be clearly different from frame to frame` |
| Sai số ô hoặc lệch lưới | Vẽ lại; nhắc `exactly ... grid of six equal cells` ở đầu prompt |

### Bước 6: viết `demo_<pet>.py`

Đọc `demo_darknix.py` (phần chú thích đầu file và từng đoạn) để hiểu cách dựng, rồi **viết một file mới** `demo_<pet>.py` cho pet của bạn. Không sửa, không import và không nhồi pet khác vào `demo_darknix.py`: mọi toạ độ, mốc thời gian và luật trúng đòn trong đó chỉ đúng cho skill của Darknix. Tên file phải là `demo_<pet>.py` thì `pet.py <pet> demo` mới tìm thấy. Cấu trúc:

1. **Hằng số**: `PET`, `MODEL` (đường dẫn pack không đuôi), kích thước cảnh `W, H, FPS = 640, 400, 20`, vị trí pet và tâm skill, và **bảng mốc thời gian tính bằng tick** (1 tick = 1/FPS giây).
2. **Nạp hình** bằng các hàm của `scene.py`:

| Hàm | Trả về |
|---|---|
| `kit()` | Sprite vẽ bằng code: `shadow`, `digits`, `scorch`, `puff`, `hit` (xem `scene_kit/README.md`) |
| `ground(W, H)` | Nền cỏ phủ kín cảnh |
| `pack_frames(MODEL, anim, số_khung, cell, fit, skin)` | Khung của pet; `skin` là `<generated>/rigged` để dùng da mới; `fit` là các hoạt ảnh dùng chung một tỉ lệ, ví dụ `"idle,skill"` |
| `pack_sprite(model, anim, số_khung, cỡ)` | Quái hoặc vật khác của pack, thu nhỏ còn `cỡ` pixel. Quái nằm ở `character/monster/monster_<tên>/monster_<tên>`, hoạt ảnh đi là `run` hoặc `idle` tuỳ con |
| `effect(PET, tên, cỡ)` | Sáu khung của một hiệu ứng, phóng tới `cỡ` pixel |
| `put(canvas, sprite, x, y, ax, ay)` | Vẽ sprite với điểm neo (`ax`, `ay`) đặt tại (x, y) |
| `white`, `tinted`, `faded`, `number` | Nháy trắng, nhuộm màu, làm mờ, vẽ số sát thương |
| `save_gif(path, frames, FPS)` | Ghi GIF với một bảng màu chung |

3. **Vòng lặp theo tick**: mỗi tick vẽ theo thứ tự nền → thứ nằm trên đất (ấn, vết cháy) → mọi thứ đứng trên đất, sắp theo toạ độ y (pet, quái, cột lửa) → hiệu ứng trên không (vụ nổ) → dấu trên đầu quái và số sát thương.

Mẹo đã dùng trong `demo_darknix.py`:

- Hoạt ảnh `skill` của pack có thể kèm hiệu ứng riêng rất rộng. Dùng `cell` lớn (560) với `fit="idle,skill"` để không bị cắt, và lấy điểm chân pet từ `idle[0].getbbox()`.
- Thứ nằm trên đất: xoay khung bằng `rotate(..., Image.NEAREST)` rồi ép chiều cao còn một nửa chiều rộng.
- Cú đánh mạnh nhất: lặp lại khung đó vài tick (khựng hình), rung cảnh vài pixel trong 8 tick, nháy trắng quái trúng đòn 3 tick.
- Số sát thương bay lên rồi mờ dần. Khi cả đám trúng cùng lúc chỉ hiện số cho một phần ba, không thì thành một cục chữ.
- Dùng `random.Random(<số cố định>)` để mỗi lần dựng ra cùng một cảnh.

Điều **không làm**, vì người dùng đã chê:

- Không làm tối hay phủ màu cả màn hình khi tung skill.
- Không dùng quầng sáng mờ kiểu cộng màu; nó nhoè và lệch chất pixel.
- Không phóng hiệu ứng bằng nội suy mượt; dùng `Image.NEAREST` để giữ pixel cứng.

```bash
python3 pet.py <pet> demo
```

```bash
python3 peek_gif.py <ASSETS_DIR>/generated/demo/<pet>_skill_lv5.gif /tmp/peek.png 0.6,1.7,2.1,2.6,2.9,4.5
```

Mở ảnh `peek.png` và kiểm tra từng pha: pet có đúng cỡ so với quái không, hiệu ứng có đặt đúng chỗ, thứ tự che nhau có đúng, số sát thương có đọc được, mép cảnh có lộ viền khi rung không. Sửa rồi dựng lại cho tới khi đạt. Ảnh dựng từ pack được lưu ở `generated/cache`, nên lần dựng sau nhanh hơn; đổi bộ da thì bộ đệm tự làm mới.

### Bước 7: báo cáo

Gửi người dùng: ảnh gốc cạnh ảnh vẽ lại, `all.gif` của thân, GIF skill, và ảnh các sheet hiệu ứng. Nói rõ tỉ lệ `rig`, sheet nào phải vẽ lại và vì sao, bước nào chỉ kiểm tra bằng khung tĩnh, và thứ gì trong cảnh là mượn (quái của pack, sprite trong `scene_kit`) chứ không phải mới vẽ.

### Tra cứu nhanh mô hình Spine

```bash
node spine/render.mjs --bones /tmp/b.json DV3/character/dragon/<tên>/<tên>
```

File ra liệt kê hoạt ảnh, xương (tên, cha, vị trí, góc) và các slot. Chạy `node spine/render.mjs` không tham số để xem các chế độ khác: `--strip` (một hoạt ảnh thành dải khung), `--aim` (xoay một xương từng bước, dùng khi cần pet hướng đầu về mục tiêu), `--rig` (dữ liệu cho `rig_skin.py`).

Pack còn có sẵn mô hình hiệu ứng của game gốc (`battle`, `skill_eff`, `skill_eff_2`, `pve_skill_eff`, `pve_boss_skill_eff`...). Chúng là hiệu ứng mượt phát sáng, không phải pixel art; xem bằng `--sheet` trước khi quyết định vẽ mới.

## Cái gì được đưa lên repo

| Thứ | Trong repo | Lý do |
|---|---|---|
| Code, tài liệu, `scene_kit/`, `demo_darknix.py` | Có | Tự viết, tự vẽ bằng code |
| `pets/<pet>/` và mọi `demo_<pet>.py` khác | Không | Nội dung riêng từng pet, agent tạo lại khi cần |
| `.env` | Không | Chứa khoá và endpoint |
| Asset pack | Không | Của bên thứ ba |
| Ảnh vẽ lại pet, bộ da đã gắn xương, GIF xem trước và demo | Không | Dẫn xuất từ hình của pack; bộ da gắn xương còn kèm bản sao file `.skel` của pack. Chúng được ghi vào `<ASSETS_DIR>/generated`, ngoài repo |

## Giới hạn

- `rig_skin.py` chỉ đúng khi ảnh vẽ lại giữ nguyên dáng và vị trí của ảnh mẫu.
- Phần cơ thể bị che trong tư thế mẫu không có màu trong ảnh mới, nên được tô bằng màu gần nhất của chính bộ phận đó.
- Chỉ có các động tác pack đã làm sẵn. Động tác mới cần sửa xương trong Spine Editor.
- Hoạt ảnh `skill` của một số pet trong pack kèm hiệu ứng riêng (Darknix có vòng ấn đỏ trên đầu); nó nằm trong mô hình nên vẫn hiện sau khi thay da.
- Model ảnh không cho kết quả giống nhau giữa hai lượt gọi. Sheet nào hỏng thì vẽ lại bằng `fx --redraw`.

## Kiểm thử

```bash
cd sprite-forge && python3 -m unittest discover -s tests
```

## Giấy phép

`sprite-forge/` giữ giấy phép MIT của bản gốc ([LICENSE](sprite-forge/LICENSE)). Asset pack Dragon Village không thuộc repo này.
