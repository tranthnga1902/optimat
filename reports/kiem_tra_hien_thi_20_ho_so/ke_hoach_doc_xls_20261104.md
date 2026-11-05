# Kế hoạch hỗ trợ DOC/XLS cũ — chỉ rà soát

Trạng thái: **đề xuất để rà soát, chưa cài thư viện, sửa mã hoặc chạy thử**. Hai định dạng vẫn bị từ chối rõ ở `project_document_io.py`; không quảng bá đã hỗ trợ. Không áp dụng với DOCX/XLSX.

## Phụ thuộc đề xuất và giới hạn

Đề xuất `olefile==0.47` để kiểm tra container OLE/stream và `xlrd==2.0.2` để đọc bảng `.xls`; hai thư viện này hiện chưa khai báo trong `requirements.txt` và chưa cài trong môi trường được rà soát. Điều kiện phiên bản Python do PyPI công bố không loại trừ Python 3.13 hiện dùng; cả hai có wheel Python thuần. Tuy nhiên classifier công bố chưa nêu 3.13, nên đây chỉ là **tương thích theo metadata**, cần kiểm thử cài đặt và chạy trên đúng môi trường Python 3.13 trước khi kết luận. [olefile 0.47](https://pypi.org/project/olefile/0.47/), [xlrd 2.0.2](https://pypi.org/project/xlrd/2.0.2/).

`olefile` đọc container OLE, không chứng minh tài liệu Word hay Excel hoàn chỉnh hoặc an toàn. `xlrd` đọc `.xls` cũ, không đọc `.xlsx` hay file có mật khẩu; thư viện lấy kết quả công thức đã lưu, không tính lại công thức, và không hỗ trợ biểu đồ, macro, hình hoặc đối tượng nhúng. Xem trước phải ghi rõ giới hạn này, không coi giá trị cache là kết quả được xác minh. [Tài liệu xlrd](https://xlrd.readthedocs.io/en/latest/).

## Hunk dự kiến, chưa thực hiện

1. `requirements.txt`: thêm hai dòng phiên bản trên sau khi được duyệt; kiểm tra license, lock/version và khả năng triển khai trong môi trường thực tế. Không cài hoặc tải thư viện trong bước rà soát này.
2. `src/optimat/api/project_document_io.py`: mở nhánh `.xls`/`.doc` riêng, vẫn kiểm giới hạn 50 MB và byte rỗng. Kiểm chữ ký OLE, mở container chỉ đọc bằng `olefile`, kiểm lỗi cấu trúc, kích thước/giới hạn số stream và dữ liệu xử lý; đối chiếu luồng tương ứng với định dạng khai báo. Chữ ký OLE đơn thuần không đủ vì DOC và XLS cùng container.
3. `.xls`: xác minh container có stream workbook phù hợp và thử parser `xlrd` trong môi trường có giới hạn tài nguyên, bắt lỗi tệp hỏng/mã hóa/không hỗ trợ. Cần xác định hỗ trợ BIFF nào theo parser, không tự khẳng định mọi file Excel cũ đều đọc được. Không thực thi macro, liên kết ngoài hoặc công thức; tệp không qua kiểm định không được nhận là đã lưu thành công.
4. `.doc`: xác minh stream `WordDocument`, kiểm FibBase và các thành phần/stream cần thiết theo phiên bản và parser được chọn. Đặc tả Microsoft quy định `wIdent = 0xA5EC`, nhưng magic/FibBase riêng lẻ **không xác thực toàn bộ file**. Vì chưa có parser DOC đầy đủ và fixture thực, chỉ coi nhánh này là **đề xuất kiểm định cấu trúc giới hạn**; không gắn nhãn “tài liệu hợp lệ hoàn chỉnh” hay khẳng định xem được. Cần thiết kế tiêu chí nhận/lưu rõ trước khi mở hỗ trợ. [MS-DOC FibBase](https://learn.microsoft.com/en-us/openspecs/office_file_formats/ms-doc/26fb6c06-4e5c-4778-ab4e-edbf26a545bb).
5. `project_document_io.py` và `project_files.py`: nếu kiểm định thành công, lưu đúng byte/sha256 và cho tải qua endpoint chủ sở hữu hiện có. Với XLS có reader, bổ sung xem sheet dưới giới hạn dòng/cột/độ dài nội dung; `can_preview` chỉ `true` khi năng lực thật sẵn sàng. DOC chưa có reader: `can_preview=false`, lý do rõ, chỉ tải bản gốc nếu chính sách kiểm định giới hạn đã được duyệt. Cả hai `can_analyze_cad=false`; XLS `TIEN_LUONG` là nguồn đối chiếu, không cộng vào BOQ.
6. `tests/test_project_document_io.py` và test API/DB tương ứng: kiểm tra validator, capability, quyền, hash download và sheet preview với đầu vào được phép. Dùng subprocess/worker có giới hạn thời gian/bộ nhớ nếu cần vì giới hạn số ô trả ra không giới hạn chi phí parser. Không thao tác với Office qua COM, không chạy macro, OCR, LLM hoặc bóc tách khi xem.

## Fixture và tiêu chí trước release

- XLS thực: chỉ dùng bản sao mẫu M1 đã được cho phép, đối chiếu SHA-256 đã ghi nhận trước khi thử, bảo toàn bản nguồn. Kiểm sheet, ô, công thức đã cache, định dạng số/ngày, preview có giới hạn, tải lại byte nguyên bản và quyền cross-user. Không đưa bảng này vào BOQ tự động.
- DOC thực: **chưa xác định được fixture thực được phép dùng**. Cần một bản sao được phép, có nguồn và hash; kiểm đúng định dạng/container và khả năng tải byte. Fixture giả có thể kiểm nhánh lỗi nhưng không chứng minh tương thích DOC thật.
- Bổ sung OLE giả/chữ ký đúng nhưng stream thiếu hoặc sai loại, cắt cụt/chains hỏng, tệp quá lớn, mã hóa, stream bất thường, DOC đổi đuôi XLS và ngược lại; mỗi trường hợp phải trả lỗi rõ, không ghi nhận thành công giả.
- Test DOCX thực từ `docs/de-cuong/*.docx` trong một bước tương thích riêng sau khi được phân công; không suy kết quả DOCX thành hỗ trợ DOC. Rà cả XML UTF-16 hợp lệ vì validator hiện từ chối byte null.
- Trước runtime: kiểm thử cô lập, không lộ tệp nguồn, không thay DB ứng dụng hay đổi owner; đồng bộ DTO capability, UI và tài liệu hạn chế. Chỉ nghiệm thu khi kiểm thử thực và phân quyền đạt.
