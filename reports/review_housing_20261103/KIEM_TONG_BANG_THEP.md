# Rà tổng hợp ↔ KLCT của 11 nhãn thép — 03/11/2026

**Kết luận: chưa đủ cơ sở trình toàn bộ 11 nhãn như đáp án chuẩn.** Hai nhãn gộp móng/bể W005 Hương và W007 Sang có mâu thuẫn rõ trong bảng bể. Những nhãn còn lại được kiểm phép cộng KLCT CAD ở mức ghi dưới đây, không xác nhận hình học, chưa duyệt thay chủ đồ án. Chưa ai duyệt cả ba quyết định trong phiếu chốt.

## Phạm vi và cách hiểu

Chỉ đọc bản trích TEXT CAD, JSON nhãn và PDF có sẵn. Mỗi dòng KLCT theo đường kính được cộng một lần; không cộng ô tổng hợp vào tổng các KLCT. Nhận diện ô `%%c`/`%%C`, dấu phẩy/chấm thập phân; truy bằng handle trong hai file [Hương](nha_huong_hai_duong_7x12_ket_cau_text.json) và [Sang](nha_sang_hai_duong_4x15_ket_cau_text.json). Các khoảng handle dưới đây chỉ là cách truy tập ô đã cộng, **không phải mọi entity trong khoảng đều là ô KLCT**. Chưa chứng minh không thiếu nhóm chỉ bằng thứ tự handle hoặc cửa sổ tọa độ.

PDF và CAD thuộc cùng thiết kế: đối chiếu chúng giúp xác định đúng ô/phạm vi, **không phải hai chứng cứ thiết kế độc lập**. Chưa tính lại chiều dài, số thanh, trọng lượng đơn vị; không tạo đáp án hình học. Không kiểm toàn 464 công tác, không sửa JSON/mã/test/DB, không chạy suite.

Đơn vị các bảng dưới là **kg**. `Δ = tổng hợp − tổng KLCT đã đọc`. Các ô thường in 0,1 kg; nếu n số con và một số tổng đều được làm tròn gần nhất đến 0,1 kg thì chênh do làm tròn tối đa khoảng `0,05×(n+1)` kg. Đây chỉ là phép kiểm khả năng, không chứng minh nguyên nhân thực tế; chưa biết quy tắc và số trước làm tròn của người thiết kế. Lệch ở sát biên cũng cần kiểm số gốc. Không dùng hệ số để hòa số.

## 11 nhãn: kết quả và mức bao phủ

