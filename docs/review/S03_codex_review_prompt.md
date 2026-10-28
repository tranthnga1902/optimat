# Prompt review S03 cho Codex

Dán nguyên khối dưới đây vào Codex (chạy ở thư mục `optimat-ai`).

---

Bạn là reviewer độc lập cho sprint **S03 – Chuẩn hóa và liên kết hồ sơ kiến trúc–kết cấu** của dự án OptiMat AI
(Python 3.13, FastAPI, ezdxf, pydantic v2). Đọc `CLAUDE.md` trước để nắm quy tắc dự án. Trả lời bằng tiếng Việt.
**Chỉ review, không sửa mã, không commit.** Kho đang có thay đổi chưa commit của nhiều phiên khác; chỉ xét các file S03 dưới đây.

## Phạm vi S03 (file mới hoặc đã sửa)

- `src/optimat/drawing/registry.py` – lõi: `Registry`, `Component`, `EvidenceRef`, `Occurrence`, `Issue`, `build_registry`,
  `_resolve`, `score`, `apply_decisions`, `floors_of`, `match_symbol`, `_handles`, `_axes`
- `src/optimat/api/mapping.py` + 2 dòng `include_router` trong `src/optimat/api/main.py`
- `src/optimat/drawing/mapping_review.html` – trang `/ui/mapping`
- `data/rules/do_tin_cay.csv` (quy tắc tin cậy TC01–TC09), dòng `BV15` cuối `data/rules/loai_ban_ve.csv`
- `data/ground_truth/s03/cases.json` (15 ca SYNTHETIC, đáp án viết tay), `scripts/make_s03_fixtures.py`
- `docs/schema/ho_so_chuan_hoa.schema.json`, `tests/test_registry.py`
- Mã dùng lại (không thuộc S03, chỉ đọc để hiểu): `src/optimat/rough/structural.py`, `src/optimat/drawing/sheets.py`,
  `dimensions.py`, `plans.py`, `concepts.py`

## Backlog và tiêu chí nghiệm thu cần đối chiếu

1. S03-01 loại bản vẽ: kiến trúc, mặt bằng móng, cột, dầm, sàn, cầu thang, mái, chi tiết thép, bảng thống kê.
2. S03-02 mapping layer và ký hiệu theo cấu hình sửa được (CSV + ghi đè `layer_overrides`, `symbol_overrides`); UI xác nhận mapping.
3. S03-03 chuẩn hóa tọa độ, cao độ tầng, trục, tên cấu kiện; đối chiếu ký hiệu trên plan và detail.
4. S03-04 ComponentRegistry + EvidenceRef (file, layout, entity handle, bbox, quy tắc).
5. S03-05 đánh dấu xung đột kích thước, chi tiết thiếu, version mismatch, đa tầng trên một file.
6. S03-06 confidence theo quy tắc minh bạch + luồng yêu cầu xác nhận.

Nghiệm thu: (a) mỗi cấu kiện đã nhận diện có file/entity nguồn; (b) phát hiện mã dầm/cột không có detail hoặc detail
mâu thuẫn; (c) **không tự điền thông số khi thiếu chiều cao/cấu tạo**. Bàn giao: schema, trang review mapping + danh
sách unmatched, 10–15 bộ bản vẽ con chuẩn + ground truth.

## Việc cần làm

1. Chạy, ghi lại kết quả thật (không đoán):
   ```powershell
   $env:PYTHONIOENCODING = "utf8"
   .venv\Scripts\python.exe -m pytest tests/test_registry.py -q
   .venv\Scripts\python.exe scripts/make_s03_fixtures.py
   .venv\Scripts\python.exe scripts/check_data.py
   ```
   `test_ket_cau_build_drawing` cần `data/drawings/build/ket_cau.dxf` (chạy ~40 s); không có file thì bị bỏ qua — ghi rõ.
