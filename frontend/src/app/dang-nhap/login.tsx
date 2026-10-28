"use client";
// Có PostgreSQL: biểu mẫu đăng nhập (api/auth.py). Chưa có: chọn vai trò như trước (chế độ kiểm thử, không có người dùng).
import Link from "next/link";
import { useState, type FormEvent } from "react";
import { post } from "@/lib/api";
import { useMe, type User } from "@/lib/auth";
import { Field, Loading, Note } from "@/components/ui";

type RoleCard = { href: string; title: string; text: string; primary: boolean };

export function LoginPanel({ roles }: { roles: RoleCard[] }) {
  const me = useMe();
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const go = (u: User) => {
    const next = new URLSearchParams(window.location.search).get("next");
    // chỉ nhận đường dẫn nội bộ, không chuyển ra trang ngoài
    window.location.href = next && next.startsWith("/") && !next.startsWith("//") ? next : u.role === "admin" ? "/tong-quan" : "/do-boc";
  };
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true); setMsg("");
    const setup = Boolean(me?.setup);
    if (setup && f.get("password") !== f.get("password2")) { setMsg("Hai lần nhập mật khẩu không khớp."); setBusy(false); return; }
    try {
      go((await post<{ user: User }>(setup ? "/api/auth/setup" : "/api/auth/login",
        { email: f.get("email"), password: f.get("password"), full_name: f.get("full_name") || "" })).user);
    }
    catch (err) { setMsg((err as Error).message); setBusy(false); }
  };

  if (!me) return <Loading />;
  if (me.auth && me.user) {
    return (
      <div className="mx-auto flex w-full max-w-[420px] flex-col gap-3.5">
        <h2 className="m-0 text-[26px] font-bold">Đã đăng nhập</h2>
        <p className="m-0 text-muted">{me.user.full_name || me.user.email} · {me.user.role === "admin" ? "Quản trị viên" : "Người dùng"}</p>
        <button className="btn primary" type="button" onClick={() => go(me.user!)}>Tiếp tục</button>
      </div>
    );
  }
  if (me.auth) {
    return (
      <form onSubmit={submit} className="mx-auto flex w-full max-w-[420px] flex-col gap-3.5">
        {me.setup ? <div>
          <h2 className="m-0 mb-1 text-[26px] font-bold">Tạo quản trị viên đầu tiên</h2>
          <p className="m-0 text-muted">Hệ thống chưa có tài khoản quản trị nào. Tài khoản tạo ở đây có toàn quyền; sau đó thêm người khác ở trang Người dùng.</p>
        </div> : <div>
          <h2 className="m-0 mb-1 text-[26px] font-bold">Đăng nhập</h2>
          <p className="m-0 text-muted">Dùng tài khoản do quản trị viên cấp.</p>
        </div>}
        <Field label="Email"><input className="field" name="email" type="email" autoComplete="username" required autoFocus /></Field>
        {me.setup && <Field label="Họ tên"><input className="field" name="full_name" autoComplete="name" /></Field>}
        <Field label="Mật khẩu" hint={me.setup ? "ít nhất 8 ký tự" : undefined}>
          <input className="field" name="password" type="password" autoComplete={me.setup ? "new-password" : "current-password"} required minLength={8} />
        </Field>
        {me.setup && <Field label="Nhập lại mật khẩu"><input className="field" name="password2" type="password" autoComplete="new-password" required minLength={8} /></Field>}
        {msg && <Note>{msg}</Note>}
        <button className="btn primary" type="submit" disabled={busy}>
          {busy ? "Đang xử lý…" : me.setup ? "Tạo tài khoản quản trị" : "Đăng nhập"}
        </button>
      </form>
    );
  }
  return (
    <div className="mx-auto flex w-full max-w-[460px] flex-col gap-3.5">
      <div>
        <h2 className="m-0 mb-1 text-[26px] font-bold">Chọn vai trò</h2>
        <p className="m-0 text-muted">Chưa kết nối PostgreSQL nên chưa bật đăng nhập (chế độ kiểm thử); chọn vai trò để vào giao diện tương ứng.</p>
      </div>
      {roles.map((r) => (
        <Link key={r.href} href={r.href} className={`flex flex-col rounded-[10px] border px-[18px] py-4 no-underline ${r.primary
          ? "border-accent bg-accent text-accent-ink" : "border-field bg-card text-ink"}`}>
          <b className="text-base">{r.title}</b><span className="text-[13px] opacity-85">{r.text}</span>
        </Link>
      ))}
    </div>
  );
}
