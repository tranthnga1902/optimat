"use client";
// Bảng dữ liệu dùng chung ở trang quản trị: cột # số thứ tự, dòng tiêu đề cố định khi cuộn,
// bấm tiêu đề để sắp xếp, lọc mọi cột, chọn ô bằng chuột hoặc phím mũi tên, tải CSV mở bằng Excel.
import { useMemo, useState, type KeyboardEvent, type ReactNode } from "react";

export type Col<R> = {
  key: string;
  title: string;
  num?: boolean;
  /** giá trị dạng chữ để lọc, sắp xếp, CSV và thanh công thức; mặc định r[key] */
  text?: (r: R) => string;
  /** nội dung hiển thị trong ô; mặc định là text */
  render?: (r: R) => ReactNode;
};

const raw = (v: unknown) => (v == null ? "" : typeof v === "object" ? JSON.stringify(v) : String(v));
const cmp = (a: string, b: string) =>
  a !== "" && b !== "" && !isNaN(Number(a)) && !isNaN(Number(b)) ? Number(a) - Number(b) : a.localeCompare(b, "vi", { numeric: true });

export function Sheet<R extends object>({ cols, rows, file = "bang.csv", controls, keep, rowClass, actions }: {
  cols: Col<R>[];
  rows: R[];
  file?: string;
  /** bộ lọc riêng của trang, đặt cạnh ô lọc */
  controls?: ReactNode;
  keep?: (r: R) => boolean;
  rowClass?: (r: R) => string;
  /** cột nút cuối dòng (Sửa, Xóa…) */
  actions?: (r: R) => ReactNode;
}) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 } | null>(null);
  const [cur, setCur] = useState<{ r: number; c: number } | null>(null);
  const val = (r: R, c: Col<R>) => (c.text ? c.text(r) : raw((r as Record<string, unknown>)[c.key]));

  const shown = useMemo(() => {
    const s = q.trim().toLowerCase();
    let out = rows.filter((r) => (!keep || keep(r)) && (!s || cols.some((c) => val(r, c).toLowerCase().includes(s))));
    if (sort) {
      const c = cols.find((x) => x.key === sort.key)!;
      out = [...out].sort((a, b) => sort.dir * cmp(val(a, c), val(b, c)));
    }
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows, cols, q, sort, keep]);

  const at = cur && cur.r < shown.length ? cur : null;
  const onKey = (e: KeyboardEvent) => {
    const d = ({ ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] } as Record<string, number[]>)[e.key];
    if (!d) return;
    e.preventDefault();
    if (!at) { if (shown.length) setCur({ r: 0, c: 0 }); return; }
    const r = at.r + d[0], c = at.c + d[1];
    if (r >= 0 && r < shown.length && c >= 0 && c < cols.length) setCur({ r, c });
  };
  const csv = () => {
    const c = (v: string) => `"${v.replace(/"/g, '""')}"`;
    const text = "﻿" + [cols.map((x) => c(x.title)).join(","), ...shown.map((r) => cols.map((x) => c(val(r, x))).join(","))].join("\r\n"); // BOM để Excel đọc đúng tiếng Việt
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
    a.download = file; a.click(); URL.revokeObjectURL(a.href);
  };
  const width = cols.length + (actions ? 1 : 0);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <input className="field" type="search" placeholder="Lọc mọi cột…" aria-label="Lọc" value={q} onChange={(e) => { setQ(e.target.value); setCur(null); }} />
        {controls}
        <button className="btn ml-auto" type="button" onClick={csv}>Tải CSV (Excel)</button>
      </div>
      <div className="overflow-hidden rounded-lg border border-rule bg-card text-[13px]">
        <div className="xl">
          <table tabIndex={0} onKeyDown={onKey}>
            <thead>
              <tr>
                <th className="rn">#</th>
                {cols.map((c) => (
                  <th key={c.key} className={c.num ? "n" : ""}>
                    <button type="button" onClick={() => { setSort((s) => ({ key: c.key, dir: s?.key === c.key ? (-s.dir as 1 | -1) : 1 })); setCur(null); }}>
                      {c.title}{sort?.key === c.key ? (sort.dir > 0 ? " ▲" : " ▼") : ""}
                    </button>
                  </th>
                ))}
                {actions && <th />}
              </tr>
            </thead>
            <tbody>
              {shown.length ? shown.map((r, i) => (
                <tr key={i} className={rowClass?.(r)}>
                  <td className="rn">{i + 1}</td>
                  {cols.map((c, j) => {
                    const v = val(r, c);
                    return (
                      <td key={c.key} className={`${c.num ? "n" : ""} ${at?.r === i && at.c === j ? "on" : ""}`} title={v.length > 40 ? v : undefined}
                        onClick={() => setCur({ r: i, c: j })}>{c.render ? c.render(r) : v}</td>
                    );
                  })}
                  {actions && <td>{actions(r)}</td>}
                </tr>
              )) : (
                <tr><td className="rn" /><td colSpan={width} className="text-muted">Không có dòng nào.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="px-2 py-1.5 text-right text-xs text-muted">
          {shown.length.toLocaleString("vi-VN")}/{rows.length.toLocaleString("vi-VN")} dòng
        </div>
      </div>
    </div>
  );
}
