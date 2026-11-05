BẢN HOÀN THIỆN complete2 - 04/11/2026

Đã xử lý 558 bảng còn lại thành 331 bảng tài nguyên, 19 bảng công tác đơn, 33 bảng tỷ lệ chi phí, 23 bảng hệ số, 42 bảng thuộc tính, 41 bảng phân loại, 48 bảng mục lục, 18 mảnh bố cục và 3 ghi chú. Các mảnh bố cục/ghi chú được giữ để truy vết, không tính là định mức mới.
Cả 3.271 dòng thiếu cơ sở đơn vị đã có basis và basis_evidence, gồm câu trích, nguồn và trang/ô bảng. Công cụ audit_quantity_basis.py so khớp đủ 3.271 câu trích và kiểm tra lại hash 30 tệp gốc.
Tổng số dòng được lập chỉ mục trong norms.jsonl là 59.050, thuộc 9.286 mã định mức. Tệp reference_tables.jsonl giữ 558 bảng vừa xử lý, 7.047 dòng tài nguyên theo mã bảng/biến thể gốc; trong số này chỉ dòng có mã công tác đầy đủ được đưa thêm vào norms.jsonl. Không tự biến mã bảng B/C/AO thành mã công tác.

TỆP MỚI
- reference_tables.jsonl: table_kind, column_paths, records và resources. Mỗi giá trị giữ hàng, cột, văn bản và tọa độ nguồn. Bảng tỷ lệ chi phí không trở thành vật liệu; mục lục không trở thành định mức.
- basis_evidence.json: 3.271 lần bổ sung cơ sở đơn vị, dùng để duyệt và đối chiếu.
- evidence_validation.json: kết quả so khớp câu trích và hash bản gốc.
- quality_report.json/completion: số lượng ban đầu, kết quả xử lý và số còn thiếu. tables_grid_only=0 có nghĩa mọi bảng đã có cấu trúc tài nguyên hoặc bảng tham chiếu, không có nghĩa cả mục lục và ghi chú đều là bảng hao phí.

TRA BẢNG THAM CHIẾU
kb.reference_table("TT38_2026_9-p11-t1", include_candidates=True)
Bảng này có table_kind=cost_rate và trường tỷ lệ %. Bộ đọc không tự nội suy hoặc áp tỷ lệ vào chi phí.
Các điều kiện chiều cao, khẩu độ, đường kính là trục chọn biến thể; không dùng đơn vị của trục này thay đơn vị công tác.
Đơn vị "chỉ tiêu" trong thí nghiệm không đồng nhất với "mẫu". "t/lần_đầu" và "t/1_lần_di_chuyển_tiếp_theo" giữ riêng điều kiện mỗi lần. "sứ_nguyên_bộ" không đồng nhất với một chiếc sứ.
Các dòng công tác bốc xếp AM.112 tính công/đơn vị vật liệu: gạch tính trên 1.000 v, xi măng trên tấn, gỗ trên m3... Chúng là hao phí nhân công, không phải lượng vật liệu mua.

TÁI TẠO PHẦN BỔ SUNG
- scripts/quantity_completion.py: nhận dạng và truy cơ sở đơn vị theo đúng nhóm mã.
- scripts/quantity_semantic_tables.py: bảng có ô gộp, cấp phối theo hàng/cột, bảng nhân công và cấu trúc tham chiếu.
- 07-hoan-thien/cache_pdf_words.py: lấy tọa độ chữ từ 392 trang có bảng cần xử lý, lưu cache trong bộ nguồn.
- python scripts/build_quantity_knowledge.py <bo-nguon>
- python scripts/audit_quantity_basis.py <bo-nguon> data/rules/vn_quantity
- python <04-xu-ly>/validate_json_pack.py data/rules/vn_quantity
- python -m pytest tests/test_quantity_knowledge.py tests/test_quantity_completion.py -q --basetemp tmp/<thu-muc-moi>

Giữ trạng thái chờ duyệt chuyên môn; chưa ghi đè CSV, database hoặc tự bật quy tắc. Số liệu có nhiều biến thể, phần trăm, ô trống và điều kiện lựa chọn vẫn giữ nguyên để kiểm tra; không tự cộng các phương án vật liệu thay thế.

THÔNG TIN NỀN CỦA BỘ NGUỒN
========================================
BỘ NGUỒN ĐO BÓC VÀ ĐỊNH MỨC JSON CHO OPTIMAT AI
Phiên bản schema: optimat.quantity-knowledge.v1

CẤU TRÚC
- manifest.json: phiên bản, số lượng và SHA-256 của từng tệp.
- sources.json: nguồn chính thức, bản gốc, ngày áp dụng, SHA-256 và số trang OCR.
- page_text.jsonl: từng trang PDF, ưu tiên chữ gốc; trang thiếu chữ dùng OCR tiếng Việt. Giữ method và trạng thái kiểm tra.
- tables.jsonl: lưới bảng, văn bản gốc từng ô, tọa độ PDF theo point, số thập phân chuẩn hóa và ngữ cảnh trước bảng.
- norms.jsonl: mỗi dòng là một tài nguyên của một mã định mức đầy đủ và một biến thể/cột bảng. Có basis, quantity, resource_unit, source_id, pdf_page, table_id, grid_row, grid_column.
- measurement_rules.json: 38 quy tắc đo bóc đã bổ sung phạm vi công tác OptiMat, mục đích, ngày áp dụng, điều kiện, tác động và văn bản nguồn.
- applicability.json: ba hồ sơ phiên bản; phải kiểm tra thêm chuyển tiếp và hợp đồng.
- schema.json: JSON Schema Draft 2020-12; chọn $defs.norm, table, page hoặc measurement_rule.
- quality_report.json: bảng chỉ còn ở dạng lưới, thiếu cơ sở định mức, tỷ lệ %, ô trống, mã có nhiều giá trị và trang OCR điểm thấp.
- schema_validation.json: kết quả kiểm tra toàn bộ schema và SHA-256.

