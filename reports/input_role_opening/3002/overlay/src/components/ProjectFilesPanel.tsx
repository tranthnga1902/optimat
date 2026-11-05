"use client";
import type { ReactNode } from "react";
import { Sheet, type Col } from "@/components/Sheet";
import { Card, Empty, Note } from "@/components/ui";
import styles from "./ProjectFilesPanel.module.css";

export type ProjectFileRevision = {
  project_id: number;
  file_id: number;
  revision_id: number;
  version: number | null;
  sha256: string | null;
  name: string;
  original_format: string;
  size_bytes: number | null;
  role: "KT" | "KC" | "HO_SO" | "TIEN_LUONG" | "THAM_KHAO" | null;
  uploaded_at: string | null;
  analysis_status?: string;
};

export type FilePreview =
  | { status: "idle" }
  | { status: "loading"; revision_id: number }
  | { status: "ready"; revision_id: number; content: ReactNode; warnings?: string[] }
  | { status: "unsupported" | "forbidden" | "error"; revision_id: number; message: string };

export type ProjectFilesPanelProps = {
  projectId: number;
  projectInfo: ReactNode;
  sourceContext?: ReactNode;
  analysisContext?: ReactNode;
  files: ProjectFileRevision[];
  selectedRevisionIds: number[];
  viewingRevisionId?: number;
  preview: FilePreview;
  loading?: boolean;
  busy?: boolean;
  error?: string;
  startBlockedReason?: string;
  uploadControls?: ReactNode;
  onView: (file: ProjectFileRevision) => void;
  onDownload: (file: ProjectFileRevision) => void;
  onSelectionChange: (revisionIds: number[]) => void;
  onStartAnalysis: () => void;
};

const roleName = (role: ProjectFileRevision["role"]) => role === "KT" ? "Kiến trúc" : role === "KC" ? "Kết cấu" : role === "HO_SO" ? "Hồ sơ" : role === "TIEN_LUONG" ? "Tiên lượng" : role === "THAM_KHAO" ? "Tham khảo" : "Chưa xác định";
const versionName = (file: ProjectFileRevision) => file.version == null ? "Chưa xác định phiên bản" : `Phiên bản ${file.version}`;
const uploadedAt = (value: string | null) => value ? new Date(value).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" }) : "Chưa xác định";

const canAnalyze = (file: ProjectFileRevision) => (file.role === "KT" || file.role === "KC") && /^(dwg|dxf)$/i.test(file.original_format);

