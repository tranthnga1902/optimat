# N02-b1 — sửa review nhóm scope phải khớp dữ liệu dòng

03/11/2026 — **CHỜ REVIEW**, không tự nhận nghiệm thu b1/N02. Chỉ sửa hai file `src/optimat/rough/rebar.py`, `tests/test_rough_rebar.py`; không worker/API/caller/DB/UI.

Lỗi review được xác nhận: trước sửa, assignment COT trên bảng toàn row DAM có thể qua validation, gộp bảng và xóa pending. Sau sửa, trong vòng validate toàn bộ assignments **trước copy/áp**, scope khác ALL phải bao phủ đúng mọi row.element_code đã biết. Mismatch ném ValueError nêu table_id, nhóm scope và nhóm dòng; b2 sẽ chuyển 422 khi được nối. `override_reason` không vượt kiểm tra này và không đổi phân loại row.

Test thêm (SYNTHETIC):

- Generic DAM → scope COT bị chặn cả khi có lý do override; valid assignment trước + bad assignment sau vẫn atomic, bảng và assignment gốc không đổi.
- ALL cho bảng DAM/COT/None giữ đúng bội số, chỉ bỏ bản sao nguyên; row None vẫn None và ghi chú Not supported còn. Thu hẹp scope xuống DAM khi có COT bị chặn.
- Tiêu đề ghi COT nhưng row DAM: mapping DAM thiếu override_reason bị chặn; có lý do thì hợp lệ, giữ nguyên DAM và chứng cứ tiêu đề cũ.

Đã chụp SOURCE-READY trước test. Chạy lại đúng nhóm pure reader theo phạm vi đã cấp, không TestClient/CAD thật/DB/full suite:

```text
python -m pytest tests/test_rough_rebar.py -k "not schedule_steel_separate_from_ratio and not no_schedule_leaves_steel_blank and not boq_excel_sheets" -q -ra -p no:cacheprovider --basetemp=reports/n02/b1/review_fix/temp_reader
```

**75 passed, 3 deselected, 0 failed/skipped/xfail, pytest exit 0**, 3.76s. Lệnh/mã thoát ở `result_reader.json`, output ở `pytest_reader.log`. Đã bỏ DATABASE_URL/OPTIMAT_TEST_DATABASE_URL và đặt OPTIMAT_NO_DOTENV/PYTHONIOENCODING/PYTHONDONTWRITEBYTECODE. Không chạy ba ca tích hợp compute/steel/BOQ bị loại; không có kết quả API/partial mới.

`before/`, `after/`, `review_fix.diff`, `hash_before.json`, `hash_after.json`, `hash_diff.json` là snapshot/diff/hash riêng cho review fix. `hash_diff_since_source_ready.json` rỗng: source không đổi qua focused; `git diff --check` exit 0. Parent b1 giữ nguyên log/hash 71 passed như lịch sử trước fix; không ghi đè.

Giới hạn giữ nguyên: resolver so assignment với source context, b2 phải tạo context từ byte upload gốc; chưa nối HTTP422/reupload/mapping qua API. Numeric + missing tới tổng/vật tư còn Q02/b3, chưa làm. Không restart/change worker đang QA. Đề nghị điều phối review độc lập, dùng hash trong thư mục review_fix cho bước tiếp.

Dòng nhật ký đề xuất: “03/11/2026 — N02-b1 review fix chặn scope khác ALL trái nhóm row trước áp mapping; ALL/None và override tiêu đề có test; pure reader 75 passed, 3 deselected, exit0; chờ review, chưa API/Q02 hoặc nghiệm thu toàn N02.”
