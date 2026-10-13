"""Từ khối lượng tường đã chốt ra bảng vật liệu cần mua và giá đang có trong danh mục.

Mỗi nhóm tường đã có phương án tường (wall_systems) thì có hai dòng vật liệu:
    vật liệu chính (gạch, khối)  = diện tích thực x số lượng / m2 tường của phương án
    vữa xây (mortar_material_id)  = diện tích thực x m3 vữa / m2 tường
Hao hụt lấy theo cột waste_pct của vật liệu; trống thì không cộng và báo thiếu. Giá lấy nguyên từ supplier_materials
(giá đại lý, báo giá, công bố giá) và, khi có PostgreSQL, dòng mới nhất của price_records. Không có giá thì để trống:
dự đoán giá là việc của mô hình XGBoost ở bước tối ưu, không phải ở bảng này.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field

from ..db.session import get_database_url, get_engine
from ..schemas import WallGroup
from .repository import Catalog


class PriceOffer(BaseModel):
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    price: Optional[float] = None
    unit: Optional[str] = None
    price_level: Optional[str] = None          # DEALER | QUOTE | BULLETIN
    price_date: Optional[str] = None
    data_kind: Optional[str] = None
    url: str = ""
    source: str = "supplier_materials"         # supplier_materials | price_records


class BillLine(BaseModel):
    wall_type: str
    role: str
    net_area_m2: float
    wall_system_id: Optional[str] = None
    kind: str = "main"                         # main (vật liệu chính) | mortar (vữa xây)
    material_id: Optional[str] = None
    material_name: Optional[str] = None
    unit: Optional[str] = None
    qty_per_m2: Optional[float] = None
    waste_pct: Optional[float] = None
    quantity: Optional[float] = None
    offers: list[PriceOffer] = Field(default_factory=list)
    best_price: Optional[float] = None
    est_cost: Optional[float] = None           # khối lượng x giá thấp nhất đang có (chưa gồm vận chuyển, nhân công)
    missing: list[str] = Field(default_factory=list)


def _text(v) -> Optional[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return str(v)[:10] if hasattr(v, "isoformat") or str(v)[:4].isdigit() else str(v)


def _num(v) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(f) else f


def price_offers(catalog: Catalog, material_ids: list[str]) -> dict[str, list[PriceOffer]]:
    """Giá đang có của từng vật liệu, giá thấp nhất trước; dòng chưa có giá (đại lý không công khai) để cuối."""
    out: dict[str, list[PriceOffer]] = {m: [] for m in material_ids}
    offers = catalog.offers(material_ids)
    units = catalog.materials.set_index("material_id").unit if not catalog.materials.empty else pd.Series(dtype=object)
    for o in offers.to_dict("records"):
        url = next((str(o[k]) for k in ("product_url", "price_page_url", "maps_url")
                    if isinstance(o.get(k), str) and o[k].strip()), "")
        out[o["material_id"]].append(PriceOffer(
            supplier_id=o["supplier_id"], supplier_name=o.get("name"), price=_num(o.get("base_price")),
            unit=o.get("sale_unit") if isinstance(o.get("sale_unit"), str) else units.get(o["material_id"]),
            price_level=_text(o.get("price_level")), price_date=_text(o.get("price_date")),
            data_kind=_text(o.get("data_kind")), url=url))
    for mid, rows in _latest_price_records(material_ids).items():
        out[mid].extend(rows)
    for mid in out:
        out[mid].sort(key=lambda p: (p.price is None, p.price or 0))
    return out


def _latest_price_records(material_ids: list[str]) -> dict[str, list[PriceOffer]]:
    """Dòng giá mới nhất cho mỗi cặp (vật liệu, nguồn) trong price_records. Chỉ khi có PostgreSQL."""
    if not material_ids or not get_database_url():
        return {}
    from sqlalchemy import bindparam, text
    sql = text("""
        SELECT DISTINCT ON (p.material_id, COALESCE(p.supplier_id, ''), p.price_level)
               p.material_id, p.supplier_id, s.name AS supplier_name, p.unit_price, p.unit, p.price_level, p.date,
               p.data_kind, p.source
        FROM price_records p LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id
        WHERE p.material_id IN :ids AND p.data_kind = 'ACTUAL'
        ORDER BY p.material_id, COALESCE(p.supplier_id, ''), p.price_level, p.date DESC""").bindparams(
        bindparam("ids", expanding=True))
    out: dict[str, list[PriceOffer]] = {}
    with get_engine().connect() as conn:
        for r in conn.execute(sql, {"ids": list(material_ids)}).mappings():
            out.setdefault(r["material_id"], []).append(PriceOffer(
                supplier_id=r["supplier_id"], supplier_name=r["supplier_name"], price=_num(r["unit_price"]),
                unit=r["unit"], price_level=r["price_level"], price_date=str(r["date"]), data_kind=r["data_kind"],
                url=r["source"] if str(r["source"]).startswith("http") else "", source="price_records"))
    return out


def _line(group: WallGroup, system_id: Optional[str], kind: str, material_id: Optional[str], qty_per_m2,
          catalog: Catalog, prices: dict[str, list[PriceOffer]], missing: list[str]) -> BillLine:
    mats = catalog.materials.set_index("material_id")
    line = BillLine(wall_type=group.wall_type, role=group.role, net_area_m2=group.net_area_m2,
                    wall_system_id=system_id, kind=kind, material_id=material_id, missing=list(missing))
    if material_id is None or material_id not in mats.index:
        return line
    m = mats.loc[material_id]
    line.material_name, line.unit = str(m["name"]), str(m["unit"])
    line.qty_per_m2 = _num(qty_per_m2)
    line.waste_pct = _num(m.get("waste_pct"))
    if line.waste_pct is None:
        line.missing.append("hao hụt thi công (%)")
    if line.qty_per_m2 is not None:
        line.quantity = round(group.net_area_m2 * line.qty_per_m2 * (1 + (line.waste_pct or 0) / 100), 3)
    line.offers = prices.get(material_id, [])
    priced = [p.price for p in line.offers if p.price is not None]
    line.best_price = min(priced) if priced else None
    if line.best_price is None:
        line.missing.append("giá")
    elif line.quantity is not None:
        line.est_cost = round(line.quantity * line.best_price)
    return line


def bill_of_materials(groups: list[WallGroup], catalog: Catalog) -> list[BillLine]:
    """Một dòng vật liệu chính và một dòng vữa cho mỗi nhóm tường đã có phương án tường."""
    view = catalog.wall_view().set_index("wall_system_id") if not catalog.wall_systems.empty else pd.DataFrame()
    mats = catalog.materials.set_index("material_id")
    plans = []
    for g in groups:
        sys_id = g.design_wall_system_id
        if sys_id is None or sys_id not in view.index:
            plans.append((g, None, "main", g.design_material_id if g.design_material_id in mats.index else None, None,
                          ["phương án tường (chọn vật liệu cho nhóm tường)"]))
            continue
        w = view.loc[sys_id]
        plans.append((g, sys_id, "main", w.material_id, w.qty_per_m2,
                      [] if pd.notna(w.qty_per_m2) else ["số lượng / m² tường (định mức)"]))
        mortar = w.get("mortar_material_id")
        if isinstance(mortar, str) and mortar:
            per_m2, miss = w.mortar_m3_per_m2, [] if pd.notna(w.mortar_m3_per_m2) else ["m³ vữa / m² tường (định mức)"]
            unit = str(mats.loc[mortar, "unit"]) if mortar in mats.index else ""
            if unit == "tấn" and pd.notna(per_m2):
                density = _num(w.get("mortar_density"))
                per_m2 = per_m2 * density / 1000 if density else None
                if density is None:
                    miss.append("khối lượng thể tích vữa (đổi m³ sang tấn)")
            plans.append((g, sys_id, "mortar", mortar, per_m2, miss))
    prices = price_offers(catalog, sorted({p[3] for p in plans if p[3]}))
    return [_line(g, s, k, m, q, catalog, prices, miss) for g, s, k, m, q, miss in plans]
