import type { Metadata } from "next";
import { Rough } from "./rough";

export const metadata: Metadata = { title: "Phần thô" };

export default function Page() {
  return <Rough />;
}
