"use client";
import { useRef, useState, type ReactNode } from "react";
import { api, post } from "@/lib/api";
import { Card } from "@/components/ui";

// Dữ liệu Registry của /api/mapping/view (src/optimat/drawing/registry.py).
type Ev = { file: string; layout: string; handle?: string | null; rule: string; text?: string };
type Comp = {
  id: string; kind: string; name: string; rules: string[]; confidence: string; needs_confirmation: boolean; status: string;
  occurrences: { view: string; floors: string[]; x_mm: number; y_mm: number; axis?: string | null; evidence: Ev }[];
  details: Ev[]; size_sources: { source: string }[]; size: Record<string, number | null>;
};
type Registry = {
  files: string[]; sheets: { ma: string; loai_ban_ve: string; co: boolean; tieu_de: string[] }[];
  views: { sheet_type: string; title: string; floors: string[]; scale?: number | null; evidence: Ev }[];
  floors: { key: string; names: string[]; elevation_m?: number | null; views: string[] }[];
  layers: { file: string; layer: string; role: string; rule?: string | null }[];
  components: Comp[]; issues: { kind: string; message: string; evidence: Ev[] }[];
  unmatched: { kind: string; text: string; evidence?: Ev | null }[]; confidence_rules: { ma: string; mo_ta: string }[];
};
type Decision = { status: string; size: Record<string, number> };

const LEVEL: Record<string, string> = { cao: "Cao", trung_binh: "Trung bình", thap: "Thấp" };
const STATUS: Record<string, string> = { tu_dong: "Chờ", xac_nhan: "Xác nhận", loai_bo: "Loại bỏ" };
// màu dòng theo độ tin cậy / quyết định
const ROW: Record<string, string> = { thap: "bg-bad-bg", trung_binh: "bg-warn-bg", xac_nhan: "bg-accent-soft", loai_bo: "opacity-45 line-through" };
const TABS = { components: "Cấu kiện", issues: "Xung đột, thiếu", unmatched: "Chưa khớp", layers: "Layer", views: "Loại bản vẽ", floors: "Tầng" };
type Tab = keyof typeof TABS;

const Small = ({ children }: { children: ReactNode }) => <span className="text-xs text-muted">{children}</span>;
const EvRef = ({ e }: { e?: Ev | null }) => (e ? <Small>{e.file} · {e.layout} · handle {e.handle ?? "—"} · {e.rule}</Small> : null);
const Lines = ({ items }: { items: ReactNode[] }) => <>{items.map((x, i) => <div key={i}>{x}</div>)}</>;

function Table({ head, children }: { head: string[]; children: ReactNode }) {
  return <div className="tw"><table><thead><tr>{head.map((h) => <th key={h}>{h}</th>)}</tr></thead><tbody>{children}</tbody></table></div>;
}

