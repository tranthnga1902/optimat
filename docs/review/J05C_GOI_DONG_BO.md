# J05c - Gói đồng bộ tối thiểu sau C01

Ngày rà: 03/11/2026. Theo [phân công điều phối](DIEU_PHOI_20261103.md), ưu tiên 3: chỉ đọc và chuẩn bị; **chưa cấp lượt ghi dữ liệu/mã hoặc chạy test/DB**. Trạng thái: **CẦN SỬA hướng dẫn phát hành; CHỜ LƯỢT SAU C01; CHỜ NGƯỜI KIỂM cho áp hồ sơ**.

Tài liệu tương đương về bằng chứng đã có: [J05C thiết kế, mục 9](../research/J05C_TRAT_THIET_KE.md). Gói này bổ sung trạng thái mới, phạm vi quyền ghi và điểm rollback còn hở; không thay hoặc viết lại bàn giao đó. [Review V2](J05BCD_CODEX_REVIEW_V2.md) mô tả mốc lịch sử SQL còn cũ; không dùng nhận định đó như hiện trạng SQL nữa.

## 1. Hiện trạng được đọc trong lượt này

| Thành phần | Bằng chứng | Kết luận |
|---|---|---|
| Mã J05c | `materials_for_works` tra `<dày>/<family>`; `wall_works` truyền phương án; `compute_rough` giữ evidence lựa chọn theo lớp | Đã triển khai, không sửa trong lượt này |
| CSV | Bốn dòng TRAT đầu tệp `data/rules/dinh_muc_phan_tho.csv` | Khóa/số mới như bảng dưới |
| SQL | `sql/05_rules.sql`, bốn INSERT TRAT tại dòng 50-53 | Hiện đã khớp khóa/số/nguồn TRAT trong CSV, không còn hai khóa cũ ở các INSERT này |
| DB vận hành | Truy vấn chỉ đọc ở review V2 trước đây trả `15=0.017`, `20=0.023`; mục 9 bàn giao nói chưa nạp DB thật | **Mốc quan sát trước**, không có truy vấn mới trong lượt này. Chưa xác nhận DB hiện tại đã đổi hay chưa; không được báo đã đồng bộ |
| DB kiểm thử | Mục 9 bàn giao ghi loader có 68 dòng, bốn khóa TRAT mới; 20 test đạt | Bằng chứng do Claude bàn giao, chưa chạy xác nhận lại trong lượt này |
| check_data | Mục 8 đã đính chính lần 0 lỗi/1915 cảnh báo là PostgreSQL; mục 9 ghi lần CSV và DB kiểm thử riêng | Đã sửa mô tả tài liệu; báo cáo scratchpad không được đính kèm trong gói này, chưa kiểm file báo cáo gốc |
| Test bổ sung | Có test family trống, quantity=None trong `tests/test_rough_plaster.py`, test loader trong `tests/test_db.py` | Đã thấy mã test; không suy thành kết quả chạy mới |

| Khóa TRAT phải có ở mỗi nguồn mới | qty m³/m² |
|---|---:|
| 15/CLAY_SOLID | 0.017 |
| 15/CLAY_HOLLOW | 0.0187 |
| 20/CLAY_SOLID | 0.023 |
| 20/CLAY_HOLLOW | 0.0253 |

Hash SHA-256 tính ở lượt rà này:

- CSV: `0E677EAA3CFFEB4AFFD1FA3BAAAFB35C288F63E05EC39481E73C437CB092D542`.
- SQL: `2108179AE52542B73A3F21BB9CBE1795E5C6CBBB3E717BE49A259959236B19D2`.

Đã đọc trực tiếp các dòng TRAT, chưa so toàn bộ SQL với mọi bảng CSV. Bàn giao mục 9 ghi SQL đã sinh từ 31 lên 68 dòng rough_norms và có thay đổi ngoài J05c. Hiệu số tổng là 37; riêng TRAT từ 2 lên 4 tăng 2, nên không mô tả cả 37 dòng tăng là ngoài J05c nếu chưa liệt kê/diff lại. Chưa xác minh độc lập số tổng và nguồn từng dòng ngoài TRAT ở lượt này.

## 2. Lệch còn phải quản lý

