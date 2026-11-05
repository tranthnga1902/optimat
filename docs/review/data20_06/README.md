# Kiểm kê D01 và chọn hồ sơ tiên phong

## Kết quả và phạm vi

`HO_SO_INVENTORY.csv` có **458 đường dẫn**, gồm 277 dòng `SYNTHETIC` và 181 dòng `UNKNOWN`. Đã đọc byte và tính SHA-256 cho 458/458 đường dẫn, kiểm chữ ký sơ bộ theo định dạng; 28/28 file được liệt kê trong metadata bốn gói VN001–VN004 có mặt và hash khớp metadata. Số dòng là số **đường dẫn**, không phải số file độc lập hay số công trình; `duplicate_count` giúp phát hiện bản sao cùng hash trong phạm vi đã quét.

Phạm vi quét: `data_nha_o/`, `outputs/nha_o_20_moi/`, `outputs/nha_o_10_dxf_v1/`, `outputs/nha_o_synthetic_v1/`, `optimat-ai/data/drawings/`; gồm DWG, DXF, PDF, XLS/XLSX, JSON, MD, DOCX, RAR, ZIP. Không khẳng định đã kiểm kê mọi tệp trên máy hoặc các thư mục bản sao ngoài phạm vi này. Nhóm `project_candidate`, vai trò suy từ tên/thư mục là **ứng viên**, không là bằng chứng kỹ thuật. File metadata/README và bản sao trong phạm vi cũng có dòng riêng.

`UNKNOWN` là nhãn kiểm kê chưa xác minh nguồn/loại dữ liệu, **không phải giá trị cho phép trong `analysis_runs.data_kind`**. Không có dòng nào trong danh mục này được nâng thành `ACTUAL` chỉ vì được đăng tải. `SYNTHETIC` theo README các tập giả lập. Cột `version` để trống vì chưa có căn cứ xác định phiên bản hồ sơ gốc; tên hoặc mốc tạo file không thay thế được bằng chứng đó.

Đọc byte/hash và file magic là kiểm tra nhẹ, **không chứng minh mở CAD thành công, cặp KT/KC đúng phiên bản, công trình đã xây, tiên lượng chính xác hay quyền huấn luyện/phân phối**. Metadata cũ nêu PDF và sheet đã được kiểm nội dung trước đây; lượt này không chạy reader CAD hàng loạt. Không tải lên hoặc mở lại runtime ứng dụng.

## Pioneer Pack đề xuất: VN002 — nhóm build, chưa được phê duyệt phát hành

Sau đối chiếu board điều phối, chọn **VN002 nhà Sang, 4 tầng 4×15** là mục tiêu làm việc Pioneer BUILD thay lựa chọn nháp VN001. `data/ground_truth/du_toan/HO_SO_NHAP_20261103.md` và `incoming_20261103.json` ghi hai DXF KT/KC build, gói PDF nguồn và 249 công tác trích từ PDF; có báo cáo sử dụng kỹ thuật trước đó. Đây là lựa chọn để hoàn thiện luồng build, **chưa phải gói đạt D01**; chưa xác định mọi file thuộc cùng phiên bản thiết kế, khả năng mở của cả cặp, quyền huấn luyện hay đáp án độc lập.

| Vai trò ứng viên | Đường dẫn tương đối từ gốc workspace | SHA-256 |
|---|---|---|
| DWG `BỘ KỸ THUẬT`, ứng viên nguồn KT | `data_nha_o/ready/VN002_nha_pho_4_tang_4x15/BO KY THUAT NHA A SANG.dwg` | `36f2b110f04522e97ba481275f4594d3ea8b71442743f72f4b8fecc8f8489bc6` |
| KC DWG theo metadata | `data_nha_o/ready/VN002_nha_pho_4_tang_4x15/HO SO KET CAU NHA A SANG - HAI DUONG   15-10-2021.dwg` | `8e049401408d381aae3aa50b624f41cc13cf2f3d7955334ecbd213b6392cd51e` |
| KT DXF build theo báo cáo nhập | `optimat-ai/data/drawings/build/nha_sang_hai_duong_4x15_kien_truc.dxf` | `719ea17b22b856bb31363fbfc9bf218f312112958e9de4f6638e2ede1f1cf8d6` |
| KC DXF build theo báo cáo nhập | `optimat-ai/data/drawings/build/nha_sang_hai_duong_4x15_ket_cau.dxf` | `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c` |
| PDF KT | `data_nha_o/ready/VN002_nha_pho_4_tang_4x15/HỒ SƠ KIẾN TRÚC PDF.pdf` | `59cad635a392c11f061d5a4f78406c00b4248f810643b9332d4b085e0809ea88` |
| PDF KC | `data_nha_o/ready/VN002_nha_pho_4_tang_4x15/HỒ SƠ KẾT CẤU.pdf` | `4b6ca4f97e80b85ae4d1df555f13ad1b531c8243f52f300ec34d436357060344` |
| Dự toán PDF nguồn | `data_nha_o/ready/VN002_nha_pho_4_tang_4x15/DU TOAN NHA PHO 4 TANG 4X15M.pdf` | `31a9cbd2b0662f3d57cf069b2ad109f6a4702a8dc92b74d5ba24bd2acfcce92b` |

Nguồn gói và thông tin quyền theo `data_nha_o/ready/VN002_nha_pho_4_tang_4x15/metadata.json`: tải miễn phí, **chưa xác nhận quyền huấn luyện/phân phối lại**. Báo cáo nhập ghi cặp DXF liên quan VN002, nhưng lượt này chưa kiểm chuyển đổi bằng hash đầu vào/đầu ra và chưa tự xác nhận `BO KY THUAT` là KT. `docs/review/claude_20261104/BAO_CAO_REVIEW.md` ghi lượt xử lý hai DXF trước đây ra 61 công tác/8 dòng vật tư chưa được đánh đã kiểm; đó là bằng chứng xử lý lịch sử, không chứng minh mở lại hiện tại hay đáp án đúng. Metadata nguồn ghi `ACTUAL`, nhưng danh mục này không nâng thành dữ liệu công trình đã xây/được phép huấn luyện khi căn cứ chưa đủ.

