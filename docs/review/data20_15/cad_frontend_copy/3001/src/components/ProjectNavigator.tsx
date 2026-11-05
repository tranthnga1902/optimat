"use client";
import type { ReactNode } from "react";
import styles from "./ProjectNavigator.module.css";

export type ProjectNavigatorItem = {
  key: string;
  name: string;
  location?: string;
  source: string;
  current?: boolean;
  open: () => void;
};
export type ProjectNavigatorProps = {
  projects: ProjectNavigatorItem[];
  totalCount: number;
  query: string;
  onQueryChange: (value: string) => void;
  onCreate: () => void;
  disabled?: boolean;
  createDisabled?: boolean;
  error?: ReactNode;
};

export function ProjectNavigator({ projects, totalCount, query, onQueryChange, onCreate, disabled, createDisabled, error }: ProjectNavigatorProps) {
  return <section className={styles.navigator} aria-label="Danh sách dự án">
    <div className={styles.heading}><h2>Danh sách dự án</h2><span className={styles.count}>{totalCount}</span></div>
    <label className={styles.search}><span className={styles.visuallyHidden}>Tìm dự án theo tên hoặc địa điểm</span>
      <input className="field" type="search" value={query} placeholder="Tìm dự án…" onChange={event => onQueryChange(event.target.value)} />
    </label>
    <button type="button" className="btn primary" disabled={disabled || createDisabled} onClick={onCreate}>+ Tạo dự án</button>
    <div className={styles.list}>
      {projects.map(project => <button key={project.key} type="button" disabled={disabled}
        className={`${styles.project} ${project.current ? styles.current : ""}`}
        aria-current={project.current ? "true" : undefined} onClick={project.open}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M3 6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z" /></svg>
        <span className={styles.projectText}><strong>{project.name}</strong>{project.current && <span className={styles.activeLabel}>Đang mở</span>}
          {project.location && <span className={styles.meta}>{project.location}</span>}<span className={styles.meta}>{project.source}</span>
        </span><span aria-hidden="true">›</span>
      </button>)}
      {!projects.length && <p className={styles.empty}>{totalCount ? "Không tìm thấy dự án phù hợp." : "Chưa có dự án. Chọn Tạo dự án để bắt đầu."}</p>}
    </div>
    {error && <div role="alert">{error}</div>}
    <p className={styles.footer}>{query.trim() ? `${projects.length}/${totalCount}` : totalCount} dự án</p>
  </section>;
}

export function ProjectWorkspaceLayout({ navigator, children, detailOpen, onBack, backDisabled }: { detailOpen: boolean; onBack: () => void; backDisabled: boolean; navigator: ReactNode; children: ReactNode }) {
  return <div className={styles.workspace} data-detail={detailOpen}><aside className={styles.sidebar}>{navigator}</aside><div className={styles.detail}><button type="button" className={styles.back} onClick={onBack} disabled={backDisabled}>← Danh sách dự án</button>{children}</div></div>;
}
