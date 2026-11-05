"use client";
// Đọc /api/data/suppliers; lưu qua /api/admin/tables/suppliers (chỉ khi có PostgreSQL). Ghi chép = dòng có ngày giờ
// thêm vào đầu cột note. Bản đồ Leaflet + nền Esri (cần mạng).
import "leaflet/dist/leaflet.css";
import { Fragment, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import type { CircleMarker, LayerGroup, Map as LMap } from "leaflet";
import { api, int, put } from "@/lib/api";
import { useReference } from "@/lib/reference";
import { Card, Field, Loading, Note, Pill, Tile, Tiles } from "@/components/ui";

type Dealer = {
  supplier_id: string; name: string; province?: string; phone?: string; address?: string; note?: string;
  lat?: number | null; lon?: number | null; verified?: boolean | null; maps_url?: string; [k: string]: unknown;
};
type FieldDef = [string, string, ("num" | "bool" | "pub" | "kind" | "date")?];

const DEALER_FIELDS: [string, FieldDef[]][] = [
  ["Liên hệ", [["name", "Tên"], ["phone", "Điện thoại"], ["zalo", "Zalo"], ["email", "Email"], ["website", "Website"], ["facebook", "Facebook"]]],
  ["Địa chỉ", [["address", "Địa chỉ"], ["ward", "Phường, xã"], ["district", "Quận, huyện"], ["province", "Tỉnh"], ["lat", "Vĩ độ", "num"], ["lon", "Kinh độ", "num"], ["maps_url", "Link bản đồ"]]],
  ["Kinh doanh", [["dealer_type", "Loại (nhà máy, cấp 1, cấp 2…)"], ["brands", "Hãng phân phối (;)"], ["opening_hours", "Giờ mở cửa"], ["lead_time_days", "Thời gian cung ứng (ngày)", "num"],
    ["delivers", "Giao hàng", "bool"], ["delivery_radius_km", "Bán kính giao (km)", "num"], ["max_truck_ton", "Xe tối đa (tấn)", "num"], ["min_order", "Đơn tối thiểu"],
    ["vat_invoice", "Xuất hóa đơn VAT", "bool"], ["payment", "Thanh toán"], ["price_public", "Công khai giá", "pub"], ["price_page_url", "Trang bảng giá"], ["tax_code", "Mã số thuế"],
    ["linked_supplier_id", "Cùng công ty với đại lý (mã, cho công bố giá CBG-…)"]]],
  ["Thu thập", [["verified", "Đã gọi xác minh", "bool"], ["collected_at", "Ngày thu thập", "date"], ["collected_by", "Người thu thập"], ["source", "Nguồn"], ["data_kind", "Loại dữ liệu", "kind"]]],
];
const OPTS: Record<string, [string, string][]> = {
  bool: [["", "chưa rõ"], ["true", "có"], ["false", "không"]],
  pub: [["", "chưa rõ"], ["YES", "có"], ["PARTIAL", "một phần"], ["NO", "không"]],
};
const has = (r: Dealer) => r.lat != null && r.lon != null;
const fill = (r: Dealer) => (r.verified ? "#0F6B5C" : "#F3B562");

/** Nội dung tooltip dựng bằng DOM (không chèn HTML). */
function tip(r: Dealer) {
  const el = document.createElement("div"), b = el.appendChild(document.createElement("b"));
  b.textContent = r.name;
  if (r.phone) el.append(document.createElement("br"), String(r.phone));
  if (r.address) {
    const s = document.createElement("span");
    s.style.cssText = "white-space:normal;display:inline-block;max-width:260px";
    s.textContent = String(r.address);
    el.append(document.createElement("br"), s);
  }
  return el;
}

export function Dealers() {
  const [rows, setRows] = useState<Dealer[] | null>(null);
  const [editable, setEditable] = useState(false);
  const [err, setErr] = useState("");
  const [q, setQ] = useState(""), [p, setP] = useState(""), [f, setF] = useState("");
  const [shown, setShown] = useState(100);
  const [open, setOpen] = useState<string | null>(null);
  const [ver, setVer] = useState(0); // đổi key form để nạp lại giá trị sau khi lưu
  const [msg, setMsg] = useState("");
  const [noteText, setNoteText] = useState("");
  const [mapMsg, setMapMsg] = useState("");
  const [mapReady, setMapReady] = useState(false);
  // loại dữ liệu (ACTUAL, SAMPLE, SYNTHETIC) theo ràng buộc của database
  const kinds = useReference().ref?.data_kinds ?? [];
  const mapDiv = useRef<HTMLDivElement>(null);
  const map = useRef<LMap | null>(null), layer = useRef<LayerGroup | null>(null);
  const markers = useRef<Record<string, CircleMarker>>({});
  const scrollTo = useRef<string | null>(null);
  // giá trị mới nhất cho các sự kiện Leaflet (gắn một lần)
  const live = useRef<{ rows: Dealer[] | null; open: string | null; editable: boolean; select: (id: string, fromMap: boolean) => void;
    save: (r: Dealer, v: Record<string, unknown>) => Promise<void> } | null>(null);
  const makeMarker = useRef<((r: Dealer) => CircleMarker) | null>(null);

  useEffect(() => {
    api<{ rows: Dealer[]; editable: boolean }>("/api/data/suppliers").then((d) => { setRows(d.rows); setEditable(d.editable); }, (e) => setErr(e.message));
  }, []);

  const provinces = useMemo(() => [...new Set((rows || []).map((r) => r.province).filter((v): v is string => !!v))].sort((a, b) => a.localeCompare(b, "vi")), [rows]);
  const list = useMemo(() => {
    const s = q.trim().toLowerCase();
    return (rows || []).filter((r) => (!p || r.province === p)
      && (!f || (f === "geo" ? has(r) : f === "nogeo" ? !has(r) : f === "ver" ? r.verified === true : r.verified !== true))
      && (!s || [r.name, r.phone, r.address, r.note, r.supplier_id].some((v) => v && String(v).toLowerCase().includes(s))));
  }, [rows, q, p, f]);

  const save = async (r: Dealer, values: Record<string, unknown>) => {
    const row = (await put<{ row: Dealer }>(`/api/admin/tables/suppliers/${encodeURIComponent(r.supplier_id)}`, values)).row;
    setRows((rs) => rs && rs.map((x) => (x.supplier_id === r.supplier_id ? { ...x, ...row } : x)));
    setVer((v) => v + 1);
  };
  const select = (id: string, fromMap: boolean) => {
    const next = open === id && !fromMap ? null : id;
    setOpen(next); setMsg(""); setNoteText("");
    const i = list.findIndex((r) => r.supplier_id === id);
    if (i >= shown) setShown(i + 1);
    const r = rows?.find((x) => x.supplier_id === id);
    if (next && map.current && r && has(r) && !fromMap) map.current.setView([r.lat!, r.lon!], Math.max(map.current.getZoom(), 14));
    if (fromMap) scrollTo.current = id;
  };
  useEffect(() => { live.current = { rows, open, editable, select, save }; });

  useEffect(() => {
    const id = scrollTo.current;
    if (!id) return;
    scrollTo.current = null;
    document.querySelector(`tr[data-id="${CSS.escape(id)}"]`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [open, shown]);

  // Leaflet đụng tới window: chỉ nạp trên trình duyệt, sau khi khung bản đồ đã có
  const loaded = rows != null;
  useEffect(() => {
    if (!loaded || !mapDiv.current) return;
    let gone = false, m: LMap | null = null;
    import("leaflet").then(({ default: L }) => {
      if (gone || !mapDiv.current) return;
      m = map.current = L.map(mapDiv.current, { preferCanvas: true }).setView([21.03, 105.85], 8);
      // nền Esri: mạng này chặn tile.openstreetmap.org, CARTO đòi khóa API
      L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19,
        attribution: "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap" }).addTo(m);
      layer.current = L.layerGroup().addTo(m);
      m.on("click", async (e) => {
        if (!live.current) return;
        const { rows, open, editable, save } = live.current, r = rows?.find((x) => x.supplier_id === open);
        if (!editable || !r || !confirm(`Đặt vị trí ${r.name} tại ${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}?`)) return;
        const lat = +e.latlng.lat.toFixed(6), lon = +e.latlng.lng.toFixed(6);
        try { await save(r, { lat, lon, maps_url: `https://www.google.com/maps/search/?api=1&query=${lat},${lon}` }); } catch (err) { alert((err as Error).message); }
      });
      // marker tạo một lần, giữ trong markers; tooltip đọc dòng mới nhất
      makeMarker.current = (r) => L.circleMarker([r.lat!, r.lon!], { radius: 6, weight: 1, color: "#0A4A40", fillColor: fill(r), fillOpacity: .9 })
        .bindTooltip(() => tip(live.current?.rows?.find((x) => x.supplier_id === r.supplier_id) || r))
        .on("click", (e) => { L.DomEvent.stopPropagation(e); live.current?.select(r.supplier_id, true); });
      setMapReady(true);
      setMapMsg("Điểm cam: chưa xác minh; điểm xanh: đã gọi xác minh. Rê chuột để xem tên, bấm để mở chi tiết.");
    }, () => setMapMsg("Không tải được thư viện bản đồ (cần mạng)."));
    return () => { gone = true; m?.remove(); map.current = layer.current = null; markers.current = {}; setMapReady(false); };
  }, [loaded]);
  useEffect(() => {
    const lg = layer.current, mk = makeMarker.current;
    if (!mapReady || !lg || !mk) return;
    lg.clearLayers();
    for (const r of list.filter(has)) {
      const m = markers.current[r.supplier_id];
      if (m) m.setLatLng([r.lat!, r.lon!]).setStyle({ fillColor: fill(r) });
      lg.addLayer(m || (markers.current[r.supplier_id] = mk(r)));
    }
  }, [list, mapReady]);

  if (err) return <Note>{err}</Note>;
  if (!rows) return <Loading />;

  const onSave = async (e: FormEvent<HTMLFormElement>, r: Dealer) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const values = Object.fromEntries(DEALER_FIELDS.flatMap(([, fs]) => fs.map(([k]) => [k, fd.get(k)])));
    setMsg("Đang lưu…");
    try { await save(r, values); setMsg("Đã lưu."); } catch (err) { setMsg((err as Error).message); }
  };
  const onNote = async (e: FormEvent<HTMLFormElement>, r: Dealer) => {
    e.preventDefault();
    const t = noteText.trim(); if (!t) return;
    const now = new Date(), stamp = `${now.toLocaleDateString("sv-SE")} ${now.toTimeString().slice(0, 5)}`;
    try { await save(r, { note: `[${stamp}] ${t}` + (r.note ? "\n" + r.note : "") }); setNoteText(""); } catch (err) { alert((err as Error).message); }
  };
  const onFilter = (set: (v: string) => void) => (e: { target: { value: string } }) => { set(e.target.value); setShown(100); };

  const detail = (r: Dealer) => (
    <tr className="ddetail"><td colSpan={5} className="bg-bg">
      <div className="flex flex-col gap-3.5 px-0.5 py-1.5">
        <div className="flex flex-wrap items-center gap-2">
          <b className="mr-auto">{r.name} <span className="text-[12.5px] text-muted">{r.supplier_id}</span></b>
          {r.phone && <a className="btn" href={"tel:" + String(r.phone).split(/[;,/]/)[0].replace(/[^\d+]/g, "")}>Gọi</a>}
          {r.maps_url && <a className="btn" href={r.maps_url} target="_blank" rel="noopener">Mở bản đồ</a>}
        </div>
        <form key={`${r.supplier_id}-${ver}`} className="flex flex-col gap-3.5" onSubmit={(e) => onSave(e, r)}>
          {DEALER_FIELDS.map(([g, fs]) => (
            <fieldset key={g} className="rounded-lg border border-rule px-3 py-2.5">
              <legend className="text-[12.5px] text-muted">{g}</legend>
              <div className="grid gap-2.5 [grid-template-columns:repeat(auto-fit,minmax(190px,1fr))]">
                {fs.map(([k, label, type]) => {
                  const v = r[k] == null ? "" : String(r[k]);
                  return (
                    <Field key={k} label={label}>
                      {type === "bool" || type === "pub" || type === "kind"
                        ? <select className="field" name={k} defaultValue={v} disabled={!editable}>{(type === "kind" ? (kinds.includes(v) || !v ? kinds : [...kinds, v]).map((k): [string, string] => [k, k]) : OPTS[type]).map(([o, t]) => <option key={o} value={o}>{t}</option>)}</select>
                        : <input className="field" name={k} defaultValue={v} disabled={!editable}
                            {...(type === "num" ? { type: "number", step: "any" } : type === "date" ? { type: "date" } : {})} />}
                    </Field>
                  );
                })}
              </div>
            </fieldset>
          ))}
          {editable && <>
            <p className="m-0 text-[12.5px] text-muted">Bấm lên bản đồ để đặt vị trí cho đại lý này.</p>
            <div className="flex flex-wrap items-center gap-2"><button className="btn primary" type="submit">Lưu thông tin</button><span className="text-[12.5px]" role="status">{msg}</span></div>
          </>}
        </form>
        <div>
          <h3 className="mt-0 mb-1.5 text-[15px]">Ghi chép</h3>
          {editable && (
            <form className="flex flex-wrap items-stretch gap-2" onSubmit={(e) => onNote(e, r)}>
              <textarea rows={2} required aria-label="Nội dung ghi chép" placeholder="Nội dung cuộc gọi, báo giá, hẹn gặp…" value={noteText} onChange={(e) => setNoteText(e.target.value)}
                className="flex-[1_1_320px] rounded-lg border border-field bg-card px-3 py-2 text-ink" />
              <button className="btn" type="submit">Thêm ghi chép</button>
            </form>
          )}
          <div className="mt-2 text-[12.5px] whitespace-pre-wrap">{r.note || "Chưa có ghi chép."}</div>
        </div>
      </div>
    </td></tr>
  );

  return (
    <>
      {!editable && <Note>Chưa kết nối PostgreSQL: chỉ xem được, không lưu sửa đổi và ghi chép.</Note>}
      <Tiles>
        <Tile k="Đại lý" v={int(rows.length)} s={`${provinces.length} tỉnh`} />
        <Tile k="Có tọa độ" v={int(rows.filter(has).length)} s="hiện trên bản đồ" />
        <Tile k="Đã xác minh" v={int(rows.filter((r) => r.verified === true).length)} s="đã gọi điện" />
      </Tiles>
      <Card>
        <div ref={mapDiv} className="z-0 h-[420px] rounded-lg bg-rule2" role="region" aria-label="Bản đồ đại lý" />
        <div className="text-[12.5px] text-muted">{mapMsg}</div>
      </Card>
      <Card>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-2">Tìm <input className="field" type="search" placeholder="tên, SĐT, địa chỉ, ghi chép" value={q} onChange={onFilter(setQ)} /></label>
          <label className="flex items-center gap-2">Tỉnh <select className="field" value={p} onChange={onFilter(setP)}><option value="">tất cả</option>{provinces.map((x) => <option key={x}>{x}</option>)}</select></label>
          <label className="flex items-center gap-2">Lọc <select className="field" value={f} onChange={onFilter(setF)}>
            <option value="">tất cả</option><option value="geo">có tọa độ</option><option value="nogeo">chưa có tọa độ</option><option value="ver">đã xác minh</option><option value="nover">chưa xác minh</option>
          </select></label>
          <span className="text-[12.5px] text-muted">{int(list.length)} đại lý</span>
        </div>
        <div className="tw"><table><thead><tr><th>Tên</th><th>Tỉnh</th><th>Điện thoại</th><th>Địa chỉ</th><th>Trạng thái</th></tr></thead><tbody>
          {list.length ? list.slice(0, shown).map((r) => (
            <Fragment key={r.supplier_id}>
              <tr data-id={r.supplier_id} className="cursor-pointer" aria-expanded={open === r.supplier_id || undefined} onClick={() => select(r.supplier_id, false)}>
                <td><b>{r.name}</b></td><td>{r.province || ""}</td><td className="text-[12.5px]">{r.phone || ""}</td><td className="text-[12.5px]">{r.address || ""}</td>
                <td>{!has(r) && <Pill level="warn">chưa có tọa độ</Pill>} {r.verified && <Pill level="ok">đã xác minh</Pill>}</td>
              </tr>
              {open === r.supplier_id && detail(r)}
            </Fragment>
          )) : <tr><td colSpan={5} className="text-muted">Không có đại lý nào.</td></tr>}
        </tbody></table></div>
        {list.length > shown && <div className="flex flex-wrap items-center gap-2"><button className="btn" type="button" onClick={() => setShown(shown + 100)}>Xem thêm</button></div>}
      </Card>
    </>
  );
}
