"""Liệt kê từng đối tượng nhận diện được trên bản vẽ: tường, cửa, cặp nét bị loại (kèm lý do) và block khớp
ký hiệu không phải cửa trong data/rules/concepts.csv (cột, cao độ, trục, nội thất...).

    python scripts/list_objects.py [file.dxf ...]

Không truyền file thì chạy data/sample/*.dxf và data/drawings/**/*.dxf.
Ghi reports/doi_tuong_nhan_dien.csv và trang xem reports/doi_tuong_nhan_dien.html, in số đếm theo bản vẽ và mặt bằng.
"""
import csv
import sys
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from optimat.drawing.dxf_reader import read_drawing  # noqa: E402
from optimat.drawing.objects import COLS, list_objects  # noqa: E402


def rows_for(path: Path):
    return list_objects(read_drawing(str(path)), path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path))


def main() -> None:
    files = [Path(a).resolve() for a in sys.argv[1:]] or \
        sorted((ROOT / "data" / "sample").glob("*.dxf")) + sorted((ROOT / "data" / "drawings").rglob("*.dxf"))
    rows = []
    for f in files:
        try:
            got = list(rows_for(f))
        except Exception as e:  # một bản vẽ hỏng không làm dừng cả danh sách
            print(f"{f.name}: LỖI {e}")
            continue
        rows += got
        print(f"{f.name}: {len(got)} đối tượng")
        for (plan, kind), n in Counter((x["mat_bang"], x["loai"]) for x in got).items():
            print(f"    {plan} | {kind}: {n}")
    out = ROOT / "reports" / "doi_tuong_nhan_dien.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        wr = csv.DictWriter(fh, COLS)
        wr.writeheader()
        wr.writerows(rows)
    page = out.with_suffix(".html")
    page.write_text(build_html(rows), encoding="utf-8")
    print(f"\nTổng {len(rows)} dòng: {dict(Counter(x['loai'] for x in rows))} -> {out.relative_to(ROOT)}, {page.name}")


NAMES = {"tuong": "Tường", "loai_bo": "Cặp nét bị loại", "cua": "Cửa", "door": "Cửa đi", "window": "Cửa sổ"}
HEAD = [("ma", "Mã"), ("layer", "Layer"), ("lop_day", "Lớp dày"), ("day_mm", "Dày đo (mm)"), ("dai_m", "Dài (m)"),
        ("rong_mm", "Rộng (mm)"), ("cao_mm", "Cao (mm)"), ("vai_tro", "Vai trò"), ("vat_lieu", "Vật liệu"),
        ("phuong_an_tuong", "Phương án tường"), ("do_tin_cay", "Tin cậy"), ("ghi_chu", "Ghi chú, lý do")]


def _svg(items: list[dict], key: str) -> str:
    """Sơ đồ mặt bằng theo tọa độ bản vẽ (mm): tường đậm theo chiều dày, cặp nét bị loại nét đứt, block là chấm."""
    xs = [r[k] for r in items for k in ("x1", "x2") if r.get(k) is not None]
    ys = [r[k] for r in items for k in ("y1", "y2") if r.get(k) is not None]
    if not xs:
        return ""
    pad = 1000
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    out = []
    for i, r in enumerate(items):
        rid = f'id="{key}-{i}"'
        if r.get("x2") is not None:
            cls = "w" if r["loai"] == "tuong" else "rj"
            sw = r.get("day_mm") or 150
            out.append(f'<line {rid} class="{cls}" x1="{r["x1"]}" y1="{-r["y1"]}" x2="{r["x2"]}" y2="{-r["y2"]}" '
                       f'stroke-width="{sw}"><title>{escape(str(r.get("ma") or NAMES.get(r["loai"], r["loai"])))}</title></line>')
        else:
            out.append(f'<circle {rid} class="pt" cx="{r["x1"]}" cy="{-r["y1"]}" r="250">'
                       f'<title>{escape(r["loai"])} {escape(str(r.get("ma") or ""))}</title></circle>')
    return (f'<svg viewBox="{x0} {-y1} {x1 - x0} {y1 - y0}" preserveAspectRatio="xMidYMid meet" role="img" '
            f'aria-label="Sơ đồ đối tượng">{"".join(out)}</svg>')


