// 404: đường dẫn không có trong ứng dụng.
import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen max-w-[520px] flex-col justify-center gap-3 p-6">
      <h1 className="m-0 text-[28px] font-bold">404 · Không tìm thấy trang</h1>
      <p className="m-0 text-muted">Đường dẫn không tồn tại hoặc đã được đổi tên.</p>
      <div className="flex flex-wrap gap-2"><Link className="btn primary" href="/">Về trang chính</Link></div>
    </main>
  );
}
