import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Database } from "./database";

export const metadata: Metadata = { title: "Cơ sở dữ liệu" };

export default function Page() {
  return (
    <>
      <Head title="Cơ sở dữ liệu">
        Các bảng PostgreSQL theo cụm (số bảng, số dòng đếm trực tiếp bên dưới). Sửa trực tiếp các bảng quy tắc nhận dạng và bảng đại lý (<code>suppliers</code>, <code>supplier_materials</code>); danh mục vật liệu, phương án tường sửa ở <code>data/catalog/materials_master.xlsx</code>.
      </Head>
      <Database />
    </>
  );
}
