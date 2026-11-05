> Hướng dẫn độc lập cho bản sửa Codex. File canonical `docs/C01_DUONG_CO_SO_BUILD.md` chưa đồng bộ vì xung đột writer; không dùng file đó để mô tả hành vi bản sửa.

# C01 — Đường cơ sở phần thô trên build

Báo cáo phát triển, **không phải độ chính xác nghiệm thu**. D02 chưa được người kiểm xác nhận; mẫu số chỉ dự kiến. Không chạy bộ test/banve1, không sửa đáp án hoặc quy tắc để khớp kết quả.

## Chạy lại với CSV cô lập

Chạy PowerShell tại thư mục repo `optimat-ai`:

```powershell
$env:OPTIMAT_NO_DOTENV='1'
$env:PYTHONIOENCODING='utf-8'
Remove-Item Env:DATABASE_URL,Env:OPTIMAT_TEST_DATABASE_URL,Env:OPTIMAT_CATALOG_OVERLAY -ErrorAction SilentlyContinue
.venv/Scripts/python.exe scripts/c01_duong_co_so.py --out reports/c01_review_fix/c01_duong_co_so_build.xlsx
```

Cờ đầu ngăn đọc `.env`; bỏ DATABASE_URL và overlay để dùng đúng CSV thật trong repo. Không nhập DB. Lệnh ghi đè **chỉ đường dẫn --out**; lượt sửa này không ghi đè workbook ban đầu của dev.

Luồng: manifest → cổng phat_trien/build → validator D02 → rough_for_case/compute_rough → ánh xạ đối chứng → bảng Excel. Hash trong workbook ghi các file mà bộ sinh hiện theo dõi; không phải chứng nhận trạng thái toàn repo hoặc snapshot DB.

## Quy tắc đọc báo cáo

- Doi_chieu_cong_tac giữ dòng gốc, OUT/chờ phân loại/chưa ánh xạ. Con `phan` đóng góp một lần; không cộng cha với con. Tổng hệ thống chỉ so một lần tại So_sanh_nhom, không phân bổ về từng dòng nguồn.
- PT_WORK chỉ chấp nhận cặp PT/mã tương thích. COP_PHA ghép theo cấu kiện; COT_THEP giữ cơ sở cấu kiện theo quy tắc hiện có. Cặp khác không tự đổi mã.
- Lượng khác None vẫn có thể chưa đủ. Công tác có missing hoặc D làm nhóm chưa đầy đủ; giữ tổng phần biết, để chênh và % trống. Nhãn có kết quả vẫn là đề xuất chưa xác nhận, không chứng nhận H1.
- So_hang_muc giữ từng dòng sổ D02, nguồn tồn tại, phạm vi và liên kết đáp án theo id hạng mục hoặc PT. Không có đáp án không đồng nghĩa không tồn tại. Hạng mục chưa rõ giữ nguyên chưa rõ.
- Vat_tu_nhom giữ lượng nguồn và lượng hệ thống quy đổi chính xác được, kể cả chưa so được. Không dùng hai số cạnh nhau như hai lượng cùng phạm vi. Mua/lắp đặt, dòng loại trừ, khác đại lượng hoặc lượng chưa đủ đều chặn phép so.
- Mã vật tư và tập mã công tác giống nhau **chưa chứng minh cùng cấu kiện, quy cách và hao hụt**. Hợp đồng hiện tại không cung cấp liên kết đủ chặt giữa từng dòng nguồn và uses; vì vậy lượt này chặn phép tính chênh vật tư, ghi lý do. Không tự phân bổ, không suy tỷ lệ. Cần dữ liệu truy vết và cơ sở lượng đã kiểm trước khi mở phép so.
- Theo_trang_thai kế thừa nhóm A/B và C/D của evaluator; không dùng nhóm C/D như KPI A/B. Đáp án 0 để % trống. Lượt này chưa đổi hợp đồng thống kê dùng chung.
- He_thong_vat_tu giữ uses/nhóm/loại và mức đủ của engine. Tổng kg không ghép trực tiếp với m³/viên.

## Kiểm và bàn giao

Snapshot trước sửa, hash, diff của lượt, log test và log chạy build nằm trong `reports/c01_review_fix/`. Xem `BAN_GIAO.md` tại đó để biết kết quả thực tế và ba nhóm đối chiếu tay. Không sửa engine/evaluator/D02/định mức trong lượt này. Chưa chạy toàn suite hoặc DB; chờ điều phối review độc lập trước cấp lượt tiếp.

Các hở thuật toán/đầu vào ghi nhận trong M01 thuộc N01/N02/N03/A01/Q01/Q02; C01 chỉ phản ánh giới hạn, chưa triển khai các sprint đó. Chưa tự nghiệm thu C01 hoặc nâng trạng thái đáp án D02.
