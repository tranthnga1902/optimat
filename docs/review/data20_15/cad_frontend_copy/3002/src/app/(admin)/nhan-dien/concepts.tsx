"use client";
import { Fragment, useEffect, useRef, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import { Card, Field, Loading, Note, Pill, Tile, Tiles } from "@/components/ui";
import css from "./concepts.module.css";

type Sig = { ma: string; khai_niem: string; tin_hieu: string; mau: string; vai_tro: string; qu: string; rong_mm?: number | null; cao_mm?: number | null; ghi_chu?: string | null };
type Data = {
  signals: Sig[]; conflicts?: Record<string, string>; rough_roles?: string[]; editable: boolean; source: string;
  clauses: { ma: string; nhom: string }[]; layer_roles: string[]; block_roles: string[]; images?: Record<string, string>;
};
type Samples = Record<string, { matches: string[]; svg: string | null }>;
type Obj = Record<string, string | number | null | undefined>;
type Form = Record<"ma" | "khai_niem" | "tin_hieu" | "mau" | "vai_tro" | "qu" | "rong_mm" | "cao_mm" | "ghi_chu", string>;

// hình minh họa ký hiệu layer theo vai trò (layer không có hình riêng như block)
const GLYPH: Record<string, ReactNode> = {
  WALL: <><path d="M5 22H95M5 38H95" /><path d="M12 38l16-16M26 38l16-16M40 38l16-16M54 38l16-16M68 38l16-16M82 38l13-13" opacity=".5" /></>,
  OPENING: <><path d="M5 50H30M70 50H95M5 56H30M70 56H95" /><path d="M30 50V12" /><path d="M30 12A38 38 0 0 1 68 50" strokeDasharray="3 3" /></>,
  ANNOTATION: <><path d="M10 40H90M10 32V48M90 32V48M6 44l8-8M86 44l8-8" /><text x="50" y="28" fontSize="12" textAnchor="middle" fill="currentColor" stroke="none">1200</text></>,
  IGNORE: <><rect x="25" y="10" width="50" height="40" rx="4" strokeDasharray="4 3" /><path d="M33 18l34 24M67 18L33 42" opacity=".6" /></>,
  COLUMN: <><path d="M5 22H38M62 22H95M5 38H38M62 38H95" /><rect x="38" y="18" width="24" height="24" fill="currentColor" fillOpacity=".35" /></>,
  BEAM: <><rect x="8" y="16" width="14" height="14" fill="currentColor" fillOpacity=".35" /><rect x="78" y="16" width="14" height="14" fill="currentColor" fillOpacity=".35" /><path d="M22 19H78M22 27H78" strokeDasharray="6 3" /></>,
  SLAB: <><rect x="10" y="10" width="80" height="40" /><path d="M10 10l80 40M90 10L10 50" opacity=".5" /></>,
  STAIR: <><rect x="10" y="10" width="80" height="40" /><path d="M22 10V50M34 10V50M46 10V50M58 10V50M70 10V50" /><path d="M16 30H84M78 25l6 5-6 5" /></>,
  LINTEL: <><path d="M5 50H30M70 50H95M30 50V20M70 50V20" /><rect x="22" y="12" width="56" height="8" fill="currentColor" fillOpacity=".35" /></>,
  FOUNDATION: <><path d="M42 5V30M58 5V30" /><path d="M20 30H80V44H20Z" fill="currentColor" fillOpacity=".35" /><path d="M12 52H88" strokeDasharray="4 3" /></>,
};
const ROLE_VI: Record<string, string> = { WALL: "tường", OPENING: "cửa", door: "cửa đi", window: "cửa sổ", ANNOTATION: "ghi chú", IGNORE: "bỏ qua",
  COLUMN: "cột", BEAM: "dầm", SLAB: "sàn", STAIR: "cầu thang", LINTEL: "lanh tô", FOUNDATION: "móng" };
const OBJ_NAME: Record<string, string> = { tuong: "Tường", loai_bo: "Cặp nét bị loại", cua: "Cửa", door: "Cửa đi", window: "Cửa sổ" };
const FIELDS = ["ma", "khai_niem", "tin_hieu", "mau", "vai_tro", "qu", "rong_mm", "cao_mm", "ghi_chu"] as const;

// khóa thẻ = khái niệm (bỏ dấu) + vai trò; trùng tên file hình trong data/rules/hinh_ky_hieu
const objKey = (s: Sig) => (s.khai_niem.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[đĐ]/g, "d").toLowerCase()
  .replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") + "-" + s.vai_tro.toLowerCase()).slice(0, 80);
const s2 = (v: unknown) => (v == null ? "" : String(v));

/** Sửa xong thì đọc lại toàn bộ trang như bản cũ (viewConcepts lại từ đầu): đổi key để dựng lại. */
export function Concepts() {
  const [n, setN] = useState(0);
  return <View key={n} reload={() => setN(n + 1)} />;
}

function View({ reload }: { reload: () => void }) {
  const [d, setD] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  const [samples, setSamples] = useState<Samples | null>(null);
  const [smsg, setSmsg] = useState("Đang đọc bản vẽ mẫu trong data/drawings để vẽ hình ký hiệu (lần đầu ~20 s)…");
  const [f, setF] = useState({ g: "tho", t: "", k: "", m: "", q: "" });
  const [form, setForm] = useState<Form | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [fmsg, setFmsg] = useState<ReactNode>("");


  useEffect(() => {
    api<Data>("/api/concepts").then((r) => {
      setD(r);
      if (r.editable) setForm(blank(r, "layer"));
      api<Samples>("/api/concepts/samples").then((x) => { setSamples(x); setSmsg("Hình block vẽ lại từ block đầu tiên khớp trong data/drawings/thu_vien, data/drawings/build; layer là hình minh họa theo vai trò."); })
        .catch((e) => { setSamples({}); setSmsg(`Không đọc được bản vẽ mẫu: ${e.message}`); });
    }, (e) => setErr(e.message));
  }, []);

  if (err) return <Note>{err}</Note>;
  if (!d) return <Loading />;
  const sig = d.signals, nLayer = sig.filter((s) => s.tin_hieu === "layer").length, bad = d.conflicts || {}, nBad = Object.keys(bad).length;
  // nhóm phần thô: tường, cửa (trừ lỗ mở) và bộ phận bê tông; còn lại là ghi chú hoặc bỏ qua khi bóc
  const group = (s: Sig) => ["WALL", "OPENING", "door", "window", ...(d.rough_roles || [])].includes(s.vai_tro) ? "tho" : s.vai_tro === "ANNOTATION" ? "ghi" : "bo";
  const sampleOf = (s: Sig) => (samples && samples[s.ma]) || { matches: [], svg: null };
  const roles = (t: string) => (t === "layer" ? d.layer_roles : d.block_roles);

  const fill = (s: Partial<Sig> | null) => {
    setEditing(s && sig.some((x) => x.ma === s.ma) ? s.ma! : null);
    const v = blank(d, s?.tin_hieu || "layer");
    for (const [k, x] of Object.entries(s || {})) if ((FIELDS as readonly string[]).includes(k) && k !== "tin_hieu") v[k as keyof Form] = s2(x);
    setForm(v); setFmsg("");
    document.getElementById("cf")?.scrollIntoView({ block: "center" });
  };
  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    const body: Record<string, unknown> = { ...form };
    for (const k of ["rong_mm", "cao_mm"]) body[k] = body[k] === "" ? null : +(body[k] as string);
    try {
      await api(editing ? `/api/concepts/${encodeURIComponent(editing)}` : "/api/concepts",
        { method: editing ? "PUT" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      reload();
    } catch (err) { setFmsg(<Pill level="bad">{(err as Error).message}</Pill>); }
  };
  const del = async (ma: string) => {
    if (!confirm(`Xóa mẫu tên "${sig.find((s) => s.ma === ma)?.mau}" (${ma})? Bản vẽ đọc sau sẽ không còn nhận theo mẫu này.`)) return;
    try { await api(`/api/concepts/${encodeURIComponent(ma)}`, { method: "DELETE" }); reload(); } catch (err) { alert((err as Error).message); }
  };

  const q = f.q.trim().toLowerCase();
  const list = sig.filter((s) => (!f.g || group(s) === f.g) && (!f.t || s.tin_hieu === f.t) && (!f.k || s.khai_niem === f.k)
    && (!f.m || !samples || String(+(sampleOf(s).matches.length > 0)) === f.m)
    && (!q || [s.ma, s.khai_niem, s.mau, s.ghi_chu, ...sampleOf(s).matches].join(" ").toLowerCase().includes(q)));
  // một thẻ cho mỗi đối tượng (khái niệm + vai trò): các mẫu tên layer/block của nó là nút trong thẻ, giữ thứ tự ưu tiên
  const objs = new Map<string, Sig[]>();
  for (const s of list) { const key = s.khai_niem + "|" + s.vai_tro; if (!objs.has(key)) objs.set(key, []); objs.get(key)!.push(s); }
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });
  const setFld = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form!, [k]: e.target.value, ...(k === "tin_hieu" ? { vai_tro: roles(e.target.value)[0] || "" } : {}) });

  return (
    <div>
      {d.editable
        ? <Note className="mb-3.5">Đang sửa trực tiếp trong PostgreSQL. Lệnh <code>python scripts/init_db.py --reload-rules</code> nạp lại từ <code>data/rules/concepts.csv</code> và xóa các sửa đổi ở đây: tải concepts.csv, chép đè file đó trước khi nạp lại.</Note>
        : <Note className="mb-3.5">Chưa kết nối PostgreSQL (DATABASE_URL), đang đọc <code>data/rules/concepts.csv</code>: chỉ xem được. Đặt DATABASE_URL rồi chạy <code>python scripts/init_db.py --reload-rules</code> để quản lý tại đây.</Note>}
      <Tiles>
        <Tile k="Ký hiệu layer" v={nLayer} s="tên layer → vai trò" />
        <Tile k="Ký hiệu block" v={sig.length - nLayer} s="tiền tố tên block → đối tượng" />
        <Tile tone={nBad ? "bad" : "ok"} k="Phần thô" v={sig.filter((s) => group(s) === "tho").length} s={nBad ? `${nBad} ký hiệu trùng` : "không có ký hiệu trùng"} />
        <Tile k="Khái niệm" v={new Set(sig.map((s) => s.khai_niem)).size} s={`nguồn: ${d.source}`} />
      </Tiles>
      {d.editable && form && (
        <Card title={editing ? `Sửa ký hiệu ${editing}` : "Thêm ký hiệu"}>
          <form id="cf" onSubmit={save} className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(170px,1fr))]">
            <Field label="Mã"><input className="field" value={form.ma} onChange={setFld("ma")} required maxLength={16} pattern="[A-Za-z0-9_\-]+" placeholder="L36, B22" /></Field>
            <Field label="Khái niệm"><input className="field" value={form.khai_niem} onChange={setFld("khai_niem")} required maxLength={64} placeholder="Cột, Cầu thang…" /></Field>
            <Field label="Tín hiệu"><select className="field" value={form.tin_hieu} onChange={setFld("tin_hieu")}><option>layer</option><option>block</option></select></Field>
            <Field label="Mẫu"><input className="field" value={form.mau} onChange={setFld("mau")} required maxLength={128} placeholder="layer: chuỗi con; block: tiền tố" /></Field>
            <Field label="Vai trò"><select className="field" value={form.vai_tro} onChange={setFld("vai_tro")}>{roles(form.tin_hieu).map((r) => <option key={r}>{r}</option>)}</select></Field>
            <Field label="Điều khoản"><select className="field" value={form.qu} onChange={setFld("qu")}>{d.clauses.map((c) => <option key={c.ma} value={c.ma}>{c.ma} · {c.nhom}</option>)}</select></Field>
            <Field label="Rộng mm"><input className="field" value={form.rong_mm} onChange={setFld("rong_mm")} type="number" min="1" step="any" /></Field>
            <Field label="Cao mm"><input className="field" value={form.cao_mm} onChange={setFld("cao_mm")} type="number" min="1" step="any" /></Field>
            <div className="[grid-column:1/-1]"><Field label="Ghi chú"><input className="field" value={form.ghi_chu} onChange={setFld("ghi_chu")} /></Field></div>
            <div className="flex flex-wrap items-center gap-2">
              <button className="btn primary" type="submit">Lưu</button><button className="btn" type="button" onClick={() => fill(null)}>Hủy</button>
              <span className="text-[12.5px]" role="status">{fmsg}</span>
            </div>
          </form>
        </Card>
      )}
      <Card>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="m-0 mr-auto text-base font-bold">{sig.length} ký hiệu</h2>
          <label>Nhóm <select className="field" value={f.g} onChange={set("g")}><option value="tho">phần thô</option><option value="ghi">ghi chú</option><option value="bo">bỏ qua khi bóc</option><option value="">tất cả</option></select></label>
          <label>Tín hiệu <select className="field" value={f.t} onChange={set("t")}><option value="">tất cả</option><option>layer</option><option>block</option></select></label>
          <label>Khái niệm <select className="field" value={f.k} onChange={set("k")}><option value="">tất cả</option>{[...new Set(sig.map((s) => s.khai_niem))].sort().map((v) => <option key={v}>{v}</option>)}</select></label>
          <label>Bản vẽ mẫu <select className="field" value={f.m} onChange={set("m")}><option value="">tất cả</option><option value="1">có khớp</option><option value="0">chưa khớp</option></select></label>
          <label>Tìm <input className="field" value={f.q} onChange={set("q")} type="search" placeholder="mã, khái niệm, mẫu, tên layer/block" /></label>
          <span className="text-[12.5px] text-muted">{objs.size} đối tượng · {list.length} mẫu tên</span>
        </div>
        <p className="my-[1em] text-[12.5px] text-muted">{smsg}</p>
        <div className={css.symgrid}>
          {objs.size ? [...objs.values()].map((ss) => (
            <Sym key={objKey(ss[0])} ss={ss} d={d} bad={bad} samples={samples} sampleOf={sampleOf} level={group(ss[0]) === "tho" ? "ok" : group(ss[0]) === "ghi" ? "info" : "bad"}
              reload={reload} onEdit={(ma) => fill(sig.find((s) => s.ma === ma)!)} onDel={del}
              onCopy={(ma) => fill({ ...sig.find((s) => s.ma === ma), ma: "", mau: "", ghi_chu: "" })} />
          )) : <p className="my-[1em] text-muted">Không có ký hiệu nào.</p>}
        </div>
      </Card>
      <TryDrawing editable={d.editable} onLayer={(l, file) => fill({ tin_hieu: "layer", mau: l, qu: "QU-08", ghi_chu: `layer ${l} (${file})` })} />
    </div>
  );
}