export function ProjectFilesPanel(props: ProjectFilesPanelProps) {
  const { projectId, files, selectedRevisionIds, viewingRevisionId, preview, busy, loading } = props;
  const revisions = files.filter(file => file.project_id === projectId);
  const selected = revisions.filter(file => selectedRevisionIds.includes(file.revision_id));
  const viewing = revisions.find(file => file.revision_id === viewingRevisionId);
  const matchingPreview = viewing && preview.status !== "idle" && preview.revision_id === viewing.revision_id ? preview : null;
  let blockedReason = props.startBlockedReason || "";
  if (!blockedReason) {
    if (new Set(selectedRevisionIds).size !== selectedRevisionIds.length) blockedReason = "Danh sách có phiên bản bị chọn trùng. Hãy chọn lại.";
    else if (selected.length !== selectedRevisionIds.length) blockedReason = "Danh sách đã chọn không còn khớp hồ sơ dự án. Hãy chọn lại.";
    else if (!selected.length) blockedReason = "Chọn phiên bản cần phân tích trong bảng hồ sơ.";
    else if (selected.some(file => !/^[a-f0-9]{64}$/i.test(file.sha256 || "") || !file.role || !Number.isSafeInteger(file.version) || (file.version ?? 0) < 1)) blockedReason = "Hồ sơ đã chọn thiếu hoặc không hợp lệ phiên bản, mã kiểm tra hoặc vai trò. Cần bổ sung trước khi phân tích.";
    else if (new Set(selected.map(file => file.file_id)).size !== selected.length) blockedReason = "Chỉ chọn một phiên bản cho mỗi tệp.";
    else if (selected.some(file => !canAnalyze(file))) blockedReason = "Chỉ chọn tệp CAD kiến trúc hoặc kết cấu để phân tích.";
    else if (!selected.some(file => file.role === "KT")) blockedReason = "Luồng bóc cả nhà cần một bản CAD kiến trúc. Chọn phiên bản kiến trúc trong hồ sơ hoặc bổ sung tệp còn thiếu.";
  }
  const cols: Col<ProjectFileRevision>[] = [
    { key: "name", title: "Tên tệp gốc" },
    { key: "role", title: "Vai trò", text: file => roleName(file.role) },
    { key: "version", title: "Phiên bản", text: file => versionName(file) },
    { key: "original_format", title: "Định dạng", text: file => file.original_format.toUpperCase() || "Chưa xác định" },
    { key: "size_bytes", title: "Dung lượng", num: true, text: file => file.size_bytes == null ? "Chưa xác định" : `${(file.size_bytes / 1024).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} KB` },
    { key: "uploaded_at", title: "Thời điểm tải", text: file => uploadedAt(file.uploaded_at) },
    { key: "analysis_status", title: "Phân tích", text: file => file.analysis_status || "Chưa xác định trạng thái" },
  ];
  return <div className={styles.panel}>
    <Card title="Thông tin dự án">{props.projectInfo}</Card>
    <Card title="Hồ sơ và tài liệu gốc">
      <p className={styles.hint}>Mở xem để kiểm tra bản vẽ. Đánh dấu riêng các phiên bản muốn phân tích.</p>
      {props.uploadControls}
      {props.error && <div role="alert"><Note>{props.error}</Note></div>}
      {loading ? <p role="status">Đang tải danh sách hồ sơ…</p> : !revisions.length ? <Empty>Chưa có bản vẽ trong dự án này.</Empty> : <Sheet
        cols={cols} rows={revisions} file="ho-so-ban-ve.csv"
        rowClass={file => file.revision_id === viewingRevisionId ? styles.viewingRow : ""}
        actions={file => <div className={styles.actions}>
          <button type="button" className="btn" disabled={busy} aria-pressed={file.revision_id === viewingRevisionId} onClick={() => props.onView(file)}>Xem</button>
          <button type="button" className="btn" disabled={busy} onClick={() => props.onDownload(file)}>Tải nguyên bản</button>
          <label><input type="checkbox" disabled={busy || (!canAnalyze(file) && !selectedRevisionIds.includes(file.revision_id))} checked={selectedRevisionIds.includes(file.revision_id)} aria-label={`Chọn phân tích ${file.name}, ${versionName(file)}`} onChange={event => props.onSelectionChange(event.target.checked ? [...selectedRevisionIds, file.revision_id] : selectedRevisionIds.filter(id => id !== file.revision_id))} /> Chọn phân tích</label>
        </div>}
      />}
      {props.sourceContext && <details><summary>Căn cứ của thông tin dự án</summary>{props.sourceContext}</details>}
    </Card>
    <Card title="Xem bản vẽ">
      {!viewing ? <Empty>Chọn “Xem” tại phiên bản muốn kiểm tra.</Empty> : <>
        <div className={styles.viewerHeading}><div><strong>{viewing.name}</strong><p className={styles.hint}>{versionName(viewing)} · {roleName(viewing.role)} · Định dạng gốc: {viewing.original_format.toUpperCase() || "Chưa xác định"}</p></div><button type="button" className="btn" disabled={busy} onClick={() => props.onDownload(viewing)}>Tải nguyên bản này</button></div>
        <p className={styles.hint}>Bản xem trước được dựng từ tệp gốc; mở xem không chạy phân tích khối lượng.</p>
        {!matchingPreview || matchingPreview.status === "loading" ? <p role="status">Đang chờ bản xem đúng phiên bản đã chọn…</p> : matchingPreview.status === "ready" ? <>
          {matchingPreview.warnings?.map((warning, index) => <Note key={index}>{warning}</Note>)}
          <div className={styles.viewer}>{matchingPreview.content}</div>
        </> : <div role="alert"><Note>{matchingPreview.message}</Note></div>}
      </>}
    </Card>
    <Card title="Phiên bản sẽ phân tích">
      {props.analysisContext}
      {!!selected.length && <ul className={styles.selection}>{selected.map(file => <li key={file.revision_id}><strong>{file.name}</strong> · {versionName(file)} · {roleName(file.role)}</li>)}</ul>}
      {selected.some(file => file.role === "KT" && canAnalyze(file)) && <p className={styles.hint}>Bản kiến trúc dùng để kiểm mặt bằng, tường và lỗ mở. {selected.some(file => file.role === "KC" && canAnalyze(file))
        ? "Bản kết cấu được đọc riêng để đối chiếu vị trí, mặt cắt và bảng thép."
        : "Chưa chọn bản kết cấu riêng. Nếu chi tiết móng, dầm, cột hoặc thép nằm ở tệp khác, hãy chọn thêm tệp đó."}</p>}
      {blockedReason && <p className={styles.hint}>{blockedReason}</p>}
      <div className={styles.start}><p className={styles.hint}>Chỉ nút này bắt đầu phân tích các phiên bản đã chọn; không yêu cầu tải lại tệp.</p><button type="button" className="btn primary" disabled={busy || loading || !!blockedReason} onClick={props.onStartAnalysis}>Bắt đầu phân tích</button></div>
    </Card>
  </div>;
}
