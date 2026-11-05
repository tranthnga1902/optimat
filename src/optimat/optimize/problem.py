"""Bài toán tối ưu đa mục tiêu cho phần tường.

Biến quyết định, cho mỗi nhóm tường: (phương án tường + nhà cung cấp, loại xe).
Phương án tường lấy từ bảng wall_systems theo lớp nhận diện bản vẽ (detect_class), cùng mã vật liệu với bước
bóc tách và tra giá. Phương án còn trống định mức, khối lượng hoặc λ thì không đưa vào tối ưu và được báo trong notes.
Ba mục tiêu cần cực tiểu: tổng chi phí, thời gian cung ứng, hệ số truyền nhiệt U.
Ràng buộc: ngân sách, hạn giao. Tải trọng xe và vật liệu loại trừ được lọc trước khi tìm kiếm.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, replace
from datetime import date

import numpy as np
import pandas as pd

from .. import config
from ..catalog.repository import Catalog, road_distance_km
from ..catalog.pricing import _latest_price_records, has_price_source, normalize_unit
from ..predict.cost_model import MaterialPriceModel
from ..rough.models import RAW_CLASSES
from ..schemas import Constraints, GroupChoice, MaterialDemand, OptimizeResult, Solution, WallGroup

BRUTE_FORCE_LIMIT = 20_000


@dataclass
class GroupSpace:
    group: WallGroup
    options: list[dict]      # mỗi phần tử: một cặp (vật liệu, nhà cung cấp) đã có đơn giá và cự ly
    labor_rate: float = 0.0  # đồng/công từ bảng labor_rates; 0 khi chưa có (đã báo trong notes)


@dataclass
class MaterialSpace:
    demand: MaterialDemand
    options: list[dict]      # mỗi phần tử: một nhà cung cấp có giá cùng đơn vị cho đúng mã thiết kế


def _material_spaces(demands: list[MaterialDemand], cons: Constraints, catalog: Catalog,
                     price_model: MaterialPriceModel | None, vehicles: pd.DataFrame) -> tuple[list[MaterialSpace], list[str]]:
    """Vật tư ngoài tường: không đổi mã (đổi thép, mác bê tông là đổi thiết kế kết cấu), chỉ chọn nhà cung cấp và xe."""
    if not demands:
        return [], []
    order_date = pd.to_datetime(cons.order_date or date.today().isoformat()).date().isoformat()
    has_truck = not vehicles.empty and not (vehicles.vehicle_id == "DELIVERY_INCLUDED").all()
    mats = catalog.materials.set_index("material_id")
    sups = catalog.suppliers.set_index("supplier_id")
    spaces, skipped, bulletin_used = [], [], []
    for d in demands:
        if d.material_id not in mats.index or normalize_unit(mats.loc[d.material_id].get("unit")) != normalize_unit(d.unit):
            skipped.append(f"{d.material_id} (khác đơn vị danh mục hoặc chưa có mã)")
            continue
        m = mats.loc[d.material_id]
        if cons.procurement_mode and m.get("data_kind") != "ACTUAL":
            skipped.append(f"{d.material_id} (vật liệu chưa ACTUAL)")
            continue
        weight = _number(m.get("unit_weight_kg"), 1e-12)
        options = []
        for o in catalog.offers([d.material_id]).to_dict("records"):
            if not _quote_compatible(o, d.unit, cons.procurement_mode, order_date):
                continue
            delivered = cons.procurement_mode and o.get("transport_included") == "YES"
            lead = _number(o.get("lead_time_days"))
            lat, lon = _number(o.get("lat"), -90), _number(o.get("lon"), -180)
            located = lat is not None and lon is not None and lat <= 90 and lon <= 180
            if lead is None or (not delivered and (not has_truck or weight is None or not located)):
                continue
            if delivered and cons.max_vehicle_ton is not None:
                limit = _number(o.get("max_truck_ton"), 1e-12)
                if limit is None or limit > cons.max_vehicle_ton:
                    continue
            price, source = _number(o.get("base_price"), 1e-12), "catalog"
            if cons.procurement_mode:
                source = f"ACTUAL/{o['price_level']}"
            elif price is None and price_model is not None and price_model.knows(d.material_id, o["supplier_id"]):
                row = pd.DataFrame([{**o, "quantity": d.quantity, "date": order_date}])
                price, source = _number(float(price_model.predict(row)[0]), 1e-12), "model"
            if price is None:
                continue
            options.append({**o, "material_name": str(m.get("name")), "quantity": d.quantity, "unit": str(m.get("unit")),
                            "unit_price": price, "price_source": source, "delivered": delivered, "lead_time_days": lead,
                            "weight_kg": d.quantity * weight if weight is not None else None,
                            "distance_km": None if delivered else road_distance_km(cons.site_lat, cons.site_lon, lat, lon),
                            "cost_basis": (f"ACTUAL, giá {o['price_date']}; nguồn: {_quote_source(o)}; " if cons.procurement_mode
                                           else "Kịch bản tham khảo; ") + _terms(o) + "giữ mã thiết kế, chỉ chọn nguồn cung; "
                                           "chưa gồm nhân công (tính theo công tác, không theo vật tư)."})
        if not options:
            options = _bulletin_options(d, str(m.get("name")), str(m.get("unit")), order_date)
            for o in options:
                _link_bulletin_dealer(o, sups, cons, weight if has_truck else None)
            if options:
                bulletin_used.append(d.material_id)
        if options:
            spaces.append(MaterialSpace(d, options))
        else:
            skipped.append(f"{d.material_id} {m.get('name')} (chưa có nhà cung cấp đủ giá, thời gian cung ứng, vị trí/khối lượng riêng)")
    notes = [f"Vật tư ngoài tường: đưa {len(spaces)}/{len(demands)} mã vào tối ưu nguồn cung (giữ mã thiết kế)."]
    if bulletin_used:
        notes.append("Dùng GIÁ CÔNG BỐ của Sở Xây dựng (tham khảo, chưa VAT, chưa vận chuyển, chưa phải báo giá) cho: "
                     + ", ".join(bulletin_used) + ". Nhà cung cấp trong công bố chưa ghép với đại lý có tọa độ và thời gian "
                     "cung ứng thì không tính cước và số ngày (ghép ở trang Đại lý, cột linked_supplier_id).")
    if skipped:
        notes.append("Tổng chi phí CHƯA gồm: " + "; ".join(skipped) + ".")
    return spaces, notes


def _bulletin_options(d: MaterialDemand, name: str, unit: str, order_date: str) -> list[dict]:
    """Giá công bố mới nhất của từng đơn vị bán (price_records BULLETIN, ACTUAL), cùng đơn vị, có nguồn, không sau ngày đặt."""
    options = []
    for p in _latest_price_records([d.material_id]).get(d.material_id, []):
        if (p.price_level != "BULLETIN" or p.price is None or p.price <= 0 or normalize_unit(p.unit) != normalize_unit(unit)
                or not p.price_date or p.price_date[:10] > order_date or not has_price_source(p.source_detail, p.url)):
            continue
        options.append({"supplier_id": p.supplier_id or "CONG_BO", "name": p.supplier_name or "Công bố giá",
                        "product_url": p.url, "material_name": name, "quantity": d.quantity, "unit": unit,
                        "unit_price": p.price, "price_source": "ACTUAL/BULLETIN", "bulletin": True, "delivered": False,
                        "lead_time_days": None, "weight_kg": None, "distance_km": None,
                        "cost_basis": f"Giá công bố {p.price_date[:10]} ({p.source_detail}); chưa VAT, chưa vận chuyển, "
                                      "chưa có thời gian cung ứng; cần báo giá đại lý trước khi mua."})
    return options


def _terms(o: dict) -> str:
    vat = {"YES": "đã gồm VAT", "NO": "chưa gồm VAT"}.get(o.get("vat_included"), "chưa rõ VAT")
    ship = {"YES": "giá đã gồm giao hàng", "NO": "giá chưa gồm giao hàng"}.get(o.get("transport_included"), "chưa rõ giao hàng")
    return f"{vat}, {ship}; "


def _link_bulletin_dealer(o: dict, sups: pd.DataFrame, cons: Constraints, weight: float | None) -> None:
    """Công ty trong công bố giá là cùng công ty với một đại lý (suppliers.linked_supplier_id): lấy tên, vị trí, thời gian
    cung ứng của đại lý để tính cước và số ngày. Giá vẫn là giá công bố (chưa VAT, chưa vận chuyển)."""
    link = sups.loc[o["supplier_id"]].get("linked_supplier_id") if o["supplier_id"] in sups.index else None
    if not isinstance(link, str) or link not in sups.index or sups.loc[link].get("data_kind") != "ACTUAL":
        return
    s = sups.loc[link]
    lat, lon, lead = _number(s.get("lat"), -90), _number(s.get("lon"), -180), _number(s.get("lead_time_days"))
    o.update(bulletin_supplier_id=o["supplier_id"], supplier_id=link, name=str(s["name"]), maps_url=s.get("maps_url"),
             lead_time_days=lead)
    located = lat is not None and lon is not None and lat <= 90 and lon <= 180
    if located and weight is not None:
        o.update(weight_kg=o["quantity"] * weight, distance_km=road_distance_km(cons.site_lat, cons.site_lon, lat, lon))
    o["cost_basis"] += (f" Đại lý cùng công ty: {s['name']} ({link}); "
                        + ("cước theo cự ly ước tính" if o["distance_km"] is not None else "đại lý chưa có tọa độ, chưa tính cước")
                        + ("; " + f"thời gian cung ứng {lead:g} ngày." if lead is not None else "; chưa có thời gian cung ứng."))


def _number(value, minimum=0.0) -> float | None:
    try:
        value = float(value)
    except (ValueError, TypeError):
        return None
    return value if math.isfinite(value) and value >= minimum else None


def _quote_source(o: dict) -> str | None:
    # source của hàng ghép thường là hồ sơ NCC, không phải chứng từ của báo giá.
    for key in ("quote_reference", "price_source_detail", "source_detail", "certificate_reference"):
        if has_price_source(source_detail=o.get(key)):
            return o[key].strip()
    for key in ("product_url", "price_page_url"):
        if has_price_source(price_url=o.get(key)):
            return o[key].strip()
    return None


def _quote_compatible(o: dict, unit: str, actual_only=False, order_date=None) -> bool:
    sale_unit = normalize_unit(o.get("sale_unit"))
    # Bộ mẫu cũ chưa có sale_unit; chỉ kịch bản SAMPLE được giữ quy ước đơn vị danh mục.
    if not sale_unit and not actual_only and o.get("data_kind") == "SAMPLE":
        sale_unit = normalize_unit(unit)
    if not sale_unit or sale_unit != normalize_unit(unit):
        return False
    if not actual_only:
        return True
    when = pd.to_datetime(o.get("price_date"), errors="coerce")
    expiry = o.get("valid_until")
    expires = pd.to_datetime(expiry, errors="coerce")
    expiry_present = expiry is not None and not pd.isna(expiry)
    return (o.get("data_kind") == "ACTUAL" and o.get("data_kind_sup") == "ACTUAL"
            and o.get("price_level") in ("DEALER", "QUOTE") and _number(o.get("base_price"), 1e-12) is not None
            and pd.notna(when) and when.date().isoformat() <= order_date
            and (not expiry_present or (pd.notna(expires) and expires.date().isoformat() >= order_date))
            and _quote_source(o) is not None
            and o.get("vat_included") == "YES" and o.get("transport_included") in ("YES", "NO"))


def _procurement_space(groups: list[WallGroup], cons: Constraints, catalog: Catalog):
    if not {"site_lat", "site_lon"} <= cons.model_fields_set:
        raise ValueError("Chế độ mua vật tư cần nhập rõ vĩ độ và kinh độ công trình.")
    if not (math.isfinite(cons.site_lat) and -90 <= cons.site_lat <= 90
            and math.isfinite(cons.site_lon) and -180 <= cons.site_lon <= 180):
        raise ValueError("Tọa độ công trình không hợp lệ.")
    when = pd.to_datetime(cons.order_date or date.today().isoformat(), errors="coerce")
    if pd.isna(when):
        raise ValueError("Ngày đặt hàng không hợp lệ.")
    order_date = when.date().isoformat()
    notes = ["Chế độ mua vật tư: chỉ dùng ACTUAL; giữ thiết kế, chỉ xét thay thế đã được duyệt và cùng lớp/vai trò.",
             "Báo giá phải có chứng từ hoặc trang giá truy được; hồ sơ nhà cung cấp và link bản đồ không chứng minh đơn giá.",
             "Cự ly đường bộ, phí xe theo cự ly và số ngày vận chuyển là ƯỚC TÍNH; ngân sách/hạn giao chỉ so trên ước tính, "
             "chưa phải cam kết báo giá giao đến công trình. U chỉ xét lớp xây, chưa gồm các lớp hoàn thiện."]
    vehicles = catalog.vehicles_up_to(cons.max_vehicle_ton).copy()
    valid = vehicles.apply(lambda r: r.get("data_kind") == "ACTUAL"
                           and _number(r.get("payload_ton"), 1e-12) is not None
                           and _number(r.get("base_fee")) is not None
                           and _number(r.get("fee_per_km")) is not None, axis=1)
    vehicles = vehicles[valid.astype(bool)].reset_index(drop=True)
    labor = catalog.labor_rates.copy()
    valid_labor = labor.apply(lambda r: r.get("data_kind") == "ACTUAL"
                             and _number(r.get("rate_per_day"), 1e-12) is not None
                             and isinstance(r.get("source"), str) and bool(r.get("source").strip())
                             and pd.notna(pd.to_datetime(r.get("valid_from"), errors="coerce")), axis=1)
    if not cons.province or not cons.province.strip():
        return [], vehicles, notes + ["Cần chọn địa bàn công trình để tra nhân công; không tự chọn tỉnh có sẵn trong danh mục."]
    labor_rate, labor_note = replace(catalog, labor_rates=labor[valid_labor.astype(bool)]).labor_rate(cons.province, order_date)
    if labor_rate is None:
        return [], vehicles, notes + ["Thiếu đơn giá nhân công ACTUAL có nguồn, ngày hiệu lực và địa bàn phù hợp."]
    notes.append(labor_note)
    spaces, blocked = [], False
    mats = catalog.materials.set_index("material_id")
    for g in groups:
        if not math.isfinite(g.net_area_m2) or g.net_area_m2 < 0:
            raise ValueError("Diện tích nhóm tường không hợp lệ.")
        if g.net_area_m2 == 0:
            continue
        if not g.design_wall_system_id or g.design_material_share < 1.0:
            notes.append(f"Tường {g.wall_type} ({g.role}): chưa xác nhận đầy đủ phương án thiết kế cho cả nhóm.")
            blocked = True
            continue
        allowed = {g.design_wall_system_id}
        if not cons.keep_design_material:
            allowed.update(cons.approved_wall_system_ids)
        systems = catalog.systems_for_wall(g.wall_type, cons.excluded_materials)
        design_rows = catalog.wall_systems[catalog.wall_systems.wall_system_id == g.design_wall_system_id]
        design_mm = _number(design_rows.iloc[0].get("masonry_thickness_mm"), 1e-12) if len(design_rows) == 1 else None
        systems = systems[systems.wall_system_id.isin(allowed) & systems.ready.astype(bool)
                          & (systems.data_kind == "ACTUAL") & (systems.material_data_kind == "ACTUAL")]
        options = []
        for sw in systems.to_dict("records"):
            if any(_number(sw.get(k), 1e-12) is None for k in (
                    "qty_per_m2", "labor_day_per_m2", "lambda_w_mk", "masonry_thickness_mm", "unit_weight_kg", "mortar_density")):
                continue
            if sw["wall_system_id"] != g.design_wall_system_id:
                if sw.get("role") != g.role:
                    continue
                if design_mm is None or not math.isclose(float(sw["masonry_thickness_mm"]), design_mm, rel_tol=0, abs_tol=1e-6):
                    notes.append(f"{sw['wall_system_id']}: bề dày khác cấu tạo thiết kế, phải tính lại khối xây trước khi so giá.")
                    continue
            mid = sw.get("mortar_material_id")
            if sw["wall_system_id"] == g.design_wall_system_id and g.design_mortar_material_id:
                chosen = g.design_mortar_material_id
                if chosen not in mats.index or mid not in mats.index:
                    continue
                if chosen != mid and (normalize_unit(mats.loc[mid].get("unit")) != normalize_unit("m³")
                                      or normalize_unit(mats.loc[chosen].get("unit")) != normalize_unit("m³")):
                    continue  # đổi mác vữa chỉ áp cho vữa trộn m³, không thay keo AAC đơn vị tấn
                mid = chosen
            if not isinstance(mid, str) or mid not in mats.index or mats.loc[mid].get("data_kind") != "ACTUAL":
                continue
            if not catalog.relations.empty and ((catalog.relations.material_id == mid)
                                                & (catalog.relations.relation_type == "COMPOSED_OF")).any():
                reason = f"Tường {g.wall_type}: vữa {mid} trộn tại chỗ cần cấp phối và giá từng thành phần xi măng/cát; " \
                         "không dùng báo giá vữa thành phẩm thay cho cấu tạo đã xác nhận."
                if reason not in notes:
                    notes.append(reason)
                continue
            mortar = mats.loc[mid]
            per_m2 = _number(sw.get("mortar_m3_per_m2"), 1e-12)
            mortar_unit = normalize_unit(mortar.get("unit"))
            if mortar_unit == normalize_unit("tấn") and per_m2 is not None:
                density = _number(sw.get("mortar_density"), 1e-12)
                per_m2 = per_m2 * density / 1000 if density is not None else None
            elif mortar_unit != normalize_unit("m³"):
                continue
            if per_m2 is None:
                continue
            in_norm = isinstance(sw.get("norm_code"), str) and sw["norm_code"].strip().startswith("AE")
            main_waste = 0.0 if in_norm else _number(sw.get("waste_pct"))
            mortar_waste = 0.0 if in_norm else _number(mortar.get("waste_pct"))
            if main_waste is None or mortar_waste is None:
                continue
            main_qty = g.net_area_m2 * sw["qty_per_m2"] * (1 + main_waste / 100)
            mortar_qty = g.net_area_m2 * per_m2 * (1 + mortar_waste / 100)
            mortar_offers = catalog.offers([mid]).to_dict("records")
            for offer in catalog.offers([sw["material_id"]]).to_dict("records"):
                if not _quote_compatible(offer, sw["unit"], True, order_date):
                    continue
                delivered = offer["transport_included"] == "YES"
                if not delivered and vehicles.empty:
                    continue
                if cons.max_vehicle_ton is not None:
                    supplier_limit = _number(offer.get("max_truck_ton"), 1e-12)
                    if vehicles.empty or (delivered and (supplier_limit is None or supplier_limit > cons.max_vehicle_ton)):
                        continue
                if any(_number(offer.get(k)) is None for k in ("lead_time_days",)):
                    continue
                lat, lon = _number(offer.get("lat"), -90), _number(offer.get("lon"), -180)
                located = lat is not None and lon is not None and lat <= 90 and lon <= 180
                if not delivered and not located:
                    continue
                companions = [m for m in mortar_offers if m.get("supplier_id") == offer["supplier_id"]
                              and _quote_compatible(m, mortar_unit, True, order_date)
                              and m.get("vat_included") == offer["vat_included"]
                              and m.get("transport_included") == offer["transport_included"]]
                if not companions:
                    continue
                mo = min(companions, key=lambda m: m["base_price"])
                o = {**offer, **sw}
                o.update(quantity=main_qty, unit_price=float(offer["base_price"]), price_source=f"ACTUAL/{offer['price_level']}",
                         distance_km=road_distance_km(cons.site_lat, cons.site_lon, lat, lon) if located and not delivered else None,
                         mortar_material_id=mid, mortar_material_name=str(mortar["name"]), mortar_quantity=mortar_qty,
                         mortar_unit=str(mortar["unit"]), mortar_unit_price=float(mo["base_price"]),
                         mortar_cost=mortar_qty * mo["base_price"], procurement_mode=True,
                         transport_included=offer["transport_included"], vat_included=offer["vat_included"],
                         cost_basis=f"ACTUAL, giá {offer['price_date']}; VAT {'đã gồm' if offer['vat_included'] == 'YES' else 'chưa gồm'}; "
                                    f"nguồn vật liệu chính: {_quote_source(offer)}; nguồn vữa: {_quote_source(mo)}; "
                                    "vật liệu chính và vữa cùng nhà cung cấp; " +
                                    ("đã gồm giao hàng, không tự tính cự ly/phí xe." if delivered
                                     else "phí giao hàng/thời gian theo mô hình ước tính."))
                mortar_kg = 1000 if mortar_unit == normalize_unit("tấn") else sw["mortar_density"]
                o["weight_kg_per_m2"] = (main_qty * sw["unit_weight_kg"] + mortar_qty * mortar_kg) / g.net_area_m2
                options.append(o)
        if not options:
            blocked = True
            notes.append(f"Tường {g.wall_type} ({g.role}, {g.net_area_m2:g} m²): thiếu phương án ACTUAL phù hợp hoặc "
                         "giá cùng đơn vị/điều kiện của vật liệu chính và vữa cùng nhà cung cấp; chưa có phương án mua đủ.")
        else:
            spaces.append(GroupSpace(g, options, labor_rate))
    if blocked:
        return [], vehicles, notes + ["Không xét ngân sách/hạn giao trên tổng thiếu nhóm; cần bổ sung các nhóm bị chặn."]
    if spaces and vehicles.empty:
        # Đây là lựa chọn giao hàng đã gồm giá, không phải bản ghi xe ACTUAL hoặc dữ liệu mẫu.
        vehicles = pd.DataFrame([{"vehicle_id": "DELIVERY_INCLUDED", "payload_ton": None, "base_fee": 0, "fee_per_km": 0}])
    return spaces, vehicles, notes


def build_space(groups: list[WallGroup], cons: Constraints, catalog: Catalog,
                price_model: MaterialPriceModel | None) -> tuple[list[GroupSpace], pd.DataFrame, list[str]]:
    if cons.procurement_mode:
        return _procurement_space(groups, cons, catalog)
    notes: list[str] = ["KỊCH BẢN THAM KHẢO: có thể dùng SAMPLE/giá mô hình; chưa gồm giá vữa và chưa đủ căn cứ mua hàng. "
                        "Cự ly, phí xe và thời gian vận chuyển là ước tính."]
    vehicles = catalog.vehicles_up_to(cons.max_vehicle_ton).reset_index(drop=True)
    if vehicles.empty:
        raise ValueError("Không có loại xe nào thỏa tải trọng tối đa đã nhập.")
    order_date = cons.order_date or date.today().isoformat()
    labor_rate, labor_note = catalog.labor_rate(cons.province, order_date)
    notes.append(labor_note if labor_rate is not None else labor_note + " Chi phí nhân công chưa tính vào tổng chi phí.")
    spaces: list[GroupSpace] = []
    for g in groups:
        if g.net_area_m2 <= 0:
            continue
        systems = catalog.systems_for_wall(g.wall_type, cons.excluded_materials)
        if cons.keep_design_material:
            if not g.design_wall_system_id:
                raise ValueError(f"Tường {g.wall_type} ({g.role}) chưa có phương án tường theo thiết kế; "
                                 "chọn vật liệu trên trang kiểm tra hoặc bỏ tùy chọn giữ vật liệu thiết kế.")
            systems = systems[systems.wall_system_id == g.design_wall_system_id]
            if len(systems) and not bool(systems.ready.iloc[0]):
                raise ValueError(f"Phương án thiết kế {g.design_wall_system_id} của tường {g.wall_type} chưa đủ số liệu để "
                                 f"tối ưu (thiếu {', '.join(systems.missing.iloc[0])}). Bổ sung trong danh mục vật liệu "
                                 "hoặc bỏ tùy chọn giữ vật liệu thiết kế.")
            notes.append(f"Tường {g.wall_type}: giữ phương án thiết kế {g.design_wall_system_id}.")
        not_ready = systems[~systems.ready.astype(bool)]
        if len(not_ready):
            notes.append(f"Tường {g.wall_type}: chưa đưa vào tối ưu " + "; ".join(
                f"{r.wall_system_id} (thiếu {', '.join(r.missing)})" for r in not_ready.itertuples()) + ".")
        systems = systems[systems.ready.astype(bool)]
        if (systems.data_kind == "SAMPLE").any():
            notes.append(f"Tường {g.wall_type}: có phương án dùng SỐ MẪU, không dùng để báo cáo.")
        offers = catalog.offers(systems.material_id.tolist())
        incomplete = offers[offers[["lat", "lon", "lead_time_days"]].isna().any(axis=1)]
        if len(incomplete):
            notes.append(f"Tường {g.wall_type}: bỏ qua đại lý chưa có tọa độ hoặc thời gian cung ứng: "
                         + ", ".join(sorted(incomplete.supplier_id.unique())) + ".")
            offers = offers.drop(incomplete.index)
        # một nhóm thiếu số liệu không làm hỏng cả lần tối ưu: bỏ nhóm đó, báo rõ tổng chi phí chưa gồm nó
        if offers.empty:
            notes.append(f"Tường {g.wall_type} ({g.role}, {g.net_area_m2:g} m²): không có phương án đủ số liệu và có nhà "
                         "cung cấp, chưa đưa vào tối ưu; tổng chi phí chưa gồm nhóm này.")
            continue
        offers = offers.merge(systems.drop(columns=["data_kind"]), on="material_id", suffixes=("", "_ws"))
        compatible = offers.apply(lambda r: _quote_compatible(r.to_dict(), r["unit"]), axis=1)
        if not compatible.all():
            notes.append(f"Tường {g.wall_type}: bỏ {int((~compatible).sum())} báo giá thiếu/khác đơn vị danh mục.")
            offers = offers[compatible]
        if offers.empty:
            notes.append(f"Tường {g.wall_type}: không có báo giá cùng đơn vị; tổng chi phí chưa gồm nhóm này.")
            continue
        no_waste = sorted(offers.material_id[offers.waste_pct.isna()].unique())
        if no_waste:
            notes.append(f"Tường {g.wall_type}: {', '.join(no_waste)} chưa có hao hụt (waste_pct), khối lượng chưa cộng hao hụt.")
        waste = offers.waste_pct.map(lambda v: 1 + v / 100 if pd.notna(v) else 1.0)
        offers = offers.assign(
            quantity=g.net_area_m2 * offers.qty_per_m2 * waste, date=order_date,
            distance_km=[road_distance_km(cons.site_lat, cons.site_lon, la, lo) for la, lo in zip(offers.lat, offers.lon)],
        )
        offers["unit_price"], offers["price_source"] = offers.base_price.astype(float), "catalog"
        if price_model is not None:
            known = offers.unit_price.isna().to_numpy() & np.array([
                price_model.knows(m, s) for m, s in zip(offers.material_id, offers.supplier_id)])
            if known.any():
                offers.loc[known, "unit_price"] = price_model.predict(offers[known])
                offers.loc[known, "price_source"] = "model"
        # đại lý không công khai giá và mô hình chưa biết cặp (vật liệu, đại lý) thì không đưa vào tối ưu
        no_price = ~offers.unit_price.map(lambda p: _number(p, 1e-12) is not None)
        if no_price.any():
            notes.append(f"Tường {g.wall_type}: bỏ {int(no_price.sum())} cặp vật liệu, đại lý chưa có giá.")
            offers = offers[~no_price]
        if offers.empty:
            notes.append(f"Tường {g.wall_type} ({g.role}, {g.net_area_m2:g} m²): chưa có giá cho vật liệu nào, chưa đưa "
                         "vào tối ưu; tổng chi phí chưa gồm nhóm này.")
            continue
        spaces.append(GroupSpace(g, offers.to_dict("records"), labor_rate or 0.0))
    if price_model is None:
        notes.append("Chưa có mô hình giá trong thư mục models/, đang dùng giá trong danh mục.")
    return spaces, vehicles, notes


def evaluate(spaces: list[GroupSpace], vehicles: pd.DataFrame, picks: list[tuple[int, int]]):
    """picks[k] = (chỉ số phương án, chỉ số xe) của nhóm tường thứ k."""
    total, days, u_num, u_den, choices = 0.0, 0.0, 0.0, 0.0, []
    envelope_exists = any(isinstance(s, GroupSpace) and s.group.role == "envelope" for s in spaces)
    for space, (oi, vi) in zip(spaces, picks):
        if isinstance(space, MaterialSpace):
            o, v = space.options[oi], vehicles.iloc[vi]
            fixed = o["delivered"] or o["distance_km"] is None  # giá công bố chưa ghép đại lý có tọa độ: không chọn xe
            trips = 0 if fixed else max(1, math.ceil(o["weight_kg"] / (v.payload_ton * 1000.0)))
            transport = 0.0 if fixed else trips * (v.base_fee + v.fee_per_km * o["distance_km"])
            cost = o["quantity"] * o["unit_price"]
            total += cost + transport
            if o["lead_time_days"] is not None:
                days = max(days, o["lead_time_days"] + math.ceil(trips / config.TRIPS_PER_DAY))
            rc = space.demand.raw_class
            choices.append(GroupChoice(
                wall_type=RAW_CLASSES.get(rc, "Vật tư khác"), raw_class=rc, material_id=space.demand.material_id,
                material_name=o["material_name"], supplier_id=o["supplier_id"], supplier_name=o["name"],
                vehicle_id="DELIVERY_INCLUDED" if o["delivered"] else "CHUA_TINH" if fixed else v.vehicle_id,
                quantity=round(o["quantity"], 3),
                unit=o["unit"], unit_price=round(o["unit_price"], 0), price_source=o["price_source"], product_url=_link(o),
                distance_km=round(o["distance_km"], 1) if o["distance_km"] is not None else None, trips=trips,
                material_cost=round(cost), main_material_cost=round(cost), transport_cost=round(transport), install_cost=0,
                cost_complete=False, transport_estimated=not o["delivered"], cost_basis=o["cost_basis"]))
            continue
        o, v, area = space.options[oi], vehicles.iloc[vi], space.group.net_area_m2
        main_material_cost = o["quantity"] * o["unit_price"]
        mortar_cost = o.get("mortar_cost", 0.0)
        material_cost = main_material_cost + mortar_cost
        delivery_included = bool(o.get("procurement_mode")) and o.get("transport_included") == "YES"
        trips = 0 if delivery_included else max(1, math.ceil(area * o["weight_kg_per_m2"] / (v.payload_ton * 1000.0)))
        transport = 0.0 if delivery_included else trips * (v.base_fee + v.fee_per_km * o["distance_km"])
        install = area * o["labor_day_per_m2"] * space.labor_rate
        total += material_cost + transport + install
        days = max(days, o["lead_time_days"] + math.ceil(trips / config.TRIPS_PER_DAY))
        if space.group.role == "envelope" or not envelope_exists:
            u = 1.0 / (config.R_SI + (o["masonry_thickness_mm"] / 1000.0) / o["lambda_w_mk"] + config.R_SE)
            u_num, u_den = u_num + u * area, u_den + area
        choices.append(GroupChoice(
            wall_type=space.group.wall_type, wall_system_id=o["wall_system_id"], material_id=o["material_id"],
            material_name=o["material_name"],
            supplier_id=o["supplier_id"], supplier_name=o["name"], vehicle_id="DELIVERY_INCLUDED" if delivery_included else v.vehicle_id,
            quantity=round(o["quantity"], 2), unit=o["unit"], unit_price=round(o["unit_price"], 0),
            price_source=o["price_source"], product_url=_link(o),
            distance_km=round(o["distance_km"], 1) if o["distance_km"] is not None else None,
            trips=trips, material_cost=round(material_cost), transport_cost=round(transport), install_cost=round(install),
            main_material_cost=round(main_material_cost), mortar_material_id=o.get("mortar_material_id"),
            mortar_material_name=o.get("mortar_material_name"), mortar_quantity=o.get("mortar_quantity"),
            mortar_unit=o.get("mortar_unit"), mortar_unit_price=o.get("mortar_unit_price"),
            mortar_cost=round(mortar_cost) if o.get("procurement_mode") else None,
            cost_complete=bool(o.get("procurement_mode")), transport_estimated=not delivery_included, supply_estimated=True,
            cost_basis=o.get("cost_basis", "Kịch bản tham khảo, chưa gồm vữa; cự ly/phí xe/thời gian là ước tính."),
        ))
    return total, days, (u_num / u_den if u_den else 0.0), choices


def _link(o: dict) -> str:
    """Liên kết của lựa chọn: trang sản phẩm nếu có, không thì liên kết Google Maps của đại lý."""
    for key in ("product_url", "maps_url"):
        value = o.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def feasible(total: float, days: float, cons: Constraints) -> bool:
    return (cons.budget is None or total <= cons.budget) and (cons.deadline_days is None or days <= cons.deadline_days)


def non_dominated(points: np.ndarray) -> np.ndarray:
    """Trả về mặt nạ các điểm không bị điểm nào khác vượt trội (mọi mục tiêu đều cực tiểu)."""
    keep = np.ones(len(points), dtype=bool)
    for i, p in enumerate(points):
        if keep[i]:
            dominated = np.all(points <= p, axis=1) & np.any(points < p, axis=1)
            if dominated.any():
                keep[i] = False
    return keep


def _to_result(spaces, vehicles, pick_list, n_eval, notes) -> OptimizeResult:
    seen, sols = set(), []
    for picks in pick_list:
        key = tuple(picks)
        if key in seen:
            continue
        seen.add(key)
        total, days, u, choices = evaluate(spaces, vehicles, list(picks))
        sols.append(Solution(total_cost=round(total), supply_days=days, u_value=round(u, 3), choices=choices))
    if sols:
        mask = non_dominated(np.array([[s.total_cost, s.supply_days, s.u_value] for s in sols]))
        sols = [s for s, k in zip(sols, mask) if k]
    sols.sort(key=lambda s: s.total_cost)
    if not sols:
        notes = notes + ["Không có phương án nào thỏa ngân sách và hạn giao; hãy nới ràng buộc."]
    return OptimizeResult(solutions=sols, n_evaluated=n_eval, notes=notes)


def solve_brute_force(spaces, vehicles, cons, notes=None) -> OptimizeResult:
    """Vét cạn: dùng cho bài toán nhỏ và làm mốc đối chứng cho NSGA-II."""
    ranges = [itertools.product(range(len(s.options)), range(len(vehicles))) for s in spaces]
    picks_ok, n = [], 0
    for picks in itertools.product(*ranges):
        n += 1
        total, days, _, _ = evaluate(spaces, vehicles, list(picks))
        if feasible(total, days, cons):
            picks_ok.append(picks)
    return _to_result(spaces, vehicles, picks_ok, n, list(notes or []))


def solve_nsga2(spaces, vehicles, cons, notes=None, pop_size=None, n_gen=None, seed=1) -> OptimizeResult:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.repair.rounding import RoundingRepair
    from pymoo.operators.sampling.rnd import IntegerRandomSampling
    from pymoo.optimize import minimize

    sizes = []
    for s in spaces:
        sizes += [len(s.options), len(vehicles)]
    # biên trên tối thiểu là 1 để toán tử lai ghép không chia cho 0; chỉ số được lấy dư khi giải mã
    upper = np.array([max(1, n - 1) for n in sizes])

    def decode(x):
        idx = [int(v) % n for v, n in zip(x, sizes)]
        return [(idx[2 * k], idx[2 * k + 1]) for k in range(len(spaces))]

    class WallProblem(ElementwiseProblem):
        def __init__(self):
            super().__init__(n_var=len(sizes), n_obj=3, n_ieq_constr=2, xl=np.zeros(len(sizes)), xu=upper, vtype=int)

        def _evaluate(self, x, out, *args, **kwargs):
            total, days, u, _ = evaluate(spaces, vehicles, decode(x))
            out["F"] = [total, days, u]
            out["G"] = [total - cons.budget if cons.budget is not None else -1.0,
                        days - cons.deadline_days if cons.deadline_days is not None else -1.0]

    algorithm = NSGA2(
        pop_size=pop_size or config.NSGA_POP_SIZE, sampling=IntegerRandomSampling(),
        crossover=SBX(prob=0.9, eta=15, vtype=float, repair=RoundingRepair()),
        mutation=PM(eta=20, vtype=float, repair=RoundingRepair()), eliminate_duplicates=True,
    )
    n_gen = n_gen or config.NSGA_GENERATIONS
    res = minimize(WallProblem(), algorithm, ("n_gen", n_gen), seed=seed, verbose=False)
    xs = [] if res.X is None else np.atleast_2d(res.X)
    return _to_result(spaces, vehicles, [tuple(decode(x)) for x in xs], res.algorithm.evaluator.n_eval, list(notes or []))


def optimize(groups: list[WallGroup], cons: Constraints, catalog: Catalog | None = None,
             price_model: MaterialPriceModel | None = None, method: str = "auto",
             materials: list[MaterialDemand] | None = None) -> OptimizeResult:
    """method: 'auto' (vét cạn nếu không gian nhỏ, ngược lại NSGA-II), 'nsga2', 'brute'.
    materials: vật tư ngoài tường, mỗi mã một biến (nhà cung cấp, xe)."""
    catalog = catalog or Catalog.load()
    walls = [g for g in groups if g.net_area_m2 > 0]
    if walls or not materials or not cons.procurement_mode:
        spaces, vehicles, notes = build_space(groups, cons, catalog, price_model)
    else:  # chỉ có vật tư ngoài tường: chế độ mua không cần nhân công tường
        spaces, vehicles, notes = [], catalog.vehicles_up_to(cons.max_vehicle_ton).reset_index(drop=True), []
        if not {"site_lat", "site_lon"} <= cons.model_fields_set:
            raise ValueError("Chế độ mua vật tư cần nhập rõ vĩ độ và kinh độ công trình.")
        if len(vehicles):
            ok = vehicles.apply(lambda r: r.get("data_kind") == "ACTUAL" and _number(r.get("payload_ton"), 1e-12) is not None
                                and _number(r.get("base_fee")) is not None and _number(r.get("fee_per_km")) is not None, axis=1)
            vehicles = vehicles[ok.astype(bool)].reset_index(drop=True)
    # nhóm tường bị chặn ở chế độ mua thì không xếp hạng tổng thiếu, kể cả khi vật tư khác đủ số
    if not (cons.procurement_mode and walls and not spaces):
        extra, extra_notes = _material_spaces(materials or [], cons, catalog, price_model, vehicles)
        spaces, notes = spaces + extra, notes + extra_notes
        if extra and vehicles.empty:
            vehicles = pd.DataFrame([{"vehicle_id": "DELIVERY_INCLUDED", "payload_ton": None, "base_fee": 0, "fee_per_km": 0}])
    if not spaces:
        return OptimizeResult(solutions=[], n_evaluated=0, notes=notes + ["Không có nhóm tường hay vật tư nào để tối ưu."], execution={'algorithm':None,'space_size':0})
    size = math.prod(len(s.options) * len(vehicles) for s in spaces)
    if method == "brute" or (method == "auto" and size <= BRUTE_FORCE_LIMIT):
        notes.append(f"Không gian tìm kiếm {size} tổ hợp: dùng vét cạn (kết quả chính xác).")
        result=solve_brute_force(spaces, vehicles, cons, notes)
        result.execution={'algorithm':'brute','space_size':size,'seed':None}
    else:
        notes.append(f"Không gian tìm kiếm {size} tổ hợp: dùng NSGA-II.")
        result=solve_nsga2(spaces, vehicles, cons, notes)
        result.execution={'algorithm':'nsga2','space_size':size,'seed':1,'pop_size':config.NSGA_POP_SIZE,'generations':config.NSGA_GENERATIONS}
    result.execution['order_date']=cons.order_date or date.today().isoformat()
    return result
