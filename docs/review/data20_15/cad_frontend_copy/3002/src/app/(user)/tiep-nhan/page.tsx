import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Ingest } from "./ingest";

export const metadata: Metadata = { title: "Tiếp nhận hồ sơ CAD" };

export default function Page() {
  return (
    <>
      <Head title="Tiếp nhận hồ sơ CAD">Nhận DXF trực tiếp và chuyển DWG để đọc. Với DWF, hãy chuyển sang DXF trước khi tải lên. Bản kiểm kê chỉ mô tả bản vẽ; khung bao không dùng để tính khối lượng.</Head>
      <Ingest />
    </>
  );
}
