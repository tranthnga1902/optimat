# Q01 round 2 — SOURCE-READY

Theo release của coordinator qua parent: thay nhóm linear_works từ (b,d) thành (b,d,source) đã được BA duyệt; giữ nguồn ở hai dòng bê tông/cốp pha, không đụng deduct_ties/N03.

## File đã sửa

- src/optimat/rough/secondary.py: thêm source vào khóa nhóm/sắp xếp, truyền source vào `_work` bê tông và cốp pha. Không đổi công thức.
- tests/test_rough_secondary.py: thêm8 ca (2kind×3source +2thứ tự nhóm trộn), kiểm structuralA/manualC/inferredC; nguồn/evidence giữ đúng; cùng tiết diện khác nguồn tách dòng, tổng khối lượng mẫu vẫn0,264m³/cốp pha2,4m². Cốp pha trong nhóm trộn kế thừa trạng thái yếu nhất cùng tầng theo chính sách có sẵn, nên đềuC, không nâng toàn cục thànhA.
- tests/test_rough_status.py: fixture copied Catalog bằng deepcopy, chỉ XM02/CA01 gán waste_pct0,data_kind SYNTHETIC trong bộ nhớ để cô lập hệ số tham khảo; giữ mọi assert quantity/range/confirmation/warnings cũ. Thêm nhánh thiếu waste_pct ->D, completeFalse, lượng muaNone, reason đúng; không sửa dữ liệu catalog hoặc A01.
- src/optimat/rough/status.py KHÔNG đổi trong round2.

## Bằng chứng

Snapshot trước sửa: *.before.py, hash_before.json. Diff riêng: round2.patch. Hash: hash_source_ready.json.

- secondary.py: F04DEE48A67056092D8D327CC1FDA95DA97AEFE10A499E2AC4135901B21B844B
- test_rough_secondary.py: C4EB3AACEC13112AE31E1EF8962A47124B16AC4763582563550C87FB1651C1C3
- test_rough_status.py: 6765256AD286BCFD598E2063B8A1626BB04938D832A761DFB46A138D6D0844E9
- status.py giữ F35DF97DE208E3CD9C9E7C67BE82197FB94819D291403695BC1DF1870652A812

CHƯA chạy test/backend/full/DB do khóa kiểm thử. SOURCE-READY không phải nghiệm thu. Giữ source/test ổn định chờ coordinator cấp lượt chạy. Không viết tài liệu chung.
