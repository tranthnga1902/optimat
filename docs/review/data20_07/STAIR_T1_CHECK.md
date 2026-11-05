# Cầu thang VN002 tầng1→2 — kiểm nguồn, chưa duyệt khối lượng

[KCp37 KC-06-01 toàn tờ](STAIR_PAGE37.png), [chi tiết bản nghiêng](STAIR_WAIST_DETAIL.png), [KTp19 KT-17](STAIR_KT_PAGE19.png), [KTp20 KT-18](STAIR_KT_PAGE20.png), [JSON nguồn bảng và tính từng hàng](STAIR_T1_SOURCE.json). Đúng cặpVN002 build đã khóa, không trộnT2→3/dầm hoặc biến thành hồ sơ mới. KT vàKC cùng thiết kế, không là đápán độc lập đãduyệt.

## Đọc trực tiếp

KCp37 tên **từ tầng1 lên tầng2**, ôtrục2–3/A–B. Ba hướng chạy bậc trênmặtbằng: vếtrái số1…6, đoạnđổi hướng chạyngang số7…11, vếphải số12…17; hai vùnggóc nối cần phânranh riêng, **không mặc định cảhai là chiếu nghỉ phẳng** vì còn cóbậc/đổi hướng. Kíchthước bao trục3580×3780; chuỗi ngang110+1180+1000+1180+110; chuỗi dọc1310+1250+1220. Các số là kíchthước trongchuỗi bảnvẽ, chưa tựcoi1180/1310 đều là bềrộngbảnsànnet ở mọi góc.

Chi tiếtcấu tạo bảnthang ghi **120mm vuông góc mặt dốc**, thépchínhØ10a100, phânbốØ8a200; **BẬC THANG XÂY GẠCH**. H150mm và+3.150 ởvùng đầu lên sàntầng2 làphần khác, không dùng150 cho bảnnghiêng hoặc cộng bê tôngtamgiác bậc gạch vàoBT.

KTp19 có nhiều mặtbằng tầng, không chọn “MẶT BẰNG THANG T3” cạnhtrênphải như nguồnT1. KTp20 cómặt cắt1–1/2–2, cốt+3.150 và+3.900 cho cácvùng/đợt khácnhau; đầuT1 sảnhKT+0.150 khác cốtKC±0.000. Chuỗi cổbậc có185 vàđầu/cuối thayđổi, không dùng17×185 đểấn định tổngcaođộ hoặc dùngchiềucao toàntầng cho từngvế. Chưachốt datum hoànthiện↔kếtcấu tại từnggối.

## Bê tông/cốp pha: phần xác định và đầu vào thiếu

Với một vế **sau khi duyệt** biên hai gối, bềrộngnetb, chiều chiếubằngr và chênh cao độ **kếtcấu**h: `L_nghiêng=sqrt(r²+h²)`, `V_bản=0,120×b×L_nghiêng`, `A_CP_đáy=b×L_nghiêng`. Bậc xây gạch tách côngtác/khối lượng; không cộng `0,5×b×r×cao_cổ_bậc` vào BT. CPcạnh, đầu bản, phần tựa dầm vàgiao nghỉ phải theo điều kiện tiếp xúc thực, không cộng mọi mặt mặc định.

Vùng sàn/chiếu tới dày150 nếu xác định được polygonnetP và không thuộc lượngsàn/dầm đãtính: `V=0,150×area(P)`; CPđáy chỉphầncần khuôn thực. Hai vùnggóc đổi hướng tính bằngpolygon/rampđúng hình, không lấyhai chữnhật nhânbừa. Nếu đã phânbổ trong côngtácsàn thì không cộng lần2 dưới cầu thang.

**Chưa có tổngV/CP đủ căn cứ** ởlượt này. Cần người đo chốt: (1) caođộ đầu/cuối của từngvế tại đườngtim bản kếtcấu; (2) ranhgối dầmchânKC-01-05/dầmsàn và vùnggóc, rộngnet; (3) datum hoànthiệnKT+0.150 soKC±0.000; (4) polygonvùng150 và phânbổ giao với sàn/dầm; (5) mặt CPthực không tiếp xúc gối/tường. Không lấyLthép3200/4000/4500 làmLnghiêng bê tông vì chứa neo/uốn và có phạmvi khác.

## Thép — đúng nhómT1 SL1, tám hàng

Đã đọc8INSERT/ATTRIB thực trongKC, kiểmSH/DK/DAI/SLA khớp8hàngp37; JSONlưuhandle từnggiátrị vàmỗihàng có`source_insert_handle`. Headernhóm CADTEXT**118E51D** ghiTHÉP BẢN THANGT1. Không nhân2 hoặc3 theo sốvế; cáchàngđã làtoàn nhómT1SL1.

| Mã | Ø | Lđơn mm | Sốthanh toànnhóm | ΣL tính lại m | Khối lượng theoKC-00 kg/m, kg |
| --- | ---: | ---: | ---: | ---: | ---: |
|1|10|3200|12|38,40|23,69280|
|2|10|3380|12|40,56|25,02552|
|3|10|4000|13|52,00|32,08400|
|4|10|4180|13|54,34|33,52778|
|5|10|4500|12|54,00|33,31800|
|6|10|4680|12|56,16|34,65072|
|7|8|1310|20|26,20|10,34900|
|8|8|1330|20|26,60|10,50700|

Đơntrọngp3KC00:Ø10=0,617kg/m;Ø8=0,395kg/m. Tổngtừ chiều dài chưa làmtròn: **Ø10 182,29882kg; Ø8 20,85600kg; tổng203,15482kg**. Tổngin182,2+20,8=**203,0kg**; chênh+0,15482kg. Tổngmỗinhóm làmtròn0,1kg là182,3 và20,9, **không gọi khớp sau làmtròn** với ôtổngin. Một vài tổngchiềudài hiểnthịmộtchữsốthậpphân nên giữsốLđơn×N trước khi cộng.

Scope làthép theobảngT1/chiều triểnkhai từngmã; chưakiểm độc lập đườngtim uốn/neo vàphânđoạn tại mọigối. Không tựgánmỗi2hàng cho1vếkhithanh cóthểchạy qua vùnggóc. Không chuyển203kg thànhtổngBT hoặc nhu cầu mua đãcóhao hụt.

Đã tạoảnh nguồn vàđọcnhỏ đúng8hàngCAD; khôngCADbatch/rough/fulltest/DB/sourceUI. Chưa córeviewerngườithật, giữ`chua_kiem`;03/06 nhậnnguồn qua01 đểtriểnkhaigeneric theoquyền. NhánhOffice/AI vẫn dừng.

## Hướng mapping snapshot được đề xuất, chưa triển khai

Nếu dùng nhập tay có nguồn theo quyềnuser, gắn vào **stair instance T1→T2 riêng**: thickness_perpendicular=120mm vớiảnhchi tiếtp37; vùngchiếutới150mm cópolygon/scope riêng; từngvế lưuwidthnet,run,delta_z,start/end/support cùng evidence hoặcNULL. Thiếu ánhxạ thì hiểnthị“chưa gán”, không đặtProjectParams120 toànnhà hoặc mặc địnhbậcBT. Nguồnnhập tay phải cótrạngtháingười dùngnhập/chờduyệt, khôngA tựnhận. Chưa córeceiptUI/snapshot/API tronglượt này vàkhôngtạo nó đểlấpQAempty. RootP0/quyềnhunk/runtime do01xếplịch,07chỉbàngiaonguồn/mapping.
