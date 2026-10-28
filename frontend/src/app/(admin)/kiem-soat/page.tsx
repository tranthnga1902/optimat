import type { Metadata } from "next";
import { DataCheck } from "./check";

export const metadata: Metadata = { title: "Kiểm soát dữ liệu" };

export default function Page() {
  return <DataCheck />;
}
