"use client";
// Khung trang: menu bên trái theo vai trò (người dùng / quản trị) và vùng nội dung.
// Có PostgreSQL thì bắt đăng nhập (AD01-03): chưa đăng nhập chuyển sang /dang-nhap, người dùng thường vào khu quản trị thấy 403.
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { logout, useMe } from "@/lib/auth";
import { store, useStored } from "@/lib/store";
import { Loading, Logo } from "./ui";

export type Role = "user" | "admin";

type Item = [href: string, title: string, icon: string, badge?: string];
type Group = { label?: string; items: Item[] };

// AD01-01: menu quản trị theo nhóm nghiệp vụ (kế hoạch Admin AD-01..06)
const ADMIN: Group[] = [
  { label: "Tổng quan", items: [["/tong-quan", "Tổng quan", "◫"], ["/kiem-soat", "Kiểm soát dữ liệu", "✓"]] },
  { label: "Dự án và người dùng", items: [["/du-an", "Dự án", "▣"], ["/nguoi-dung", "Người dùng", "☺"]] },
  { label: "Quy tắc CAD", items: [["/nhan-dien", "Ký hiệu nhận diện", "⌗"], ["/quy-tac", "Quy tắc bóc tách", "☷"]] },
  { label: "Vật liệu và định mức", items: [["/danh-muc", "Danh mục vật liệu", "▤"]] },
  { label: "Nhà cung cấp và giá", items: [["/dai-ly", "Đại lý", "⌖"], ["/gia", "Giá, nhà cung cấp", "▥"]] },
  { label: "AI và tối ưu", items: [["/mo-hinh", "Mô hình, cấu hình", "✧"]] },
  { label: "Hệ thống", items: [["/co-so-du-lieu", "Cơ sở dữ liệu", "◴"]] },
];