**So sánh:** VN001 cũng là build theo `incoming_20261103.json`, có cặp KT/KC theo báo cáo nhập và dự toán; một test đọc riêng DXF KT được ghi tại `docs/review/J05BCD_CODEX_REVIEW_V2.md`, song quyền và version tương tự chưa rõ. Tân Bình đã được đăng ký BUILD trong `cases.csv` và VN004 là bản trùng theo báo cáo nhập, nhưng có gate từ chối upload hiện hành; không chọn để thử upload hoặc làm Pioneer mới. VN003 là cùng công trình Dĩ An đã đăng ký **TEST**, phải giữ split và không dùng để chỉnh quy tắc BUILD.

Việc cần làm trước khi gói thực sự sẵn sàng: xác nhận quyền và bảo mật/ẩn danh; chứng minh cặp KT–KC cùng công trình, đúng phiên bản và lineage DWG→DXF; mở cả hai file trong lượt được giao; kiểm đơn vị/tầng/vùng hình; lập đáp án và để người độc lập kiểm; chỉ sau đó tạo manifest có ID và nạp vào DB thử nghiệm. Không thay thế các bước đó bằng file giả lập.

## Năm ứng viên nguồn ngoài để tiếp tục thẩm định

| Ưu tiên | Gói | Căn cứ hiện có | Khoảng trống trước D01 |
|---|---|---|---|
| 1 | VN002 4 tầng 4×15 — BUILD | Metadata liệt kê PDF KT/KC, DWG KC và `BO KY THUAT`, PDF dự toán; báo cáo nhập ghi cặp DXF build. | Cần xác minh nội dung KT trong DWG, ghép cặp/version và quyền; không suy từ tên. |
| 2 | VN001 2 tầng 7×12 — BUILD | Gói nguồn liệt kê DWG/PDF KT–KC và PDF dự toán; báo cáo nhập ghi cặp DXF build. | Quyền huấn luyện, phiên bản, lineage và mở cặp chưa được xác nhận trong lượt này. |
| 3 | VN003 nhà phố 3 tầng — TEST | Gói `PHAN KIEN TRUC.dwg`, `PHAN KET CAU.dwg`, XLS dự toán; báo cáo nhập nói cùng Dĩ An đã đăng ký test. | Giữ TEST, không gộp vào BUILD; quyền, phiên bản và xác minh kỹ thuật chưa đủ; Excel dùng mã chữ VNI cũ. |
| 4 | `11_nha_o_AiPro` | Có `Kien truc.dwg`, `Ket Cau.dwg`, `Mong.dwg` theo tên. | Danh mục loại do thiếu dự toán; chưa chứng minh công trình thực, quyền hoặc cùng revision. |
| 5 | `06_nha_cap4_5x20` | Có một DWG, PDF và Excel. | Chưa chứng minh DWG có đủ KT/KC; Excel theo danh mục chỉ chi tiết gạch và tổng hợp chi phí, không đủ dự toán toàn nhà; quyền và thực tế chưa xác minh. |

Năm mục là danh sách **đề xuất thẩm định**, không phải năm hồ sơ thực sẵn sàng; hai mục cuối thiếu đáng kể. Mục tiêu ít nhất hai công trình TEST độc lập là **yêu cầu thu thập**, không chứng minh hiện đã có hai file hay hai bộ hồ sơ đủ điều kiện. `VN004_nha_o_Tan_Binh` được kiểm kê theo metadata/hash nhưng có gate từ chối upload hiện hành, không đưa vào Pioneer hoặc thử upload. Các thư mục trùng VN002/VN003 ghi tại `data_nha_o/excluded.json` không tính là công trình độc lập. Các tập P/H là đối chứng giả lập, không tính vào chỉ tiêu năm hồ sơ thực; các mẫu cùng bộ sinh không được chia ngẫu nhiên thành train/test độc lập như thể khác nguồn.

Khi được phân quyền sửa canonical sau này, cần đối chiếu `data/ground_truth/du_toan/incoming_20261103.json`, `cases.csv`, metadata trong `data_nha_o/ready/` và manifest D01 với cùng identity/split/version/quyền; không sửa các tệp đó trong lượt kiểm kê. VN001/VN002 chưa được đăng ký làm case evaluator theo báo cáo nhập, còn VN003 phải giữ alias Dĩ An TEST và VN004 alias Tân Bình BUILD. Không tự cập nhật `cases.csv` bằng dữ liệu chưa kiểm.

## Cột và sử dụng danh mục

Đọc CSV bằng UTF-8 BOM để Excel nhận dấu. `path` tương đối từ `C:/Users/Admin/Downloads/optimat-ai_6`; `source` có thể là link nguồn hoặc file README/metadata nội bộ và để trống khi chưa biết. `usage_rights` không phải giấy phép đã xác minh; `read_status` chỉ nói đọc byte. `signature_check` là sơ bộ, còn `parser_open_status` phản ánh chưa chạy parser trong lượt này. `duplicate_count` chỉ đếm bản sao cùng SHA-256 trong phạm vi quét, không đếm file giống nội dung nhưng byte khác. Không dùng CSV này làm lệnh import DB.

Chi tiết ánh xạ và các điều kiện nhập nằm trong `SCHEMA_MAPPING.md`. Không sửa file gốc, không nhập DB, không khẳng định đã có 20 bảng trên DB ứng dụng.
