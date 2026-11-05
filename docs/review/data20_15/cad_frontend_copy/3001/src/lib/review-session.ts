import type { Confirmed, Data, PlanParams, PlanState, Structural } from "@/app/(user)/do-boc/model";
import type { DrawingVersion, WorkReceipt, WorkSnapshot } from "./work-review";
import { approvedWork, sameWorkVersion } from "./work-review";
import { adviceScope, type AdviceSelection, type SavedAdvice } from "@/app/(user)/dieu-chinh/advice-scope";

export type ReviewSession = Partial<DrawingVersion> & { materialRevision?: string; data: Data; states: Record<number, PlanState>; planP: Record<number, PlanParams>; confirmed: Record<number, Confirmed>; structural: Structural | null; pi: number };
export const MATERIAL_PARAMS = new Set(["concrete_supply", "concrete_grade", "lean_concrete_grade", "masonry_mortar_grade", "plaster_mortar_grade", "screed_mortar_grade", "formwork_type", "waterproof_material_id", "material_classes"]);

type PlanChoice = { lineId:string; originalId:string|null; materialId:string; needsDesignReview:boolean; needsGeometryReview:boolean };
/** Xác nhận đề xuất để mở lại, kể cả khi chưa có bản tính vật tư sau chốt. Mã thay thế luôn chờ kiểm thiết kế. */
export function saveReviewedProposal(expected: WorkSnapshot, choices: PlanChoice[]) {
  const read = <T,>(key:string): T|null => JSON.parse(localStorage.getItem(key) || "null") as T|null;
  const actual=read<WorkSnapshot>("optimat-rough"), receipt=read<WorkReceipt>("optimat-work-review"), session=read<ReviewSession>("optimat-review");
  if (!actual || !sameWorkVersion(expected,actual) || expected.materialRevision!==actual.materialRevision ||
      actual.projectUid!==read<string>("optimat-project-uid") || !approvedWork(actual,receipt,session)) throw Error("Bản kiểm đã đổi. Hãy mở lại phương án hiện tại.");
  if(session?.data.file!==actual.file || session.materialRevision!==actual.materialRevision || !receipt)throw Error("Phiên vật liệu đã thay đổi.");
  if (new Set(choices.map(c=>c.lineId)).size!==choices.length) throw Error("Phương án có dòng vật tư trùng.");
  const prior=read<SavedAdvice>("optimat-material-selection");
  const scoped=prior?.projectUid===actual.projectUid && prior.drawingId===actual.drawingId && prior.reviewId===actual.reviewId && prior.materialRevision===actual.materialRevision
    ? prior.choices.filter(c=>c.rowIndex!==null) : [];
  if(scoped.some(c=>choices.some(p=>p.lineId===c.lineId)))throw Error("Dòng có lựa chọn riêng theo cấu kiện. Kiểm tra lại phạm vi trước khi lưu.");
  const context=adviceScope(actual,receipt,null,actual.materialRevision);
  if(!context.materials.length)throw Error("Bản kiểm chưa có dòng vật tư.");
  const picked:AdviceSelection[]=choices.map(c=>{
    const line=/^m(0|[1-9]\d*)$/.test(c.lineId) ? actual.result.materials[Number(c.lineId.slice(1))] : undefined;
    if(!line || (line.material_id ?? null)!==c.originalId || !c.materialId.trim()) throw Error("Mã nguồn hoặc dòng vật tư không khớp bản kiểm.");
    return {lineId:c.lineId,originalId:c.originalId,originalName:line.name,materialId:c.materialId,scope:"Toàn bộ phần thô của dự án",
      rowIndex:null,reviewId:actual.reviewId,disposition:c.originalId!==c.materialId || c.needsGeometryReview || c.needsDesignReview?"proposed":"specified"};
  });
  const selections=[...scoped,...picked];
  const unresolved=context.materials.filter(m=>!selections.some(c=>c.lineId===m.lineId) || !m.complete || m.quantity_with_waste==null)
    .map(m=>({lineId:m.lineId,materialId:m.material_id,missing:m.missing}));
  const conditional=receipt.partial || !!unresolved.length || selections.some(c=>c.disposition==="proposed");
  const ready=!conditional && read<boolean>("optimat-materials-ready")===true;
  const key=JSON.stringify([actual.projectUid,actual.drawingId,actual.file,actual.reviewId,actual.materialRevision ?? null,ready]);
  const plan={key,...context.binding,file:actual.file,partial:receipt.partial,choices,scopedChoices:scoped,unresolved,
    status:conditional?"conditional":"selected",confirmedAt:new Date().toISOString()};
  const updates:Record<string,string>={"optimat-material-selection":JSON.stringify({projectUid:actual.projectUid,drawingId:actual.drawingId,reviewId:actual.reviewId,
    materialRevision:actual.materialRevision,choices:selections}),["optimat-proposal-"+actual.projectUid]:JSON.stringify(plan)};
  const draft=read<{reviewId:string;selections?:AdviceSelection[]}>("optimat-material-draft");
  if(draft?.reviewId===actual.reviewId) updates["optimat-material-draft"]=JSON.stringify({...draft,selections:[...(draft.selections || []).filter(c=>c.rowIndex!==null),...picked]});
  if(conditional) Object.assign(updates,{"optimat-materials-ready":"false","optimat-optimization":"null"});
  saveTogether(updates);
  return plan;
}