| Nhãn | Tổng KLCT CAD đã đọc theo Ø | Ô tổng hợp đang làm nhãn | Δ theo Ø | Bao phủ / nhận định |
| --- | --- | --- | --- | --- |
| Hương W005 móng+bể | Móng: Ø6 36,2; Ø8 298,3; Ø10 394,8; Ø16 707,9; Ø18 240,4. Bể: Ø6 16,6; Ø8 27,5; Ø10 164,8; Ø12 44,8 | Móng: 36,2; 298,3; 394,9; 708,2; 240,3. Bể: 15,7; 27,5; 163,8; 43,6 | Móng: 0; 0; +0,1; +0,3; −0,1. Bể: **−0,9; 0; −1,0; −1,2** | Đã xem đủ bảng bể PDF trang 14; mâu thuẫn rõ. Phần móng mới đối chiếu tập KLCT CAD, chưa xác nhận toàn bộ phạm vi từng trang. Chặn nhãn gộp. |
| Hương W010 cột | Ø6 95,6; Ø16 556,5; Ø18 107,9 | 95,6; 556,5; 107,9 | 0; 0; 0 | Hai nhóm KLCT CAD khớp số tổng; chưa kiểm đầy đủ từng thanh/trang, không kết luận nghiệm thu. |
| Hương W012 dầm | Ø6 251,0; Ø16 612,5; Ø18 581,6 | 251,0; 612,6; 581,8 | 0; +0,1; +0,2 | Tập KLCT CAD trong khoảng bên dưới; còn phải xác nhận phạm vi các bảng/trang. +0,1 có thể do làm tròn; Ø18 gồm ba ô, +0,2 sát biên kiểm làm tròn, chưa kết luận nguyên nhân. |
| Hương W014 sàn | Ø10 2185,6 từ năm KLCT | 2185,7 | +0,1 | Năm ô CAD đã cộng; có thể do làm tròn (biên 0,30); chưa rà đủ hình và phạm vi từng sàn trên PDF. |
| Hương W017 lanh tô | Ø6 35,7; Ø10 68,7; Ø16 92,9 | 35,8; 68,7; 92,9 | +0,1; 0; 0 | Các KLCT trong hai cột thống kê CAD; ảnh trang 30–31 hỗ trợ phạm vi lanh tô. Ø16 khớp 21,9+46,5+24,5=92,9. Ø6 lệch nhỏ có thể do làm tròn; chưa kiểm từng thanh. Quyết định Ø16 chỉ áp quy cách/ô 92,9, không duyệt cả tổng lanh tô. |
| Sang W007 móng+bể | Móng: Ø6 44,3; Ø8 209,0; Ø10 51,1; Ø12 97,1; Ø16 985,7; Ø20 1104,0. Bể phốt: 13,7; 23,1; 116,8; 37,6 (Ø6/8/10/12). Bể nước: 13,7; 168,4; **37,6** (Ø6/10/12) | Móng: 44,3; 209,0; 51,1; 97,2; 985,6; 1103,8. Bể phốt khớp các số trên. Bể nước: 13,7; 168,4; **36,9** | Móng: 0;0;0;+0,1;−0,1;−0,2. Bể phốt: 0 tất cả. Bể nước: 0;0;**−0,7** | Đã xem trọn hai bảng bể PDF trang 18; bể nước mâu thuẫn rõ. Móng mới tập KLCT CAD, chưa xác nhận hết trang. Không duyệt tổng 2,9012/2,9019 t. |
| Sang W012 cột | Ø6 145,3; Ø18 330,6; Ø20 687,6 | 145,3; 330,4; 687,6 | 0; **−0,2**; 0 | Ba KLCT/đường kính CAD. Ø18 53,9+222,8+53,9=330,6; −0,2 sát biên bốn lần làm tròn, chưa chứng minh do làm tròn. Cần số chưa làm tròn và bảng chi tiết trước trình tổng sạch. |
| Sang W014 dầm | Ø6 337,9; Ø16 299,1; Ø18 650,6; Ø20 1877,8 | 337,9; 299,1; 650,7; 1878,0 | 0;0;+0,1;+0,2 | Tập KLCT CAD; chưa xác nhận đủ phạm vi các trang dầm. Lệch nhỏ có khả năng làm tròn, chưa kiểm được số gốc. |
| Sang W016 sàn | Ø10 2345,3 từ bảy KLCT | 2345,1 | −0,2 | Bảy ô CAD đã cộng; nằm trong biên 0,40 nếu làm tròn thông thường. Chưa kiểm đủ phạm vi từng sàn/PDF và số trước làm tròn. |
| Sang W018 thang | Ø8 20,8+21,7+21,7=64,2; Ø10 182,2+201,4+201,4=585,0 | 64,2; 585,0 | 0;0 | Đã cộng ba nhóm KLCT CAD, không chỉ hai nhóm giống nhau. Chưa đối chiếu toàn bộ bảng PDF hoặc từng thanh; chỉ kết luận khớp phép cộng tập KLCT đã đọc. |
| Sang W020 lanh tô | Ø6 24,1; Ø10 41,9; Ø12 21,9; Ø16 28,3 | 24,1; 41,8; 21,9; 28,3 | 0;−0,1;0;0 | Tám nhóm KLCT CAD, Ø10 có bảy ô; lệch −0,1 có thể do làm tròn (biên 0,40). Chưa kiểm lại toàn bộ từng thanh/PDF. |

## Bằng chứng lỗi bể Hương — mới phát hiện

PDF kết cấu **trang 14, khung tên KC-01-08**, [ảnh riêng](huong_be_page14.png), bảng thống kê thép bể phốt:

- DM-1: Ø6 **8,9** (`100557B`), Ø12 **24,2** (`100557C`).
- DM-2: Ø6 **7,7** (`100558D`), Ø12 **20,6** (`100558E`).
- Tổng KLCT Ø6 = **16,6**, nhưng tổng cuối bảng **15,7** (`10055E9`): thiếu 0,9 kg so với các dòng. Hai ô KLCT và ô tổng đến 0,1 kg không giải thích được chênh này bằng làm tròn thông thường (biên 0,15).
- Tổng KLCT Ø12 = **44,8**, nhưng tổng cuối bảng **43,6** (`10055EC`): thiếu 1,2 kg, cũng vượt biên 0,15.
- Đáy bể KLCT Ø10 **124,8** (`1005546`), TĐ-1 **21,8** (`10055B8`), TĐ-2 **18,2** (`10055E2`) cộng **164,8**; tổng cuối **163,8** (`10055EB`), thiếu 1,0 kg, vượt biên 0,20.
- Ngay trong nhóm đáy bể, ba khối lượng dòng in **50,8 + 65,8 + 9,9 = 126,5** khác KLCT **124,8** (lệch 1,7 kg), cũng vượt biên 0,20. Vì vậy thay ô tổng cuối bằng tổng KLCT cũng **chưa giải quyết hết mâu thuẫn**; chưa xác định dòng hoặc tầng tổng nào đúng.
- Ø8 KLCT **14,8 + 12,7 = 27,5**, khớp ô tổng `10055EA`; không đủ để xác nhận toàn bảng.

Tổng các ô cuối bể 250,6 kg; tổng KLCT được in 253,7 kg, chênh 3,1 kg. Đây chỉ là mô tả mâu thuẫn, **không đề nghị thay số**. W005 gộp bể vào móng nên nhãn 1,9285 t cũng chưa đủ điều kiện trình duyệt sạch.

## Bằng chứng bể Sang

PDF kết cấu **trang 18 KC-01-12**, [ảnh riêng](sang_be_page18.png):

