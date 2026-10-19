"""Trang quan sát khái niệm: định nghĩa của Quy ước bản vẽ v1.0 đặt cạnh kết quả đối chiếu trên một bản vẽ.

    build_concept_html(report) -> HTML tự chứa (không cần mạng, mở bằng trình duyệt bất kỳ)
Bốn phần: (1) từng điều khoản QU: định nghĩa, cách hệ thống kiểm, kết quả trên bản vẽ này, bằng chứng;
(2) ký hiệu nhận dạng trong concepts.csv và ký hiệu nào đã khớp, ngưỡng hình học đang dùng;
(3) từng mặt bằng: sơ đồ tường, cửa, cột tô theo nguồn (quy ước / đoán bằng hình học), danh sách bộ phận kèm lý do;
(4) so với đáp án đo tay khi có. Trang chỉ hiển thị, không tính lại.
"""
from __future__ import annotations

from collections import Counter
from html import escape

from .. import config
from .concepts import load_signals
from .convention_check import ConventionReport, PlanConcepts
from .walls import STRIP_CONFIDENCE

STATUS_VI = {"dat": "Đạt", "vi_pham": "Vi phạm", "chua_kiem": "Chưa kiểm", "khong_ap_dung": "Không áp dụng"}
SOURCE_VI = {"quy_uoc": "Theo quy ước", "hinh_hoc": "Đoán bằng hình học", "nguoi_dung": "Người dùng chỉ định"}
BAND_VI = {"cao": "cao", "trung_binh": "trung bình", "thap": "thấp", "": "—"}

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--rule:#e3e2dc;--ok:#1f7a4d;--ok-bg:#e3f3ea;
--bad:#b3261e;--bad-bg:#fbe7e5;--todo:#8a6100;--todo-bg:#fdf1d6;--na:#5d5d58;--na-bg:#ecebe6;
--src-qu:#1f7a4d;--src-hh:#d07a00;--src-nd:#2f5fb3;--low:#b3261e;--plan-bg:#fbfbf9}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--card:#1f1f1d;--ink:#ecebe6;--muted:#a3a29b;
--rule:#34332f;--ok:#5cc58c;--ok-bg:#16301f;--bad:#f08a80;--bad-bg:#3a1a17;--todo:#e3b552;--todo-bg:#33280f;--na:#b4b3ac;
--na-bg:#2a2a27;--src-qu:#5cc58c;--src-hh:#f0a53a;--src-nd:#7fa8f0;--low:#f08a80;--plan-bg:#191918}}
:root[data-theme="dark"]{--bg:#161615;--card:#1f1f1d;--ink:#ecebe6;--muted:#a3a29b;--rule:#34332f;--ok:#5cc58c;--ok-bg:#16301f;
--bad:#f08a80;--bad-bg:#3a1a17;--todo:#e3b552;--todo-bg:#33280f;--na:#b4b3ac;--na-bg:#2a2a27;--src-qu:#5cc58c;--src-hh:#f0a53a;
--src-nd:#7fa8f0;--low:#f08a80;--plan-bg:#191918}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 64px}h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 10px}
h3{font-size:15px;margin:0 0 8px}p{margin:6px 0}.muted{color:var(--muted)}small{font-size:12px}
.card{background:var(--card);border:1px solid var(--rule);border-radius:10px;padding:14px 16px;margin:10px 0}
.verdict{display:inline-block;padding:4px 10px;border-radius:999px;font-weight:600}
.chip{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}
.dat{color:var(--ok);background:var(--ok-bg)}.vi_pham{color:var(--bad);background:var(--bad-bg)}
.chua_kiem{color:var(--todo);background:var(--todo-bg)}.khong_ap_dung{color:var(--na);background:var(--na-bg)}
.lv{font-weight:700;font-size:12px;padding:1px 6px;border-radius:4px;border:1px solid var(--rule)}
.lvB{color:var(--bad);border-color:var(--bad)}
table{border-collapse:collapse;width:100%}th,td{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid var(--rule)}
th{font-size:12px;color:var(--muted);font-weight:600}.tw{overflow-x:auto}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.stat{border:1px solid var(--rule);border-radius:8px;padding:6px 10px;background:var(--card)}
.stat b{font-size:18px;display:block}
.filters{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}.filters button{font:inherit;padding:4px 10px;border-radius:999px;
border:1px solid var(--rule);background:var(--card);color:var(--ink);cursor:pointer}.filters button[aria-pressed="true"]{border-color:var(--ink)}
details summary{cursor:pointer;color:var(--muted)}ul.ev{margin:4px 0 0;padding-left:18px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--muted)}.sw{display:inline-block;width:18px;height:4px;vertical-align:middle;margin-right:4px}
.plan{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:14px}@media (max-width:820px){.plan{grid-template-columns:1fr}}
svg.map{width:100%;height:auto;background:var(--plan-bg);border:1px solid var(--rule);border-radius:8px}
.src-quy_uoc{color:var(--src-qu)}.src-hinh_hoc{color:var(--src-hh)}.src-nguoi_dung{color:var(--src-nd)}
.hidden{display:none}
"""

JS = """
document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{
  const f=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',x===b));
  document.querySelectorAll('tr[data-status]').forEach(r=>r.classList.toggle('hidden',f!=='all'&&r.dataset.status!==f));
}));
"""


def _e(v) -> str:
    return escape("" if v is None else str(v))


def _chip(status: str) -> str:
    return f'<span class="chip {status}">{STATUS_VI[status]}</span>'


def _verdict(r: ConventionReport) -> str:
    if r.trong_quy_uoc is None:
        return '<span class="verdict khong_ap_dung">Không áp dụng: file không có mặt bằng kiến trúc</span>'
    if r.trong_quy_uoc:
        return '<span class="verdict dat">Trong quy ước: không vi phạm điều khoản bắt buộc (B)</span>'
    return ('<span class="verdict vi_pham">Ngoài quy ước: có vi phạm điều khoản bắt buộc (B). Vẫn bóc tách, '
            'nhưng không tính vào số liệu cam kết tầng 1</span>')


def _checks_html(r: ConventionReport) -> str:
    rows, group = [], None
    for c in r.checks:
        if c.nhom != group:
            group = c.nhom
            rows.append(f'<tr><th colspan="5" style="padding-top:16px;color:var(--ink)">{_e(group)}</th></tr>')
        ev = (f'<details><summary>{len(c.bang_chung)} bằng chứng</summary><ul class="ev">'
              + "".join(f"<li>{_e(x)}</li>" for x in c.bang_chung) + "</ul></details>") if c.bang_chung else ""
        rows.append(f'<tr data-status="{c.trang_thai}"><td><b>{_e(c.ma)}</b><br><span class="lv{" lvB" if c.muc == "B" else ""}" '
                    f'title="{"Bắt buộc" if c.muc == "B" else "Khuyến nghị"}">{_e(c.muc)}</span></td>'
                    f'<td>{_e(c.dieu_khoan)}</td><td class="muted"><small>{_e(c.cach_kiem)}</small></td>'
                    f'<td>{_chip(c.trang_thai)}</td><td>{_e(c.ket_qua)}{ev}</td></tr>')
    return ('<div class="tw"><table><thead><tr><th>Mã</th><th>Định nghĩa (điều khoản)</th><th>Hệ thống kiểm</th>'
            '<th>Trên bản vẽ này</th><th>Kết quả, bằng chứng</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def _signals_html(r: ConventionReport) -> str:
    by_signal: dict[str, list[str]] = {}
    for layer, ma in r.layer_signal.items():
        by_signal.setdefault(ma, []).append(layer)
    block_hits = Counter()
    for p in r.plans:
        for o in p.openings:
            for s in load_signals():
                if s.tin_hieu == "block" and f"ký hiệu {s.ma} " in o.ly_do:
                    block_hits[s.ma] += 1
    rows = []
    for s in load_signals():
        if s.tin_hieu == "layer":
            hit = ", ".join(by_signal.get(s.ma, []))
        else:
            hit = f"{block_hits[s.ma]} lỗ mở" if block_hits[s.ma] else ""
        size = f"{s.rong_mm:.0f}×{s.cao_mm:.0f} mm" if s.rong_mm and s.cao_mm else ""
        rows.append(f"<tr><td>{_e(s.ma)}</td><td>{_e(s.khai_niem)}</td><td>{_e(s.qu)}</td><td>{_e(s.tin_hieu)}</td>"
                    f"<td><code>{_e(s.mau)}</code></td><td>{_e(s.vai_tro)}</td><td>{_e(size)}</td>"
                    f'<td>{_e(hit) if hit else "<span class=muted>—</span>"}</td></tr>')
    classes = ", ".join(f"lớp {k}: {lo:.0f}–{hi:.0f}" for k, (lo, hi) in config.WALL_THICKNESS_CLASSES.items())
    geo = [
        ("QU-09", "Dải chiều dày giữa hai nét tường (mm)", classes),
        ("QU-09", "Hai nét chồng nhau tối thiểu", f"{config.MIN_WALL_OVERLAP_MM:.0f} mm, lệch góc ≤ {config.PARALLEL_ANGLE_TOL_DEG:g}°"),
        ("QU-08", "Tự nhận layer tường khi tên không theo quy ước",
         f"tổng cặp nét ≥ {config.WALL_LAYER_MIN_SCORE_MM:.0f} mm và ≥ {config.WALL_LAYER_REL_SCORE:.0%} layer cao nhất"),
        ("QU-10", "Tường một nét + hatch", f"độ tin cậy {STRIP_CONFIDENCE:g}; cặp nét có hatch trên layer khác: 0,5"),
        ("QU-14", "Cung cánh cửa", f"bán kính {config.DOOR_ARC_RADIUS_MM[0]:.0f}–{config.DOOR_ARC_RADIUS_MM[1]:.0f} mm, góc 60–120°; "
                                   f"khe tường được nối ≤ {config.MAX_OPENING_GAP_MM:.0f} mm"),
        ("QU-16", "Cột (vùng tô đặc gần chữ nhật)", f"cạnh {config.COLUMN_SIDE_MM[0]:.0f}–{config.COLUMN_SIDE_MM[1]:.0f} mm, "
                                                    f"dài/rộng ≤ {config.COLUMN_MAX_ASPECT:g}, lấp đầy ≥ {config.COLUMN_MIN_FILL:.0%}"),
    ]
    geo_rows = "".join(f"<tr><td>{_e(q)}</td><td>{_e(n)}</td><td>{_e(v)}</td></tr>" for q, n, v in geo)
    return (f'<div class="card"><h3>Ký hiệu nhận dạng (data/rules/concepts.csv)</h3><p class="muted"><small>Dòng khớp đầu tiên '
            f'thắng. Cột cuối: layer, lỗ mở trên bản vẽ này đã khớp ký hiệu đó.</small></p><div class="tw"><table><thead><tr>'
            f'<th>Mã</th><th>Khái niệm</th><th>QU</th><th>Tín hiệu</th><th>Mẫu</th><th>Vai trò</th><th>Mặc định</th>'
            f'<th>Khớp trên bản vẽ này</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></div>'
            f'<div class="card"><h3>Ngưỡng hình học đang dùng (config.py)</h3><p class="muted"><small>Dùng khi bản vẽ không theo '
            f'ký hiệu quy ước. Mục B5 của quy ước yêu cầu chuyển dần sang ngưỡng tương đối.</small></p><div class="tw"><table>'
            f'<thead><tr><th>QU</th><th>Ngưỡng</th><th>Giá trị</th></tr></thead><tbody>{geo_rows}</tbody></table></div></div>')


def _plan_svg(p: PlanConcepts) -> str:
    x0, y0, x1, y1 = p.bbox
    pad = 600
    w, h = max(1.0, x1 - x0) + 2 * pad, max(1.0, y1 - y0) + 2 * pad
    colors = {"quy_uoc": "var(--src-qu)", "hinh_hoc": "var(--src-hh)", "nguoi_dung": "var(--src-nd)"}
    parts = []
    for wl in p.walls:
        a, b, c, d = wl.hinh
        dash = ' stroke-dasharray="6 4"' if wl.muc_tin_cay == "thap" else ""
        parts.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{colors[wl.nguon]}" stroke-width="3" '
                     f'vector-effect="non-scaling-stroke"{dash}><title>{_e(wl.id)} · {_e(wl.khai_niem)} · '
                     f'{_e(SOURCE_VI[wl.nguon])} · tin cậy {BAND_VI[wl.muc_tin_cay]}: {_e(wl.ly_do)}</title></line>')
    for cl in p.columns:
        cx, cy, bw, bh = cl.hinh
        parts.append(f'<rect x="{cx - bw / 2}" y="{cy - bh / 2}" width="{bw}" height="{bh}" fill="{colors[cl.nguon]}" '
                     f'opacity="0.7"><title>{_e(cl.id)} · {_e(cl.ly_do)}</title></rect>')
    r = max(w, h) / 160
    for o in p.openings:
        ox, oy = o.hinh
        parts.append(f'<circle cx="{ox}" cy="{oy}" r="{r:.0f}" fill="none" stroke="{colors[o.nguon]}" stroke-width="2" '
                     f'vector-effect="non-scaling-stroke"><title>{_e(o.id)} · {_e(o.khai_niem)}: {_e(o.ly_do)}</title></circle>')
    # trục y của bản vẽ CAD hướng lên: lật lại trong SVG
    return (f'<svg class="map" viewBox="{x0 - pad} {-(y1 + pad)} {w} {h}" role="img" aria-label="Sơ đồ {_e(p.name)}">'
            f'<g transform="scale(1,-1)">{"".join(parts)}</g></svg>')


def _plan_html(p: PlanConcepts) -> str:
    src = Counter(w.nguon for w in p.walls)
    length = Counter()
    for w in p.walls:
        length[w.nguon] += w.dai_m or 0
    bands = Counter(w.muc_tin_cay for w in p.walls)
    stats = "".join(f'<div class="stat"><b class="src-{k}">{length[k]:.1f} m</b><small>{SOURCE_VI[k]} · {src[k]} tường</small></div>'
                    for k in ("quy_uoc", "hinh_hoc", "nguoi_dung") if src[k])
    stats += (f'<div class="stat"><b>{len(p.openings)}</b><small>lỗ mở</small></div>'
              f'<div class="stat"><b>{len(p.columns)}</b><small>cột</small></div>'
              f'<div class="stat"><b>{"Kín" if p.closed else "Hở"}</b><small>tường bao (QU-13)</small></div>')
    must = bands["thap"]
    rows = []
    for el in p.walls + p.openings + p.columns:
        rows.append(f'<tr><td>{_e(el.id)}</td><td>{_e(el.khai_niem)}</td><td class="src-{el.nguon}">{SOURCE_VI[el.nguon]}</td>'
                    f'<td>{_e(el.qu)}</td><td>{BAND_VI[el.muc_tin_cay]}{"" if el.do_tin_cay is None else f" ({el.do_tin_cay:.2f})"}</td>'
                    f'<td><small>{_e(el.ly_do)}</small></td></tr>')
    gt = ""
    if p.gt:
        g = p.gt
        pct = lambda v: "—" if v is None else f"{v:.0%}"
        gt = (f'<p><b>So với đáp án đo tay:</b> precision {pct(g.get("precision"))}, recall {pct(g.get("recall"))}, đúng lớp '
              f'{pct(g.get("class_ok"))}, sai số diện tích tường {pct(g.get("area_err"))} '
              f'({g.get("auto_m")} m tự nhận / {g.get("gt_m")} m đáp án).</p>')
    title = f' <small class="muted">(tiêu đề gốc trùng: "{_e(p.title)}")</small>' if p.title else ""
    level = "" if p.level_m is None else f" · cao độ {p.level_m:+.2f} m"
    height = "cao tầng chưa có (nhập trên trang kiểm tra)" if p.height_mm is None else f"cao tầng {p.height_mm:.0f} mm"
    return (f'<div class="card"><h3>{_e(p.name)}{title}</h3><p class="muted"><small>{height}{level}'
            f'{" · " + _e(", ".join(p.rooms[:6])) if p.rooms else ""}</small></p>'
            f'<div class="plan"><div>{_plan_svg(p)}</div><div><div class="stats">{stats}</div>'
            + (f'<p style="margin-top:10px">Có <b>{must}</b> tường độ tin cậy thấp: bắt buộc duyệt trên trang kiểm tra (B4).</p>' if must else "")
            + gt + '</div></div>'
            f'<details style="margin-top:10px"><summary>{len(rows)} bộ phận và lý do nhận</summary><div class="tw"><table><thead><tr>'
            f'<th>Mã</th><th>Khái niệm</th><th>Nguồn</th><th>QU</th><th>Tin cậy</th><th>Lý do</th></tr></thead><tbody>{"".join(rows)}'
            f'</tbody></table></div></details></div>')


def build_concept_html(r: ConventionReport) -> str:
    cnt = Counter((c.muc, c.trang_thai) for c in r.checks)
    stats = "".join(f'<div class="stat"><b>{n}</b><small>{label}</small></div>' for label, n in (
        ("vi phạm bắt buộc (B)", cnt[("B", "vi_pham")]), ("vi phạm khuyến nghị (K)", cnt[("K", "vi_pham")]),
        ("đạt", sum(v for (m, s), v in cnt.items() if s == "dat")),
        ("chưa kiểm", sum(v for (m, s), v in cnt.items() if s == "chua_kiem")),
        ("không áp dụng", sum(v for (m, s), v in cnt.items() if s == "khong_ap_dung"))))
    filters = "".join(f'<button type="button" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">{v}</button>'
                      for k, v in (("all", "Tất cả"), ("vi_pham", "Vi phạm"), ("chua_kiem", "Chưa kiểm"), ("dat", "Đạt")))
    legend = ('<div class="legend"><span><i class="sw" style="background:var(--src-qu)"></i>Theo quy ước (khớp ký hiệu)</span>'
              '<span><i class="sw" style="background:var(--src-hh)"></i>Đoán bằng hình học (người dùng duyệt)</span>'
              '<span><i class="sw" style="background:var(--src-nd)"></i>Người dùng chỉ định</span>'
              '<span>Nét đứt: tin cậy thấp · Ô vuông: cột · Vòng tròn: lỗ mở · Rê chuột để xem lý do</span></div>')
    plans = "".join(_plan_html(p) for p in r.plans) or '<p class="muted">Không có mặt bằng kiến trúc.</p>'
    warns = "".join(f"<li>{_e(w)}</li>" for w in r.warnings)
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Khái niệm bản vẽ</title><style>{CSS}</style></head><body><main>
<h1>Đối chiếu bản vẽ với Quy ước v1.0</h1>
<p class="muted">{_e(r.file)} · 23 điều khoản từ data/rules/quy_uoc.csv · ký hiệu từ data/rules/concepts.csv</p>
<div class="card">{_verdict(r)}<div class="stats">{stats}</div>{f'<ul class="ev">{warns}</ul>' if warns else ""}</div>
<h2>1. Định nghĩa và kết quả theo từng điều khoản</h2><div class="filters">{filters}</div>{_checks_html(r)}
<h2>2. Ký hiệu nhận dạng</h2>{_signals_html(r)}
<h2>3. Theo mặt bằng</h2>{legend}{plans}
</main><script>{JS}</script></body></html>"""