2. Đối chiếu từng mục backlog và tiêu chí nghiệm thu ở trên với mã: mục nào **đạt / đạt một phần / chưa đạt**, dẫn `file:dòng`.
3. Săn lỗi, ưu tiên:
   - **Tự điền số** (vi phạm Quy ước B7): có đường nào làm `Component.size` có giá trị mà không có `SizeValue` nguồn?
     `apply_decisions` có xóa/ghi đè sai số liệu bản vẽ không (mỗi thông số người dùng nhập thắng riêng từng khóa)?
   - **Bằng chứng**: `_handles` khớp chữ theo điểm chèn làm tròn mm — chữ xoay, căn lề (`align_point`), MTEXT, chữ trong
     block lồng, `unit_scale` ≠ 1 có làm `handle` sai hoặc `None`? Hai chữ trùng điểm chèn thì sao?
   - **Chuẩn hóa tầng** `floors_of`: TRỆT/LẦU (miền Nam) vs TẦNG (miền Bắc), "LẦU 2-LẦU 5", "SÂN THƯỢNG" (ST) khác "MÁI",
     tiêu đề có cao độ âm "(-0.45)", "TL 1/50"; có khớp `structural.floor_count` không (số phần tử phải bằng nhau)?
   - **Xung đột**: chữ ghi vs mặt cắt vs nét mặt bằng; dung sai `SIZE_TOLERANCE`; xung đột khi mặt bằng vẽ tỷ lệ 0,5.
   - **Trục** `_axes`: phân trục đứng/ngang theo khoảng cách tới cạnh khung — trường hợp sai?
   - **Mức tin cậy** `score`: quy tắc trong CSV mà mã không dùng, hoặc mã dùng mà CSV không có (KeyError)? Sửa mức trong CSV có
     đổi kết quả mà không cần sửa mã? `lru_cache` có làm sửa CSV không có hiệu lực khi server đang chạy?
   - **API**: kiểm đầu vào (`symbol_overrides` sai vai trò, file không phải DXF/DWG, JSON hỏng); `/api/mapping/confirm` nhận
     `Registry` do client gửi lên — client sửa `size_sources`/`rules` để vượt luồng xác nhận được không? Đánh giá mức rủi ro.
   - **Trang** `mapping_review.html`: thoát HTML (XSS từ chữ trong bản vẽ), trạng thái `decisions` sau "Đọc hồ sơ" lại,
     nhập số âm/0, quyết định cho cấu kiện đã đổi id.
   - **Hiệu năng**: `build_registry` gọi `find_plans`, `find_views`, `detail_sections`, `_lines` cho từng hình — có vòng lặp
     O(n²) nào nổ trên bản vẽ 8–20 MB không?
4. Ground truth: 15 ca trong `cases.json` có thật sự độc lập với mã (đáp án viết tay, không sinh ra từ đầu ra)? Ca nào thiếu
   (ví dụ: móng có chi tiết, cột ghi tiết diện mâu thuẫn, hai file kiến trúc + kết cấu khác tầng, mặt bằng tỷ lệ 0,5)?
   Ghi rõ đây là dữ liệu SYNTHETIC, không dùng để báo cáo độ chính xác (quy tắc trong `CLAUDE.md`).
5. Giới hạn đã biết (không tính là lỗi, chỉ ghi nhận nếu sai lệch với tài liệu): chưa nhận cầu thang, sàn, mái, lanh tô thành
   cấu kiện; tiết diện cột chỉ đọc từ chữ ghi; bbox chữ ước lượng (`shortcut:` trong `_ev`); chưa lưu hồ sơ vào PostgreSQL
   (đổi lược đồ cần duyệt).

## Định dạng trả lời

1. **Kết quả chạy** (lệnh → số đạt/lỗi/bỏ qua, trích lỗi nếu có).
2. **Bảng nghiệm thu**: mục | trạng thái | bằng chứng `file:dòng` | ghi chú.
3. **Lỗi** xếp từ nặng tới nhẹ, mỗi lỗi: mức (chặn / nặng / nhẹ), `file:dòng`, kịch bản tái hiện cụ thể (đầu vào → kết quả sai),
   đề xuất sửa ngắn. Không liệt kê góp ý phong cách.
4. **Ca ground truth nên thêm** (tối đa 5).
5. Kết luận một dòng: S03 có đủ điều kiện nghiệm thu không, nếu không thì còn thiếu gì.
