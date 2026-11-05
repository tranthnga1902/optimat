"use client";

import type { ReviewSession } from "./review-session";
import { store, useStored } from "./store";
import { approvedWork, type WorkReceipt, type WorkSnapshot } from "./work-review";

function reviewedKey(projectUid: string, drawing: ReviewSession | null, work: WorkSnapshot | null,
  receipt: WorkReceipt | null, ready: boolean) {
  if (!projectUid || drawing?.projectUid !== projectUid || !work || drawing.data?.file !== work.file ||
      work.materialRevision !== drawing.materialRevision ||
      !Array.isArray(work.result?.works) || !approvedWork(work, receipt, drawing)) return null;
  return JSON.stringify([projectUid, work.drawingId, work.file, work.reviewId, work.materialRevision || null, ready]);
}

export function usePurchaseSession() {
  const project = useStored("optimat-project-uid", "");
  const drawing = useStored<ReviewSession | null>("optimat-review", null);
  const work = useStored<WorkSnapshot | null>("optimat-rough", null);
  const receipt = useStored<WorkReceipt | null>("optimat-work-review", null);
  const ready = useStored<boolean>("optimat-materials-ready", false);
  const draftKey = reviewedKey(project, drawing, work, receipt, ready);
  const key = ready === true && work?.materialRevision ? draftKey : null;
  return { key, work: key ? work : null, ready, draftKey, reviewed: draftKey ? work : null, receipt };
}

/** Kiểm lại ngay trước khi dùng phản hồi API, kể cả khi tab khác vừa đổi bản kiểm. */
export function currentPurchaseKey() {
  const work = store.get<WorkSnapshot | null>("optimat-rough", null);
  return store.get<boolean>("optimat-materials-ready", false) === true && work?.materialRevision ? currentDraftKey(work) : null;
}

export function currentDraftKey(work = store.get<WorkSnapshot | null>("optimat-rough", null)) {
  return reviewedKey(store.get("optimat-project-uid", ""), store.get<ReviewSession | null>("optimat-review", null),
    work, store.get<WorkReceipt | null>("optimat-work-review", null), store.get("optimat-materials-ready", false));
}
