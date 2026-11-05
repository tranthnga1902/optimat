# Điểm cần chốt thép bể — 03/11/2026

**Phạm vi:** rà hồ sơ hiện có để chủ đồ án và điều phối quyết định từng dữ kiện còn thiếu; không chốt thay, không sửa mã/test/normalized/DB hoặc tổng nguồn. Báo cáo bổ sung này làm rõ giới hạn của [42 mã đã tính](BOC_TUNG_THANH_THEP_BE.md); không mở rộng các công tác khác. CAD và PDF cùng thiết kế, không coi là chứng cứ thiết kế độc lập.

## 0. Đã tìm được bảng đơn trọng và lớp bảo vệ trong hồ sơ

Nguồn: **PDF kết cấu trang 3, KC-00**, [Hương](huong_notes_page3.png), [Sang](sang_notes_page3.png). Bên trái, mục5.2 bảng3 ghi đơn trọng Ø6=0,222; Ø8=0,395; Ø10=0,617; Ø12=0,888 kg/m. Vì vậy phương án gọi là “bảng đơn trọng phụ” ở báo cáo42 mã thực tế **có căn cứ ngay trong hồ sơ**, nên có thể trình dùng cho nhãn khối lượng theo hồ sơ, thay vì chọn khối lượng riêng7850 và diện tích tròn lý thuyết. Hai cách không trộn với nhau.

Hệ quả cần đính chính khi đọc báo cáo cũ: nếu giữ chiều dài triển khai thép chủØ12 hiện có, Hương50,4m×0,888=**44,7552kg**; mỗi bể Sang42,4m×0,888=**37,6512kg**. Làm tròn cuối đến0,1kg lần lượt44,8 và37,7kg; khác tổng các ô con đã làm tròn44,8/37,6. Đây là phép tính có điều kiện theo chiều dài hiện có, **chưa tự đổi nhãn**, không chứng minh toàn bể. Các số44,745830/37,643317kg ở báo cáo cũ thuộc mô hình khối lượng riêng7850 đã khai báo, không phải kết quả duy nhất theo hồ sơ.

Ghi chú bên phải trang3 cho biết:

| Nội dung | Hương | Sang | Handle CAD truy được |
| --- | --- | --- | --- |
| Dầm móng và dầm sàn tầng hầm | A=30mm | A=30mm | `EA913E/EA9140`; `10FF765/10FF767` |
| Sàn | A=15mm khi h≥10cm; A=10mm khi h<10cm | A=25mm khi h>15cm; A=20mm khi h≤15cm | `EA9149/EA914B/EA914D`; `10FF770/10FF772/10FF774` |
| Dầm thông thường | A≥25mm và A≥D | A≥25mm và A≥D | `EA9145/EA9147`; `10FF76C/10FF76E` |

Chưa thấy ghi chú riêng ngay chi tiết bể ghi đè rõ lớp bảo vệ chung. Cần quyết định DM bể áp mục dầm móng hay mục dầm, và cách quy đổi kích thước hình dạng thanh (ngoài thép/đường tim); không suy ra c=25mm chỉ từ đoạn thẳng bằng kích thước bê tông trừ50mm. Sàn đáy/nắp150mm nếu áp mục sàn chung thì Hương15mm, Sang20mm. Không mang cover của nhà này sang nhà kia.

**Câu chốt 0:** Có đồng ý dùng đơn trọng bảng3 KC-00 của từng hồ sơ, cộng chiều dài chưa làm tròn rồi mới làm tròn tổng theoØ đến0,1kg không? Nếu chọn giữ cách trình bày tổng của các dòng đã làm tròn, phải lưu đó là trường hiển thị nguồn riêng, không thay tổng tính từ chiều dài. Chưa có lựa chọn được ghi nhận.

## 1. Miền rải hai lớp Ø10 a150: xác định phần có thể đọc, chưa chọn số thanh

Nguồn và vị trí:

