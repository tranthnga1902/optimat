# Bộ số liệu MẪU cho kiểm thử tối ưu

Danh mục thật (`data/catalog`, sinh từ `materials_master.xlsx`) còn trống một số thông số nên chỉ có phương án
gạch đặc nung GN01 đủ số để tối ưu. Các file ở đây đè lên đúng các dòng còn thiếu bằng SỐ MẪU (`data_kind = SAMPLE`)
để kiểm thử chạy được NSGA-II trên nhiều phương án. Không dùng cho báo cáo.

    Catalog.from_csv("data/sample/catalog")
