# C-2 mã3/4 — đã có chiều dài trong nguồn

Đã xem [PDFp22 KC-02-04](C2_REBAR_PAGE22.png) và đọc trực tiếp INSERT/ATTRIB cùngKC hash22cda910…: [source rows vàca đối chứng](C2_REBAR_SOURCE_ROWS.json).

Hình dọc đoạn+3.150→+6.750 vàMC2–2 chỉ **2Ø20 mã3 +2Ø20 mã4**. Bảng bênphải nhóm **C-2(SL2)**, khôngnhómC-1/C-1A:

| Mã | INSERT | DAI mm | SL1 | SLA | TổngL m | TL in kg |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
|3|118CDA7|4300|2|4|17,2|42,4|
|4|118CDB3|4300|2|4|17,2|42,4|

Handle/tọađộ từngATTRIB vàheader nhómC-2 được giữ trongJSON. Đây làtrích source quaezdxf, **chưa phải production generic reader đãpass**.

**Một cột4/A:** 2mã×2thanh/mã×4,30m=17,20m; theo bảng đơntrọngp3 KC00 Ø20CB400V=2,470kg/m → **42,484kg**. HaiTL in42,4kg/mã là tổng **hai cột**; phân bổ(42,4+42,4)/2=**42,4kg/một cột**. Chênh **+0,084kg**. 42,484 làmtròn0,1kg thành42,5, nên **không gọi khớp sau làmtròn**; giữ hai cơsở tính/in riêng.

**Hai cột cùngloại:** tổng34,40m→**84,968kg**, so haiTL in84,8kg, chênh+0,168kg. Không lấySL2 nhân lặp sau khi đã dùngSLA4. Đây làca sốhọc cóđiềukiện, không tạo2instancegiả hoặc tựchạyReader.

**Ca chống trộn nhóm:** C-1 có118CCC5/118CCD1 cũngmã3/4,Ø20,L4300,SL1=2,SLA4; C-1A có118CD2A/118CD36 cùngmã/Ø/L nhưngSLA8. JSON giữ4hàng này làmnguồn âm: chỉkhớpmãthanh/Ø/L khôngđủ; readerphải rànggroupheader/ranh nhóm/sốloại C-2. Khôngmaphardcodeproduction bằng cácID trongbáocáo.

Scope là **đợtthép dọc lắpđặt gắn đoạnMC2–2**, chiều4300 bao gồm phần vượt khoảngcaođộ3600 (uốn/nối/neo theochi tiết); không phải khối lượng thanh cắt đúng biên hai sàn. Không tự thay4300 bằng3600 hoặc cộng neo thêm vào4300. Đai mã7 **77/cột làtoàn chiều cao**, số riêngđoạn nàyNULL. Chưa tínhlượngmua/hao hụt hoặc trừ thép giao nút.

Lưu ý mới trênPDF: đaiC-2 mã7 ghiL800,77/CK,154toàn nhóm nhưngcột tổngL in132,2m;154×0,800=123,2m. Đây làmâu thuẫn riêng cần giữcáchly, **không sửa nguồn hoặc dùng nó tính đaiđoạn**. Chưa đọcATTRIBhàng7 tronglượt nhỏnày, nhậnxét dựa ảnhp22; cầnxácminh tiếp nếuđượcgiao.

Chuyển01 cho03/02/06 dùngnguồn thật đểràgeneric/materialgrade. Khôngđổiapproval/canonical/code/DB; chưa cóngườikiểm vàkhôngproductionruntime/fulltest.
