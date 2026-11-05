"""Chuyển DWG sang DXF bằng LibreDWG; giữ ODA cho máy đã cài.

Chỉnh sửa từ app/parsers/dwg_parser.py của dự án floor-plan-exit-router
(https://github.com/Codedrin/floor-plan-exit-router, commit be08c17, giấy phép MIT,
Copyright (c) 2026 Master Drin). Xem THIRD_PARTY_NOTICES.md.
Thay đổi so với bản gốc: bỏ phụ thuộc vào mô hình dữ liệu của dự án gốc, thông báo tiếng Việt,
thêm thư mục cài đặt mặc định trên Windows.

DWG được chuyển sang DXF trước rồi đọc bằng ezdxf.
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
    """Máy chưa cài hoặc không tìm thấy bộ chuyển đổi DWG."""


class DwgConversionError(DrawingError):
    """Không chạy được bộ chuyển đổi hoặc việc chuyển đổi thất bại."""


def _candidate_install_globs() -> list[str]:
    return [
        "C:/Program Files/ODA/ODAFileConverter*/ODAFileConverter.exe",
        "C:/Program Files (x86)/ODA/ODAFileConverter*/ODAFileConverter.exe",
        "/usr/bin/ODAFileConverter",
        "/opt/ODA/ODAFileConverter*/ODAFileConverter",
    ]


def find_converter() -> str | None:
    """Ưu tiên LibreDWG; hỗ trợ ODA trên các máy cài đặt cũ."""
    libre_path = os.environ.get("LIBREDWG_CONVERTER_PATH")
    if libre_path and Path(libre_path).is_file():
        return libre_path
    libre = shutil.which("dwg2dxf")
    if libre:
        return libre
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
        "Để đọc file DWG cần LibreDWG (dwg2dxf): thêm vào PATH hoặc đặt LIBREDWG_CONVERTER_PATH. "
        "Máy cũng có thể dùng ODA File Converter, hiện chưa được cài hoặc không tìm thấy "
        f"trên máy này. Tải tại {ODA_DOWNLOAD_URL}, cài đặt, rồi thêm thư mục cài vào PATH hoặc đặt biến môi "
        "trường ODA_CONVERTER_PATH trỏ tới file ODAFileConverter.exe. Cách tạm thời: mở bản vẽ bằng phần mềm "
        "CAD, lưu dưới dạng .dxf rồi tải file đó lên."
    )


def convert_dwg_to_dxf(dwg_path: str, output_dir: str) -> str:
    """Chạy bộ chuyển đổi, chỉ trả DXF khi thành công và file không rỗng."""
    converter = find_converter()
    if not converter:
        raise DwgConversionUnavailable(unavailable_message())

    with tempfile.TemporaryDirectory() as input_dir:
        staged_dwg = Path(input_dir) / "drawing.dwg"
        shutil.copy(dwg_path, staged_dwg)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        expected_output = Path(output_dir).resolve() / (Path(dwg_path).stem + ".dxf")
        # Thư mục tạm riêng tránh đọc nhầm DXF còn lại từ lần chuyển trước.
        converted = Path(input_dir) / "output"
        converted.mkdir()
        generated = converted / "drawing.dxf"
        is_libre = Path(converter).stem.lower() == "dwg2dxf" or converter == os.environ.get("LIBREDWG_CONVERTER_PATH")
        name = "LibreDWG" if is_libre else "ODA File Converter"
        # ODAFileConverter <thư mục vào> <thư mục ra> <phiên bản> <loại> <đệ quy> <kiểm tra> [bộ lọc]
        args = ([converter, "-a", "r2018", "-o", str(generated), str(staged_dwg)] if is_libre else
                [converter, input_dir, str(converted), _OUTPUT_DXF_VERSION, "DXF", "0", "1"])
        try:
            result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    timeout=CONVERSION_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            raise DwgConversionError(f"Chuyển DWG quá thời gian {CONVERSION_TIMEOUT_SECONDS} giây.") from exc
        except OSError as exc:
            raise DwgConversionError(f"Không chạy được {name}; kiểm tra cài đặt bộ chuyển đổi.") from exc
        if result.returncode != 0:
            raise DwgConversionError(
                f"{name} báo lỗi (mã {result.returncode}): {(result.stderr or result.stdout)[-2000:]}")
        if not generated.is_file() or generated.stat().st_size == 0:
            raise DwgConversionError(
                f"{name} đã chạy nhưng không tạo ra file .dxf hợp lệ. File DWG có thể bị hỏng "
                "hoặc thuộc phiên bản không được hỗ trợ.")
        shutil.copyfile(generated, expected_output)
        return str(expected_output)
