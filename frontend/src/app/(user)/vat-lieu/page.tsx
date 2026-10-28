import type { Metadata } from "next";
import { Bill } from "./bill";

export const metadata: Metadata = { title: "Vật liệu và giá" };

export default function Page() {
  return <Bill />;
}
