"""Từ khối lượng tường đã chốt ra bảng vật liệu cần mua và giá đang có trong danh mục.

Mỗi nhóm tường đã có phương án tường (wall_systems) thì có hai dòng vật liệu:
    vật liệu chính (gạch, khối)  = diện tích thực x số lượng / m2 tường của phương án
    vữa xây (mortar_material_id)  = diện tích thực x m3 vữa / m2 tường
Hao hụt lấy theo cột waste_pct của vật liệu; trống thì không cộng và báo thiếu. Giá lấy nguyên từ supplier_materials
(giá đại lý, báo giá, công bố giá) và, khi có PostgreSQL, dòng mới nhất của price_records. Không có giá thì để trống:
dự đoán giá là việc của mô hình XGBoost ở bước tối ưu, không phải ở bảng này.
"""
from __future__ import annotations

import math
import unicodedata
from datetime import date
from typing import Optional
from urllib.parse import urlsplit

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
    valid_until: Optional[str] = None
    vat_included: Optional[str] = None
    transport_included: Optional[str] = None
    data_kind: Optional[str] = None
    url: str = ""
    source: str = "supplier_materials"         # supplier_materials | price_records
    source_detail: Optional[str] = None
    supplier_data_kind: Optional[str] = None
    unit_source: Optional[str] = None
    raw_price: Optional[str] = None
    eligible: bool = False
    rejection_reasons: list[str] = Field(default_factory=list)
    is_reference: bool = False


class BillLine(BaseModel):
    wall_type: str
    role: str
    net_area_m2: float
    wall_system_id: Optional[str] = None
    kind: str = "main"                         # main (vật liệu chính) | mortar (vữa xây)
    is_intermediate: bool = False
    material_id: Optional[str] = None
    material_name: Optional[str] = None
    unit: Optional[str] = None
    qty_per_m2: Optional[float] = None
    waste_pct: Optional[float] = None
    waste_included: bool = False
    quantity: Optional[float] = None
    offers: list[PriceOffer] = Field(default_factory=list)
    best_price: Optional[float] = None
    best_offer: Optional[PriceOffer] = None
    price_note: Optional[str] = None
    est_cost: Optional[float] = None           # khối lượng x giá thấp nhất đang có (chưa gồm vận chuyển, nhân công)
    missing: list[str] = Field(default_factory=list)


def _text(v) -> Optional[str]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return v.isoformat()[:10] if isinstance(v, date) else str(v)


def _num(v) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def normalize_unit(unit) -> str:
    """Chỉ chuẩn hóa cách viết cùng đơn vị; không đổi bao/kiện/kg/tấn hoặc suy số lượng."""
    if not isinstance(unit, str):
        return ""
    return " ".join(unicodedata.normalize("NFKC", unit).casefold().split())


def has_price_source(source_detail=None, price_url=None) -> bool:
    """Chứng từ hoặc trang giá cụ thể; link bản đồ không chứng minh đơn giá."""
    for value, document in ((source_detail, True), (price_url, False)):
        if not isinstance(value, str):
            continue
        text = value.strip()
        if not text or text.casefold() in {"actual", "sample", "synthetic", "n/a", "na", "unknown", "chưa rõ", "không rõ", "nan", "none", "null", "supplier_materials", "price_records"}:
            continue
        if text.casefold().startswith(("http://", "https://")):
            try:
                parsed = urlsplit(text)
                host, path = (parsed.hostname or "").casefold(), parsed.path.casefold()
                parsed.port  # Kiểm cổng sai định dạng trước khi nhận URL làm nguồn.
            except ValueError:
                continue
            maps = (host.startswith("maps.") or "openstreetmap.org" in host or "waze.com" in host
                    or ("google." in host and path.startswith("/maps")) or (host == "goo.gl" and path.startswith("/maps"))
                    or ("bing.com" in host and path.startswith("/maps")))
            if host and not any(c.isspace() for c in host) and not maps:
                return True
        elif document and "://" not in text and not text.casefold().startswith(("google maps", "bản đồ", "maps:")):
            return True
    return False


