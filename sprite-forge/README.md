# Sprite Forge (bản dùng API riêng)

Bản sửa của [0x0funky/agent-sprite-forge](https://github.com/0x0funky/agent-sprite-forge) (MIT, commit `64fd0b5`). Bản gốc vẽ ảnh bằng công cụ sinh ảnh có sẵn của Codex; bản này vẽ qua **một API ảnh tuỳ chọn kiểu OpenAI và API key của bạn**, nên không phụ thuộc agent nào: đã chạy tay từ terminal; cài làm skill cho Codex theo bản gốc, cho Claude Code thì chưa thử.

## Khác bản gốc ở đâu

- Thêm `skills/generate2dsprite/scripts/image_api.py`: gọi API, lưu PNG và prompt. Cả hai skill dùng chung script này.
- Mọi chỗ trong `SKILL.md` và `references/` nói "built-in `image_gen`" / "`view_image`" đổi thành gọi `image_api.py` và truyền ảnh mẫu bằng `--ref`.
- Bỏ skill `video2dsprite` (cần công cụ tạo video riêng của Grok Build) và thư mục ảnh minh hoạ `src/`.
- Bỏ bước gọi script tách nền riêng của Codex trong hướng dẫn prop pack; `extract_prop_pack.py` tự tách nền hồng.
- Các script xử lý ảnh của bản gốc giữ nguyên.

## Cài đặt

```bash
python3 -m pip install -r requirements.txt
```

Cài skill cho Codex:

```bash
mkdir -p ~/.codex/skills && cp -R ./skills/* ~/.codex/skills/
```

Cài skill cho Claude Code:

```bash
mkdir -p ~/.claude/skills && cp -R ./skills/* ~/.claude/skills/
```

Mở phiên agent mới sau khi cài. Hai skill phải nằm cạnh nhau vì `generate2dmap` gọi script của `generate2dsprite`.

## Cấu hình API

Khoá đọc từ biến môi trường, hoặc từ file `.env` gần nhất nằm phía trên script (các dòng `TÊN=giá trị`; biến trong shell được ưu tiên). Giữ `.env` trong `.gitignore`. Không script nào ghi khoá ra file; đừng đưa khoá vào code hay commit.

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `IMAGE_KEY` | API key | bắt buộc |
| `IMAGE_API` | endpoint sửa ảnh (dùng khi có ảnh mẫu), dạng `.../v1/images/edits` | bắt buộc |
| `IMAGE_API_GENERATE` | endpoint vẽ mới (không ảnh mẫu) | `IMAGE_API` đổi `/edits` thành `/generations` |
| `IMAGE_MODEL` | tên model | `gpt-image-2` |
| `IMAGE_API_STYLE` | `json`: body JSON, ảnh mẫu gửi kèm dạng data URI. `multipart`: form upload, có `size` | `json` |

Ví dụ dùng model khác qua form upload:

```bash
export IMAGE_API=https://<dịch-vụ-của-bạn>/v1/images/edits IMAGE_MODEL=qwen-image-3.0-pro IMAGE_API_STYLE=multipart
```

API trả `data[0].b64_json` hay `data[0].url` đều được.

## Gọi tay

Vẽ một sheet:

```bash
python3 skills/generate2dsprite/scripts/image_api.py --prompt-file prompt.txt --out raw.png
```

Có ảnh mẫu thì thêm `--ref ref.png` (lặp lại được). Rồi cắt khung, canh và xuất GIF:

```bash
python3 skills/generate2dsprite/scripts/generate2dsprite.py process --input raw.png --target asset --mode impact --rows 2 --cols 2 --output-dir out --strict-qc
```

Kết quả trong `out/`: từng khung PNG, `sheet-transparent.png`, `animation.gif`, `pipeline-meta.json`.

## Lưu ý

- Một lượt gọi mất một đến hai phút và tính tiền theo API của bạn.
- Một số model tự tách nền và trả ảnh trong suốt thay vì nền hồng `#FF00FF`. `image_api.py` dọn lớp mờ còn sót (alpha rất thấp về 0, gần đặc về 255); các script xử lý nhận cả hai kiểu.
- Model kiểu `gpt-image` vẽ đẹp nhưng không giữ đúng dáng ảnh mẫu; cần giữ dáng thì dùng model giữ dáng tốt hơn.

## Kiểm thử

```bash
python3 -m unittest discover -s tests
```

## Giấy phép

MIT, giữ nguyên của bản gốc. Xem [LICENSE](LICENSE).
