import type { Metadata } from "next";
import { EstimateCheck } from "./check";

export const metadata: Metadata = { title: "Kiểm tra sai lệch dự toán" };

export default function Page() {
  return <EstimateCheck />;
}
