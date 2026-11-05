# Bộ số liệu MẪU cho kiểm thử tối ưu

Danh mục thật (`data/catalog`, sinh từ `materials_master.xlsx`) còn trống một số thông số nên chỉ có phương án
gạch đặc nung GN01 đủ số để tối ưu. Các file ở đây đè lên đúng các dòng còn thiếu bằng SỐ MẪU (`data_kind = SAMPLE`)
để kiểm thử chạy được NSGA-II trên nhiều phương án. Không dùng cho báo cáo.

    Catalog.from_csv("data/sample/catalog")

`suppliers.csv`, `supplier_materials.csv`, `vehicles.csv`: đại lý, giá đại lý và phương tiện MẪU, chuyển từ `data/catalog`
ngày 19/10/2026 (danh mục thật chưa có đại lý nào; nhập đại lý thật qua nút "Quản lý đại lý" trên `/app#gia`).