1. **CSV/SQL TRAT đã khớp ở trạng thái đọc được; DB vận hành chưa có bằng chứng đồng bộ mới.** Mã mới với DB khóa cũ trả thiếu ngay cả với nền đã biết. Mã cũ với dữ liệu khóa mới cũng không tìm được khóa theo dày thuần. Phải chốt phiên bản mã và dữ liệu cùng lần phát hành, không tự fallback về khóa cũ để che lệch nguồn.
2. **Phạm vi nạp rộng hơn phần cần sửa:** `scripts/init_db.py --reload-rules` xóa/nạp lại sáu bảng trong `RULE_TABLES`, không chỉ rough_norms. Script còn có các bước create_all/nạp bảng trống; lệnh này không phải migration chỉ dành J05c. `sql/05_rules.sql` cũng chứa sáu bảng và có BEGIN/COMMIT. Vì vậy không coi hai cách là tương đương về mọi tác dụng phụ/khả năng hoàn tác.
3. **Rollback hiện tại thiếu phạm vi:** mục 9 đề xuất sao lưu riêng rough_norms rồi cho chạy reload sáu bảng. Nếu chọn nạp sáu bảng, phải chốt/sao lưu/khôi phục đủ sáu bảng bị tác động. Nếu chỉ được phép rough_norms, cần thao tác nạp có giới hạn bảng đó, transaction và bản sao đúng phiên bản được review trước; chưa có quyền tạo script mới trong lượt này. Không chạy toàn 05 rồi chỉ khôi phục một bảng.
4. **Cache tiến trình:** `load_norms` có cache; đổi DB không tự bảo đảm các worker đang chạy đọc dữ liệu mới. Kế hoạch phát hành cần khởi động lại tiến trình hoặc cơ chế xóa cache hiện có sau nạp thành công. Kiểm nguồn trong tiến trình mới, không chỉ query DB rồi kết luận ứng dụng đã dùng số mới.

## 3. Bản sửa tối thiểu đề xuất cho lượt được cấp sau C01

Không cần đổi công thức J05c, không cần schema mới. Trước hết sửa hướng dẫn phát hành/rollback tại mục 9 của tài liệu thiết kế cho đúng phạm vi nạp đã được chọn. Đính kèm hoặc chuyển bằng chứng test/check_data từ scratchpad sang vị trí bàn giao được điều phối cấp, có nguồn CSV/DB kiểm thử và hash; không ghi đè reports chung.

Đối với dữ liệu, ưu tiên kiểm lại SQL đã sinh hiện tại; không sinh lại thêm nếu nó đã khớp và không có thay đổi nguồn mới. Nếu cần sinh, dùng script chuẩn, khóa cả các tệp mà script có thể ghi, kiểm diff ngoài TRAT. Không sửa tay SQL sinh.

Trước triển khai thực, người phụ trách phải trình điều phối/chủ đồ án **một** phạm vi nạp cụ thể (rough_norms riêng hoặc cả sáu bảng), snapshot/backup thực tế và rollback tương ứng; đối chiếu baseline C01 và phiên bản chạy. Không dùng git HEAD như bản sao DB hoặc bản mã phát hành mặc định vì workspace có nhiều thay đổi chưa commit. Không hoàn nguyên cả file bằng checkout/reset làm mất phần việc của phiên khác; chỉ rollback phần diff J05c từ snapshot đã khóa.

Nếu đồng bộ DB vận hành được cho phép sau này: kiểm chỉ đọc nguồn/khóa hiện thời trước, sao lưu phạm vi đã chốt, nạp theo kế hoạch được review, restart/cache refresh và smoke check. Hiện **chưa có quyền nạp DB thật**, chưa thực hiện bất kỳ bước ghi nào.

## 4. File và quyền cần điều phối cấp

