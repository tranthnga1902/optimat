# Gate fix — kiểm trọng tâm

Lệnh tái sinh: `.venv/Scripts/python.exe scripts/review_housing_quantities.py`.

Lệnh test: `.venv/Scripts/python.exe -m pytest tests/test_review_housing_quantities.py tests/test_import_housing_estimates.py -q -p no:cacheprovider --basetemp reports/review_housing_20261103/gate_fix/pytest_tmp_20261103_a`.

Kết quả: **9 passed in 3.06s**, exit0. Lượt đầu dùng temp mặc định gặp lỗi tạo thư mục sandbox:8 passed,1 setup error; đã đổi temp sang thư mục báo cáo riêng, không sửa logic để bỏ test.

Test tái sinh hai lần trong thư mục cô lập chứng minh gate còn sống, hai dòng mâu thuẫn không có eligible_label_id, giữ11 nhãn bằng chứng nhưng chỉ9 nhãn liên kết mức bảng;455 dòng cách ly. Source estimate byte-for-byte không đổi qua tái sinh; human_approval=false. Test gate dùng issue type/status, không tên case.

before_hashes.json, after_hashes.json và changes.diff ghi trạng thái file tương ứng trước/sau. Không chạy full suite, không DB, không D02/cases/catalog/rules. Tính lại42 mã thanh bể lưu riêng cấp báo cáo, chưa dùng số mới thay nhãn hiện có. Tổng bể chưa chốt; cần quyết định số thanh bố trí/cửa thăm/quy ước uốn.
