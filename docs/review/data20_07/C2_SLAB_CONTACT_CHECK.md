# H120 và nút đầu C-2 tại4/A — kiểm nguồn thiết kế

[Toàn trang24 KC-03-02](C2_SLAB_PAGE24_CONTEXT.png), [vùng3–4/A–B](C2_SLAB_3_4_A_B.png), [chú giải](C2_SLAB_LEGEND.png), [biên nhận nguồn](C2_SLAB_CONTACT_RECEIPT.json). CùngPDF/KC VN002 đã khóa; không dùng một tờsàn khác hoặc thuộc tính toàncôngtrình để điền120.

## Đọc được và quan hệ theo hình thiết kế

- Tờghi **MẶT BẰNG KẾT CẤU SÀN TẦNG3**. Ô3–4/A–B có kíchthước trục5180×4000; C-2 tại4/A ởgóc dưới phải, đốichiếu mặtbằng địnhvị p19. Hai dầmbiên theo trục4 vàA gặp tại nút này; vùngsàn phía trong nằm về phía3/B. Trục4–A làtrục nhà, không phải tuyếnmặt cắt.
- Ghi chú **+6.750 / H=120MM** nằm trongphần phải của hình, liênhệ với vùngsàn giáp hệdầmbiên4/A. CADchữ tươngứng `11767BC`(caođộ),`11767BF`(H120), title`117622B`; raw/tọađộ đã có ởgóiC2_A4_CAD_SOURCE. Chúgiải **ôtrắng: bản sànBTCT dày12cm** củng cố vùngkhôngpattern gần4/A.
- Có phânvùng khác trên **cùngtờ**: hatchchéo chéo đôi gần3/B làsàn12cm hạcốt5cm; vùngdấu+15cm vàsànchéo nằm quanh2–3; ôdấuX(lỗmở) quanh2–3/B. Bêntrái ghi+7.500/H120, khác caođộ phầnphải+6.750. Vìvậy khônggán mộtcađộ/dàysànchung cho cảtờ.
- Trong vùngkề4/A trênhình đã xem, khôngthấy kýhiệu lỗmở/hạcốt/thay dày ngaytại góc nút; khôngmang hatchhạcốt gần3/B sang4/A. Đây là **đọc kýhiệu/ranh thiết kế từPDF**, chưa là kếtquả kiểm polygonCAD hoặc phát hiệnmọilỗ.

## Khi có thể dùng120 và khi chưa đủ

**Bổ sung đã xem độc lập trang29 KC-04-03, khung tênCHI TIẾT DẦM:** [ảnhtoàntờ](C2_BEAM_D14A_PAGE29.png), [mặtcắt3–3](C2_BEAM_SECTION33.png). Dầm **D1-4A(SL01)** cóhìnhdọc từtrục1→4, nhịpcuối3–4=5180; đầu phía1 ghi+7.500, đoạncuối phía4 ghi+6.750, đổi cao750mm. Mặtcắt **3–3** đượcchỉ ở vùng gầngối4, ghi b220,cánh120,sườndưới280,tổng400mm. NhãnD1-4A(22×40) trêntrụcA của p24 và nhịp/cuốitrục4 tạo thêm căn cứ liênkết thiết kế dầm biên đi vào nút4/A. Không lấy cao+7.500 phía1 áp cho nút4/A.

Chi tiết3–3 củngcố **cánh120mm ở dầm biên đoạncuối+6.750**, nên nguồnH120 không chỉ làghi chú trêncùngmặtbằng. Đây là đốichiếu **khác hình trong cùngthiết kế**, không phải đápán/nguồn độc lập. Không suy từ hìnhcánh mộtphía rằngpolygon sàn thực phủtrọn tiếtdiệncột hoặc tấtcảsàn tầng3 đều120. Chưa tríchhandleCADriêng tờ29 trong lượt này; sourcePDFpage/ảnh/hash ởreceipt. Không tựđổi chínhsáchBOQ từ120+280=400.

Đủ căn cứ **trình số đo thiết kế cóđiềukiện**: mặt sàntrên+6.750, vùngsàn thường12cm gần nút4/A, kết hợp tiết diệnC-2 p22 để tínhlăngtrụnet theo quyước cột mặtbằng. Không chọnH120 chỉ vì note cùngtờ; đã xét trục/vùng giáp nút vàlegend, tách cácvùngđặcthù.

**Chưa đủ chứng minh tiếp xúc hìnhhọc/đếm giao mộtlần trong runtime.** Mặt sàn ởgóc liênkết qua hệdầmbiên; khôngtự kếtluận cómộtpolygonbảnsàn bao trọn tiết diệncột220×220 hoặc đãsởhữuphần nút. Cần nguồnCAD đượcgiải block/transform đúng, chọn đúng vùngsàn thường, lậpquan hệ dầm–cột–sàn vàquyướcphânbổ giao. Chưacóclosedpolygon/diệntíchgiao/dầmclip receipt thì cácgiátrịđó đểNULL.

Dođó **gross0,174240m³** làlăngtrụmộtđoạn; **net0,168432m³** vẫn là đốichiếu theoquyước đã nêu, khôngthành kếtquảđãkiểm củaengine. Nếu readerchưa gắnvùngH120đúngnút thì hiểnthịthiếu, khôngfallback120 từoracle/toàntờ. Nếu phânbổ nút theoquyước khác phải đốichiếu lại cảdầm/sàn, không chỉtrừ thêm400mm vào cột.

Lượt07 đã xemảnhPDF đầyđủ rồi tríchvùng/legend, ghiSHAảnh/locatorvàphầnthiếu. Chưađo lạiCADboundaries, chưachạyreader/runtime/full/DB, chưa sửa production/canonical. `chua_kiem`,humanapprovalfalse; chuyển01 để03/06 nhận nguồn và giới hạn.
