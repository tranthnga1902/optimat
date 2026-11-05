// Đăng nhập (có PostgreSQL) hoặc chọn vai trò (chế độ kiểm thử đọc CSV, chưa bật đăng nhập).
import type { Metadata } from "next";
import { Logo } from "@/components/ui";
import { LoginPanel } from "./login";

export const metadata: Metadata = { title: "Đăng nhập" };

const ROLES = [
  { href: "/do-boc", title: "Người dùng", text: "Chủ nhà, kỹ sư, nhà thầu: tải bản vẽ, kiểm tra đo bóc, xem vật liệu, giá và phương án", primary: true },
  { href: "/tong-quan", title: "Quản trị viên", text: "Kiểm soát dữ liệu vật liệu, phương án tường, giá, nhà cung cấp và mô hình", primary: false },
];

export default function Login() {
  return (
    <div className="flex min-h-screen flex-wrap">
      <div className="flex flex-[1_1_420px] flex-col justify-between gap-10 bg-nav-user p-14 text-white max-[860px]:px-4 max-[860px]:py-7">
        <div className="flex items-center gap-2.5 text-lg font-bold"><Logo color="#7FD6BF" /> OptiMat AI</div>
        <div>
          <h1 className="m-0 text-[38px] leading-tight font-bold">Từ bản vẽ đến phương án vật liệu tối ưu</h1>
          <p className="max-w-[460px] text-[16.5px] text-nav-muted">Đọc bản vẽ DXF, đo bóc khối lượng tường, tra vật liệu và giá theo danh mục, đề xuất phương án cân bằng chi phí, thời gian cung ứng và khả năng cách nhiệt.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {["AI Agent", "XGBoost", "NSGA-II"].map((t) => <span key={t} className="rounded-full border border-[#3C5A50] px-3 py-1.5 text-[13px] text-nav-muted">{t}</span>)}
        </div>
      </div>
      <div className="flex flex-[1_1_460px] flex-col justify-center p-14 max-[860px]:px-4 max-[860px]:py-7">
        <LoginPanel roles={ROLES} />
      </div>
    </div>
  );
}
