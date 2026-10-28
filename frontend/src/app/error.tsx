"use client";
// Lỗi khi hiển thị trang: báo lỗi và cho thử lại, không để màn hình trắng.
import Link from "next/link";
import { useEffect } from "react";

export default function ErrorPage({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => { console.error(error); }, [error]);
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-[560px] flex-col justify-center gap-3 p-6">
      <h1 className="m-0 text-[24px] font-bold">Trang gặp lỗi</h1>
      <p className="m-0 text-muted">{error instanceof Error ? error.message : "Lỗi không xác định."} Thử lại; nếu vẫn lỗi, kiểm tra máy chủ API.</p>
      <div className="flex flex-wrap gap-2">
        <button className="btn primary" type="button" onClick={() => retry()}>Thử lại</button>
        <Link className="btn" href="/">Về trang chính</Link>
      </div>
    </main>
  );
}
