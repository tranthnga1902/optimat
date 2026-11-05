import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Catalog } from "./catalog";

export const metadata: Metadata = { title: "Vật liệu và phương án tường" };

export default function Page() {
  return (
    <>
      <Head title="Vật liệu và phương án tường">
        Mã dùng chung cho bóc tách, tối ưu và tra giá. Nguồn: <code>data/catalog/materials_master.xlsx</code> → <code>python scripts/build_materials_sql.py</code> (sinh SQL và CSV cùng lúc).
      </Head>
      <Catalog />
    </>
  );
}
