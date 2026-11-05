# VN001 — đối chiếu mẫu kiểm trang3–4 tiên lượng

Đã đọc `data_nha_o/mau_kiem_tra_vn001.json` ởworkspace ngoài repo và đối chiếu bộVN001 build hiện có; không thay nguồn hoặcDB. [Biên nhận10 dòng/sốhọc](VN001_P3_P4_RECHECK.json) giữSHA mẫu kiểm và phép nhânDecimal/half-up0,001m³. Đây là source arithmetic audit, không training ground truth đãduyệt.

## Hai dòng BM-5

Nguồn hình: **PDF KCp8 KC-01-02** [mặtbằng](../../../reports/review_housing_20261103/huong_kc_page_8.png), **p10 KC-01-04** [mặtcắt](../../../reports/review_housing_20261103/huong_kc_page_10.png). Đã xem lại ảnh ởlượt này, không chỉ suy từhai chiều dài.

| Dòng nguồn | Nối vị trí/chi tiết | Phép tính nguồn và giới hạn |
| --- | --- | --- |
| p3 BM-5, L10,48m | **BM-4 tại trụcB**, nhãnCAD1000001; chi tiết1002FE7 ghiL12080mm,SL01. HaiBM-1 dọc biên rộng800mm:12,08−2×0,80=10,48m |10,48×1×1,15×1,3=15,66760→**15,668m³**. Phù hợpchiềudài khônggiao; chưa xác nhận bềrộng/chiềusâu/hệsốđào. Đềxuất ghi tênchuẩn BM-4 riêng, giữ labelBM-5 nguyênbản. |
| p4 BM-5, L10,99m | **BM-5 tại trụcA**, nhãnCAD1000057; chi tiết1003162 ghiL12590mm,SL01.12,59−2×0,80=10,99m |10,99×1×1,15×1,3=16,43005→**16,430m³**. Giữ BM-5 cho dòngnày, không xóa là“trùngdòng” hoặc gộp hai lượng. |

Đây làhai cấu kiện/loại vịtrí khácnhau, không phảihai lần cùngmộtBM-5. Chiều dài full vànet làhai phạmvi; không thay10,48 bằng12,08 hoặc10,99 bằng12,59 mà không đổi phânbổgiao cảhệ. Chứng cứ này hỗtrợ lỗi tên nguồn và quyước chiều dài, chưa chứng minh tổng đào đúng hìnhhọc.

## Độ phủ từng nhóm nguồn

| Dòng | Sốhọc | Hìnhhọc/nguồn đủ tới đâu |
| --- | --- | --- |
| BM-1 |21,797m³ khớp |p8/p10 cóhai băngbiên trục1/4,L7290,SL02. Chưa duyệt chiều rộngđào1m, sâu1,15m và1,3. |
| BM-2 |14,621m³ khớp |p8 cóhai băngtrục2/3; p10 L7290;7,29−3×0,80=4,89m giải thíchnet. Không coiđó là duyệt toàn thể tíchđào. |
| BM-3 |14,383m³ khớp |Băngngang trụcC,L12290;12,29−1,60=10,69m. Nguồn đào0,9m khácbềđáyBT0,8m nhưng chưa có căn cứ để gọi sai vìkhácđạilượng. |
| BM-5 dòngp3 |15,668m³ khớp |Tên tươngứngBM-4 trụcB như trên. |
| BM-5 dòngp4 |16,430m³ khớp |BM-5 trụcA như trên. |
| TC1-1 |1,047m³ khớp |p10 chi tiếtTC1-1;handle10032F8 L3500mm,SL01. Mẫuđào0,92×0,25 chưa tựchứngminh từ hìnhbậc; không đồng nhất tiết diệnbậc với hốđào. |
| TC1-2 |0,475m³ khớp |p10 handle10032F9 L1590mm,SL01; cácchiềuđào cònchờ. |
| DCT |0,342m³ khớp |Chưa truy đủhình/kíchthước0,9×0,65×0,45; giữchưa kiểmhìnhhọc. |
| MG1-1 |0,805m³ khớp |BảntríchCAD10041B5 ghiL3440mm,SL01; lượt này chưa mởảnhmặtcắtMG đểduyệt0,45×0,4 hoặc vịtrí. |
| Bểphốt |18,533m³ khớp |Mẫu2,7×3,2×1,65; chi tiếtbểp13 có phủbì2500×3000 vànhô100 mỗi bên, hỗtrợphânbiệt hìnhbể/hốđào. Chưa chốt sâuđào1,65,miềnđào/hệsố; không lấyBTbể hoặcthépbể làm chứng cứ thểtíchđào. |

**10/10 phépnhân khớp sốin sau làmtròn**, tổngcácdòngin104,101m³; tổngcác tíchchưalàmtròn nằm trongJSON. Không chuyển104,101m³ thànhlượngđào độc lậpđãkiểm. Hệsố1,3 chỉ táihiệnnguồn, chưa chứngminh ýnghĩa hoặc chấpnhận. Giữ chua_kiem/ngườikiểmtrống; quyềntraining/phânphốichưaxácnhận.

Không thay mẫukiểm, tiênlượngcanonical hoặc dữliệuDB. Đềxuất00 trình xácnhận hẹp tênBM-4 cho dòng10,48m vàgiữ hai dòngriêng; chưa tựkýthay hoặc đặttoànnhóm đãkiểm.