- Bể phốt: Ø6 7,7+6,0=13,7 (`11735CE`,`11735CA`); Ø8 12,4+10,7=23,1 (`11735C8`,`11735C6`); Ø10 84,2+18,8+13,8=116,8 (`11735D5`,`11735C9`,`11735C7`); Ø12 20,6+17,0=37,6 (`11735CF`,`11735CB`). Khớp các ô tổng `11735D6`–`11735D9` ở mức KLCT↔tổng hợp. Chưa kiểm toàn bộ từng thanh từ hình học.
- Bể nước: Ø6 7,7+6,0=13,7 (`11735D1`,`11735B5`), Ø10 84,2+84,2=168,4 (`11735DB`,`11735DD`), khớp tổng `11735DE`,`11735DF`.
- Bể nước Ø12: **20,6+17,0=37,6** (`11735D2`,`11735B6`), nhưng tổng **36,9** (`11735E0`), thiếu **0,7 kg**. Hai KLCT khớp bốn dòng khối lượng 10,1+10,5+8,3+8,7. Không thấy dòng trừ 0,7 kg trên bảng; chưa xác định nguyên nhân. Biên làm tròn bốn dòng và một tổng khoảng 0,25 kg, nhỏ hơn 0,7.

Không chốt tổng W007: 2,9012 t là phép cộng các ô tổng hợp cũ; 2,9019 t chỉ thay riêng Ø12 nước bằng tổng chi tiết, còn phụ thuộc kiểm phần móng và các lớp số khác. Không coi hai số là đáp án đã xác minh.

## Chỉ mục tập KLCT CAD đã cộng (để kiểm lại phạm vi)

| Nhãn / phần | Handle KLCT đã đọc; loại trừ ô tổng cuối |
| --- | --- |
| Hương W005 móng | Các ô theo Ø từ `1014548` đến `10147E3`; tổng cuối `1014D92`–`1014D96`. Cần xác nhận đầy đủ trang móng, không dùng khoảng handle làm bằng chứng duy nhất. |
| Hương W005 bể | `1005546`, `100557B/C`, `100558D/E`, `10055B7/B8`, `10055E1/E2`; tổng `10055E9`–`10055EC`. |
| Hương W010 | `1015370/71`, `10153A3/A4/A5`; tổng `1015953/54/55`. |
| Hương W012 | Các ô theo Ø từ `1019732` đến `1019A0B`, gồm `1019906/07` (không bỏ sót nhóm này); tổng `1019FB9/FBA/FBB`. |
| Hương W014 | `1017118`, `10171F5`, `101724C`, `10172C3`, `101734C`; tổng `1018240`. |
| Hương W017 | Các ô theo Ø từ `10188C2` đến `1018B47`; tổng `10190F5/F6/F7`. Ø16 con `10188C4`, `10188EC`, `1018A21`. |
| Sang W007 móng | Các ô theo Ø từ `118C4D0` đến `118C6FD`, gồm `118C5E0/E1`; tổng `118F2E7`–`118F2EC`. |
| Sang W012 | `118CD0A/B/C`, `118CD87/88/89`, `118CDEC/DED/DEE`; tổng `118F894/895/896`. |
| Sang W014 | Các ô theo Ø từ `118D3D8` đến `118D717`; tổng `118FE3E/3F/40/41`. |
| Sang W016 | `118DD14`, `118DD73`, `118DDC6`, `118DE25`, `118DE6C`, `118DEBD`, `118DEFC`; tổng `11903E9`. |
| Sang W018 | `118E51B/51C`, `118E593/594`, `118E60B/60C`; tổng `1190991/992`. |
| Sang W020 | `118EBDD/BDE`, `118EC1D/1E`, `118EC5D/5E`, `118EC83/84`, `118ECA9/CAA`, `118ECCF/CD0`, `118ED11/12/13`, `118ED38/39`; tổng `1190F3A/3B/3C/3D`. |

## Phần chưa kiểm và bàn giao

1. Chặn sử dụng hai nhãn gộp móng/bể như đáp án chuẩn; đề nghị điều phối cấp lượt dữ liệu sau khi hết khóa để ghi cảnh báo mới. Lượt này chỉ báo cáo, không đổi gate JSON nên các cờ có sẵn chưa phản ánh hết phát hiện.
2. Cần kiểm đủ ranh giới bảng/trang, hệ số số lượng cấu kiện, từng dòng thanh và số chưa làm tròn cho các nhãn còn lại. Các tổng KLCT khớp không chứng minh hình học đúng.
3. Ø18 cột Sang lệch 0,2 kg và Ø18 dầm Hương lệch 0,2 kg cần ưu tiên xem số chi tiết/số gốc; chưa quy lỗi hoặc duyệt sạch vì chỉ khả năng làm tròn sát biên.
4. Ảnh Hương trang 14 được render từ PDF nguồn để đọc lỗi bảng; không chỉnh nội dung ảnh. Chỉ thêm báo cáo này và ảnh bằng chứng trong lượt rà giới hạn, không mở phạm vi 453 dòng cách ly.
