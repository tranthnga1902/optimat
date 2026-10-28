import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Rules } from "./rules";

export const metadata: Metadata = { title: "Quy tắc bóc tách" };

export default function Page() {
  return (
    <>
      <Head title="Quy tắc bóc tách">
        Các bảng quy tắc dùng khi đọc bản vẽ và bóc khối lượng. Sửa ở đây ghi thẳng vào PostgreSQL và có hiệu lực ngay ở lần bóc tách sau. Di chuột lên tên cột để xem cách điền.
      </Head>
      <Rules />
    </>
  );
}