function blank(d: Data, tin_hieu: string): Form {
  return { ma: "", khai_niem: "", tin_hieu, mau: "", vai_tro: (tin_hieu === "layer" ? d.layer_roles : d.block_roles)[0] || "",
    qu: d.clauses[0]?.ma || "", rong_mm: "", cao_mm: "", ghi_chu: "" };
}

type SymProps = {
  ss: Sig[]; d: Data; bad: Record<string, string>; samples: Samples | null; sampleOf: (s: Sig) => { matches: string[]; svg: string | null };
  level: "ok" | "info" | "bad"; reload: () => void; onEdit: (ma: string) => void; onDel: (ma: string) => void; onCopy: (ma: string) => void;
};

function Sym({ ss, d, bad, samples, sampleOf, level, reload, onEdit, onDel, onCopy }: SymProps) {
  const [open, setOpen] = useState(false);
  const [msg, setMsg] = useState("");
  const [blk, setBlk] = useState("");
  const s0 = ss[0], key = objKey(s0), img = (d.images || {})[key];
  // hình tự động: block của thư viện mẫu trước, rồi block bản vẽ thật, không có block thì hình minh họa vai trò
  const blocks = ss.filter((s) => s.tin_hieu === "block" && sampleOf(s).svg);
  const withPic = blocks.find((s) => sampleOf(s).matches[0].includes("thu_vien")) || blocks[0] || ss.find((s) => s.tin_hieu === "layer") || s0;
  const choices = [...new Set(ss.filter((s) => s.tin_hieu === "block").flatMap((s) => sampleOf(s).matches))];
  const matches = ss.flatMap((s) => sampleOf(s).matches), sizes = ss.filter((s) => s.rong_mm || s.cao_mm);
  const kinds = (["layer", "block"] as const).map((tk) => [tk, ss.filter((s) => s.tin_hieu === tk)] as const).filter(([, x]) => x.length);
  const blockSvg = !img && withPic.tin_hieu !== "layer" ? sampleOf(withPic).svg : null;
  const done = (p: Promise<unknown>) => p.then(reload, (e) => setMsg(e.message));

  const chip = (s: Sig) => (
    <span className={`${css.chip}${bad[s.ma] ? " " + css.bad : ""}`} title={s.ma + (s.ghi_chu ? " · " + s.ghi_chu : "") + (bad[s.ma] ? " · Trùng: " + bad[s.ma] : "")}>
      {d.editable ? <><button type="button" onClick={() => onEdit(s.ma)}>{s.mau}</button><button type="button" className={css.del} onClick={() => onDel(s.ma)} aria-label={`Xóa ${s.ma}`}>✕</button></> : s.mau}
    </span>
  );

  return (
    <article className={css.sym}>
      {/* SVG block do API của chính hệ thống vẽ lại từ bản vẽ mẫu (/api/concepts/samples) */}
      <div className={css.symimg} title={img ? "Hình đã đặt" : withPic.tin_hieu === "layer" ? "Hình minh họa vai trò " + (ROLE_VI[s0.vai_tro] || s0.vai_tro) : sampleOf(withPic).matches[0] || ""}
        {...(blockSvg ? { dangerouslySetInnerHTML: { __html: blockSvg } } : {})}>
        {/* eslint-disable-next-line @next/next/no-img-element -- hình tải lên do API phục vụ, kích thước tùy ý */}
        {blockSvg ? undefined : img ? <img src={img} alt={`Hình minh họa ${s0.khai_niem}`} />
          : withPic.tin_hieu === "layer" ? <svg viewBox="0 0 100 60" fill="none" stroke="currentColor">{GLYPH[withPic.vai_tro] || GLYPH.IGNORE}</svg>
          : <span className="text-[12.5px] text-muted">{samples ? "chưa thấy block này trong bản vẽ mẫu" : "đang tải hình…"}</span>}
      </div>
      <div className={css.symbody}>
        <div><b>{s0.khai_niem}</b> <Pill level={level}>{ROLE_VI[s0.vai_tro] || s0.vai_tro}</Pill> <span className="text-[12.5px] text-muted">{[...new Set(ss.map((s) => s.qu))].join(", ")}</span></div>
        {kinds.map(([tk, x]) => (
          <div key={tk} className="text-[12.5px]">{tk === "layer" ? "Tên layer chứa" : "Tên block"}: {x.map((s, i) => <Fragment key={s.ma}>{i > 0 && " "}{chip(s)}</Fragment>)}</div>
        ))}
        {sizes.length > 0 && <div className="text-[12.5px]">{sizes.map((s) => `${s.mau}: ${s.rong_mm ?? "?"}×${s.cao_mm ?? "?"} mm`).join(" · ")}</div>}
        <div className="text-[12.5px] text-muted">{samples ? (matches.length ? `Khớp ${matches.length} trong bản vẽ mẫu: ${matches.slice(0, 4).join(", ")}${matches.length > 4 ? "…" : ""}` : "Chưa khớp layer/block nào trong bản vẽ mẫu") : ""}</div>
        {ss.filter((s) => bad[s.ma]).map((s) => <div key={s.ma} className="rounded-md bg-bad-bg px-2 py-1.5 text-[12.5px] text-bad-ink">Trùng {s.ma}: {bad[s.ma]}</div>)}
        <div className="flex flex-wrap items-center gap-2">
          {d.editable && <button className="btn" type="button" onClick={() => onCopy(s0.ma)}>+ Mẫu tên</button>}
          <button className="btn" type="button" aria-expanded={open} onClick={() => setOpen(!open)}>Đổi hình</button>
        </div>
        {open && (
          <div className={css.picbox}>
            <label className="text-[12.5px]">Tải hình (SVG, PNG, JPG, WEBP, tối đa 2 MB) <input type="file" accept=".svg,.png,.jpg,.jpeg,.webp" onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const fd = new FormData(); fd.append("file", file);
              setMsg("Đang tải lên…");
              done(api(`/api/concepts/images/${key}`, { method: "PUT", body: fd }));
            }} /></label>
            {choices.length > 0 && <>
              <label className="text-[12.5px]">Hoặc dùng block trong bản vẽ mẫu <select className="field" value={blk || choices[0].replace(/ \([^)]*\)$/, "")} onChange={(e) => setBlk(e.target.value)}>
                {choices.map((m) => <option key={m} value={m.replace(/ \([^)]*\)$/, "")}>{m}</option>)}</select></label>
              <button className="btn" type="button" onClick={() => {
                setMsg("Đang lưu…");
                done(api(`/api/concepts/images/${key}/block`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ block: blk || choices[0].replace(/ \([^)]*\)$/, "") }) }));
              }}>Dùng block này</button>
            </>}
            {img && <button className="btn" type="button" onClick={() => { if (confirm("Bỏ hình đã đặt, dùng lại hình tự động?")) done(api(`/api/concepts/images/${key}`, { method: "DELETE" })); }}>Về hình tự động</button>}
            <span className="text-[12.5px]" role="status">{msg}</span>
          </div>
        )}
      </div>
    </article>
  );
}