export function Mapping() {
  const files = useRef<HTMLInputElement>(null);
  const [reg, setReg] = useState<Registry | null>(null);
  const [ver, setVer] = useState(0); // đổi key để ô nhập thông số (không điều khiển) nạp lại giá trị mới
  const [tab, setTab] = useState<Tab>("components");
  const [only, setOnly] = useState(false);
  const [msg, setMsg] = useState("");
  const [layerOv, setLayerOv] = useState<Record<string, Record<string, string>>>({});
  const [symbolOv, setSymbolOv] = useState<Record<string, string>>({});
  const [decisions, setDecisions] = useState<Record<string, Decision>>({});

  async function run(p: Promise<Registry>, done = "") {
    setMsg("Đang xử lý…");
    try { setReg(await p); setVer((v) => v + 1); setMsg(done); return true; } catch (e) { setMsg("Lỗi: " + (e as Error).message); return false; }
  }
  function read() {
    const list = files.current?.files;
    if (!list?.length) return setMsg("Chưa chọn bản vẽ.");
    const fd = new FormData();
    for (const f of list) fd.append("files", f);
    fd.append("layer_overrides", JSON.stringify(layerOv));
    fd.append("symbol_overrides", JSON.stringify(symbolOv));
    run(api<Registry>("/api/mapping/view", { method: "POST", body: fd }));
  }
  async function confirm() {
    if (await run(post<Registry>("/api/mapping/confirm", { registry: reg, decisions }), "Đã xác nhận.")) setDecisions({});
  }
  function download() {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(reg, null, 2)], { type: "application/json" }));
    a.download = "ho_so_chuan_hoa.json";
    a.click();
  }
  const decide = (id: string, f: (d: Decision) => void) =>
    setDecisions((all) => { const d = structuredClone(all[id] ?? { status: "xac_nhan", size: {} }); f(d); return { ...all, [id]: d }; });

  const views: Record<Tab, () => ReactNode> = {
    components: () => (
      <Table head={["Ký hiệu", "Trên mặt bằng", "Chi tiết", "Thông số (mm)", "Tin cậy", "Nguồn", "Quyết định"]}>
        {reg!.components.filter((c) => !only || c.needs_confirmation).map((c) => {
          const occ = c.occurrences;
          return (
            <tr key={c.id} className={ROW[c.status === "tu_dong" ? c.confidence : c.status]}>
              <td><b>{c.name}</b><br /><Small>{c.kind}</Small></td>
              <td>{occ.length} lần<br /><Small>{[...new Set(occ.flatMap((o) => o.floors))].join(", ")}</Small></td>
              <td>{c.details.length ? <Lines items={c.details.slice(0, 3).map((d) => d.text)} /> : <i>không có</i>}</td>
              <td>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(c.size).map(([k, v]) => (
                    <label key={k} className="whitespace-nowrap">{k.replace("_mm", "")}{" "}
                      <input type="number" min={1} defaultValue={decisions[c.id]?.size[k] ?? v ?? ""} title={v == null ? "Thiếu: nhập tay, hệ thống không tự điền" : ""}
                        className={`w-[70px] rounded border bg-card px-1 ${v == null ? "border-bad-ink outline-2 outline-bad-ink" : "border-field"}`}
                        onChange={(e) => { const t = e.target.value; decide(c.id, (d) => { if (t) d.size[k] = Number(t); else delete d.size[k]; }); }} />
                    </label>
                  ))}
                </div>
                <Small>{c.size_sources.map((s) => s.source).join(", ")}</Small>
              </td>
              <td>{LEVEL[c.confidence]} {c.needs_confirmation ? "⚠" : ""}<br />
                {c.rules.map((r) => <abbr key={r} className="mr-1" title={reg!.confidence_rules.find((x) => x.ma === r)?.mo_ta}>{r}</abbr>)}</td>
              <td>{occ.length ? <Lines items={occ.slice(0, 2).map((o) => <>{o.view} ({o.x_mm}, {o.y_mm}){o.axis ? " trục " + o.axis : ""}<br /><EvRef e={o.evidence} /></>)} />
                : <EvRef e={c.details[0]} />}</td>
              <td>
                <select className="rounded border border-field bg-card px-1" aria-label={`Quyết định ${c.name}`} value={decisions[c.id]?.status ?? c.status}
                  onChange={(e) => { const s = e.target.value; decide(c.id, (d) => { d.status = s; }); }}>
                  {Object.entries(STATUS).map(([s, t]) => <option key={s} value={s}>{t}</option>)}
                </select>
              </td>
            </tr>
          );
        })}
      </Table>
    ),
    issues: () => (
      <Table head={["Loại", "Nội dung", "Bằng chứng"]}>
        {reg!.issues.map((i, n) => <tr key={n}><td>{i.kind}</td><td>{i.message}</td><td><Lines items={i.evidence.slice(0, 3).map((e, j) => <EvRef key={j} e={e} />)} /></td></tr>)}
      </Table>
    ),
    unmatched: () => (
      <>
        <Small>Ký hiệu chưa có quy tắc: gán vai trò rồi bấm &quot;Đọc hồ sơ&quot; để đọc lại. Quy tắc lâu dài: data/rules/ky_hieu_cau_kien.csv.</Small>
        <Table head={["Loại", "Nội dung", "Bằng chứng", "Gán"]}>
          {reg!.unmatched.map((u, n) => (
            <tr key={n}><td>{u.kind}</td><td>{u.text}</td><td><EvRef e={u.evidence} /></td>
              <td>{u.kind === "ky_hieu" && (
                <select className="rounded border border-field bg-card px-1" aria-label={`Gán ${u.text}`} value={symbolOv[u.text] ?? ""}
                  onChange={(e) => { const v = e.target.value; setSymbolOv((o) => { const x = { ...o }; if (v) x[u.text] = v; else delete x[u.text]; return x; }); }}>
                  <option value="">—</option>{["BEAM", "COLUMN", "FOUNDATION"].map((r) => <option key={r}>{r}</option>)}
                </select>)}</td></tr>
          ))}
        </Table>
      </>
    ),
    layers: () => (
      <>
        <Small>Đổi vai trò layer rồi bấm &quot;Đọc hồ sơ&quot;. Quy tắc lâu dài: data/rules/concepts.csv (trang /co-so-du-lieu).</Small>
        <Table head={["File", "Layer", "Quy tắc", "Vai trò"]}>
          {reg!.layers.map((l) => (
            <tr key={l.file + "\0" + l.layer} className={l.role === "UNKNOWN" ? ROW.thap : ""}><td>{l.file}</td><td>{l.layer}</td><td>{l.rule ?? "chưa có"}</td>
              <td><select className="rounded border border-field bg-card px-1" aria-label={`Vai trò ${l.layer}`} value={layerOv[l.file]?.[l.layer] ?? l.role}
                onChange={(e) => { const v = e.target.value; setLayerOv((o) => ({ ...o, [l.file]: { ...o[l.file], [l.layer]: v } })); }}>
                {["WALL", "OPENING", "ANNOTATION", "IGNORE", "UNKNOWN"].map((r) => <option key={r}>{r}</option>)}
              </select></td></tr>
          ))}
        </Table>
      </>
    ),
    views: () => (
      <>
        <h3 className="m-0 text-[15px] font-bold">Loại bản vẽ</h3>
        <Table head={["Mã", "Loại", "Tiêu đề tìm thấy"]}>
          {reg!.sheets.map((s) => <tr key={s.ma} className={s.co ? "" : ROW.trung_binh}><td>{s.ma}</td><td>{s.loai_ban_ve}</td><td>{s.co ? <Lines items={s.tieu_de} /> : <i>chưa có</i>}</td></tr>)}
        </Table>
        <h3 className="m-0 text-[15px] font-bold">Hình vẽ</h3>
        <Table head={["Loại", "Tiêu đề", "Tầng", "Tỷ lệ", "Nguồn"]}>
          {reg!.views.map((v, n) => <tr key={n}><td>{v.sheet_type}</td><td>{v.title}</td><td>{v.floors.join(", ")}</td><td>{v.scale ?? "—"}</td><td><EvRef e={v.evidence} /></td></tr>)}
        </Table>
      </>
    ),
    floors: () => (
      <Table head={["Tầng", "Mặt bằng kiến trúc", "Cao độ (m)", "Hình vẽ"]}>
        {reg!.floors.map((f) => <tr key={f.key}><td>{f.key}</td><td><Lines items={f.names} /></td><td>{f.elevation_m ?? "—"}</td><td><Lines items={f.views} /></td></tr>)}
      </Table>
    ),
  };

  const wait = reg?.components.filter((c) => c.needs_confirmation).length ?? 0;
  return (
    <>
      <Card>
        <div className="flex flex-wrap items-center gap-2">
          <input ref={files} type="file" accept=".dxf,.dwg" multiple aria-label="Bản vẽ" />
          <button className="btn primary" type="button" onClick={read}>Đọc hồ sơ</button>
          <button className="btn" type="button" disabled={!reg} onClick={confirm}>Lưu xác nhận</button>
          <button className="btn" type="button" disabled={!reg} onClick={download}>Tải JSON</button>
          <span className="ml-auto text-muted" role="status">{msg}</span>
        </div>
        <div className="text-muted">
          {reg ? `${reg.files.join(", ")}: ${reg.components.length} cấu kiện, ${wait} chờ xác nhận, ${reg.issues.length} xung đột/thiếu, ${reg.unmatched.length} chưa khớp.`
            : 'Chọn một hay nhiều bản vẽ (kiến trúc, kết cấu) cùng hồ sơ rồi bấm "Đọc hồ sơ".'}
        </div>
      </Card>
      {reg && (
        <Card>
          <nav className="flex flex-wrap gap-1.5" role="tablist">
            {(Object.entries(TABS) as [Tab, string][]).map(([k, t]) => {
              const n = k === "issues" ? reg.issues.length : k === "unmatched" ? reg.unmatched.length : 0;
              return <button key={k} type="button" role="tab" aria-selected={k === tab} onClick={() => setTab(k)}
                className={`btn min-h-9 ${k === tab ? "border-accent text-accent" : "border-rule"}`}>{t}{n ? ` (${n})` : ""}</button>;
            })}
          </nav>
          {tab === "components" && <label className="flex items-center gap-1.5"><input type="checkbox" checked={only} onChange={(e) => setOnly(e.target.checked)} /> Chỉ cấu kiện chờ xác nhận</label>}
          <div key={ver} className="flex flex-col gap-3">{views[tab]()}</div>
        </Card>
      )}
    </>
  );
}
