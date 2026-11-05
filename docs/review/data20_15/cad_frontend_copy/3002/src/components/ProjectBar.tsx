"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useStored } from "@/lib/store";

export function ProjectBar() {
  const name = useStored("optimat-project-name", "");
  if (usePathname() === "/du-an-cua-toi") return null;
  return <div className="flex flex-wrap items-center gap-3 border-b border-rule bg-card px-5 py-2">
    <strong>{name || "Chưa mở dự án"}</strong>
    <Link className="btn" href="/du-an-cua-toi">{name ? "Quản lý dự án và lịch sử" : "Nhập thông tin dự án"}</Link>
  </div>;
}
