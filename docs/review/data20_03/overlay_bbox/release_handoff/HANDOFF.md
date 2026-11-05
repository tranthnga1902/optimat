# Bàn giao viewer/render trên đúng base triển khai

- Base: opening-backend-candidate, đường dẫn và hash từng file trong manifest.json. Chỉ đọc candidate, không đổi runtime.
- release.patch chỉ sửa src/optimat/drawing/viewer.py, render.py và thêm hai file test. Không chứa Office, cầu thang, API, structural.py hoặc _clusters.
- Kiểm trên apply_check/: `git -c core.autocrlf=false apply --check <release.patch>` exit 0; áp dụng exit 0, hash byte khớp target. Giữ newline từng file.
- Test trên bản sao base đã áp dụng patch: 16 passed in 6.89s, exit 0, log focused.log. Hai source base và bốn target không đổi hash sau test.
- display_bbox=[minX,minY,maxX,maxY] là viewer mm/Y xuống, cùng origin; có thể âm. Frontend fitBox bbox, không fitSize(display_size) đơn độc. Legacy size/bbox_mm và phạm vi nhận diện giữ nguyên.
- overview.origin tường minh; whole view dùng renderer.view(None, origin), explicit plan vẫn bbox+1500mm. Native bounds lấy từ recorded geometry; primitive fallback gồm cung nhỏ R100.
- drawing_work_signals chỉ cấp hồ sơ: plans rỗng, hoặc mọi plan không có tường/lỗ và có tiêu đề KC. Gộp layer/block và tiêu đề có nguồn; không tự gán tầng/khối lượng hoặc gọi read_structural/render bổ sung.
- Render lỗi từng view/overview: giữ nhận diện, cad_missing=true và warnings riêng. Không bắt lỗi nhận diện/hash tại đây.
- Chưa chạy VN002, API, PostgreSQL, full suite hoặc restart runtime. Bộ test dùng dữ liệu tổng hợp và CSV cục bộ trên bản sao.
