import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Ingest } from "./ingest";

export const metadata: Metadata = { title: "Tiếp nhận hồ sơ CAD" };

export default function Page() {
  return (
    <>
      <Head title="Tiếp nhận hồ sơ CAD">Nhận .dxf, .dwg. Bản kiểm kê chỉ mô tả bản vẽ; khung bao không dùng để tính khối lượng.</Head>
      <Ingest />
    </>
  );
}
