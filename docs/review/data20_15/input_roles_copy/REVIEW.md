# QA15 — INPUT roles trên opening candidates

05/11/2026. **PASS source/harness trên exact overlay; bàn giao patch có finding newline.** Manifest SHA256 `fa9d7f71b4aa2337bb3f2ac1e2aea6caea71d41731a2502db7019b6ff28b6e4c`. Bốn file overlay khớp target trước/sau, bốn file base giữ hash. Hai harness nguyên bản chạy trên bản sao mỗi nền: panel SSR 5 trạng thái/nền và upload hook harness đều EXIT0 (4 lượt). Receipt ở `receipt.json`, log riêng trong 3001/3002. Không sửa candidate/runtime.

## Finding bàn giao

`git -c core.autocrlf=false apply --check` trên copy exact base: 3001 đạt nhưng ProjectDossier kết quả hash `414b0c...` khác target `a19f570...`; 3002 check không áp được mặc định. Với `--ignore-space-change`, cả hai áp được, nhưng 3002 cả hai file khác byte target. Cả ba file lệch đều khớp overlay sau chuẩn hóa CRLF thành LF. Cần owner cung cấp patch tái tạo đúng target hoặc quy trình newline tường minh kèm hash; chưa đóng exact patch reproduction. Các harness chạy trên **overlay byte đúng manifest**, không nhận patch output lệch hash là target. Không thấy blocker logic mới trong delta đã review.

## Đối chiếu IN01–06

| Ca | Bằng chứng / giới hạn |
|---|---|
| IN01 | PARTIAL source/harness: CAD mới role trống, chọn file chưa POST, UI và handler chặn trống, role KC/KT/THAM_KHAO được chuyển đúng vào FormData giả lập. 3001 một file và reset role; 3002 role riêng từng file. Không chứng minh bytes lưu, history/version hay sửa role hồ sơ đã lưu. |
| IN02 | PARTIAL SSR: empty và hai revision cùng file bị chặn. Delta giữ phiên bản/sha validation và cho bỏ chọn tài liệu không hỗ trợ đã chọn. Chưa restore/draft hoặc đổi scope thực. |
| IN03 | PASS năm trạng thái SSR: empty/KC-only/duplicate blocked, KT-only và KT+KC cho Start; chỉ CAD KT/KC được chọn mới theo source. Không kiểm backend fail-closed, PDF-only riêng hoặc reader accuracy. |
| IN04 | NOT_RUN: không có fixture liên kết file/tờ/section/mâu thuẫn trong lượt này. |
| IN05 | NOT_RUN runtime: không fault/race/stale project/version/role hoặc reload draft. Delta không sửa effect identity guards; không lấy source review thay race evidence. |
| IN06 | PARTIAL SSR/source: có mô tả KT và cảnh báo chưa có KC hoặc KC đọc riêng. Chưa chứng minh reader thực hiện lời mô tả, effective/manual/design hay accessibility browser. |

3001 không thêm Office/multiple, giữ accept DWG/DXF; 3002 giữ queue và default Excel TIEN_LUONG/PDF HO_SO hiện hữu. Queue harness dùng React hook giả và projectResponse giả, **không phải actual multi-upload/UI browser**. Không build/DB/upload thật/browser live/full/TestClient. Junction dependency bị môi trường từ chối khi chuẩn bị; dùng NODE_PATH tới dependency đã có, không đổi dependency hay xin escalation. DIM vẫn PREPARED/NOT_RUN. HTTP bbox SYN của 01 là receipt riêng, không VN002 và không bằng chứng cho INPUT.
