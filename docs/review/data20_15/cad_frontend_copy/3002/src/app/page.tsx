"use client";
// Trang gốc: vào thẳng giao diện theo vai trò đã chọn lần trước, chưa chọn thì sang trang chọn vai trò.
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { store } from "@/lib/store";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const role = store.get<string | null>("optimat-role", null);
    router.replace(role === "admin" ? "/tong-quan" : role ? "/do-boc" : "/dang-nhap");
  }, [router]);
  return null;
}
