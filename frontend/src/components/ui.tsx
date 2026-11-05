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

// Biểu tượng nét 24×24 tự vẽ (không thêm thư viện): tên -> đường vẽ.
const ICONS = {
  folder: "M3 6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z",
  file: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z M14 3v5h5 M9 13h6 M9 17h6",
  check: "M4 4h16v16H4Z M8 12l3 3 5-6",
  layers: "M12 3 2 8l10 5 10-5Z M2 13l10 5 10-5",
  tag: "M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9Z M8 8h.01",
  sliders: "M4 6h10 M18 6h2 M4 12h4 M12 12h8 M4 18h12 M20 18h0 M16 4v4 M10 10v4 M18 16v4",
  upload: "M12 16V4 M7 9l5-5 5 5 M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3",
  branch: "M6 3v12 M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M18 9a9 9 0 0 1-9 9",
  pin: "M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12Z M12 11.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z",
  building: "M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16 M16 9h3a1 1 0 0 1 1 1v11 M2 21h20 M8 7h4 M8 11h4 M8 15h4",
  stack: "M4 20h16 M4 15h16 M4 10h16 M6 5h12",
  db: "M12 8c4.4 0 8-1.3 8-3s-3.6-3-8-3-8 1.3-8 3 3.6 3 8 3Z M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5 M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
  text: "M4 6h16 M4 10h16 M4 14h10 M4 18h7",
  edit: "M4 20h4L19 9l-4-4L4 16Z M13.5 6.5l4 4",
  plus: "M12 5v14 M5 12h14",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Z M20 20l-4-4",
  chevron: "M9 6l6 6-6 6",
} as const;
export type IconName = keyof typeof ICONS;
export const Icon = ({ name, size = 18, className = "" }: { name: IconName; size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={`shrink-0 ${className}`}>
    <path d={ICONS[name]} />
  </svg>
);

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
  const list: [string, string][] = [["/du-an-cua-toi", "1. Dự án"], ["/do-boc", "2. Bóc tách bản vẽ"], ["/phan-tho", "3. Kiểm tra công tác và khối lượng"], ["/dieu-chinh", "4. Chọn vật liệu"], ["/vat-lieu", "5. Vật liệu và giá"], ["/toi-uu", "6. Tối ưu"]];
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