type InventoryRow = { name: string; types: Record<string, number>; count: number; rule: string | null; pattern: string | null; role: string | null };

function TryDrawing({ editable, onLayer }: { editable: boolean; onLayer: (layer: string, file: string) => void }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [st, setSt] = useState<{ note?: string; busy?: string; r?: { rows: Obj[]; unknown_layers: string[]; layers?: InventoryRow[] }; file?: string }>({});
  const [layerQuery, setLayerQuery] = useState("");
  const [tk, setTk] = useState("");
  const run = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return setSt({ note: "Chọn file .dxf hoặc .dwg trước." });
    setSt({ busy: `Đang nhận diện ${file.name}…` }); setTk("");
    const fd = new FormData(); fd.append("file", file);
    try { setSt({ r: await api("/api/concepts/try", { method: "POST", body: fd }), file: file.name }); } catch (err) { setSt({ note: (err as Error).message }); }
  };
  const name = (o: Obj) => OBJ_NAME[String(o.loai)] || String(o.loai), count: Record<string, number> = {};
  st.r?.rows.forEach((o) => { count[name(o)] = (count[name(o)] || 0) + 1; });
  const rows = st.r?.rows.filter((o) => !tk || name(o) === tk) || [];

  return (
    <Card title="Thử trên bản vẽ">
      <p className="my-[1em] text-[12.5px] text-muted">Chạy nhận diện với bảng ký hiệu hiện hành, liệt kê từng đối tượng và các layer chưa có ký hiệu.</p>
      <div className="flex flex-wrap items-center gap-2"><input ref={fileRef} type="file" accept=".dxf,.dwg" aria-label="Chọn bản vẽ" /><button className="btn primary" type="button" disabled={!!st.busy} onClick={run}>Nhận diện</button></div>
      <div>
        {st.note && <Note>{st.note}</Note>}
        {st.busy && <p className="my-[1em] text-muted">{st.busy}</p>}
        {st.r && <>
          <h3>Danh mục layer của bản vẽ</h3>
          <p>Nguồn: {st.file}. Số lượng tính theo đối tượng trực tiếp trong Model Space, mỗi block chèn tính một lần.</p>
          <label>Tìm layer, kiểu đối tượng, quy tắc hoặc vai trò <input className="field" type="search" value={layerQuery} onChange={e=>setLayerQuery(e.target.value)} /></label>
          {st.r.layers ? <div className="tw"><table><thead><tr>{["Layer","Số đối tượng","Kiểu đối tượng","Quy tắc ưu tiên thắng","Vai trò",""].map(h=><th key={h}>{h}</th>)}</tr></thead>
            <tbody>{st.r.layers.filter(l=>[l.name,l.rule,l.pattern,l.role,...Object.keys(l.types),l.rule ? "đã khớp" : "chưa khớp"].join(" ").toLocaleLowerCase().includes(layerQuery.trim().toLocaleLowerCase())).map(l=><tr key={l.name}><td>{l.name}</td><td>{l.count}</td><td>{Object.entries(l.types).map(([k,n])=>k+" × "+n).join(", ") || "—"}</td><td>{l.rule ? l.rule+" · "+l.pattern : "Chưa khớp"}</td><td>{l.role || "—"}</td><td>{editable && <button type="button" className="btn" onClick={()=>onLayer(l.name,st.file!)}>Điền mẫu</button>}</td></tr>)}</tbody></table></div> : <Note>Máy chủ chưa trả danh mục layer.</Note>}
          <h3>Kết quả nhận diện theo ký hiệu</h3>
          <p className="my-[1em]">{Object.keys(count).length ? Object.entries(count).map(([k, v], i) => <Fragment key={k}>{i > 0 && " "}<Pill level="info">{`${v} ${k}`}</Pill></Fragment>)
            : <Pill level="warn">không nhận được đối tượng nào</Pill>}</p>
          {st.r.unknown_layers.length > 0 && <p className="my-[1em] text-[12.5px]"><b>{st.r.unknown_layers.length} layer chưa có ký hiệu{editable ? " (bấm để thêm)" : ""}:</b>{" "}
            {st.r.unknown_layers.map((l, i) => <Fragment key={l}>{i > 0 && " "}{editable
              ? <button className="btn m-0.5 min-h-8" type="button" onClick={() => onLayer(l, st.file!)}>{l}</button> : <code>{l}</code>}</Fragment>)}</p>}
          <div className="flex flex-wrap items-center gap-2"><label>Loại <select className="field" value={tk} onChange={(e) => setTk(e.target.value)}><option value="">tất cả</option>{Object.keys(count).map((k) => <option key={k}>{k}</option>)}</select></label></div>
          <div className="tw"><table className="nonum"><thead><tr><th>Mặt bằng</th><th>Loại</th><th>Mã</th><th>Layer</th><th>Lớp dày</th><th className="n">Dài m</th><th>Vai trò</th><th>Vật liệu</th><th className="n">Tin cậy</th><th>Ghi chú, lý do</th></tr></thead>
            <tbody>{rows.length ? rows.map((o, i) => (
              <tr key={i}><td>{s2(o.mat_bang)}</td><td>{name(o)}</td><td>{s2(o.ma)}</td><td>{s2(o.layer)}</td><td>{s2(o.lop_day)}</td><td className="n">{s2(o.dai_m)}</td>
                <td>{s2(o.vai_tro)}</td><td>{s2(o.phuong_an_tuong || o.vat_lieu)}</td><td className="n">{s2(o.do_tin_cay)}</td><td className="text-[12.5px]">{s2(o.ghi_chu)}</td></tr>
            )) : <tr><td colSpan={10} className="text-muted">Không có đối tượng nào.</td></tr>}</tbody></table></div>
        </>}
      </div>
    </Card>
  );
}
