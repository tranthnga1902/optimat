import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Models } from "./models";

export const metadata: Metadata = { title: "Mô hình và cấu hình" };

export default function Page() {
  return (
    <>
      <Head title="Mô hình và cấu hình">
        Mô hình giá XGBoost huấn luyện trên máy (<code>python -m optimat.predict.train</code>); chỉ số chỉ dùng để báo cáo khi dữ liệu là ACTUAL.
      </Head>
      <Models />
    </>
  );
}