export function Shell({ role, children }: { role: Role; children: ReactNode }) {
  const path = usePathname();
  const plans = useStored<unknown[]>("optimat-confirmed", []);
  const rough = useStored<unknown>("optimat-rough", null);
  useEffect(() => { store.set("optimat-role", role); }, [role]);
  const me = useMe();
  const router = useRouter();
  useEffect(() => { if (me?.auth && !me.user) router.replace(`/dang-nhap?next=${encodeURIComponent(path)}`); }, [me, path, router]);
  const user = me?.user;

  const collapsed = useStored<boolean>("optimat-nav-collapsed", false);
  const groups: Group[] = role === "admin" ? ADMIN
    : [{ items: [["/do-boc", "Hồ sơ và đo bóc", "▣"], ["/vat-lieu", "Vật liệu và giá", "▤", plans.length ? `${plans.length} mặt bằng` : ""],
       ["/phan-tho", "Phần thô", "☷", rough ? "đã tính" : ""], ["/toi-uu", "Phương án tối ưu", "✧"], ["/tiep-nhan", "Tiếp nhận hồ sơ CAD", "⇪"],
       ["/mapping", "Duyệt mapping", "⌗"]] }];
  const admin = role === "admin";
  const accent = admin ? "#F3B562" : "#7FD6BF";

  return (
    <div className="flex min-h-screen max-[860px]:flex-col">
      <nav aria-label="Menu" className={`sticky top-0 flex h-screen ${collapsed ? "w-[72px]" : "w-[248px]"} shrink-0 flex-col gap-5 overflow-y-auto px-3 py-5 text-white max-[860px]:static max-[860px]:h-auto max-[860px]:w-auto max-[860px]:gap-3 max-[860px]:p-3.5 ${admin ? "bg-nav-admin" : "bg-nav-user"}`}>
        <div className={`flex h-10 items-center gap-2.5 text-[17px] font-bold ${collapsed ? "flex-col justify-center gap-1 px-0" : "px-3"}`}>
          <Logo color={accent} size={26} />{!collapsed && <span className="whitespace-nowrap">OptiMat AI</span>}
          <button type="button" onClick={() => store.set("optimat-nav-collapsed", !collapsed)} aria-label={collapsed ? "Mở rộng menu" : "Thu gọn menu"}
            title={collapsed ? "Mở rộng menu" : "Thu gọn menu"}
            className={`grid size-7 place-items-center rounded-md text-sm font-normal text-nav-muted hover:bg-white/10 max-[860px]:hidden ${collapsed ? "" : "ml-auto"}`}>{collapsed ? "»" : "«"}</button>
        </div>
        <div className="flex flex-col gap-4 max-[860px]:flex-row max-[860px]:flex-wrap max-[860px]:gap-1">
          {groups.map((g) => (
            <div key={g.label || "menu"} className="flex flex-col gap-0.5 max-[860px]:contents">
              {g.label && (collapsed
                ? <hr className="mx-3 mb-1 border-white/10 max-[860px]:hidden" />
                : <div className="px-3 pb-1 text-[11px] font-semibold tracking-[.08em] whitespace-nowrap text-nav-muted uppercase opacity-60 max-[860px]:hidden">{g.label}</div>)}
              {g.items.map(([href, t, icon, b]) => {
                const on = path === href;
                return (
                  <Link key={href} href={href} aria-current={on ? "page" : undefined} title={collapsed ? t : undefined} aria-label={collapsed ? t : undefined}
                    className={`flex h-10 items-center gap-3 rounded-lg px-3 text-[14px] whitespace-nowrap no-underline transition-colors ${collapsed ? "justify-center" : ""} ${on
                      ? `font-semibold text-white ${admin ? "bg-nav-on-admin" : "bg-nav-on-user"}` : "text-nav-muted hover:bg-white/5 hover:text-white"}`}
                    style={on ? { boxShadow: `inset 3px 0 0 ${accent}` } : undefined}>
                    <span aria-hidden className="w-5 shrink-0 text-center text-[15px] leading-none" style={on ? { color: accent } : undefined}>{icon}</span>
                    {!collapsed && <span className="min-w-0 flex-1 truncate">{t}</span>}
                    {!collapsed && b && <span className="rounded-full bg-white/15 px-2 py-px text-[11.5px] text-white">{b}</span>}
                  </Link>
                );
              })}
            </div>
          ))}
        </div>
        {!collapsed && <div className="mt-auto flex flex-col gap-3 border-t border-white/10 pt-4 text-[13px] text-nav-muted max-[860px]:mt-0">
          <div className="flex items-center gap-2.5 px-3">
            <span aria-hidden className="grid size-8 shrink-0 place-items-center rounded-full bg-white/10 text-[12px] font-bold" style={{ color: accent }}>
              {(user?.full_name || user?.email || (admin ? "QT" : "ND")).slice(0, 2).toUpperCase()}
            </span>
            <span className="min-w-0 leading-tight">
              <b className="block truncate text-white">{user ? user.full_name || user.email : admin ? "Quản trị viên" : "Người dùng"}</b>
              <span className="text-[12px]">{user ? (user.role === "admin" ? "Quản trị viên" : "Người dùng") : "Chưa bật đăng nhập"}</span>
            </span>
          </div>
          <div className="flex flex-col [&>*]:flex [&>*]:h-8 [&>*]:items-center [&>*]:rounded-md [&>*]:px-3 [&>*]:text-left [&>*]:no-underline [&>*:hover]:bg-white/5" style={{ color: accent }}>
            {(!user || user.role === "admin") && <Link href={admin ? "/do-boc" : "/tong-quan"}>{admin ? "Xem giao diện người dùng" : "Sang trang quản trị"}</Link>}
            {user ? <button type="button" onClick={logout}>Đăng xuất</button> : <Link href="/dang-nhap">Đổi vai trò</Link>}
            <a href="/docs" target="_blank" rel="noopener">Tài liệu API</a>
          </div>
        </div>}
      </nav>
      {/* trang đo bóc chiếm trọn vùng nội dung (bản vẽ + danh sách), không đệm */}
      <main className={`flex min-w-0 flex-1 flex-col ${path === "/do-boc" ? "" : "gap-[18px] px-[30px] pt-[26px] pb-10 max-[860px]:px-4 max-[860px]:pt-[18px] max-[860px]:pb-8"}`}>
        {!me || (me.auth && !user) ? <Loading>Đang kiểm tra đăng nhập…</Loading>
          : admin && user && user.role !== "admin" ? <Forbidden /> : children}
      </main>
    </div>
  );
}

/** 403: đã đăng nhập nhưng không có quyền quản trị. API cũng trả 403 nên gọi thẳng cũng không được. */
function Forbidden() {
  return (
    <div className="flex flex-col items-start gap-3">
      <h1 className="m-0 text-[23px] font-bold">403 · Không có quyền truy cập</h1>
      <p className="m-0 text-muted">Trang này chỉ dành cho quản trị viên. Liên hệ quản trị viên nếu bạn cần được cấp quyền.</p>
      <Link className="btn primary" href="/do-boc">Về trang người dùng</Link>
    </div>
  );
}
