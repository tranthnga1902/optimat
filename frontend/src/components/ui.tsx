// Thành phần giao diện dùng chung, giữ đúng kiểu của app.html cũ.
import Link from "next/link";
import type { ReactNode } from "react";

export type Level = "ok" | "warn" | "bad" | "info";

export const Pill = ({ level, children }: { level: Level; children: ReactNode }) => <span className={`pill ${level}`}>{children}</span>;

export function Logo({ color, size = 28 }: { color: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" fill="none" stroke={color} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="4" y="20" width="12" height="12" /><rect x="20" y="20" width="12" height="12" /><rect x="12" y="6" width="12" height="12" />
    </svg>
  );
}

/** Đầu trang: tiêu đề, mô tả, nút bên phải. */
export function Head({ title, children, actions }: { title: string; children?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="m-0 text-[23px] font-bold">{title}</h1>
        {children && <p className="mt-1 mb-0 max-w-[70ch] text-muted">{children}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export const Card = ({ title, children, className = "", style }: { title?: ReactNode; children: ReactNode; className?: string; style?: React.CSSProperties }) => (
  <section className={`flex min-w-0 flex-col gap-3 rounded-xl border border-rule bg-card p-[18px] ${className}`} style={style}>
    {title && <h2 className="m-0 text-base font-bold">{title}</h2>}
    {children}
  </section>
);

export const Tiles = ({ children }: { children: ReactNode }) => (
  <div className="grid gap-3.5 [grid-template-columns:repeat(auto-fit,minmax(170px,1fr))]">{children}</div>
);

const TONE: Record<string, string> = {
  "": "border-rule bg-card",
  ok: "border-transparent bg-accent-soft text-accent-deep",
  warn: "border-transparent bg-warn-bg text-warn-ink",
  bad: "border-transparent bg-bad-bg text-bad-ink",
};
export function Tile({ k, v, s, tone = "" }: { k: ReactNode; v: ReactNode; s?: ReactNode; tone?: "" | "ok" | "warn" | "bad" }) {
  const sub = tone ? "" : "text-muted";
  return (
    <div className={`rounded-xl border px-4 py-3.5 ${TONE[tone]}`}>
      <div className={`text-[13px] ${sub}`}>{k}</div>
      <div className="text-[26px] font-bold tabular-nums">{v}</div>
      {s != null && <div className={`text-[12.5px] ${sub}`}>{s}</div>}
    </div>
  );
}

export const Note = ({ children, tone = "warn", className = "" }: { children: ReactNode; tone?: "warn" | "ok"; className?: string }) => (
  <div className={`rounded-[10px] px-3.5 py-3 ${tone === "ok" ? "bg-accent-soft text-accent-deep" : "bg-warn-bg text-warn-ink"} ${className}`}>{children}</div>
);

export const Empty = ({ children }: { children: ReactNode }) => (
  <div className="rounded-[10px] border border-dashed border-field p-7 text-center text-muted">{children}</div>
);

export const Loading = ({ children = "Đang tải…" }: { children?: ReactNode }) => <div className="text-muted">{children}</div>;

/** Thanh bước của luồng người dùng. done: các bước đã xong. */
export function Steps({ cur, done }: { cur: string; done: Record<string, boolean> }) {
  const list: [string, string][] = [["/do-boc", "1. Bản vẽ và đo bóc"], ["/vat-lieu", "2. Vật liệu và giá"], ["/phan-tho", "Phần thô"], ["/toi-uu", "3. Tối ưu"]];
  return (
    <ol className="m-0 flex list-none flex-wrap gap-2 p-0">
      {list.map(([href, t]) => {
        const on = href === cur, ok = done[href] && !on;
        return (
          <li key={href}>
            <Link href={href} aria-current={on ? "step" : undefined}
              className={`inline-flex rounded-full border px-3.5 py-[7px] font-medium no-underline ${on ? "border-accent bg-accent font-semibold text-accent-ink"
                : ok ? "border-transparent bg-accent-soft font-semibold text-accent-deep" : "border-rule bg-card text-muted"}`}>{t}</Link>
          </li>
        );
      })}
    </ol>
  );
}

/** Ô nhập có nhãn ở trên (biểu mẫu). */
export const Field = ({ label, hint, children }: { label: ReactNode; hint?: ReactNode; children: ReactNode }) => (
  <label className="flex flex-col gap-1.5 font-semibold" title={typeof hint === "string" ? hint : undefined}>
    {label}{hint && <span className="text-[12.5px] font-normal text-muted">{hint}</span>}{children}
  </label>
);

/** Phân trang cho danh sách lấy từ API (page bắt đầu từ 1). */
export function Pager({ page, size, total, onPage }: { page: number; size: number; total: number; onPage: (p: number) => void }) {
  const last = Math.max(1, Math.ceil(total / size));
  return (
    <div className="flex flex-wrap items-center gap-2 text-[13px] text-muted">
      <span className="mr-auto">{total.toLocaleString("vi-VN")} dòng · trang {page}/{last}</span>
      <button className="btn" type="button" disabled={page <= 1} onClick={() => onPage(page - 1)}>‹ Trước</button>
      <button className="btn" type="button" disabled={page >= last} onClick={() => onPage(page + 1)}>Sau ›</button>
    </div>
  );
}