/** Lưu cùng snapshot và kết quả xác nhận; quota không được để hai module đọc hai phiên khác nhau. */
export function saveMaterialSession(session: ReviewSession, confirmed: Confirmed[], params: Record<string, string>, work: WorkSnapshot, receipt: WorkReceipt | null, choices: AdviceSelection[] = []) {
  if (session.data.plans.some((_, i) => !session.states[i]?.scope) || !session.data.plans.some((_, i) => session.states[i]?.scope === "count")) throw new Error("Xác nhận phạm vi từng mặt bằng trước khi lưu vật liệu.");
  if (Object.keys(session.confirmed).some((key) => session.states[Number(key)]?.scope !== "count")) throw new Error("Kết quả có hình tham khảo; xác nhận lại phạm vi trước khi lưu.");
  if (session.data.plans.some((_, i) => session.states[i]?.scope === "count" && !session.confirmed[i])) throw new Error("Chưa xác nhận đủ các mặt bằng được tính.");
  const updates = { "optimat-review": JSON.stringify(session),
    "optimat-confirmed": JSON.stringify(confirmed), "optimat-rough-params": JSON.stringify(params),
    "optimat-rough": JSON.stringify(work), "optimat-work-review": JSON.stringify(receipt), "optimat-optimization": "null",
    "optimat-material-selection": JSON.stringify({ projectUid: work.projectUid, drawingId: work.drawingId, reviewId: work.reviewId, materialRevision: work.materialRevision, choices }),
    "optimat-materials-ready": JSON.stringify(!!work.materialRevision && !!receipt?.confirmed) };
  try { saveTogether(updates); }
  catch (error) {
    if (!(error instanceof DOMException && error.name === "QuotaExceededError")) throw error;
    updates["optimat-review"] = JSON.stringify(session, (key, value) => key === "cad" ? undefined : value);
    saveTogether(updates);
  }
}

export function saveTogether(updates: Record<string, string>) {
  const previous = Object.fromEntries(Object.keys(updates).map((key) => [key, localStorage.getItem(key)]));
  const written: string[] = [];
  try {
    for (const [key, value] of Object.entries(updates)) { localStorage.setItem(key, value); written.push(key); }
  } catch (error) {
    for (const key of written.reverse()) {
      if (previous[key] === null) localStorage.removeItem(key);
      else localStorage.setItem(key, previous[key]!);
    }
    throw error;
  }
  for (const key of Object.keys(updates)) window.dispatchEvent(new CustomEvent("optimat-store", { detail: key }));
}
