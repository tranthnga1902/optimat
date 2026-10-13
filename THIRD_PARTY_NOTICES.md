# Mã nguồn của bên thứ ba

Dự án này có dùng lại và chỉnh sửa mã từ dự án sau. Khi viết báo cáo đồ án, cần ghi rõ phần này
là mã kế thừa, không phải mã tự phát triển.

## floor-plan-exit-router

- Nguồn: https://github.com/Codedrin/floor-plan-exit-router (commit be08c1747f1482a74e0b6fed1a082ff26a7fc0b6)
- Giấy phép: MIT

| File trong dự án này | Lấy từ file gốc | Mức độ |
|---|---|---|
| `src/optimat/drawing/dwg_convert.py` | `app/parsers/dwg_parser.py` | Giữ logic tìm và gọi ODA File Converter; bỏ phụ thuộc vào mô hình dữ liệu gốc, đổi thông báo sang tiếng Việt |
| `src/optimat/drawing/layer_classifier.py` | `app/detection/layer_classifier.py` | Giữ cách tổ chức (quy tắc mặc định, ghi đè theo file); viết lại bộ quy tắc cho tên layer tiếng Việt và vai trò dùng cho đo bóc |
| `tests/test_drawing_io.py` (một phần) | `tests/test_dwg_parser.py` | Chuyển thể các bài kiểm thử tìm ODA File Converter |

Các phần KHÔNG lấy từ dự án trên: nhận diện tường theo chiều dày, đo bóc, trừ lỗ cửa, mô hình giá,
tối ưu, agent, cơ sở dữ liệu.

### Nội dung giấy phép MIT của dự án gốc

MIT License

Copyright (c) 2026 Master Drin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
