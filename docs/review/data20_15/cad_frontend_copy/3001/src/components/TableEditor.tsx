"use client";
// Xem, thêm, sửa, xóa dòng một bảng database (api/admin_db.py). Dùng ở trang Giá, Quy tắc bóc tách, Cơ sở dữ liệu.
import { useEffect, useRef, useState, type FormEvent } from "react";
import { api } from "@/lib/api";
import { Sheet, type Col } from "@/components/Sheet";
import { Card, Loading, Note } from "@/components/ui";

/** comment: cách điền cột, lấy từ lược đồ database (models.py, comment=) */
type Column = { name: string; type: string; nullable: boolean; comment?: string | null };
type Table = { columns: Column[]; key: string[]; rows: Record<string, unknown>[]; total: number; editable: boolean; source_file: string };

const NUM = ["integer", "float", "bigint"];
const str = (v: unknown) => (v == null ? "" : String(v));

export function TableEditor({ name }: { name: string }) {
  const [t, setT] = useState<Table | null>(null);
  const [err, setErr] = useState("");
  const [ver, setVer] = useState(0);
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");
  const box = useRef<HTMLDivElement>(null), formRef = useRef<HTMLFormElement>(null);

  useEffect(() => { box.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }, []);
  useEffect(() => {
    let live = true;
    api<Table>(`/api/admin/tables/${encodeURIComponent(name)}`).then((d) => { if (live) { setT(d); setErr(""); } }, (e) => live && setErr(e.message));
    return () => { live = false; };
  }, [name, ver]);

  const reset = () => { setEditing(null); setForm({}); setMsg(""); };
  const reload = () => { reset(); setVer((v) => v + 1); };

  if (err) return <div ref={box}><Card><Note>{err}</Note></Card></div>;
  if (!t) return <div ref={box}><Card><Loading>Đang tải {name}…</Loading></Card></div>;

  const cols = t.columns.filter((c) => c.name !== "id"), key = t.key[0];
  const sheetCols: Col<Record<string, unknown>>[] = t.columns.map((c) => ({ key: c.name, title: c.name, num: NUM.includes(c.type) }));

  const edit = (r: Record<string, unknown>) => {
    setEditing(str(r[key]));
    setForm(Object.fromEntries(cols.map((c) => [c.name, str(r[c.name])])));
    formRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  };
  const del = async (id: string) => {
    if (!confirm(`Xóa dòng ${id} của ${name}?${name === "suppliers" ? " Các dòng giá của đại lý này cũng bị xóa." : ""}`)) return;
    try { await api(`/api/admin/tables/${encodeURIComponent(name)}/${encodeURIComponent(id)}`, { method: "DELETE" }); reload(); }
    catch (e) { alert((e as Error).message); }
  };
  const save = async (e: FormEvent) => {
    e.preventDefault();
    const body = Object.fromEntries(cols.map((c) => [c.name, form[c.name] ?? ""]));
    setMsg("Đang lưu…");
    try {
      await api(`/api/admin/tables/${encodeURIComponent(name)}${editing == null ? "" : "/" + encodeURIComponent(editing)}`,
        { method: editing == null ? "POST" : "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      reload();
    } catch (e) { setMsg((e as Error).message); }
  };

  return (
    <div ref={box}>
      <Card>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="m-0 mr-auto text-base font-bold">
            <code>{name}</code> · {t.total.toLocaleString("vi-VN")} dòng{t.total > t.rows.length ? ` (hiện ${t.rows.length})` : ""}
          </h2>
          {t.editable && <a className="btn" href={`/api/admin/tables/${encodeURIComponent(name)}/csv`} title="CSV đúng định dạng file nguồn, để chép đè trước khi nạp lại">Tải CSV nguồn</a>}
        </div>
        {t.editable && <>
          <p className="m-0 text-[12.5px] text-muted">
            Lệnh <code>init_db.py {t.source_file.startsWith("data/rules") ? "--reload-rules" : "--reset"}</code> nạp lại từ file CSV và xóa sửa đổi ở đây: tải CSV, chép đè <code>{t.source_file}</code> trước khi nạp lại.
          </p>
          <form ref={formRef} onSubmit={save} className="grid items-end gap-3 [grid-template-columns:repeat(auto-fit,minmax(170px,1fr))]">
            {cols.map((c) => (
              <label key={c.name} className="flex flex-col gap-1.5 font-semibold" title={c.comment || undefined}>
                <span>{c.name}{c.nullable ? "" : " *"}</span>
                {c.comment && <span className="text-[12.5px] font-normal text-muted">{c.comment}</span>}
                <input className="field" name={c.name} required={!c.nullable} value={form[c.name] ?? ""}
                  type={NUM.includes(c.type) ? "number" : c.type === "date" ? "date" : "text"} step={NUM.includes(c.type) ? "any" : undefined}
                  // khóa chính nhập tay (supplier_id) chỉ nhập khi thêm dòng: bảng khác tham chiếu tới nên không đổi khi sửa
                  readOnly={editing != null && c.name === key}
                  onChange={(e) => setForm((f) => ({ ...f, [c.name]: e.target.value }))} />
              </label>
            ))}
            <div className="flex flex-wrap items-center gap-2">
              <button className="btn primary" type="submit">{editing == null ? "Thêm dòng" : `Lưu dòng ${editing}`}</button>
              <button className="btn" type="button" onClick={reset}>Hủy</button>
              <span className="text-[12.5px]" role="status">{msg}</span>
            </div>
          </form>
        </>}
        <Sheet cols={sheetCols} rows={t.rows} file={`${name}.csv`}
          actions={t.editable ? (r) => <>
            <button className="btn" type="button" onClick={() => edit(r)}>Sửa</button>{" "}
            <button className="btn" type="button" onClick={() => del(str(r[key]))}>Xóa</button>
          </> : undefined} />
      </Card>
    </div>
  );
}
