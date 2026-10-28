"use client";
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Sheet, type Col } from "@/components/Sheet";
import { Card, Loading, Note, Pill, Tile, Tiles } from "@/components/ui";

type Material = { id: string; name: string; family: string; family_label: string };
type WallSystem = { wall_system_id: string; material_id: string; family: string; detect_class?: string; ready: boolean; data_kind: string; missing?: string[] };
type Row = WallSystem & { family_label: string; name: string; status: string; missing_text: string };

const COLS: Col<Row>[] = [
  { key: "family_label", title: "Họ vật liệu" },
  { key: "material_id", title: "Mã vật liệu", render: (r) => <b>{r.material_id}</b> },
  { key: "name", title: "Tên vật liệu" },
  { key: "wall_system_id", title: "Phương án tường", render: (r) => <b>{r.wall_system_id}</b> },
  { key: "detect_class", title: "Lớp tường", render: (r) => r.detect_class || "chưa gán" },
  { key: "status", title: "Trạng thái", render: (r) => <Pill level={r.ready ? "ok" : "warn"}>{r.status}</Pill> },
  { key: "data_kind", title: "Loại dữ liệu", render: (r) => (r.data_kind !== "ACTUAL" ? <Pill level="info">{r.data_kind}</Pill> : r.data_kind) },
  { key: "missing_text", title: "Còn thiếu" },
];

export function Catalog() {
  const [d, setD] = useState<{ materials: Material[]; wall_systems: WallSystem[] } | null>(null);
  const [err, setErr] = useState("");
  const [fam, setFam] = useState("");
  const [ready, setReady] = useState("");
  useEffect(() => { api("/api/catalog/wall-materials").then(setD, (e) => setErr(e.message)); }, []);

  const view = useMemo(() => {
    if (!d) return null;
    const mats = Object.fromEntries(d.materials.map((m) => [m.id, m]));
    const famLabel = Object.fromEntries(d.materials.map((m) => [m.family, m.family_label]));
    const fams = [...new Set([...d.materials.map((m) => m.family), ...d.wall_systems.map((s) => s.family)])];
    const rows: Row[] = d.wall_systems.map((s) => ({ ...s, family_label: famLabel[s.family] || s.family, name: mats[s.material_id]?.name || "",
      detect_class: s.detect_class || "", status: s.ready ? "đủ số liệu" : "còn thiếu", missing_text: (s.missing || []).join(", ") }))
      .sort((a, b) => a.family_label.localeCompare(b.family_label, "vi"));
    return { rows, fams, famLabel, ready: rows.filter((r) => r.ready).length };
  }, [d]);

  if (err) return <Note>{err}</Note>;
  if (!d || !view) return <Loading />;
  const S = d.wall_systems.length;
  return (
    <>
      <Tiles>
        <Tile k="Phương án tường" v={S} s={`${d.materials.length} vật liệu tường · ${view.fams.length} họ`} />
        <Tile tone="ok" k="Đủ số liệu để tối ưu" v={view.ready} s="được đưa vào NSGA-II" />
        <Tile tone={view.ready < S ? "warn" : ""} k="Còn thiếu số liệu" v={S - view.ready} s="bổ sung trong materials_master.xlsx" />
      </Tiles>
      <Card>
        <Sheet cols={COLS} rows={view.rows} file="phuong_an_tuong.csv"
          rowClass={(r) => (r.ready ? "" : "[&>td:nth-child(9)]:text-warn-ink")}
          keep={(r) => (!fam || r.family === fam) && (!ready || String(+r.ready) === ready)}
          controls={<>
            <select className="field" aria-label="Họ vật liệu" value={fam} onChange={(e) => setFam(e.target.value)}>
              <option value="">Mọi họ vật liệu</option>
              {view.fams.map((f) => <option key={f} value={f}>{view.famLabel[f] || f}</option>)}
            </select>
            <select className="field" aria-label="Trạng thái" value={ready} onChange={(e) => setReady(e.target.value)}>
              <option value="">Mọi trạng thái</option><option value="1">Đủ số liệu</option><option value="0">Còn thiếu</option>
            </select>
          </>} />
      </Card>
    </>
  );
}
