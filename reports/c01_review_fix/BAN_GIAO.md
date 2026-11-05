# C01 sửa bốn lỗi review — chờ điều phối review độc lập

Người sửa lượt này: Codex, 03/11/2026. **Chưa tự nghiệm thu.** Không mở N01/A01, không sửa engine/evaluator/D02/định mức hoặc tài liệu chung.

## File và xung đột

- Đã sửa từng đoạn trong scripts/c01_duong_co_so.py và tests/test_c01_duong_co_so.py. Snapshot byte gốc trong snapshot/, hash_before.csv; hash_after_edit.csv/hash_final.json ghi bản sửa. Kiểm sau chạy build: hai file mã/test vẫn đúng hash cuối của lượt.
- C01_fix.patch chứa đúng diff so snapshot và bản tài liệu do Codex tạo. **Phần tài liệu trong patch chưa phản ánh file đang nằm trên đĩa**: sau khi tạo, docs/C01_DUONG_CO_SO_BUILD.md bị writer khác thay bằng bản mở đầu “Người lập: Claude (dev)” (quan sát mốc 16:31:03, độ dài 11.972 byte). Đã dừng ghi vùng này, không ghi đè.
- Bản quan sát của writer khác được giữ ở C01_document_observed_other_writer.md. Tài liệu đó còn nói điều kiện vật tư theo logic cũ, thiếu So_hang_muc và chứa kết quả workbook cũ. **Cần điều phối khóa writer, áp/hợp nhất phần docs trong C01_fix.patch rồi review lại tài liệu.** Không coi tài liệu hiện tại đã đồng bộ.
- Không xác định được handle tiến trình writer; bằng chứng trực tiếp là nội dung file mới thay bản vừa tạo. Không kết luận full suite/DB đang chạy từ timestamp. Lượt này không chạy chúng.

## Bốn sửa chữa

1. Cặp PT/mã không tương thích không tự đổi mã; COP_PHA/COT_THEP giữ quy tắc riêng.
2. Có lượng nhưng missing hoặc D: giữ tổng biết, he_thong_du=False, chênh/% trống; dòng là một phần.
3. Xuất So_hang_muc đầy đủ từng dòng, nguồn/tồn tại/phạm vi và liên kết đáp án; không có đáp án không bị hiểu thành không tồn tại.
4. Vật tư không so tổng hai phạm vi khác nhau. Giữ lượng quy đổi biết được ngay cả khi không so được.

**Giới hạn điểm 4:** hợp đồng hiện tại chỉ có cong_tac_id ở nguồn và uses.work/plan/quantity ở hệ thống; không có liên kết xác nhận cùng bộ cấu kiện, cùng quy cách/phạm vi và cách phân bổ hao hụt mua. Tập mã công tác bằng nhau chỉ là điều kiện cần. Vì vậy code chặn toàn bộ phép chênh vật tư hiện tại; đây là báo thiếu bằng chứng, **không phải hoàn thiện chức năng đối chiếu vật tư**. Test kiểm cả khác tập công tác và cùng tập nhưng chưa chứng minh cùng chi tiết. Để mở, cần dữ liệu truy vết được kiểm xác nhận từ từng dòng nguồn đến đúng tập uses/cấu kiện cùng quy cách, kèm cơ sở lượng mua và hao hụt tương đương; chưa đổi schema/engine để tạo cổng đó trong lượt này.

## Kiểm đã chạy

```powershell
$env:OPTIMAT_NO_DOTENV='1'
$env:PYTHONIOENCODING='utf-8'
Remove-Item Env:DATABASE_URL,Env:OPTIMAT_TEST_DATABASE_URL,Env:OPTIMAT_CATALOG_OVERLAY -ErrorAction SilentlyContinue
.venv/Scripts/python.exe -m pytest tests/test_c01_duong_co_so.py tests/test_ground_truth_manifest.py tests/test_ground_truth_d02.py tests/test_evaluate_rough.py -q -p no:cacheprovider --basetemp=reports/c01_review_fix/pytest_tmp
.venv/Scripts/python.exe scripts/c01_duong_co_so.py --out reports/c01_review_fix/c01_duong_co_so_build.xlsx
```

- pytest.log: **42 passed, EXIT=0**. SYNTHETIC chỉ kiểm hành vi, không đo độ chính xác.
- build.log: **EXIT=0**, chạy build 46; bỏ banve1 đúng cổng. Không .env, DATABASE_URL hay overlay mẫu; nguồn danh mục CSV repo, không DB.
- Workbook riêng không đè workbook dev: 64 dòng gốc, 65 con; 31 IN, 28 OUT, 3 hỗn hợp, 2 chưa phân loại. So_hang_muc 47 dòng, 18 chưa rõ; mẫu số 34 dự kiến, 0 da_kiem. 25 nhóm công tác, 17 nhóm được phép đối chứng theo logic hiện có; **không phải KPI nghiệm thu**. 24 dòng vật tư, 0 dòng đủ chứng minh để so. workbook_check.json lưu kiểm đếm.
- Chưa chạy toàn suite/DB hoặc nghiệm thu nghiệp vụ. Không nâng D02 da_kiem. Các hở thuật toán trong M01 vẫn thuộc sprint sau.

## Ba nhóm đối chiếu tay trên workbook lượt sửa

1. **Công tác cột:** nhóm COT dùng 46-C08 duy nhất; tham chiếu 17,092 m³, hệ thống 18,625 m³ (A), chênh 1,533 m³, +9,0%. Bốn dòng con C08.1–C08.4 không cộng thêm vào số gốc, không thành bốn phép so độc lập. Đây là chênh nguồn chưa kiểm.
2. **Dòng gộp lót móng/nền:** 46-C05 = C05.1 2,744 + C05.2 9,040 = 11,784 m³. Nhóm BE_TONG_LOT đối chiếu 11,784 với hệ thống 10,796 (C), chênh −0,988 m³, −8,4%. Cha/con chỉ góp một lần; ghi phụ thuộc foundations, không coi khớp thông số là chứng minh tự nhận đúng.
3. **Vật tư mua/lắp đặt:** 46-V01 đá mua 126,3733 m³; lượng hệ thống biết 104,070 m³ nhưng chưa đủ nên không chênh/%. 46-V24 cọc lắp đặt 308 m không ghép với lượng mua; ghi rõ hệ thống không xuất lượng lắp đặt riêng theo quy cách. Nhóm thép >10 chưa rõ không tự ghép ≤18. Các dòng mua khác cũng chưa có bằng chứng cùng phạm vi/hao hụt, không được dùng 0 phép so như bằng chứng chức năng đã hoàn thiện.

Dòng nhật ký đề xuất: “03/11/2026 — Codex sửa bốn lỗi C01, 42 test trọng tâm đạt, xuất workbook build riêng; mã/test ổn định theo hash. CHỜ REVIEW; tài liệu C01 bị writer khác thay, cần khóa/hợp nhất patch; đối chiếu vật tư còn chờ dữ liệu truy vết cùng phạm vi và hao hụt. Chưa full suite/DB, chưa N01/A01.”