- Hương **trang13 KC-01-07**, mặt bằng đáy góc trên trái và mặt cắt1-1 phía dưới: [toàn trang](huong_be_page13.png), [phóng to](huong_day_be_crop.png). Mã1/mã2 ghi **2Ø10 a150**, mặt cắt có cả lớp trên và dưới. Phủ bì dầm bao3000×2500; lọt lòng2560×2060; phần bê tông nhô ngoài mỗi bên100. Bảng thanh trang14 có đoạn thẳng2950/2450, số26/40.
- Sang bể phốt **trang16 KC-01-10**, [ảnh](sang_be_page16.png); bể nước **trang17 KC-01-11**, [ảnh](sang_be_page17.png). Phủ bì2500×2000; lọt lòng2060×1560; ghi2Ø10 a150. Bảng trang18 có đoạn2450/1950, số22/30 ở đáy và nắp bể nước.

**Xác định được:** có hai lớp, hai phương; đoạn rải theo phương vuông góc thanh; không lấy chiều dài thanh cộng móc làm miền rải. Chiều phủ bì dầm bao, chiều lọt lòng và mép bê tông ngoài là ba ranh khác nhau. Các số thanh26/40,22/30 chưa được giải thích bằng một ranh rải và quy tắc biên thống nhất.

**Câu chốt 1A:** Với mỗi phương đáy/nắp, thanh rải phủ qua dầm bao đến mép nào: (a) mép phủ bì dầm bao3000×2500 hoặc2500×2000; (b) giới hạn lọt lòng; (c) mép bản nhô100mm ngoài dầm; hay miền khác cần đánh dấu trên ảnh? Ghi ranh bắt đầu/kết thúc bằng kích thước, không chỉ chọn “theo bản vẽ”. Nắp có lỗ mở phải xử lý riêng ở mục3.

**Câu chốt 1B:** Sau khi xác định lớp bảo vệ và offset đường tim, có bắt buộc có thanh tại cả hai biên và mọi khoảng≤150mm không, hay giữ bước đúng150mm từ biên đầu và chừa phần dư biên cuối? Hai phương án tính có điều kiện:

- Đặt cả hai biên, khoảng không quáa: `n_mỗi_lớp=ceil(S/a)+1`, chia lại bước `S/(n−1)`.
- Rải bướca từ biên đầu, chưa bắt buộc có thanh tại biên cuối: `n_mỗi_lớp=floor(S/a)+1`; phải ghi phần dư và kiểm điều kiện mép cuối. Không dùng cách này để tự giảm thanh nếu thiết kế yêu cầu hai biên.

Ví dụ **chỉ để thấy tác động quyết định**, không phải số thay thế: giả sử rải theo phủ bì dầm bao, cover áp mục sàn chung, S đo giữa tim hai thanh biên `S=B−2(c+d/2)`, d10:

| Vùng | S ngang/ngang dài mm | Bước150 từ đầu (hai lớp) | Cả hai biên, bước≤150 (hai lớp) |
| --- | --- | --- | --- |
| Hương B2500/3000, c15 | 2460/2960 | 34/40 | 36/42 |
| Sang B2000/2500, c20 | 1950/2450 | 28/34 | 28/36 |

Các số trong bảng này chỉ đúng nếu chốt đúng ranh, cover và quy tắc nêu trên. Chưa chốt ranh nên **không tự thay26/40 hoặc22/30**. Chiều thanh triển khai cũng phải xét lại nếu thay ranh/cover; không tăng số thanh mà mặc nhiên giữ mọi chiều dài cũ.

**Chân chó a600×600:** mặt cắt Hương trang13 và Sang trang16/17 có chỉ dẫn; hình dạng thanh trong bảng có tổng đoạn800mm. Chưa có đánh dấu từng vị trí lưới và vị trí tránh dầm/lỗ mở. Câu chốt1C: rải lưới bắt đầu cách mép bao nhiêu, trên miền nào, tại lỗ mở có bỏ/thêm chân chó không? Với miền đường timSx,Sy và offset xác định, số chân chó là tích hai số vị trí theo bước600, trừ các vị trí bị loại được đánh dấu; không mặc nhiên chọn20/16 theo bảng.

## 2. Đai DM: cover tìm được, điểm đầu/cuối chưa có kích thước

Nguồn: mặt cắt DM-1/DM-2 bên phải [Hương trang13](huong_be_page13.png), [Sang trang16](sang_be_page16.png)/[trang17](sang_be_page17.png); hình dạng đai [Hương trang14](huong_be_bar_shapes.png), [Sang trang18](sang_be_page18.png).

