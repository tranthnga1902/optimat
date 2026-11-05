import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Users } from "./users";

export const metadata: Metadata = { title: "Người dùng" };

export default function Page() {
  return (
    <>
      <Head title="Người dùng">
        Tạo tài khoản, phân quyền, khóa hoặc mở khóa. Không xóa tài khoản: xóa sẽ xóa luôn dự án của người đó, nên chỉ khóa. Mọi thay đổi ghi vào nhật ký.
      </Head>
      <Users />
    </>
  );
}
