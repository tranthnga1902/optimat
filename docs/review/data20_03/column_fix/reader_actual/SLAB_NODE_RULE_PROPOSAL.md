# Đề xuất rule gán sàn đỉnh cột theo nút/ô và nguồn

Ngày04/11/2026. Bổ sung báo cáo sau nguồn07; **không sửa source freeze hoặc tự điền H vào reader**. Đã đọc C2_SLAB_CONTACT_CHECK.md/receipt và xem ảnh C2_BEAM_SECTION33.png + C2_SLAB_3_4_A_B.png. Bốn ảnh được receipt chỉ định đã khớp SHA tại slab_evidence_hash_check.json. Không mở PDF/CAD hoặc chạy lại test trong lượt bổ sung này.

## Bằng chứng mới cho thiết kế, chưa là output reader

Ảnh mặt cắt3–3 cho b220, cánh120, sườn280, tổng400. Mặt bằng cho ô3–4/A–B, ghi chú+6.750/H120; vùng hạ cốt/hatch và ô mở nằm ở phần khác. Báo cáo07 nối dầmD1-4A trên trụcA/nhịp3–4 với mặt cắt3–3 gần đầu4 tại+6.750, tách đầu khác+7.500. Đây là đối chiếu các hình cùng thiết kế, không phải ground truth độc lập hoặc xác nhận toàn nút đã được clip.

Nguồn07 ghi rõ: chưa có handleCAD riêng cho tờ29, closed_slab_polygon, diện tích tiếp xúc cột–sàn và beam_clipping_receipt đều NULL; human_approval=false/chua_kiem. Hình cánh một phía không chứng minh polygon bản sàn phủ cả tiết diện cột. Không lấy thép dầm3–3 làm thép cột2–2 hoặc chọn mác/nhu cầu mua từ ảnh.

## Rule tổng quát đề xuất — chưa có consumer tự động đầy đủ

ID tài liệu: COT-TOP-SLAB-NODE-01, không phải khóa config đã được engine đọc.

1. **Cột đích:** instance theo đúng hai trục và đoạn z, file/revision/hash; mã loại không đủ làm identity. Mỗi view có hệ biến đổi riêng, nối qua trục đã kiểm, không so tọa độ modelspace hai tờ như cùng origin.
2. **Dầm tại nút:** nhãn dầm trên plan phải nối được với hình dầm đúng mã, tầng, đoạn giữa hai trục và đầu gối; chọn mức cao của đầu tại cột. Không dùng mức cao đầu bên kia hoặc trung vị cao độ cả hình. Mã phân đoạn giữ nguyên separator, không biến D1-4A thành D14A rồi ghép nhầm.
3. **Mặt cắt áp dụng:** cần dấu chỉ/dấu cắt gắn với đoạn/gối dầm đó và caption tương ứng, không chỉ cùng số3–3 trên tờ. DIM phải đo đúng cánh sàn, có endpoints và biên; không dùng tổng chiều cao dầm hoặc sườn dầm thay dày sàn. Kiểm cánh+sườn=tổng chỉ là phép đối chiếu tiết diện, không tự phân bổ thể tích nút.
4. **Ô/vùng sàn:** xác định biên vùng tại nút hoặc quan hệ nút–dầm–sàn được kiểm. H và cao độ phải thuộc cùng vùng, cùng tầng trên, đúng z đỉnh cột; phải phân biệt lỗ mở, vùng hạ cốt, thay dày, sàn nghiêng. Khung ô trục không tự là polygon sàn; cùng tờ/cùng tầng/cùng H chưa đủ.
5. **Đối chiếu chéo:** dày ở mặt cắt và H của vùng phải tương thích; xung đột giữ pending. Giữ handlepath, layer, view, filehash và các phép nối; không dùng tên trang hoặc số tính tay làm rule production.
6. **Chính sách đo tại nút:** phải nêu rõ một trong hai phương pháp đã được BA/người kiểm chốt: (a) giao hình học thật thì khoản trừ dựa diện tích giao thực, không mặc nhiên b×h; (b) quy ước BOQ cột đến đáy sàn trên toàn tiết diện thì khoản trừ b×h×t, đồng thời phải xác định bên dầm/sàn sở hữu nút để tránh trừ hoặc cộng hai lần. Hai phương pháp không được âm thầm thay nhau.
7. **Chỉ áp tự động khi đủ cả chuỗi:** khi mọi liên kết, nguồn, scope và chính sách đã đủ mới phát top_slab_thickness_mm/source cùng receipt/căn cứ phân bổ. Nếu thiếu bất kỳ bước nào thì chỉ giữ top_slab_candidates, lý do và net NULL. Gross có nguồn được giữ riêng; không dùng gross như lượng net mua vật tư.

