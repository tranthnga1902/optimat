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
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from .. import config
from ..catalog.repository import Catalog, road_distance_km
from ..predict.cost_model import MaterialPriceModel
from ..schemas import Constraints, GroupChoice, OptimizeResult, Solution, WallGroup

BRUTE_FORCE_LIMIT = 20_000


@dataclass
class GroupSpace:
    group: WallGroup
    options: list[dict]      # mỗi phần tử: một cặp (vật liệu, nhà cung cấp) đã có đơn giá và cự ly


def build_space(groups: list[WallGroup], cons: Constraints, catalog: Catalog,
                price_model: MaterialPriceModel | None) -> tuple[list[GroupSpace], pd.DataFrame, list[str]]:
    notes: list[str] = []
    vehicles = catalog.vehicles_up_to(cons.max_vehicle_ton).reset_index(drop=True)
    if vehicles.empty:
        raise ValueError("Không có loại xe nào thỏa tải trọng tối đa đã nhập.")
    order_date = cons.order_date or date.today().isoformat()
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
        if offers.empty:
            raise ValueError(f"Không có phương án tường đủ số liệu và có nhà cung cấp cho tường {g.wall_type}.")
        offers = offers.merge(systems.drop(columns=["data_kind"]), on="material_id", suffixes=("", "_ws"))
        waste = offers.waste_pct.map(lambda v: 1 + v / 100 if pd.notna(v) else config.WASTE_FACTOR)
        offers = offers.assign(
            quantity=g.net_area_m2 * offers.qty_per_m2 * waste, date=order_date,
            distance_km=[road_distance_km(cons.site_lat, cons.site_lon, la, lo) for la, lo in zip(offers.lat, offers.lon)],
        )
        offers["unit_price"], offers["price_source"] = offers.base_price.astype(float), "catalog"
        if price_model is not None:
            known = np.array([price_model.knows(m, s) for m, s in zip(offers.material_id, offers.supplier_id)])
            if known.any():
                offers.loc[known, "unit_price"] = price_model.predict(offers[known])
                offers.loc[known, "price_source"] = "model"
        # đại lý không công khai giá và mô hình chưa biết cặp (vật liệu, đại lý) thì không đưa vào tối ưu
        no_price = offers.unit_price.isna()
        if no_price.any():
            notes.append(f"Tường {g.wall_type}: bỏ {int(no_price.sum())} cặp vật liệu, đại lý chưa có giá.")
            offers = offers[~no_price]
        if offers.empty:
            raise ValueError(f"Chưa có giá cho vật liệu nào của tường {g.wall_type}.")
        spaces.append(GroupSpace(g, offers.to_dict("records")))
    if price_model is None:
        notes.append("Chưa có mô hình giá trong thư mục models/, đang dùng giá trong danh mục.")
    return spaces, vehicles, notes


def evaluate(spaces: list[GroupSpace], vehicles: pd.DataFrame, picks: list[tuple[int, int]]):
    """picks[k] = (chỉ số phương án, chỉ số xe) của nhóm tường thứ k."""
    total, days, u_num, u_den, choices = 0.0, 0.0, 0.0, 0.0, []
    envelope_exists = any(s.group.role == "envelope" for s in spaces)
    for space, (oi, vi) in zip(spaces, picks):
        o, v, area = space.options[oi], vehicles.iloc[vi], space.group.net_area_m2
        material_cost = o["quantity"] * o["unit_price"]
        trips = max(1, math.ceil(area * o["weight_kg_per_m2"] / (v.payload_ton * 1000.0)))
        transport = trips * (v.base_fee + v.fee_per_km * o["distance_km"])
        install = area * o["labor_day_per_m2"] * config.LABOR_RATE_PER_DAY
        total += material_cost + transport + install
        days = max(days, o["lead_time_days"] + math.ceil(trips / config.TRIPS_PER_DAY))
        if space.group.role == "envelope" or not envelope_exists:
            u = 1.0 / (config.R_SI + (o["masonry_thickness_mm"] / 1000.0) / o["lambda_w_mk"] + config.R_SE)
            u_num, u_den = u_num + u * area, u_den + area
        choices.append(GroupChoice(
            wall_type=space.group.wall_type, wall_system_id=o["wall_system_id"], material_id=o["material_id"],
            material_name=o["material_name"],
            supplier_id=o["supplier_id"], supplier_name=o["name"], vehicle_id=v.vehicle_id,
            quantity=round(o["quantity"], 2), unit=o["unit"], unit_price=round(o["unit_price"], 0),
            price_source=o["price_source"], product_url=_link(o), distance_km=round(o["distance_km"], 1),
            trips=trips, material_cost=round(material_cost), transport_cost=round(transport), install_cost=round(install),
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
             price_model: MaterialPriceModel | None = None, method: str = "auto") -> OptimizeResult:
    """method: 'auto' (vét cạn nếu không gian nhỏ, ngược lại NSGA-II), 'nsga2', 'brute'."""
    catalog = catalog or Catalog.load()
    spaces, vehicles, notes = build_space(groups, cons, catalog, price_model)
    if not spaces:
        return OptimizeResult(solutions=[], n_evaluated=0, notes=notes + ["Không có nhóm tường nào để tối ưu."])
    size = math.prod(len(s.options) * len(vehicles) for s in spaces)
    if method == "brute" or (method == "auto" and size <= BRUTE_FORCE_LIMIT):
        notes.append(f"Không gian tìm kiếm {size} tổ hợp: dùng vét cạn (kết quả chính xác).")
        return solve_brute_force(spaces, vehicles, cons, notes)
    notes.append(f"Không gian tìm kiếm {size} tổ hợp: dùng NSGA-II.")
    return solve_nsga2(spaces, vehicles, cons, notes)
