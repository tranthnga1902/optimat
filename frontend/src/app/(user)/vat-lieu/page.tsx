import type { Metadata } from "next";
import { Bill } from "./bill";
import styles from "./bill.module.css";

export const metadata: Metadata = { title: "Vật liệu và giá" };

export default function Page() {
  return <div className={styles.page}><Bill /></div>;
}