QUY ƯỚC SỐ
Số thập phân được lưu bằng chuỗi để tránh sai số float. Ví dụ 0,017 -> "0.017".
Theo cách ghi số Việt Nam, 1.020 kg được chuẩn hóa thành "1020", ghi number_format=vi_dot_thousands và đánh dấu để rà soát. Văn bản gốc vẫn giữ quantity_raw. Dạng 0.833 được hiểu là thập phân, không phải 833.
Ô trống hoặc dấu gạch có quantity=null, không đổi thành 0.
quantity là hao phí trên toàn bộ basis. Lượng tài nguyên = lượng công tác × quantity / basis.quantity; đơn vị công tác phải khớp basis.unit.
Ví dụ basis 100 m, lượng công tác 10 m, hao phí 0,2 cái: kết quả 0,02 cái.
Dòng value_type=percentage cần cơ sở chi phí riêng; không nhân như lượng vật liệu.
quantity_per_basis_unit chỉ để tra cứu đối chiếu, không nhân thêm cùng quantity một lần nữa.
Cấp phối vật liệu cho 1 m3 VỮA bê tông không tự động đồng nhất với lượng cho 1 m3 KẾT CẤU bê tông.

ĐỌC TỪ MODULE
from datetime import date
from optimat.rough.quantity_knowledge import QuantityKnowledge, resource_consumption

kb = QuantityKnowledge()
rows = kb.norms_for_code("AK.21120", as_of=date(2026, 11, 4), include_candidates=True)
mortar = next(r for r in rows if r["resource_name"] == "Vữa xi măng")
print(resource_consumption(mortar, "10", "m2", preview=True))  # Decimal("0.170")
rules = kb.rules_for_work("XAY", as_of=date(2025, 4, 1), purpose="estimate", include_candidates=True)

Không truyền include_candidates thì chỉ trả dữ liệu enabled=true, review_status=approved, có approved_by và approved_on. Bộ hiện tại chưa có bản ghi được duyệt chuyên môn nên truy vấn mặc định trả rỗng. Đây là tích hợp bộ đọc dữ liệu nguồn, chưa thay bộ tính hoặc hệ số đang vận hành.
preview=True là tính thử trên bản ghi được chọn rõ; không xác nhận định mức phù hợp dự án.
Mã có nhiều biến thể/kết quả phải chọn bằng điều kiện và nguồn; không lấy dòng đầu tiên một cách mặc định.
Quy tắc có work_scope=outside_current_rough_module được giữ để mở rộng tra cứu, không áp dụng lên mọi công tác phần thô.

TÁI TẠO DỮ LIỆU
Các công cụ OCR/trích bảng nằm trong thư mục 04-xu-ly của bộ nguồn gốc tại outputs/bo-quy-tac-boc-tach-vn-2026-11-04.
1. python <04-xu-ly>/ocr_scans.py <bo-nguon> --jobs 3
2. python <04-xu-ly>/extract_norm_tables.py <bo-nguon> --jobs 4
3. python <04-xu-ly>/repair_resource_labels.py <bo-nguon>
4. python scripts/build_quantity_knowledge.py <bo-nguon>
5. python <04-xu-ly>/validate_json_pack.py data/rules/vn_quantity
6. python -m pytest tests/test_quantity_knowledge.py -q --basetemp tmp/quantity-knowledge-tests-<ten-moi>

Công cụ chuẩn bị dữ liệu cần pdfplumber, pypdfium2, Pillow, jsonschema và Tesseract; bộ đọc trong module chỉ dùng thư viện chuẩn Python. OCR dùng Tesseract ở C:\Program Files\Tesseract-OCR và mô hình vie.traineddata tại 04-xu-ly/tessdata.
Mô hình tiếng Việt: https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/vie.traineddata
SHA-256 mô hình đã dùng: 79df64caf7bcfb2a27df5042ecb6121e196eada34da774956995747636d5bfa1
PDF gốc không bị chỉnh sửa. Cache từng trang/bảng cho phép chạy tiếp nếu bị gián đoạn.

PHẠM VI KIỂM TRA
Đã kiểm tra schema, dấu số, trang nguồn, liên kết bảng, checksum, ranh giới phiên bản và các phép quy đổi. Có đối chiếu trực quan một số trang; không xác nhận toàn bộ hơn 55 nghìn hao phí bằng đọc tay.
Không tự bịa hệ số chuyển đổi, mã vật liệu danh mục, neo/nối, hao hụt, cơ sở phần trăm hoặc đơn vị còn thiếu.
Những bảng không tách chắc chắn được thành dòng tài nguyên vẫn giữ nguyên lưới có tọa độ. Bảng tỷ lệ chi phí, bảng phân loại và bảng đặc biệt không bị ép thành hao phí vật liệu.
OCR có thể sai dấu, mã và công thức dù điểm nhận dạng cao. Dùng bản gốc để quyết định pháp lý hoặc con số đang bị đánh dấu; ưu tiên bản chữ gốc thay bản OCR trùng nội dung nếu có.
Quyết định 1041 là hướng dẫn tham khảo; các quy tắc lịch sử của TT13/2021 không tự áp dụng cho mọi hồ sơ 2026.
Không ghi DB, thay đổi CSV định mức hoặc bật quy tắc chờ duyệt trong bộ tính hiện hành.
