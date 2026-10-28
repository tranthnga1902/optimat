import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Mapping } from "./mapping";

export const metadata: Metadata = { title: "Duyệt mapping" };

export default function Page() {
  return (
    <>
      <Head title="Duyệt mapping hồ sơ kiến trúc–kết cấu" />
      <Mapping />
    </>
  );
}
