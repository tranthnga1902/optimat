"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import styles from "./AssistantWindow.module.css";

export type AssistantWindowProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  context?: ReactNode;
  children: ReactNode;
};

export function AssistantWindow({ open, onOpenChange, title = "AI hỗ trợ", context, children }: AssistantWindowProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const window = dialog.current;
    if (!window || !open) return;
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    window.showModal();
    return () => {
      if (window.open) window.close();
      if (opener?.isConnected) opener.focus();
    };
  }, [open]);

  return <dialog ref={dialog} className={styles.window} aria-labelledby={titleId}
    onCancel={event => { event.preventDefault(); onOpenChange(false); }}>
    <div className={styles.layout}>
      <header className={styles.header}>
        <div className={styles.heading}><h2 id={titleId}>{title}</h2>{context && <div className={styles.context}>{context}</div>}</div>
        <button className="btn" type="button" onClick={() => onOpenChange(false)} aria-label="Thu gọn cửa sổ AI hỗ trợ" title="Thu gọn cửa sổ AI hỗ trợ">−</button>
      </header>
      <div className={styles.body}>{children}</div>
    </div>
  </dialog>;
}
