# WorkDimensions — hợp đồng backend phiên03, SOURCE-READY trước focused

Mọi field cũ giữ tên/kiểu/default; trường thêm tương thích JSON. Chưa test terminal, không gọi đã nghiệm thu. Snapshot/hash/diff trong thư mục này. Backend không sửa BOQ/frontend/DB, không lấy TypeScript cũ làm bằng chứng.

```python
label: str
basis: Literal['input', 'reference', 'union', 'deduction'] = 'input'
count: Optional[float] = None
repetitions: int = Field(default=1, ge=1)
length_m: Optional[float] = None
gross_length_m: Optional[float] = None
deducted_length_m: Optional[float] = None
width_m: Optional[float] = None
height_m: Optional[float] = None
floor_height_m: Optional[float] = None
bottom_level_m: Optional[float] = None
top_level_m: Optional[float] = None
slope_ratio: Optional[float] = None
faces: Optional[float] = None
concrete_height_m: Optional[float] = None
thickness_m: Optional[float] = None
top_length_m: Optional[float] = None
top_width_m: Optional[float] = None
slope_length_m: Optional[float] = None
diameter_m: Optional[float] = None
area_m2: Optional[float] = None
opening_area_m2: Optional[float] = None
net_area_m2: Optional[float] = None
source: str
field_sources: dict[str, str] = Field(default_factory=dict)
missing_fields: list[str] = Field(default_factory=list)
not_applicable_fields: list[str] = Field(default_factory=list)
note: str = ''
```

model_config=ConfigDict(allow_inf_nan=False): mọi field số từ chối NaN/±inf, không đổi thành0. ValidationError là ValueError, route compute_rough hiện bắt và trả422, không nới serializer.

- Dài/rộng/cao/dày/cao độ/Ø theo m; diện tích m²; slope_ratio/số mặt/count/repetitions không có đơn vị.
- count cho một cấu kiện/lớp/thanh của một lần; repetitions là số lần lặp tầng. Tổng vật lý (nếu được áp dụng) dùng count×repetitions, không nhân length; count0/None không thành1.
- basis=input là hình học đầu vào; reference giữ raw/tham khảo (không nhân thành net); union tổng hợp đoạn hợp không là cấu kiện mới; deduction là khoản trừ không có hình hộp giả. Không cộng reference+union. quantity/missing/status cuối WorkItem vẫn là căn cứ về lượng; metadata/đã kiểm không nâng A/B/C/D.
- Producer truyền field=None → missing_fields; không truyền field không dùng → not_applicable_fields. 0 đã biết giữ0. JSON round-trip giữ hai danh sách và field_sources, không phân loại lại mọi null thành thiếu. Source rỗng được giữ thiếu nguồn, không bịa vị trí bản vẽ.
- length_m dầm là net; gross_length_m là trục, deducted_length_m khoản trừ. height_m là cao toàn tiết diện dầm, concrete_height_m là cao tính BT. Field_sources ghi đúng nhánh Beam/params được dùng.
- floor_height_m khác height_m cao xây/cao cột; bottom_level_m/top_level_m có dấu, không lấy trị tuyệt đối. top_length_m/top_width_m là đỉnh móng vát. Directvolume ưu tiên thì kích thước chỉ reference.
- Sàn area/opening/net riêng, không sinh rectangle. Khi void chưa biết, metadata net_area=None; không sửa công thức cũ bằng metadata. Hở về mức đủ của sàn chưa nhập void trong engine là giới hạn đã có, cần01 phân riêng nếu muốn sửa, không tuyên bố đóng bằng gói này.
- Thang length_m là chạy ngang, slope_length_m dài nghiêng; bậc/chiếu nghỉ/dầm là record riêng. Steel diameter_m và dài cắt/count từ bảng; thép hàm lượng/manual giữ dimensions=[] khi không có hình học thanh.
- _neg có record deduction, không cạnh giả. N03 giữ từng raw reference kèm union riêng; thiếu vị trí/CP đáy/partial vẫn theo N03/Q02, không mất raw hoặc đổi trạng thái bằng metadata.

UI02 cần dùng field bổ sung trong detail và phân biệt missing_fields/not_applicable_fields; note không phải input cho thuật toán. BOQ hiện chưa xuất đầy đủ dimensions mới: ngoài quyền gói03, cần01 cấp owner trước khi nghiệm thu API/UI/BOQ. Chưa kiểm browser/ACTUAL-build.
