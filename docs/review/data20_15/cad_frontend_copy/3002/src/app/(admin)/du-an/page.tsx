import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Projects } from "./projects";

export const metadata: Metadata = { title: "Dự án" };

export default function Page() {
  return (
    <>
      <Head title="Dự án">Dự án của mọi người dùng, kèm hồ sơ bản vẽ, các lần bóc tách và tối ưu. Chọn một dự án để xem chi tiết.</Head>
      <Projects />
    </>
  );
}
