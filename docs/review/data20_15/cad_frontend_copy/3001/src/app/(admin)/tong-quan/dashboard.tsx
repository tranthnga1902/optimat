"use client";
// Tổng quan (AD01-06): đếm từ database qua /api/admin/dashboard.
import Link from "next/link";
import { useEffect, useState } from "react";
import { api, int } from "@/lib/api";
import { Card, Empty, Loading, Note, Tile, Tiles } from "@/components/ui";

type Log = { log_id: number; action: string; email: string | null; detail: Record<string, unknown>; created_at: string };
type Dash = {
  connected: boolean; projects?: number; files?: number; takeoffs?: number; takeoffs_confirmed?: number; runs?: number; runs_agent?: number;
  users?: number; users_active?: number; data_errors?: number | null; api_cost?: number | null; recent?: Log[];
};

export const ACTIONS: Record<string, string> = {
  login: "Đăng nhập", login_failed: "Đăng nhập sai", user_create: "Tạo tài khoản", user_update: "Sửa tài khoản",
  user_lock: "Khóa tài khoản", user_unlock: "Mở khóa tài khoản", admin_insert: "Thêm dòng", admin_update: "Sửa dòng", admin_delete: "Xóa dòng",
};

export const when = (s: string | null) => (s ? new Date(s).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" }) : "");

export function Dashboard() {
  const [d, setD] = useState<Dash | null>(null);
  const [err, setErr] = useState("");
  const load = () => { api<Dash>("/api/admin/dashboard").then((r) => { setD(r); setErr(""); }, (e) => setErr(e.message)); };
  useEffect(load, []);
  if (err) return <Note>{err} <button className="btn" type="button" onClick={load}>Thử lại</button></Note>;
  if (!d) return <Loading />;
  if (!d.connected) return <Note>Chưa kết nối PostgreSQL (DATABASE_URL): chưa có dự án, người dùng hay lượt chạy nào để thống kê.</Note>;
  return (
    <>
      <Tiles>
        <Tile k="Dự án" v={int(d.projects!)} s={<Link href="/du-an">Xem danh sách</Link>} />
        <Tile k="Hồ sơ CAD" v={int(d.files!)} s="file DWG, DXF đã tải lên" />
        <Tile k="Lượt bóc tách" v={int(d.takeoffs!)} s={`${int(d.takeoffs_confirmed!)} đã xác nhận`} />
        <Tile k="Lỗi dữ liệu cần xử lý" v={d.data_errors == null ? "—" : int(d.data_errors)} tone={d.data_errors ? "bad" : ""}
          s={d.data_errors == null ? "chưa kiểm được" : <Link href="/kiem-soat">Kiểm soát dữ liệu</Link>} />
        <Tile k="Lần tối ưu" v={int(d.runs!)} s={`${int(d.runs_agent!)} lần qua AI Agent`} />
        <Tile k="Người dùng" v={int(d.users!)} s={<>{int(d.users_active!)} đang mở · <Link href="/nguoi-dung">Quản lý</Link></>} />
        <Tile k="Chi phí API" v={d.api_cost == null ? "—" : d.api_cost} s="chưa ghi vào database (AD05-08)" />
      </Tiles>
      <Card title="Hoạt động gần đây">
        {d.recent!.length ? (
          <div className="tw">
            <table className="nonum">
              <thead><tr><th>Thời gian</th><th>Người thực hiện</th><th>Thao tác</th><th>Chi tiết</th></tr></thead>
              <tbody>
                {d.recent!.map((r) => (
                  <tr key={r.log_id}>
                    <td className="whitespace-nowrap">{when(r.created_at)}</td>
                    <td>{r.email || "hệ thống"}</td>
                    <td>{ACTIONS[r.action] || r.action}</td>
                    <td className="text-[12.5px] text-muted">{summary(r.detail)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <Empty>Chưa có thao tác nào được ghi.</Empty>}
      </Card>
    </>
  );
}

const summary = (d: Record<string, unknown>) =>
  [d.table && `bảng ${d.table}`, d.id != null && `dòng ${d.id}`, d.email, d.fields && `sửa: ${(d.fields as string[]).join(", ")}`]
    .filter(Boolean).join(" · ");
