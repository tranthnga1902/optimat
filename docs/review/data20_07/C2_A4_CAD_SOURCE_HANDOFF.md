# Nguồn CAD nhỏ cho reader generic —03/06/01

Artifact **`docs/review/data20_07/C2_A4_CAD_SOURCE.json`**, khoảng302KB, KC đúng hash `22cda9103ace1a6c0826805836f309a97bef71c03dc27d3508efdb56fe0ec19c`. Đây là trích thuộc tính nguồn, không phải input chứa đáp án production. Không thêm expectedgross/net hoặc ép ID4/A vào result. Oracle tính tay vẫn ởfile riêng.

Callshape đọc: `payload=json.load(open(path, encoding='utf-8')); for view in payload['views']: entities=view['entities']`. Mỗientity có`handle/type/attributes`; INSERT có`attribs`, LWPOLYLINE/LEADER có`vertices`, DIMENSION có`measurement_raw` và cácdefpoints/rawtext; HATCH giữpolylineboundary khi có. `referenced_block_definitions` giữ3 blockdefinition được tham chiếu; phải ápINSERT transform và giữ đườngdẫn lầnchèn khi đọc chữ/trục trongblock. Không đọcblocklocalnhưmodelspace.

Ba cửa sổ kiểm có76/234/82entity: mặt bằng định vịp19, chi tiết cộtp22, sàn tầng3p24. Bbox là cửa sổ trích thủ công **chưa phải sheet/viewbbox đã nhận dạng**; titlehandle/PDFpage phục vụ tìm lại. Không kết luận axis/leader/hatch đã được match đúng từ việc entity nằm cùngcửa sổ.

Locator chữ: titlep19`118449C`; C-2 gần4/B`11844DA`, gần4/A`11844E1`; titlechi tiết`11858E8`; caođộchi tiết`11858DD`(+3.150),`11858E1`(+6.750); titlesàntầng3`117622B`, caođộ`11767BC`. Reader cần tự kiểmtrục/leader/bounds và liêntầng từentity, không hardcode các locator thành nhận dạng production. Raw legacyencoding được giữ, cần decode theo textstyle. SourceINSUNITS=0 chưa tự quyđổi hìnhhọc; DIM/ngữcảnhhồsơ cần kiểm.

Nguồn có entity nhãntrục/hìnhcột/kíchthước, nhưng extraction không suy ngầm section2–2,2cạnh220 hoặc H120 thành số đã chọn. Nếu readerchưa đủ đối tượng/quan hệ thì báo thiếu; không fallbackoracle. Tầng2+3 và một đoạnC-2đã được đọcPDF trongoracle, cònartifact này chỉ là nguồnCAD để03 táihiện/vágeneric theo quyền01.

Lượt này chỉ đọcmodelspace/thuộctính trong3cửa sổ vàblockdefinitionliênquan; không rough/full/DB/runtime/browser/AI, khôngsourceproduction/canonical. Giữchua_kiem và khôngtạophêduyệt. `ONE_ELEMENT_TRACE` cũ giữ nguyên.
