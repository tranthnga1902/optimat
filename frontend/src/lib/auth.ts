"use client";
// Phiên đăng nhập (api/auth.py). auth = false: chưa có PostgreSQL, chưa bật đăng nhập (giữ cách chọn vai trò cũ).
// Phân quyền thật nằm ở API (401/403); phía giao diện chỉ chuyển trang cho đúng.
import { useEffect, useState } from "react";
import { api } from "./api";

export type User = { user_id: number; email: string; full_name: string; role: "admin" | "user"; is_active: boolean; created_at: string | null };
// setup: database chưa có quản trị viên nào, trang đăng nhập cho tạo người đầu tiên
export type Me = { auth: boolean; user: User | null; setup?: boolean };

export function useMe(): Me | null {
  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => { api<Me>("/api/auth/me").then(setMe, () => setMe({ auth: false, user: null, setup: false })); }, []);
  return me;
}

export async function logout() {
  await api("/api/auth/logout", { method: "POST" });
  // tải lại hẳn trang để xóa mọi dữ liệu của phiên cũ đang nằm trong bộ nhớ trình duyệt
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination
  window.location.assign("/dang-nhap");
}
