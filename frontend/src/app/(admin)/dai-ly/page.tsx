import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Dealers } from "./dealers";

export const metadata: Metadata = { title: "Đại lý" };

export default function Page() {
  return (
    <>
      <Head title="Đại lý">
        Danh bạ đại lý vật liệu miền Bắc (nạp bằng <code>scripts/import_dealers.py</code>). Bấm một dòng hoặc một điểm trên bản đồ để xem chi tiết, sửa và ghi chép.
      </Head>
      <Dealers />
    </>
  );
}
