import type { Metadata } from "next";
import { Optimize } from "./optimize";

export const metadata: Metadata = { title: "Phương án tối ưu" };

export default function Page() {
  return <Optimize />;
}