def select_best_offer(offers, unit, material_data_kind, actual_only, as_of=None) -> tuple[Optional[PriceOffer], list[PriceOffer]]:
    """Trả giá được chọn và bản sao mọi giá kèm lý do; không sửa nguồn hoặc quy đổi đơn vị.

    Giá công bố chỉ tham khảo. Chế độ thật ưu tiên DEALER/QUOTE có nhà cung cấp ACTUAL.
    """
    on = date.fromisoformat(as_of) if isinstance(as_of, str) else (as_of or date.today())
    checked = [o.model_copy(deep=True) if isinstance(o, PriceOffer) else PriceOffer.model_validate(o if isinstance(o, dict) else vars(o)) for o in offers]
    for offer in checked:
        reasons = []
        if offer.price is None or not math.isfinite(offer.price) or offer.price <= 0:
            reasons.append("Giá chưa có hoặc không phải số dương hữu hạn")
        if not normalize_unit(offer.unit):
            reasons.append("Chưa rõ đơn vị báo giá; không suy từ đơn vị danh mục")
        elif normalize_unit(offer.unit) != normalize_unit(unit):
            reasons.append(f"Đơn vị báo giá {offer.unit} khác {unit}; chưa có căn cứ quy đổi")
        if offer.price_level not in {"DEALER", "QUOTE", "BULLETIN"}:
            reasons.append("Chưa rõ mức giá")
        try:
            price_date = date.fromisoformat(offer.price_date or "")
        except ValueError:
            price_date = None
        if price_date and price_date > on:
            reasons.append("Ngày giá nằm trong tương lai so với ngày tính")
        if offer.valid_until:
            try:
                expires = date.fromisoformat(offer.valid_until)
            except ValueError:
                reasons.append("Ngày hết hiệu lực báo giá không hợp lệ")
            else:
                if expires < on:
                    reasons.append("Báo giá đã hết hiệu lực tại ngày tính")
                if price_date and expires < price_date:
                    reasons.append("Ngày hết hiệu lực đứng trước ngày giá")
        if actual_only:
            if material_data_kind != "ACTUAL":
                reasons.append("Vật liệu danh mục không phải ACTUAL")
            if offer.data_kind != "ACTUAL":
                reasons.append("Giá không phải ACTUAL")
            if offer.price_level in {"DEALER", "QUOTE"} and not offer.supplier_id:
                reasons.append("Giá mua chưa có mã nhà cung cấp")
            if offer.price_level in {"DEALER", "QUOTE"}:
                if offer.source == "price_records":
                    reasons.append("Giá đại lý ghi nhận trong lịch sử, cần báo giá mua hiện hành")
                if offer.vat_included not in {"YES", "NO"}:
                    reasons.append("Chưa rõ đơn giá đã gồm VAT hay chưa")
                if offer.transport_included not in {"YES", "NO"}:
                    reasons.append("Chưa rõ đơn giá đã gồm giao hàng hay chưa")
            if offer.supplier_id and offer.supplier_data_kind != "ACTUAL":
                reasons.append("Nhà cung cấp chưa xác định là ACTUAL")
            if price_date is None:
                reasons.append("Chưa có ngày giá hợp lệ")
            if not has_price_source(offer.source_detail, offer.url):
                reasons.append("Chưa có chứng từ hoặc trang nguồn của bản giá; liên kết bản đồ không chứng minh giá")
        offer.rejection_reasons = reasons
        offer.eligible = not reasons
        offer.is_reference = offer.price_level == "BULLETIN"
    compatible = [o for o in checked if o.eligible]
    if actual_only:
        commercial = [o for o in compatible if not o.is_reference]
        compatible = commercial or compatible
        # Không tự chọn cơ sở thuế hoặc cước. Một công bố đơn lẻ vẫn xem được để tham khảo.
        terms = {(o.vat_included, o.transport_included) for o in compatible}
        known_terms = all(v in {"YES", "NO"} for pair in terms for v in pair)
        if len(compatible) > 1 and (len(terms) != 1 or not known_terms):
            for o in compatible:
                o.eligible = False
                o.rejection_reasons.append("Cần cùng điều kiện VAT và giao hàng trước khi so đơn giá")
            return None, checked
    return (min(compatible, key=lambda o: o.price) if compatible else None), checked


