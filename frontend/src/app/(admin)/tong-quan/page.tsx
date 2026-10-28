import type { Metadata } from "next";
import { Head } from "@/components/ui";
import { Dashboard } from "./dashboard";

export const metadata: Metadata = { title: "Tổng quan" };

export default function Page() {
  return (
    <>
      <Head title="Tổng quan hệ thống">Số liệu đếm trực tiếp trong PostgreSQL, không có số minh họa. Ô trống là chưa có dữ liệu.</Head>
      <Dashboard />
    </>
  );
}
