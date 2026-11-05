import type { ReactNode } from "react";
import type { ProjectInfo } from "@/lib/projects";
import styles from "./ProjectInfoSummary.module.css";

type Field = "location" | "buildingType" | "floors" | "note" | "materialNeeds";
export type ProjectInfoSummaryProps = {
  name: string;
  info: ProjectInfo;
  storageLabel?: string;
  sources?: Partial<Record<Field, ReactNode>>;
};

const fields: { key: Field; label: string; unit?: string; long?: boolean }[] = [
  { key: "location", label: "Địa điểm" },
  { key: "buildingType", label: "Loại công trình" },
  { key: "floors", label: "Số tầng", unit: "tầng" },
  { key: "note", label: "Mô tả", long: true },
  { key: "materialNeeds", label: "Nhu cầu vật liệu", long: true },
];

function TextValue({ value, label }: { value: string; label: string }) {
  if (value.length <= 180 && value.split("\n").length <= 3) return <p className={styles.value}>{value}</p>;
  return <details className={styles.longText}>
    <summary aria-label={`Mở hoặc thu gọn ${label.toLocaleLowerCase("vi-VN")}`}>
      <span className={styles.preview}>{value}</span>
      <span className={styles.expand}>Xem đầy đủ</span><span className={styles.collapse}>Thu gọn</span>
    </summary>
    <p className={styles.value}>{value}</p>
  </details>;
}

export function ProjectInfoSummary({ name, info, storageLabel, sources }: ProjectInfoSummaryProps) {
  const present = fields.filter(field => info[field.key]?.trim());
  const missing = fields.filter(field => !info[field.key]?.trim());
  const unknownSources = present.filter(field => !sources?.[field.key]);
  return <section className={styles.summary} aria-label="Thông tin công trình">
    <h3 className={styles.name}>{name.trim() ? name : "Chưa có tên công trình"}</h3>
    {(present.some(field => !field.long) || storageLabel) && <dl className={styles.grid}>
      {present.filter(field => !field.long).map(field => <div className={styles.field} key={field.key}>
        <dt>{field.label}</dt><dd>{info[field.key]}{field.unit && ` ${field.unit}`}</dd>
        {sources?.[field.key] && <dd className={styles.source}>Nguồn: {sources[field.key]}</dd>}
      </div>)}
      {storageLabel && <div className={styles.field}><dt>Nơi lưu</dt><dd>{storageLabel}</dd></div>}
    </dl>}
    {present.filter(field => field.long).map(field => <div key={field.key} className={styles.description}>
      <h4>{field.label}</h4><TextValue value={info[field.key]!} label={field.label} />
      {sources?.[field.key] && <div className={styles.source}>Nguồn: {sources[field.key]}</div>}
    </div>)}
    {!!missing.length && <p className={styles.note}>Chưa có thông tin: {missing.map(field => field.label.toLocaleLowerCase("vi-VN")).join(", ")}.</p>}
    {!!unknownSources.length && <p className={styles.note}>Chưa xác định nguồn: {unknownSources.map(field => field.label.toLocaleLowerCase("vi-VN")).join(", ")}.</p>}
  </section>;
}