| File/vùng | Quyền cần ở lượt sau | Lý do |
|---|---|---|
| `docs/research/J05C_TRAT_THIET_KE.md` mục 9 | Ghi đoạn phát hành/rollback và bằng chứng | Sửa phạm vi nạp, mốc dữ liệu, cache |
| `sql/05_rules.sql` | Chỉ ghi nếu cần sinh lại sau rà diff | Hiện TRAT đã khớp; có nhiều thay đổi ngoài J05c cần giữ |
| `sql/01_schema.sql`, `sql/02_seed_sample.sql` | Khóa nếu chạy export_sql.py | Script có thể ghi cả ba tệp, không tự nhận quyền sửa ngoài 05 |
| `data/rules/dinh_muc_phan_tho.csv` | Chỉ đọc/khóa phiên bản; ghi khi có lỗi nguồn mới được giao | Bốn khóa đã đúng; không mở raw_class |
| `tests/test_rough_plaster.py`, `tests/test_db.py` | Chỉ đọc; ghi nếu test thiếu/thất bại cụ thể được giao | Hai ca bổ sung và assertion DB đã tồn tại |
| `walls.py`, `materials.py`, `takeoff.py`, `models.py` | Không cần ghi cho việc đồng bộ hiện tại | Công thức đã có; tránh chồng phiên C01 và phần việc khác |
| Báo cáo riêng cho J05c | Cấp thư mục đầu ra riêng | Không ghi đè `reports/data_check.*` của phiên khác |
| PostgreSQL kiểm thử | Cấp lượt độc quyền chạy/nạp test | Fixture có thể reset; xác minh đúng DB riêng trước khi chạy |
| PostgreSQL vận hành | Chờ chủ đồ án cho phép phạm vi nạp cụ thể | Không phải quyền được giao trong gói này |

Metadata `rough_norms.raw_class` của J05b/J05d là thay đổi schema khác, **chờ chủ đồ án duyệt**, không cần để đồng bộ J05c. Không triển khai kèm, không đổi đơn vị CP04 hoặc thêm liều phụ gia.

## 5. Kiểm tra cần chạy khi được cấp lượt

Các lệnh/ca sau là kế hoạch, **không chạy ở lượt lập gói**:

1. Nhóm CSV: `pytest tests/test_rough_plaster.py tests/test_rough_materials.py tests/test_rough_walls.py tests/test_rough_status.py -q`, tiến trình test không dùng DB vận hành. Kiểm nguồn loader thực sự CSV và bốn khóa mới; family trống, thiếu lượng, AAC/chưa rõ vẫn thiếu, nền đặc/rỗng đúng, CAN_NEN không đổi.
2. Nhóm DB riêng: bài `tests/test_db.py::test_rules_and_families_from_db` cùng fixture seeded_db sau khi điều phối cấp DB kiểm thử. Fixture reset chỉ được chạy khi xác nhận đích là DB kiểm thử. Xác minh cả loader và kết quả vật liệu GN01/GN02 qua đường DB; assertion bốn khóa một mình chưa chứng minh số đầu ra.
3. check_data theo từng nguồn bằng cách cô lập đúng môi trường/catalog/loader, báo cáo riêng, ghi hash và nguồn. Không dùng 0 lỗi của DB cũ để duyệt CSV mới. Không in URL/mật khẩu kết nối.
4. Full pytest chỉ do điều phối cấp lượt sau cùng; không lấy các con số lịch sử 43/20/390/395 làm kết quả hiện tại. Lỗi encoding trước đây không tái hiện khi chạy riêng ở review V2, không vì vậy kết luận toàn suite đã đạt.
5. Sau nạp được phép ở môi trường đích: tiến trình mới/refresh cache, kiểm bốn khóa, ca trát có nền xác định, API/BOQ cùng số/đơn vị và phần thiếu; không gọi đây là KPI trên hồ sơ thực khi chưa có người kiểm D02.

## 6. Bàn giao cho điều phối

- **File tạo duy nhất:** `docs/review/J05C_GOI_DONG_BO.md`.
- **Bằng chứng mới:** đọc SQL đã cập nhật, CSV, nhánh tra mã, loader DB/CSV, cache, script nạp sáu bảng, test bổ sung và bàn giao mục 9; tính hai hash nêu trên. Không truy vấn DB ở lượt này.
- **Không thực hiện:** sửa mã/CSV/SQL/DB, nạp DB, test trọng tâm/full/DB, check_data hoặc sửa báo cáo chung. Không chỉnh NHAT_KY/SPRINTS/kế hoạch và không đánh da_kiem/nghiệm thu.
- **Còn thiếu:** reviewer kiểm báo cáo gốc/DB kiểm thử khi được cấp lượt; phạm vi phát hành/backup/rollback rõ ràng; quyền nạp DB vận hành; xác nhận nghiệp vụ D02. Triển khai sau đường cơ sở C01 theo điều phối.
- **Dòng đề xuất để điều phối ghi nhật ký:** “03/11/2026 - Rà chỉ đọc J05c: TRAT CSV/SQL hiện khớp bốn khóa; DB vận hành chưa xác minh lại; lập J05C_GOI_DONG_BO.md, chỉ ra phạm vi reload sáu bảng/rollback/cache, chưa chạy test hoặc nạp DB; chờ lượt sau C01.”
