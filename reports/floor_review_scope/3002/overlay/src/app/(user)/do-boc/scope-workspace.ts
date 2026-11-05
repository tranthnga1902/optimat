import type { ReviewSession } from "@/lib/review-session";
import { saveTogether } from "@/lib/review-session";
import type { Confirmed } from "./model";
import { scopeIndices, scopedBodies } from "./floor-review";

// Mỗi nhóm giữ bản tính và biên nhận riêng; lịch sử dự án đã lưu toàn bộ optimat-review.
const keys = ["optimat-rough", "optimat-work-review", "optimat-material-draft", "optimat-material-selection", "optimat-materials-ready", "optimat-optimization"] as const;
type Cached = { drawingId?: string; materialRevision?: string; values: Record<string,string> };
export type ScopeHistory = Record<string,Cached>;

export function switchReviewScope(session: ReviewSession, indices: number[], pi: number, published: Confirmed[]) {
  const from = scopeIndices(session.data.plans,session.reviewScope).join(",");
  const to = indices.join(",");
  const history = { ...session.scopeHistory };
  const current = Object.fromEntries(keys.map(k => [k,localStorage.getItem(k) ?? (k === "optimat-materials-ready" ? "false" : "null")]));
  if (from !== to && keys.some(k => !["null","false"].includes(current[k]))) {
    history[from] = { drawingId:session.drawingId, materialRevision:session.materialRevision, values:current };
  }
  const cached = history[to];
  const restore = from === to ? current : cached && cached.drawingId === session.drawingId ? cached.values : {};
  const updates = Object.fromEntries(keys.map(k => [k, restore[k] ?? (k === "optimat-materials-ready" ? "false" : "null")]));
  const materialRevision = from === to ? session.materialRevision : cached?.drawingId === session.drawingId ? cached?.materialRevision : undefined;
  const scope = indices.length === session.data.plans.length ? undefined : indices;
  const next = { ...session, reviewScope:scope, reviewSelection:indices, pi, materialRevision, scopeHistory:history };
  const summaries = Object.values(scopedBodies(next.data.plans,next.states,next.confirmed,indices));
  updates["optimat-confirmed"] = JSON.stringify([...published.filter(p => p.file !== next.data.file), ...summaries.map(p => {
    const { file,plan,height_mm,groups,total_net_area_m2,confirmed_at,takeoff_id } = p;
    const partial = Object.fromEntries(Object.entries(p).filter(([k]) => ["complete","known_net_area_m2","pending_openings","pending_groups"].includes(k)));
    return {file,plan,height_mm,groups,total_net_area_m2,confirmed_at,takeoff_id:takeoff_id || null,...partial};
  })]);
  const write = (raw:string) => { saveTogether({...updates,"optimat-review":raw}); return raw; };
  let raw: string;
  try { raw = write(JSON.stringify(next)); }
  catch { raw = write(JSON.stringify(next,(k,v)=>k === "cad" ? undefined : v)); }
  return { raw, history, materialRevision, scope };
}
