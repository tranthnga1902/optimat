import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Concepts } from "./concepts";

export const metadata: Metadata = { title: "Ký hiệu nhận diện bản vẽ" };

export default function Page() {
  return (
    <>
      <Head title="Ký hiệu nhận diện bản vẽ" actions={<a className="btn" href="/api/concepts/csv">Tải concepts.csv</a>}>
        Tên layer, tên block nào thì là đối tượng gì (bảng <code>drawing_concepts</code>, Quy ước bản vẽ v1.0). Dòng khớp đầu tiên thắng. Sửa ở đây thì lần đọc bản vẽ sau dùng ngay.
      </Head>
      <Concepts />
    </>
  );
}