Đọc được tiết diện220×300mm, Ø6 a150, chiều dài DM-1/DM-2 Hương3000/2500, Sang2500/2000, mỗi loại2 dầm. Bảng hình dạng đai170×250 và hai đoạn60 cho triển khai960mm. Ghi chú chung mục dầm móngA30 không tự giải thích ngay170×250; phải biết170/250 đo ngoài thép hay tim và có ghi đè cover hay không. Không được chọnA25 chỉ để khớp hình dạng.

**Câu chốt2A:** DM bể áp coverA30 theo mục dầm móng, hay có chủ ý ápA25 của dầm và kích thước170×250? Nếu chấp nhận hình dạng960mm cho dữ liệu phát triển, ghi rõ là chiều triển khai chi tiết được ưu tiên, chưa xác minh cover tương ứng; không gọi đây là đối chứng hình học độc lập.

**Câu chốt2B:** Tim đai đầu/cuối cách đầu bê tông bao nhiêu? Có đai cả tại hai đầu miền rải không? Với `S=L−e_đầu−e_cuối`, hai lựa chọn ceil/floor như mục1. Nếu **giả sử** e_đầu=e_cuối=30mm (chỉ minh họa, chưa có kích thước tim đai30 trên chi tiết), số đai/dầm là:

| L mm | S mm | Floor+1 | Ceil+1 | Số/dầm trong bảng |
| --- | --- | ---: | ---: | ---: |
| Hương DM-1 3000 | 2940 | 20 | 21 | 21 |
| Hương DM-2 / Sang DM-1 2500 | 2440 | 17 | 18 | 18 |
| Sang DM-2 2000 | 1940 | 13 | 14 | 14 |

Đây là một cấu hình có thể giải thích số đai bảng nếu chọn cả hai biên, **không chứng minh e=30mm là thiết kế**. Cover đến mép thép khác khoảng đến tim đai, nên không đồng nhất hai đại lượng. Cần chủ đồ án chọn và ghi rõ offset/rule trước chốt nhãn đai.

## 3. Cửa thăm và nắp bể nước Sang: có chi tiết riêng, bảng thanh chưa bao phủ rõ

Nguồn **trang17 KC-01-11**: mặt bằng nắp trên giữa có một ô mở ghi600×500; mặt cắt2-2 ở dưới giữa; [chi tiết nắp phóng to](sang_nap_cua_tham_crop.png). Hình nắp ghi đoạn700, phủ bì800 và bậc50 mỗi bên trong mặt cắt; dày80/bậc50, tổng130. Có ký hiệu **Ø8 a200 ở hai cao độ** (hai đường dẫn cùng mã2) và **1Ø10 mã3** nhô lên dạng quai. Không nên đọc hai đường dẫn đó thành chắc chắn “hai phương trong mặt bằng”: hiện là mặt cắt, cần xác định thêm phương còn lại.

**Đã xác định:** có ô cửa thăm và nắp riêng; không có nhóm thống kê nắp riêng trong bảng thép bể nước trang18 đã đọc. Chưa chứng minh800 là cả hai cạnh của nắp hoặc có bao nhiêu lớp/hệ thanh theo mỗi phương. Không đếm các chấm minh họa trên hình thành số thanh thực khi đã có ký hiệu bước.

**Câu chốt3A:** Bóc1 nắp theo ô mở đang thể hiện hay có thêm nắp khác? Kích thước nắp theo phương vuông góc mặt cắt là bao nhiêu? Chủ đồ án cần xác nhận kích thước hai phương, không tự suy nắp vuông800×800 từ một mặt cắt.

**Câu chốt3B:** Hai ký hiệuØ8 a200 là hai lớp mã2 theo cùng mặt cắt hay hệ thanh khác? Hãy xác nhận số lớp, phương, cover và móc hai đầu. Công thức có điều kiện: `N8=Σ_lớp,phương n_vị_trí`, `L8=Σ N_mã×L_triển_khai_mã`; n_vị_trí tính theoS và quy tắc biên đã chốt, không chọn trước4/5 thanh khi thiếu cạnh thứ hai.

