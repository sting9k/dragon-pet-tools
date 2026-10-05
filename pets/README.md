# pets/

Nội dung riêng của từng pet, do agent tạo khi làm pet đó. **Không đưa lên git** (thư mục này bị chặn trong `.gitignore`, trừ file này).

Mỗi pet một thư mục:

```
pets/<pet>/
  pet.json        mô hình trong pack, câu mô tả để vẽ lại, tên skill, danh sách hiệu ứng
  prompts/<tên>.txt   prompt của từng sheet hiệu ứng
  raw/<tên>.png       sheet model trả về
  fx/<tên>/           khung đã cắt, sheet trong suốt, GIF xem thử
```

Cách tạo: xem "Hướng dẫn cho agent" trong [README](../README.md). Prompt mẫu: [docs/fx-prompt-examples.md](../docs/fx-prompt-examples.md).
