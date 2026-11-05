import type { Metadata } from "next";
import { Review } from "./Review";

export const metadata: Metadata = { title: "Hồ sơ và đo bóc" };

export default function Page() {
  return <Review />;
}