**Câu chốt3C:** Quai1Ø10 mã3 có chiều cao nhô, khoảng hai chân, chiều neo mỗi chân và bán kính uốn bao nhiêu? Nếu không có kích thước đủ, giữ riêng “1 quaiØ10, chiều dài chưa xác định”; chưa quy đổi kg từ hình vẽ không theo tỷ lệ. Không lấy dày80/130 làm toàn chiều dài quai.

**Câu chốt3D:** Thanh sàn trên bể qua ô600×500 được cắt và neo thế nào, có thanh tăng cường mép không? Phương án (a) bóc sàn nguyên rồi trừ từng đoạn đi qua lỗ và cộng neo/tăng cường có kích thước; (b) chia miền rải quanh ô mở để đếm từng thanh còn lại. Cả hai phải lập cùng bản đồ từng thanh và ra cùng phạm vi; không vừa trừ diện tích lỗ theo tỷ lệ vừa trừ chiều dài thanh lần nữa. Chưa có kích thước neo/tăng cường đủ thì để các phần đó thiếu, không tự thêm cấu tạo.

## 4. Thanh cong628mm của tấm đan: có phép giải thích hình học nhưng cần chốt quy ước

Nguồn: [hình dạng phóng to Hương trang14](huong_be_bar_shapes.png), mã3 của TĐ-1/TĐ-2, và [Sang trang18](sang_be_page18.png). Hình có hai đoạn150, hai đoạn70, phần cong bên trái kèm chỉ dẫn60; bảng ghi chiều dài628mm, Ø8. Mỗi tấm3 thanh mã3,4 tấm mỗi loại:12 thanh TĐ-1 +12 TĐ-2 cho mỗi bể phốt.

Nếu **60 là bán kính đường tim cung nửa tròn**, chiều dài `2×150+2×70+π×60=628,495559mm`, có thể trình628mm nếu làm tròn đếnmm. Nếu60 là đường kính đường tim thì cùng mô hình chỉ534,247780mm. Nếu60 đo đến mép trong/ngoài thép, phải đổi về bán kính timR±4mm trước tính, làm đổi chiều dài mỗi thanh khoảng12,566mm. Chưa thấy ký hiệuR/Ø hoặc quy ước ghi kích thước riêng tại ô hình dạng này đủ để chọn một cách độc lập chỉ từ chữ60; không chọnR60 chỉ vì ra gần628.

**Câu chốt4:** Chủ đồ án có đồng ý quy ước cho dữ liệu phát triển rằng60 là bán kính đường tim và150/70 là chiều dài đoạn thẳng tiếp tuyến, dùng628,495559mm trước làm tròn không? Hoặc ưu tiên chiều triển khai628mm đã ghi làm dữ liệu nguồn, giữ nhãn `schedule_developed_length_not_independent_geometry`; hoặc tiếp tục cách ly riêng mã3 cho đến khi có quy ước hình dạng rõ. Cần chọn một phương án và lưu phạm vi; không duyệt toàn bộ tấm đan từ riêng quyết định này.

## Thứ tự trình quyết định

1. Đơn trọng theo bảng3 và quy tắc làm tròn cuối (đã có căn cứ rõ).
2. Cover/ranh miền rải, số lớp và quy tắc hai biên; ghi tọa độ/offset để sinh được từng vị trí, không chỉ đồng ý số tổng.
3. DM: loại cover áp dụng, datum kích thước đai và offset đầu/cuối.
4. Cửa thăm: hai cạnh, số lớp/phương, quai và xử lý thanh qua lỗ.
5. Quy ước cung60/628mm hoặc giữ riêng chiều triển khai nguồn.

Chỉ sau các lựa chọn cụ thể mới tính lại tổng bể và trình nhãn phát triển. Không cần yêu cầu chung chung “tìm QS ngoài”, nhưng lời đồng ý một quy ước phát triển không chứng minh nghiệm thu sai số độc lập. Các tổng nguồn vẫn giữ nguyên và hai nhãn mâu thuẫn vẫn bị cách ly. Không có câu trả lời hoặc chữ ký chủ đồ án nào được ghi thay trong báo cáo này.