def price_offers(catalog: Catalog, material_ids: list[str]) -> dict[str, list[PriceOffer]]:
    """Giá đang có của từng vật liệu, giá thấp nhất trước; dòng chưa có giá (đại lý không công khai) để cuối."""
    out: dict[str, list[PriceOffer]] = {m: [] for m in material_ids}
    offers = catalog.offers(material_ids)
    for o in offers.to_dict("records"):
        url = next((str(o[k]) for k in ("product_url", "price_page_url") if has_price_source(price_url=o.get(k))),
                   next((str(o[k]) for k in ("product_url", "price_page_url", "maps_url")
                         if isinstance(o.get(k), str) and o[k].strip()), ""))
        out[o["material_id"]].append(PriceOffer(
            supplier_id=o["supplier_id"], supplier_name=o.get("name"), price=_num(o.get("base_price")),
            unit=_text(o.get("sale_unit")), unit_source="sale_unit" if normalize_unit(o.get("sale_unit")) else None,
            price_level=_text(o.get("price_level")), price_date=_text(o.get("price_date")),
            valid_until=_text(o.get("valid_until")),
            vat_included=_text(o.get("vat_included")), transport_included=_text(o.get("transport_included")),
            data_kind=_text(o.get("data_kind")), supplier_data_kind=_text(o.get("data_kind_sup")),
            source_detail=next((_text(o.get(k)) for k in ("price_source_detail", "source_detail", "quote_reference", "certificate_reference")
                                if has_price_source(o.get(k))), None), raw_price=str(o.get("base_price")), url=url))
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
        WITH dated AS (
            SELECT p.*, DENSE_RANK() OVER (
                PARTITION BY p.material_id, p.supplier_id, p.price_level, p.unit, p.source
                ORDER BY p.date DESC) AS recency
            FROM price_records p WHERE p.material_id IN :ids AND p.data_kind = 'ACTUAL'
        )
        SELECT p.material_id, p.supplier_id, s.name AS supplier_name, p.unit_price, p.unit, p.price_level, p.date,
               p.data_kind, p.source, p.vat_included, p.transport_included, s.data_kind AS supplier_data_kind
        FROM dated p LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id
        WHERE p.recency = 1 ORDER BY p.id""").bindparams(
        bindparam("ids", expanding=True))
    out: dict[str, list[PriceOffer]] = {}
    with get_engine().connect() as conn:
        for r in conn.execute(sql, {"ids": list(material_ids)}).mappings():
            out.setdefault(r["material_id"], []).append(PriceOffer(
                supplier_id=r["supplier_id"], supplier_name=r["supplier_name"], price=_num(r["unit_price"]),
                unit=r["unit"], price_level=r["price_level"], price_date=str(r["date"]), data_kind=r["data_kind"],
                vat_included=r["vat_included"], transport_included=r["transport_included"],
                url=r["source"] if str(r["source"]).startswith("http") else "", source="price_records",
                source_detail=r["source"], supplier_data_kind=r["supplier_data_kind"], unit_source="price_records.unit",
                raw_price=str(r["unit_price"])))
    return out


def _line(group: WallGroup, system_id: Optional[str], kind: str, material_id: Optional[str], qty_per_m2,
          catalog: Catalog, prices: dict[str, list[PriceOffer]], missing: list[str], actual_only: bool = False,
          waste_included: bool = False) -> BillLine:
    mats = catalog.materials.set_index("material_id")
    line = BillLine(wall_type=group.wall_type, role=group.role, net_area_m2=group.net_area_m2,
                    wall_system_id=system_id, kind=kind, material_id=material_id, missing=list(missing),
                    waste_included=waste_included)
    if material_id is None or material_id not in mats.index:
        return line
    m = mats.loc[material_id]
    line.material_name, line.unit = str(m["name"]), str(m["unit"])
    line.qty_per_m2 = _num(qty_per_m2)
    line.waste_pct = _num(m.get("waste_pct"))
    if line.waste_pct is None and not waste_included:
        line.missing.append("hao hụt thi công (%)")
    elif line.waste_pct is not None and line.waste_pct < 0 and not waste_included:
        line.missing.append("hao hụt thi công (%) không được âm")
    if line.qty_per_m2 is not None:
        waste = 0 if waste_included else (line.waste_pct or 0)
        line.quantity = round(group.net_area_m2 * line.qty_per_m2 * (1 + waste / 100), 3)
    line.best_offer, line.offers = select_best_offer(prices.get(material_id, []), line.unit, m.get("data_kind"), actual_only)
    line.best_price = line.best_offer.price if line.best_offer else None
    if line.best_offer and line.best_offer.is_reference:
        line.price_note = "Giá công bố tham khảo theo ngày nguồn; không phải báo giá mua/giao hàng hiện hành"
    if line.best_price is None:
        line.missing.append("giá")
    elif line.quantity is not None and not line.missing:
        line.est_cost = round(line.quantity * line.best_price)
    parts = catalog.relations
    if kind == "mortar" and not parts.empty and ((parts.material_id == material_id) & (parts.relation_type == "COMPOSED_OF")).any():
        line.is_intermediate = True
        line.best_offer = None
        line.best_price = None
        line.est_cost = None
        line.price_note = "Vữa trộn tại chỗ là lượng trung gian; xem xi măng, cát theo cấp phối trong bảng phần thô"
        line.missing.append("chi phí thành phần vữa theo cấp phối (xem bảng phần thô)")
        for offer in line.offers:
            offer.eligible = False
            offer.rejection_reasons.append("Không dùng đơn giá vữa thành phẩm cho vữa trộn tại chỗ có cấp phối")
    return line


def bill_of_materials(groups: list[WallGroup], catalog: Catalog, actual_only: bool = False) -> list[BillLine]:
    """Giá cùng đơn vị; actual_only ưu tiên giá mua ACTUAL, công bố chỉ làm tham khảo.

    Đơn vị bán thiếu không được suy từ danh mục. Định mức AE đã gồm hao hụt cho gạch và vữa.
    """
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
        base_mortar = w.get("mortar_material_id")
        mortar = getattr(g, "design_mortar_material_id", None) or base_mortar
        if isinstance(mortar, str) and mortar:
            per_m2, miss = w.mortar_m3_per_m2, [] if pd.notna(w.mortar_m3_per_m2) else ["m³ vữa / m² tường (định mức)"]
            unit = str(mats.loc[mortar, "unit"]) if mortar in mats.index else ""
            if normalize_unit(unit) == "tấn" and pd.notna(per_m2):
                density = _num(w.get("mortar_density")) if mortar == base_mortar else None
                per_m2 = per_m2 * density / 1000 if density and density > 0 else None
                if density is None or density <= 0:
                    miss.append("khối lượng thể tích vữa (đổi m³ sang tấn)")
            elif normalize_unit(unit) != "m3":
                per_m2 = None
                miss.append(f"cách đổi m³ vữa sang {unit or 'đơn vị chưa rõ'}")
            plans.append((g, sys_id, "mortar", mortar, per_m2, miss))
        else:
            plans.append((g, sys_id, "mortar", None, None, ["vữa của phương án tường (chưa chọn mã vật liệu)"]))
    prices = price_offers(catalog, sorted({p[3] for p in plans if p[3]}))
    return [_line(g, s, k, m, q, catalog, prices, miss, actual_only,
                  bool(s and str(view.loc[s].get("norm_code", "")).startswith("AE")))
            for g, s, k, m, q, miss in plans]
