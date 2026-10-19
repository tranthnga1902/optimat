"""Cấu hình chung của OptiMat AI. Sửa ở đây thay vì sửa rải rác trong mã."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
CATALOG_DIR = DATA_DIR / "catalog"
MODELS_DIR = ROOT / "models"

# Biến môi trường cục bộ (DATABASE_URL, OPENAI_API_KEY...) trong file .env ở thư mục gốc, không đưa lên Git.
# Biến đã đặt sẵn trong môi trường thắng file .env.
_ENV = ROOT / ".env"
import os as _os
if _ENV.exists() and not _os.environ.get("OPTIMAT_NO_DOTENV"):   # pytest đặt cờ này: kiểm thử không dùng database thật
    for _line in _ENV.read_text(encoding="utf-8").splitlines():
        _k, _eq, _v = _line.strip().partition("=")
        if _eq and _k and not _k.startswith("#"):
            _os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# ---- Nhận diện bản vẽ ----
# Ký hiệu nhận dạng theo Quy ước bản vẽ v1.0 (tên layer -> vai trò, tiền tố block cửa)
# nằm trong data/rules/concepts.csv; 23 điều khoản QU trong data/rules/quy_uoc.csv (drawing/concepts.py).

# Lớp chiều dày tường (mm): tên lớp -> (nhỏ nhất, lớn nhất) của khoảng cách hai nét song song.
# Dải đủ rộng để nhận cả tường 100 (lớp 110), 200 (lớp 220), 300 (lớp 330) gặp trên bản vẽ thật.
WALL_THICKNESS_CLASSES = {"110": (85, 135), "150": (136, 175), "220": (176, 260), "330": (280, 370)}
MIN_WALL_OVERLAP_MM = 300.0
PARALLEL_ANGLE_TOL_DEG = 1.0
WALL_LAYER_MIN_SCORE_MM = 2000.0   # tổng chiều dài cặp nét tối thiểu để tự nhận một layer là layer tường
WALL_LAYER_REL_SCORE = 0.6         # và không dưới tỷ lệ này so với layer điểm cao nhất
MAX_OPENING_GAP_MM = 3600.0        # khe giữa hai đoạn tường thẳng hàng có cửa thì được nối lại
DOOR_ARC_RADIUS_MM = (450.0, 1300.0)

# Chiều cao tầng và kích thước cửa là thông số của dự án (bảng projects), không có giá trị mặc định (Quy ước B7).

# Cột trên mặt bằng kiến trúc: vùng tô đặc (SOLID, kể cả hatch đã bị tách thành tam giác) gần chữ nhật, hai cạnh trong
# khoảng này (mm) và lấp đầy khung bao ít nhất COLUMN_MIN_FILL. Mới chỉnh trên 2 bản vẽ build (cột 200×200, 220×220).
COLUMN_SIDE_MM = (150.0, 700.0)
COLUMN_MAX_ASPECT = 4.0
COLUMN_MIN_FILL = 0.8
# Tên mặt bằng tầng trệt (đã bỏ dấu, chữ thường), dùng khi bản vẽ không ghi đủ cao độ các tầng
GROUND_PLAN_PATTERNS = (r"\btret\b", r"\btang 1\b", r"\btang mot\b")

# ---- Chi phí và tối ưu ----
# Hao hụt lấy từ materials.waste_pct, đơn giá nhân công từ bảng labor_rates (PostgreSQL); thiếu thì báo, không điền mặc định.
ROAD_FACTOR = 1.3              # cự ly đường bộ ~ đường chim bay x hệ số; thay bằng OSRM khi tích hợp
TRIPS_PER_DAY = 4
R_SI, R_SE = 0.13, 0.04        # nhiệt trở bề mặt trong, ngoài (m2K/W)

NSGA_POP_SIZE = 60
NSGA_GENERATIONS = 80

# ---- Mô hình ngôn ngữ điều phối agent ----
# LLM_PROVIDER: "openai" (mặc định), "ollama" (mô hình cục bộ) hoặc "none" (chỉ dùng regex và lời giải thích theo mẫu).
# Khóa API đọc từ biến môi trường OPENAI_API_KEY, không ghi vào mã hay đưa lên Git.
import os as _os
LLM_PROVIDER = _os.environ.get("LLM_PROVIDER", "openai").lower()
OPENAI_URL = _os.environ.get("OPENAI_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_MODEL = _os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")   # kiểm tra mã mô hình chính xác trên trang OpenAI
OPENAI_TIMEOUT_S = 60.0
AGENT_MAX_TURNS = 8
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3:4b"      # chỉ dùng khi LLM_PROVIDER = "ollama"