## Khoảng trống hiện hành và nơi cần nối

- structural_column_instances.py::_slab_source_candidates mới nối chữh với cao độ và tầng trên, trả region_confirmed=False; chưa dựng vùng hoặc nối dầm plan→hình dầm→mặt cắt. instance_column_works không dùng candidate để tự trừ. Giữ nguyên hành vi này.
- Cần trích nativeCAD cho tờ chi tiết dầm mới, giữ handlepath và dấu cắt/level theo đoạn. ẢnhPDF chỉ là chứng cứ review, không là input đo được bơm tay vào reader.
- Cần kiểm mã dầm phân đoạn trong consumer: ky_hieu_cau_kien.csv hiện có mẫu BEAM dạng d\d+[a-z]?/(dm|dp)\d+[a-z]?/dct\d*, chưa bao internalhyphen D1-4A. element_of chỉ bỏ gạch nối giữa prefix chữ và số, không giải quyết toàn bộ tên dầm phân đoạn. Cần01 giao hunk/rule tương thích, không tự sửa CSV chuẩn trong lượt báo cáo.
- Cần nguồn biên vùng và phép phân bổ nút, không chỉ thêm một cột mô tả. UI02 cần hiện ứng viên + nguồn + lý do chưa áp; API06 giữ payload. Phiên03 chưa kiểm giao diện/runtime nên không khẳng định nhánh này đã hiển thị cho user.

## Ca dương/âm đề xuất cho lần triển khai sau — chưa chạy

| Ca | Kỳ vọng |
|---|---|
| Cùng instance/grid, cùng z đỉnh, cùng vùng không lỗ/hạ cốt, đúng dấu cắt và policy/clip receipt đủ | Cho phép dùng t đo từ nguồn, lưu đầy đủ receipt; net theo policy, không hằng số |
| H ở ô khác cùng tầng, kể cả cùng con số | Không gán vào nút đích; candidate/reason, net NULL |
| Cùng ô trục có hai vùng cao độ khác nhau | Phân vùng riêng; chưa phân giải thì NULL |
| Đầu kia của cùng dầm cao hơn | Không mang cao độ đầu kia tới cột đích |
| Vùng hạ cốt sát nút, vùng thường ở nơi khác | Không dùng H/note vùng thường thay vùng tại nút |
| Lỗ mở hoặc biên sàn không phủ đủ phần cần tính | Không tự trừ b×h×t; cần giao thật hoặc policy được chốt |
| Cùng mã dầm ở view/tầng khác hoặc sourcehash khác | Không ghép chỉ theo mã; pending nguồn |
| Caption3–3 giống nhau ở hai chi tiết | Phải có dấu chỉ tới đúng đoạn; không nearestcaption |
| DIM đo sườn/tổng dầm hoặc chỉ một bên cánh | Không coi là dày/phủ toàn nút nếu thiếu quan hệ |
| Note và mặt cắt khác dày | Xung đột, không chọn max/min để đạt đáp án |
| Một khoản giao nút đã thuộc sàn/dầm | Chặn cộng/trừ lặp, không thay net bằng số tham chiếu |

## Kết luận bàn giao01/00

Nguồn mới tăng căn cứ thiết kế cho H120 tại hệ nút đang xem, nhưng chưa đủ để đổi region_confirmed hoặc tự xuất net trong production. Bản final_v3/gross ACTUAL vẫn giữ nguyên, source freeze/hash không đổi. Giữ candidate và lý do hiện có là nhánh đúng hiện tại; chỉ mở hunk gán tự động khi có sourceCAD/scope/quan hệ và policy tương ứng. Giữ20bảng, không tạo bảng mới.
