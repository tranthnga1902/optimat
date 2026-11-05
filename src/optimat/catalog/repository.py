"""Nạp danh mục vật liệu, nhà cung cấp, phương tiện.

Nguồn dữ liệu: PostgreSQL khi có biến môi trường DATABASE_URL, ngược lại đọc các file CSV
trong data/catalog (dùng cho kiểm thử và khi chưa dựng cơ sở dữ liệu). Biến OPTIMAT_CATALOG_OVERLAY trỏ tới một
thư mục CSV đè lên các dòng cùng khóa (kiểm thử dùng data/sample/catalog: số MẪU cho phương án còn thiếu số liệu).
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .. import config
from ..db.session import get_database_url, get_engine


# Thông số phương án tường cần có để đưa vào tối ưu, kèm tên tiếng Việt để báo còn thiếu
READY_FIELDS = {"qty_per_m2": "số lượng vật liệu / m² tường", "labor_day_per_m2": "công / m² tường",
                "weight_kg_per_m2": "khối lượng tường kg/m²", "lambda_w_mk": "hệ số dẫn nhiệt λ",
                "masonry_thickness_mm": "chiều dày khối xây"}
CSV_TABLES = {"material_groups": "group_id", "material_families": "family_id", "materials": "material_id", "wall_systems": "wall_system_id",
              "material_aliases": None, "material_relations": None, "suppliers": "supplier_id", "supplier_materials": None,
              "vehicles": "vehicle_id", "labor_rates": None}


@dataclass
class WallResolution:
    """Kết quả quy đổi họ vật liệu (hoặc mã vật liệu) đọc từ bản vẽ + lớp chiều dày tường sang mã của danh mục."""
    material_id: str | None = None
    wall_system_id: str | None = None
    family: str | None = None
    candidates: list[str] = field(default_factory=list)   # các phương án còn phải chọn khi chưa xác định được một
    note: str | None = None


def _empty(cols: list[str]) -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype=object) for c in cols})


@dataclass
class Catalog:
    materials: pd.DataFrame
    suppliers: pd.DataFrame
    supplier_materials: pd.DataFrame
    vehicles: pd.DataFrame
    wall_systems: pd.DataFrame = field(default_factory=lambda: _empty(["wall_system_id", "material_id", "detect_class"]))
    aliases: pd.DataFrame = field(default_factory=lambda: _empty(["alias", "material_id"]))
    # quan hệ vật liệu: REQUIRES (vật liệu đi kèm) và COMPOSED_OF (cấp phối: vữa -> xi măng, cát)
    relations: pd.DataFrame = field(default_factory=lambda: _empty(
        ["material_id", "relation_type", "related_material_id", "quantity", "quantity_unit", "source", "note"]))
    families: pd.DataFrame = field(default_factory=lambda: _empty(["family_id", "name", "sort_order", "is_wall"]))
    labor_rates: pd.DataFrame = field(default_factory=lambda: _empty(["province", "grade", "rate_per_day", "valid_from"]))
    # 5 nhóm vật liệu của đề cương (material_groups): gộp bảng vật liệu phần thô theo nhóm cho bộ tối ưu
    material_groups: pd.DataFrame = field(default_factory=lambda: _empty(["group_id", "sort_order", "name", "description"]))
    price_records: pd.DataFrame | None = None       # chỉ nạp khi tra giá (bảng lớn)

    @classmethod
    def load(cls, folder: Path | str | None = None) -> "Catalog":
        """Không truyền folder: dùng PostgreSQL nếu đã cấu hình, ngược lại dùng CSV mặc định."""
        if folder is None and get_database_url():
            return cls.from_db()
        return cls.from_csv(folder or os.environ.get("OPTIMAT_CATALOG_OVERLAY") or None)

    @classmethod
    def from_db(cls, url: str | None = None) -> "Catalog":
        with get_engine(url).connect() as conn:
            def table(name: str) -> pd.DataFrame:
                return pd.read_sql_query(f'SELECT * FROM "{name}"', conn)
            return cls(materials=table("materials"), suppliers=table("suppliers"),
                       supplier_materials=table("supplier_materials").drop(columns=["id"]),
                       vehicles=table("vehicles"), wall_systems=table("wall_systems"),
                       aliases=table("material_aliases").drop(columns=["id"]),
                       relations=table("material_relations").drop(columns=["id"], errors="ignore"),
                       families=table("material_families"), labor_rates=table("labor_rates").drop(columns=["id"]),
                       material_groups=table("material_groups"))

    @classmethod
    def from_csv(cls, folder: Path | str | None = None) -> "Catalog":
        """Đọc data/catalog. folder khác: file nào có trong folder thì đè lên dòng cùng khóa của data/catalog
        (dùng cho bộ số liệu mẫu của kiểm thử, data/sample/catalog)."""
        base, extra = Path(config.CATALOG_DIR), Path(folder) if folder else None
        tables = {}
        for name, key in CSV_TABLES.items():
            df = pd.read_csv(base / f"{name}.csv") if (base / f"{name}.csv").exists() else _empty([key or "material_id"])
            if extra is not None and extra.resolve() != base.resolve() and (extra / f"{name}.csv").exists():
                over = pd.read_csv(extra / f"{name}.csv")
                df = pd.concat([df, over], ignore_index=True)
                if key:
                    df = df.drop_duplicates(key, keep="last").reset_index(drop=True)
            tables[name] = df
        return cls(materials=tables["materials"], suppliers=tables["suppliers"],
                   supplier_materials=tables["supplier_materials"], vehicles=tables["vehicles"],
                   wall_systems=tables["wall_systems"], aliases=tables["material_aliases"],
                   relations=tables["material_relations"], families=tables["material_families"],
                   labor_rates=tables["labor_rates"], material_groups=tables["material_groups"])

    # ------------------------------------------------------------------ họ vật liệu, nhân công
    def wall_families(self) -> dict[str, str]:
        """Họ vật liệu xây tường (bảng material_families, is_wall) -> tên hiển thị, theo sort_order."""
        f = self.families
        f = f[f.is_wall.astype(str).str.lower().isin(["true", "1"])].sort_values("sort_order")
        return dict(zip(f.family_id, f.name))

    def labor_rate(self, province: str | None = None, on: str | None = None) -> tuple[float | None, str]:
        """Đơn giá nhân công đồng/công từ bảng labor_rates: tỉnh đã chọn (không chọn thì phải chỉ có một tỉnh),
        bản công bố mới nhất có hiệu lực tới ngày on. Không xác định được một số thì trả None kèm lý do."""
        r = self.labor_rates.dropna(subset=["rate_per_day"])
        if province:
            r = r[r.province == province]
        if on:
            r = r[pd.to_datetime(r.valid_from, errors="coerce").fillna(pd.Timestamp.min) <= pd.Timestamp(on)]
        if r.empty:
            return None, "Chưa có đơn giá nhân công" + (f" của {province}" if province else "") + " trong bảng labor_rates."
        if r.province.nunique() > 1:
            return None, "Bảng labor_rates có nhiều tỉnh (" + ", ".join(sorted(r.province.unique())) + "), cần chọn tỉnh."
        latest = r[pd.to_datetime(r.valid_from, errors="coerce") == pd.to_datetime(r.valid_from, errors="coerce").max()]
        latest = latest if len(latest) else r
        if latest.rate_per_day.nunique() > 1:
            return None, "Bảng labor_rates có nhiều bậc thợ cùng ngày hiệu lực, chưa chọn được một đơn giá."
        row = latest.iloc[0]
        kind = f", {row.data_kind}" if "data_kind" in row and row.data_kind != "ACTUAL" else ""
        return float(row.rate_per_day), f"Đơn giá nhân công {row.rate_per_day:,.0f} đồng/công ({row.province}, bậc {row.grade}{kind})."

    # ------------------------------------------------------------------ phương án tường
    def wall_view(self) -> pd.DataFrame:
        """Phương án tường kèm định mức theo 1 m2 tường, cùng công thức với view v_wall_systems trong SQL.
        Cột missing liệt kê thông số còn trống; ready = đủ để tối ưu. Không điền số thiếu."""
        ws = self.wall_systems.copy()
        if ws.empty:
            return ws.assign(family=None, ready=False, missing=None)
        ws["detect_class"] = ws.detect_class.map(lambda v: None if pd.isna(v) else str(int(float(v))))
        cols = ["material_id", "name", "family", "unit", "lambda_w_mk", "unit_weight_kg", "waste_pct", "data_kind"]
        mats = self.materials[[c for c in cols if c in self.materials.columns]].rename(
            columns={"name": "material_name", "data_kind": "material_data_kind"})
        ws = ws.merge(mats, on="material_id", how="left")
        num = lambda c: pd.to_numeric(ws.get(c), errors="coerce")      # noqa: E731
        t = num("masonry_thickness_mm") / 1000
        ws["qty_per_m2"] = num("units_per_m3") * t * num("unit_factor")
        ws["mortar_m3_per_m2"] = num("mortar_m3_per_m3") * t
        ws["labor_day_per_m2"] = num("labor_day_per_m3") * t
        ws["weight_kg_per_m2"] = ws.qty_per_m2 * num("unit_weight_kg") + ws.mortar_m3_per_m2 * num("mortar_density")
        ws["missing"] = [[label for col, label in READY_FIELDS.items() if pd.isna(row[col])] for _, row in ws.iterrows()]
        ws["ready"] = ws.missing.map(lambda m: not m) & ws.detect_class.notna()
        kinds = ws[["data_kind", "material_data_kind"]].astype(str)
        ws["data_kind"] = ["SAMPLE" if "SAMPLE" in (a, b) else a for a, b in zip(kinds.data_kind, kinds.material_data_kind)]
        return ws

    def systems_for_wall(self, wall_type: str, excluded: list[str] | None = None) -> pd.DataFrame:
        """Phương án tường thuộc lớp nhận diện wall_type. excluded: họ vật liệu hoặc mã vật liệu bị loại."""
        ws = self.wall_view()
        ws = ws[ws.detect_class == wall_type]
        if excluded:
            ex = set(excluded)
            ws = ws[~ws.family.isin(ex) & ~ws.material_id.isin(ex)]
        return ws.reset_index(drop=True)

    def family_materials(self, family: str) -> list[str]:
        return sorted(self.materials[self.materials.get("family") == family].material_id)

    def material_name(self, material_id: str) -> str | None:
        row = self.materials[self.materials.material_id == material_id]
        return None if row.empty else str(row.name.iloc[0])

    def resolve_wall(self, targets: list[str], wall_type: str) -> WallResolution:
        """targets: họ vật liệu (AAC) hoặc mã vật liệu (GN01) mà quy tắc bóc tách trả về.
        Chỉ chọn khi danh mục có đúng một phương án tường cùng lớp; nhiều phương án thì trả danh sách để người dùng chọn."""
        fam = self.materials.set_index("material_id").get("family", pd.Series(dtype=object))
        mats: set[str] = set()
        for t in targets:
            mats |= {t} if t in fam.index else set(self.family_materials(t))
        families = sorted({fam.get(m) for m in mats if isinstance(fam.get(m), str)})
        family = "|".join(families) or None
        if not mats:
            return WallResolution(family=family, note=f"Danh mục chưa có vật liệu thuộc {', '.join(targets)}.")
        ws = self.wall_systems.assign(detect_class=self.wall_systems.detect_class.map(
            lambda v: None if pd.isna(v) else str(int(float(v)))))
        hit = ws[ws.material_id.isin(mats) & (ws.detect_class == wall_type)].sort_values("wall_system_id")
        if hit.material_id.nunique() == 1:
            ids = hit.wall_system_id.tolist()
            return WallResolution(hit.material_id.iloc[0], ids[0] if len(ids) == 1 else None, family,
                                  ids if len(ids) > 1 else [])
        if len(hit) > 1:
            return WallResolution(family=family, candidates=hit.wall_system_id.tolist(),
                                  note=f"Tường {wall_type}: {family} có {len(hit)} phương án, cần chọn trên trang kiểm tra.")
        if len(mats) == 1:
            m = next(iter(mats))
            return WallResolution(m, None, family, note=f"Danh mục chưa có phương án tường {m} cho lớp {wall_type}.")
        return WallResolution(family=family, note=f"Danh mục chưa có phương án tường {family} cho lớp {wall_type}.")

    # ------------------------------------------------------------------ nguồn cung
    def offers(self, material_ids: list[str]) -> pd.DataFrame:
        """Các cặp (vật liệu, nhà cung cấp) trong danh mục, kèm thông tin nhà cung cấp (giá có thể trống)."""
        sm = self.supplier_materials[self.supplier_materials.material_id.isin(material_ids)]
        out = sm.merge(self.suppliers, on="supplier_id", suffixes=("", "_sup"))
        if "lead_time_days_sup" in out:  # báo giá không ghi thời gian cung ứng: dùng của đại lý
            out["lead_time_days"] = out.lead_time_days.astype(float).fillna(out.lead_time_days_sup.astype(float))
        return out

    def vehicles_up_to(self, max_ton: float | None) -> pd.DataFrame:
        if max_ton is None:
            return self.vehicles
        return self.vehicles[self.vehicles.payload_ton <= max_ton + 1e-9]


@lru_cache(maxsize=1)
def default_catalog() -> Catalog:
    """Danh mục dùng chung khi bóc tách (đọc một lần cho mỗi tiến trình)."""
    return Catalog.load()


def road_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Ước lượng cự ly đường bộ = đường chim bay x hệ số. Thay bằng OSRM khi tích hợp bản đồ."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a)) * config.ROAD_FACTOR
