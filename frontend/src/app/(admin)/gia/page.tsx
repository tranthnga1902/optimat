import type { Metadata } from "next";
import { Offers } from "./offers";

export const metadata: Metadata = { title: "Giá và nhà cung cấp" };

export default function Page() {
  return <Offers />;
}
