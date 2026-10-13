"""Cấu hình chung của OptiMat AI. Sửa ở đây thay vì sửa rải rác trong mã."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
CATALOG_DIR = DATA_DIR / "catalog"
MODELS_DIR = ROOT / "models"

# ---- Nhận diện bản vẽ ----
# Quy tắc gán vai trò cho layer nằm trong drawing/layer_classifier.py.
OPENING_BLOCK_PREFIXES = ("D", "S", "W", "CD", "CS")

# Lớp chiều dày tường (mm): tên lớp -> (nhỏ nhất, lớn nhất) của khoảng cách hai nét song song.
# Dải đủ rộng để nhận cả tường 100 (lớp 110), 200 (lớp 220), 300 (lớp 330) gặp trên bản vẽ thật.
WALL_THICKNESS_CLASSES = {"110": (85, 135), "150": (136, 175), "220": (176, 260), "330": (280, 370)}
MIN_WALL_OVERLAP_MM = 300.0
PARALLEL_ANGLE_TOL_DEG = 1.0
WALL_LAYER_MIN_SCORE_MM = 2000.0   # tổng chiều dài cặp nét tối thiểu để tự nhận một layer là layer tường
WALL_LAYER_REL_SCORE = 0.6         # và không dưới tỷ lệ này so với layer điểm cao nhất
MAX_OPENING_GAP_MM = 3600.0        # khe giữa hai đoạn tường thẳng hàng có cửa thì được nối lại
DOOR_ARC_RADIUS_MM = (450.0, 1300.0)

# Kích thước lỗ mở mặc định (rộng, cao) theo tiền tố tên block, dùng khi block không có thuộc tính.
DEFAULT_OPENINGS_MM = {"D": (900, 2200), "CD": (900, 2200), "S": (1200, 1400), "CS": (1200, 1400), "W": (1200, 1400)}
DEFAULT_FLOOR_HEIGHT_MM = 3300.0

# ---- Chi phí và tối ưu ----
WASTE_FACTOR = 1.05            # hao hụt vật liệu
LABOR_RATE_PER_DAY = 350_000   # đồng/công, SỐ MẪU: thay bằng đơn giá nhân công của tỉnh
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
