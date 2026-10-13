"""Chuyển DWG sang DXF bằng ODA File Converter.

Chỉnh sửa từ app/parsers/dwg_parser.py của dự án floor-plan-exit-router
(https://github.com/Codedrin/floor-plan-exit-router, commit be08c17, giấy phép MIT,
Copyright (c) 2026 Master Drin). Xem THIRD_PARTY_NOTICES.md.
Thay đổi so với bản gốc: bỏ phụ thuộc vào mô hình dữ liệu của dự án gốc, thông báo tiếng Việt,
thêm thư mục cài đặt mặc định trên Windows.

DWG là định dạng nhị phân đóng của Autodesk, không có thư viện Python miễn phí nào đọc trực tiếp
một cách tin cậy. Cách làm thực tế là chuyển sang DXF trước rồi đọc bằng ezdxf.
"""
from __future__ import annotations

import glob
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ODA_DOWNLOAD_URL = "https://www.opendesign.com/guestfiles/oda_file_converter"
CONVERSION_TIMEOUT_SECONDS = 120
_OUTPUT_DXF_VERSION = "ACAD2018"


class DrawingError(Exception):
    """Lỗi đọc bản vẽ mà API nên báo cho người dùng (mã 422), không phải lỗi hệ thống."""


class DwgConversionUnavailable(DrawingError):
    """Máy chưa cài hoặc không tìm thấy ODA File Converter."""


class DwgConversionError(DrawingError):
    """Đã chạy ODA File Converter nhưng việc chuyển đổi thất bại."""


def _candidate_install_globs() -> list[str]:
    return [
        "C:/Program Files/ODA/ODAFileConverter*/ODAFileConverter.exe",
        "C:/Program Files (x86)/ODA/ODAFileConverter*/ODAFileConverter.exe",
        "/usr/bin/ODAFileConverter",
        "/opt/ODA/ODAFileConverter*/ODAFileConverter",
    ]


def find_converter() -> str | None:
    """Tìm ODA File Converter theo thứ tự: biến môi trường ODA_CONVERTER_PATH, PATH, thư mục cài mặc định."""
    env_path = os.environ.get("ODA_CONVERTER_PATH")
    if env_path and Path(env_path).is_file():
        return env_path
    which_result = shutil.which("ODAFileConverter")
    if which_result:
        return which_result
    for pattern in _candidate_install_globs():
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def is_available() -> bool:
    return find_converter() is not None


def unavailable_message() -> str:
    return (
        "Để đọc file DWG cần phần mềm ODA File Converter (miễn phí), hiện chưa được cài hoặc không tìm thấy "
        f"trên máy này. Tải tại {ODA_DOWNLOAD_URL}, cài đặt, rồi thêm thư mục cài vào PATH hoặc đặt biến môi "
        "trường ODA_CONVERTER_PATH trỏ tới file ODAFileConverter.exe. Cách tạm thời: mở bản vẽ bằng phần mềm "
        "CAD, lưu dưới dạng .dxf rồi tải file đó lên."
    )


def convert_dwg_to_dxf(dwg_path: str, output_dir: str) -> str:
    """Chạy ODA File Converter ở chế độ hàng loạt, trả về đường dẫn file .dxf tạo ra."""
    converter = find_converter()
    if not converter:
        raise DwgConversionUnavailable(unavailable_message())

    with tempfile.TemporaryDirectory() as input_dir:
        staged_dwg = Path(input_dir) / Path(dwg_path).name
        shutil.copy(dwg_path, staged_dwg)
        # ODAFileConverter <thư mục vào> <thư mục ra> <phiên bản> <loại> <đệ quy> <kiểm tra> [bộ lọc]
        args = [converter, input_dir, output_dir, _OUTPUT_DXF_VERSION, "DXF", "0", "1"]
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=CONVERSION_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            raise DwgConversionError(f"Chuyển DWG quá thời gian {CONVERSION_TIMEOUT_SECONDS} giây.") from exc
        if result.returncode != 0:
            raise DwgConversionError(
                f"ODA File Converter báo lỗi (mã {result.returncode}): {result.stderr or result.stdout}")
        expected_output = Path(output_dir) / (staged_dwg.stem + ".dxf")
        if not expected_output.exists():
            raise DwgConversionError(
                "ODA File Converter đã chạy nhưng không tạo ra file .dxf. File DWG có thể bị hỏng "
                "hoặc thuộc phiên bản không được hỗ trợ.")
        return str(expected_output)
