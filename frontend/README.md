# OptiMat AI: giao diện web

Next.js 16 (App Router) · React 19 · Tailwind CSS 4 · TypeScript. Giao diện gọi API FastAPI qua đường `/api`
(Next chuyển tiếp, xem `next.config.ts`), nên chạy cả hai.

## Chạy khi phát triển

```bash
# cửa sổ 1, thư mục optimat-ai/
uvicorn optimat.api.main:app --reload --app-dir src     # API ở http://127.0.0.1:8000

# cửa sổ 2, thư mục optimat-ai/frontend/
npm install          # lần đầu
npm run dev          # giao diện ở http://localhost:3000
```

API chạy ở địa chỉ khác thì đặt biến `OPTIMAT_API`, ví dụ `OPTIMAT_API=http://127.0.0.1:8001 npm run dev`.

## Chạy bản build

```bash
npm run build
npm start
```

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `src/app/dang-nhap` | Chọn vai trò |
| `src/app/(user)/…` | Người dùng: `do-boc` (kiểm tra bóc tách), `vat-lieu`, `phan-tho`, `toi-uu`, `tiep-nhan` (hồ sơ CAD), `mapping` |
| `src/app/(admin)/…` | Quản trị: `kiem-soat`, `danh-muc`, `dai-ly`, `gia`, `nhan-dien`, `quy-tac`, `co-so-du-lieu`, `mo-hinh` |
| `src/components/Shell.tsx` | Khung trang và menu theo vai trò |
| `src/components/Sheet.tsx` | Bảng kiểu Excel: cột #, tiêu đề cố định, sắp xếp, lọc, thanh công thức, tải CSV |
| `src/components/ui.tsx` | Thành phần nhỏ: tiêu đề trang, thẻ số liệu, nhãn trạng thái, thanh bước |
| `src/lib/api.ts`, `src/lib/store.ts` | Gọi API; lưu tạm trên trình duyệt (vai trò, mặt bằng đã chốt, kết quả phần thô) |
| `src/app/globals.css` | Bảng màu (sáng, tối), chữ Be Vietnam Pro 13px cho ô dữ liệu, kiểu bảng |

Bảng thường bọc trong `<div className="tw">` tự có cột # đánh số; thêm `className="nonum"` cho bảng đã có số.