def build_html(rows: list[dict]) -> str:
    """Trang tự chứa: tổng hợp, rồi từng bản vẽ / mặt bằng có sơ đồ và bảng đối tượng; ô lọc theo chữ và theo loại."""
    total = Counter(NAMES.get(r["loai"], r["loai"]) for r in rows)
    chips = "".join(f"<span class=chip><b>{n}</b> {escape(k)}</span>" for k, n in total.most_common())
    kinds = "".join(f"<option>{escape(k)}</option>" for k in sorted(total))
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        groups.setdefault((r["ban_ve"], r["mat_bang"]), []).append(r)
    sections = []
    for g, ((file, plan), items) in enumerate(groups.items()):
        cnt = ", ".join(f"{n} {escape(k).lower()}" for k, n in Counter(NAMES.get(r["loai"], r["loai"]) for r in items).most_common())
        body = []
        for i, r in enumerate(items):
            kind = NAMES.get(r["loai"], r["loai"])
            cells = "".join(f"<td>{escape(str(r[c])) if r.get(c) not in (None, '') else ''}</td>" for c, _ in HEAD)
            body.append(f'<tr data-ref="p{g}-{i}" data-kind="{escape(kind)}"><td>{escape(kind)}</td>{cells}</tr>')
        sections.append(f'<section><h2>{escape(plan)} <small>{escape(file)}</small></h2><p class=muted>{cnt}</p>'
                        f'<div class=plan>{_svg(items, f"p{g}")}</div><div class=tw><table><thead><tr><th>Loại</th>'
                        + "".join(f"<th>{h}</th>" for _, h in HEAD) + f'</tr></thead><tbody>{"".join(body)}</tbody></table></div></section>')
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Đối tượng nhận diện</title><style>
:root{{--bg:#fafaf9;--fg:#1c1917;--mut:#78716c;--line:#e7e5e4;--card:#fff;--wall:#2563eb;--rej:#dc2626;--pt:#16a34a;--hi:#f59e0b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1c1917;--fg:#f5f5f4;--mut:#a8a29e;--line:#44403c;--card:#292524;--wall:#60a5fa;--rej:#f87171;--pt:#4ade80}}}}
body{{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}}
main{{max-width:1200px;margin:auto}} h1{{margin:0 0 4px}} h2{{margin:0;font-size:17px}} h2 small,.muted{{color:var(--mut);font-weight:400}}
.chip{{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:2px 10px;margin:2px;background:var(--card)}}
.bar{{position:sticky;top:0;background:var(--bg);padding:8px 0;display:flex;gap:8px;flex-wrap:wrap;z-index:1}}
input,select{{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}}
section{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:14px 0}}
.plan svg{{width:100%;max-height:420px;background:var(--bg);border-radius:6px}}
.w{{stroke:var(--wall);stroke-linecap:square}} .rj{{stroke:var(--rej);stroke-dasharray:300 200;opacity:.7}} .pt{{fill:var(--pt)}}
.hi{{stroke:var(--hi)!important;fill:var(--hi)!important;opacity:1}}
.tw{{overflow-x:auto;margin-top:10px}} table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{text-align:left;padding:4px 8px;border-bottom:1px solid var(--line);white-space:nowrap}} th{{color:var(--mut);font-weight:600}}
tr:hover td{{background:color-mix(in srgb,var(--hi) 18%,transparent)}}
.legend span::before{{content:"";display:inline-block;width:14px;height:4px;margin:0 4px 2px 10px;vertical-align:middle}}
.lw::before{{background:var(--wall)}} .lr::before{{background:var(--rej)}} .lp::before{{background:var(--pt);height:10px!important;width:10px!important;border-radius:50%}}
</style></head><body><main><h1>Đối tượng nhận diện từ bản vẽ</h1>
<p class=muted>{len(rows)} đối tượng, {len(groups)} mặt bằng. Sinh bởi scripts/list_objects.py; ký hiệu theo data/rules/concepts.csv.</p>
<p>{chips}</p><p class="muted legend"><span class=lw>tường</span><span class=lr>cặp nét bị loại</span><span class=lp>block (cột, cao độ, nội thất...)</span> · rê chuột lên dòng để thấy vị trí</p>
<div class=bar><input id=q type=search placeholder="Lọc: mã, layer, ghi chú..." aria-label="Lọc"><select id=k aria-label="Loại"><option value="">Mọi loại</option>{kinds}</select></div>
{"".join(sections)}</main><script>
const q=document.getElementById('q'),k=document.getElementById('k');
function f(){{const t=q.value.toLowerCase(),v=k.value;document.querySelectorAll('tbody tr').forEach(r=>{{r.hidden=!(r.textContent.toLowerCase().includes(t)&&(!v||r.dataset.kind===v))}})}}
q.oninput=k.onchange=f;
document.querySelectorAll('tbody tr').forEach(r=>{{const s=document.getElementById(r.dataset.ref);if(!s)return;
r.onmouseenter=()=>s.classList.add('hi');r.onmouseleave=()=>s.classList.remove('hi')}});
</script></body></html>"""


if __name__ == "__main__":
    main()
