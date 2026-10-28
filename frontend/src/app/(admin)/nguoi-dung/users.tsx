"use client";
// Quản lý người dùng (AD01-04): /api/admin/users.
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api, post, put } from "@/lib/api";
import type { User } from "@/lib/auth";
import { Card, Empty, Field, Loading, Note, Pager, Pill } from "@/components/ui";
import { when } from "../tong-quan/dashboard";

type Page = { total: number; page: number; size: number; rows: User[] };
const SIZE = 50;

export function Users() {
  const [q, setQ] = useState({ q: "", role: "", active: "", sort: "user_id", order: "asc", page: 1 });
  const [d, setD] = useState<Page | null>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [editing, setEditing] = useState<User | "new" | null>(null);

  const load = useCallback(() => {
    const p = new URLSearchParams({ ...q, page: String(q.page), size: String(SIZE) });
    api<Page>(`/api/admin/users?${p}`).then((r) => { setD(r); setErr(""); }, (e) => setErr(e.message));
  }, [q]);
  useEffect(load, [load]);

  const done = (text: string) => { setMsg({ text, ok: true }); setEditing(null); load(); };
  const fail = (e: unknown) => setMsg({ text: (e as Error).message, ok: false });
  const toggle = async (u: User) => {
    if (u.is_active && !confirm(`Khóa tài khoản ${u.email}? Người này bị đăng xuất ngay.`)) return;
    try { await put(`/api/admin/users/${u.user_id}`, { is_active: !u.is_active }); done(`${u.is_active ? "Đã khóa" : "Đã mở khóa"} ${u.email}.`); }
    catch (e) { fail(e); }
  };
  const save = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.currentTarget)) as Record<string, string>;
    try {
      if (editing === "new") { await post("/api/admin/users", f); done(`Đã tạo tài khoản ${f.email}.`); }
      else if (editing) {
        await put(`/api/admin/users/${editing.user_id}`, { full_name: f.full_name, role: f.role, ...(f.password ? { password: f.password } : {}) });
        done(`Đã lưu ${editing.email}.`);
      }
    } catch (e) { fail(e); }
  };
  const set = (k: string, v: string) => setQ((o) => ({ ...o, [k]: v, page: 1 }));

  return (
    <>
      <Card>
        <div className="flex flex-wrap items-end gap-2">
          <Field label="Tìm"><input className="field" placeholder="Email, họ tên" value={q.q} onChange={(e) => set("q", e.target.value)} /></Field>
          <Field label="Vai trò">
            <select className="field" value={q.role} onChange={(e) => set("role", e.target.value)}>
              <option value="">Tất cả</option><option value="admin">Quản trị viên</option><option value="user">Người dùng</option>
            </select>
          </Field>
          <Field label="Trạng thái">
            <select className="field" value={q.active} onChange={(e) => set("active", e.target.value)}>
              <option value="">Tất cả</option><option value="true">Đang mở</option><option value="false">Đã khóa</option>
            </select>
          </Field>
          <Field label="Sắp xếp">
            <select className="field" value={`${q.sort}:${q.order}`} onChange={(e) => { const [sort, order] = e.target.value.split(":"); setQ((o) => ({ ...o, sort, order })); }}>
              <option value="user_id:asc">Cũ nhất trước</option><option value="created_at:desc">Mới nhất trước</option>
              <option value="email:asc">Email A→Z</option><option value="full_name:asc">Họ tên A→Z</option>
            </select>
          </Field>
          <button className="btn primary ml-auto" type="button" onClick={() => { setEditing("new"); setMsg(null); }}>+ Tạo tài khoản</button>
        </div>
        {msg && <Note tone={msg.ok ? "ok" : "warn"}>{msg.text}</Note>}
        {editing && (
          <form key={editing === "new" ? "new" : editing.user_id} onSubmit={save}
            className="grid items-end gap-3 rounded-[10px] border border-rule p-3.5 [grid-template-columns:repeat(auto-fit,minmax(190px,1fr))]">
            <Field label="Email *"><input className="field" name="email" type="email" required readOnly={editing !== "new"}
              defaultValue={editing === "new" ? "" : editing.email} /></Field>
            <Field label="Họ tên"><input className="field" name="full_name" defaultValue={editing === "new" ? "" : editing.full_name} /></Field>
            <Field label="Vai trò">
              <select className="field" name="role" defaultValue={editing === "new" ? "user" : editing.role}>
                <option value="user">Người dùng</option><option value="admin">Quản trị viên</option>
              </select>
            </Field>
            <Field label={editing === "new" ? "Mật khẩu *" : "Mật khẩu mới"} hint={editing === "new" ? "ít nhất 8 ký tự" : "để trống nếu không đổi"}>
              <input className="field" name="password" type="password" autoComplete="new-password" minLength={8} required={editing === "new"} />
            </Field>
            <div className="flex gap-2">
              <button className="btn primary" type="submit">{editing === "new" ? "Tạo" : "Lưu"}</button>
              <button className="btn" type="button" onClick={() => setEditing(null)}>Hủy</button>
            </div>
          </form>
        )}
      </Card>
      <Card>
        {err ? <Note>{err}</Note> : !d ? <Loading /> : !d.rows.length ? <Empty>Không có tài khoản nào khớp.</Empty> : <>
          <div className="tw max-h-[65vh] overflow-y-auto">
            <table className="nonum">
              <thead className="sticky top-0 bg-card"><tr><th>Email</th><th>Họ tên</th><th>Vai trò</th><th>Trạng thái</th><th>Ngày tạo</th><th /></tr></thead>
              <tbody>
                {d.rows.map((u) => (
                  <tr key={u.user_id}>
                    <td>{u.email}</td><td>{u.full_name}</td>
                    <td>{u.role === "admin" ? <Pill level="info">Quản trị viên</Pill> : "Người dùng"}</td>
                    <td>{u.is_active ? <Pill level="ok">Đang mở</Pill> : <Pill level="bad">Đã khóa</Pill>}</td>
                    <td className="whitespace-nowrap">{when(u.created_at)}</td>
                    <td className="whitespace-nowrap">
                      <button className="btn" type="button" onClick={() => { setEditing(u); setMsg(null); }}>Sửa</button>{" "}
                      <button className="btn" type="button" onClick={() => toggle(u)}>{u.is_active ? "Khóa" : "Mở khóa"}</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={d.page} size={d.size} total={d.total} onPage={(page) => setQ((o) => ({ ...o, page }))} />
        </>}
      </Card>
    </>
  );
}
