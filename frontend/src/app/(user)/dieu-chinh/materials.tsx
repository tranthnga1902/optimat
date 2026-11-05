"use client";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Card, Empty, Head, Steps } from "@/components/ui";
import { store } from "@/lib/store";
import { useReference } from "@/lib/reference";
import { MATERIAL_PARAMS, saveMaterialSession, type ReviewSession } from "@/lib/review-session";
import { initState, payload, postJson, roughFields, roughValues, roughRequest, type RoughResult, type Confirmed } from "../do-boc/model";
import { reviewMatchesConfirmed } from "../do-boc/Review";
import { approvedWork, geometryChanged, sameWorkVersion, unchangedCheckedRows, type WorkSnapshot, type WorkReceipt, type WorkVersion } from "@/lib/work-review";
import { AdviceSheet } from "./AdviceSheet";
import { MaterialAdvisor } from "@/components/MaterialAdvisor";
import { Sheet } from "@/components/Sheet";
import { carrySelections, type AdviceSelection, type SavedAdvice } from "./advice-scope";

type MaterialDraft = WorkVersion & { choices: Record<number, Record<string, string | null>>; params: Record<string, string>; selections?: AdviceSelection[] };

export function Materials() {
  const [session, setSession] = useState<ReviewSession | null>(null);
  const [params, setParams] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [advice, setAdvice] = useState<{ work: WorkSnapshot; receipt: WorkReceipt } | null>(null);
  const [selections, setSelections] = useState<AdviceSelection[]>([]);
  const [draftVersion, setDraftVersion] = useState("");
  const { ref, error } = useReference();
  const mounted = useRef(false);
  const base = useRef<WorkSnapshot | null>(null);
  const conflict = useRef(false);
  const [stale, setStale] = useState(false);
  useEffect(() => {
    const changed = (e: StorageEvent) => {
      if (e.key && !["optimat-project-uid", "optimat-work-review", "optimat-review", "optimat-rough", "optimat-material-draft"].includes(e.key)) return;
      conflict.current = true; setStale(true); setSaved(false); setMessage("Dự án đã thay đổi ở tab khác. Tải lại trước khi lưu.");
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, []);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    const current = store.get<ReviewSession | null>("optimat-review", null);
    const review = store.get<WorkReceipt | null>("optimat-work-review", null);
    const latest = store.get<WorkSnapshot | null>("optimat-rough", null);
    if (!latest || !approvedWork(latest, review, current) || current?.projectUid !== store.get("optimat-project-uid", "")) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- thông báo cổng khôi phục snapshot trình duyệt
      setMessage("Hãy kiểm tra và lưu công tác, khối lượng ở bước trước khi chọn vật liệu."); return;
    }
    if (current && current.data.plans.every((_, i) => !!current.states[i]?.scope) && current.data.plans.some((_, i) => current.states[i]?.scope === "count") && reviewMatchesConfirmed(current.data.file, current.confirmed, store.get<Confirmed[]>("optimat-confirmed", []))) {
      const draft = store.get<MaterialDraft | null>("optimat-material-draft", null);
      base.current = latest;
      const matching = sameWorkVersion(latest, draft) ? draft : null;
      const selectionsSaved = store.get<SavedAdvice | null>("optimat-material-selection", null);
      const previous = selectionsSaved?.drawingId === latest.drawingId && selectionsSaved?.projectUid === latest.projectUid && selectionsSaved?.reviewId === latest.reviewId
        && selectionsSaved.materialRevision === latest.materialRevision ? selectionsSaved.choices : [];
      setSelections(matching?.selections ?? previous);
      if (review) setAdvice({ work: latest, receipt: review });
      setSession({ ...current, states: Object.fromEntries(current.data.plans.map((p, i) => {
        const state = current.states[i] || initState(p);
        return [i, { ...state, walls: state.walls.map((w) => matching?.choices[i] && w.id in matching.choices[i] ? { ...w, mat: matching.choices[i][w.id] } : w) }];
      })) });
      setParams(matching?.params || roughValues());
      setSaved(!!latest.materialRevision && current.materialRevision === latest.materialRevision && store.get("optimat-materials-ready", false));
    } else setMessage("Hãy xác nhận và lưu khối lượng các mặt bằng trong module Bóc tách trước.");
  }, []);
  const persistDraft = useCallback(() => {
    if (!session) return true;
    if (!base.current || conflict.current || !sameWorkVersion(base.current, store.get("optimat-rough", null))) return false;
    try {
      const { projectUid, drawingId, reviewId, file } = base.current;
      const draft: MaterialDraft = { projectUid, drawingId, reviewId, file, choices: Object.fromEntries(Object.entries(session.states).map(([i, state]) => [i, Object.fromEntries(state.walls.map((w) => [w.id, w.mat]))])), params, selections };
      localStorage.setItem("optimat-material-draft", JSON.stringify(draft));
      return true;
    } catch { setMessage("Chưa lưu được lựa chọn trên trình duyệt. Hãy giữ trang này mở và thử lại."); return false; }
  }, [session, params, selections]);
  // eslint-disable-next-line react-hooks/set-state-in-effect -- đồng bộ bản nháp vào storage và báo lỗi quota nếu thất bại
  useEffect(() => { persistDraft(); }, [persistDraft]);
  useEffect(() => {
    const guard = (event: MouseEvent) => {
      const link = event.target instanceof Element ? event.target.closest("a[href]") : null;
      if (link && (busy || !persistDraft())) { event.preventDefault(); event.stopPropagation(); }
    };
    document.addEventListener("click", guard, true);
    return () => document.removeEventListener("click", guard, true);
  }, [persistDraft, busy]);
  const markDraft = () => {
    setSaved(false); setDraftVersion(crypto.randomUUID());
    store.set("optimat-optimization", null); store.set("optimat-materials-ready", false);
  };
  const changeWall = (index: number, id: string, material: string) => {
    if (!session) return;
    const state = session.states[index];
    setSession({ ...session, states: { ...session.states, [index]: { ...state, walls: state.walls.map((w) => w.id === id ? { ...w, mat: material || null, edited: true } : w) } } });
    markDraft();
  };
  const save = async () => {
    if (!session || !base.current || busy || !persistDraft()) return;
    const original = base.current;
    const validate = () => {
      const receipt = store.get<WorkReceipt | null>("optimat-work-review", null);
      const actual = store.get<WorkSnapshot | null>("optimat-rough", null);
      if (conflict.current || !sameWorkVersion(original, actual) || original.materialRevision !== actual?.materialRevision ||
          session.projectUid !== store.get("optimat-project-uid", "") || !approvedWork(actual, receipt, session))
        throw new Error("Phiên kiểm khối lượng đã thay đổi. Hãy tải lại trước khi lưu.");
      return receipt;
    };
    setBusy(true); setMessage("");
    try {
      const currentReceipt = validate();
      const proposedRequest = roughRequest(session.data, session.states, session.planP, original.request.project_id, session.structural, params);
      if (original.materialRevision && currentReceipt && JSON.stringify(proposedRequest) === JSON.stringify(original.request)) {
        const materialRevision = crypto.randomUUID();
        const next = { ...session, materialRevision };
        const work = { ...original, materialRevision };
        saveMaterialSession(next, store.get<Confirmed[]>("optimat-confirmed", []), params, work, currentReceipt, selections);
        base.current = work; setSession(next); setDraftVersion(""); setSaved(true); setAdvice({ work, receipt: currentReceipt });
        setMessage("Đã lưu phương án đã chọn theo bản khối lượng hiện tại." + (selections.some(c => c.disposition === "proposed") ? " Mã thay thế vẫn chờ kiểm thiết kế." : ""));
        return;
      }
      const confirmed: Record<number, Confirmed> = {};
      for (const [i, plan] of session.data.plans.entries()) {
        if (session.states[i]?.scope !== "count") continue;
        confirmed[i] = await postJson<Confirmed>("/api/takeoff/confirm", payload(session.data, plan, session.states[i], Number(store.get("optimat-project", "")) || null), "Không lưu được lựa chọn vật liệu.");
        if (!mounted.current) return;
      }
      const others = store.get<Confirmed[]>("optimat-confirmed", []).filter((p) => p.file !== session.data.file);
      const next = { ...session, confirmed };
      const request = roughRequest(next.data, next.states, next.planP, Number(store.get("optimat-project", "")) || null, next.structural, params);
      const calculated = await postJson<RoughResult>("/api/takeoff/rough", request, "Chưa tính được vật tư theo lựa chọn mới.");
      if (!mounted.current) return;
      const receipt = validate();
      const changed = geometryChanged(original.result, calculated);
      const work: WorkSnapshot = { ...original, request, result: calculated, at: new Date().toISOString(),
        reviewId: changed ? crypto.randomUUID() : original.reviewId, materialRevision: changed ? undefined : crypto.randomUUID() };
      if (changed) work.drawingId = crypto.randomUUID();
      next.drawingId = work.drawingId;
      next.materialRevision = work.materialRevision;
      const pending = changed && receipt ? { ...receipt, drawingId: work.drawingId, reviewId: work.reviewId,
        checked: unchangedCheckedRows(original.result, calculated, receipt), partial: false, confirmed: false } : receipt;
      // Chỉ chuyển quyết định sang kết quả mới khi dòng vật tư vẫn đúng mã và phạm vi.
      const remaining = carrySelections(original, work, selections);
      saveMaterialSession(next, [...others, ...Object.values(confirmed)], params, work, pending, remaining);
      base.current = work;
      if (changed) {
        setSession(null); setSaved(false);
        setMessage("Lựa chọn đã lưu làm thay đổi khối lượng hoặc cấu tạo. Kiểm lại kết quả ở bước 3 trước khi xem giá."); return;
      }
      setSelections(remaining); setDraftVersion("");
      if (receipt) setAdvice({ work, receipt });
      setSession(next); setSaved(true); setMessage("Đã lưu phương án vật liệu và tính lại nhu cầu vật tư." +
        (remaining.some(c => c.disposition === "proposed") ? " Mã đề xuất thay thế được lưu để kiểm thiết kế; bảng giá vẫn dùng quy cách hiện hành." : " Có thể tiếp tục xem vật liệu và giá."));
    } catch (e) { store.set("optimat-materials-ready", false); setSaved(false); setMessage(`${(e as Error).message} Các lựa chọn đang sửa vẫn được giữ trên trang; hãy thử lưu lại.`); }
    finally { if (mounted.current) setBusy(false); }
  };
  const grades: Record<string, string[]> = { concrete_grade: ref?.concrete_grades || [], lean_concrete_grade: ref?.concrete_grades || [],
    masonry_mortar_grade: ref?.mortar_grades || [], plaster_mortar_grade: ref?.mortar_grades || [], screed_mortar_grade: ref?.mortar_grades || [] };
  const changeParam = (key: string, value: string) => {
    setParams({ ...params, [key]: value }); markDraft();
  };
  return <>
    <Steps cur="/dieu-chinh" done={{ "/do-boc": !!session }} />
    <Head title="Chọn vật liệu" actions={<Link className="btn" href="/phan-tho">Về kiểm tra khối lượng</Link>}>Chọn vật liệu theo bản khối lượng đã kiểm. Phương án đề xuất lấy từ danh mục và nhận dạng bản vẽ.</Head>
    {message && <p role="status">{message}</p>}
    {!session ? <Empty><Link href="/phan-tho">Mở bước Kiểm tra công tác và khối lượng</Link></Empty> : <>
      {advice && <Card title="Bảng phương án vật liệu phần thô">
        <AdviceSheet key={advice.work.reviewId} work={advice.work} receipt={advice.receipt} version={advice.work.materialRevision}
          params={params} onParam={changeParam} fields={roughFields(ref).flatMap(([, fields]) => fields)
            .filter(([key]) => MATERIAL_PARAMS.has(key)).map(([key,label,type]) => ({ key,label,
              options:(Array.isArray(type) ? type : (grades[key] || []).map((v):[string,string] => [v,v])).filter(([v]) => !!v) }))}
          catalogOptions={[...session.data.materials.map(m => ({ id: m.id, name: m.name || m.id, raw: "gach", wallClasses: Object.keys(m.systems || {}) })),
            ...(ref?.waterproof_materials || []).map(m => ({ ...m, raw: "chong_tham" })),
            ...advice.work.result.materials.filter(m => m.material_id && m.raw_class && !["gach","chong_tham"].includes(m.raw_class)).map(m => ({ id: m.material_id!, name: m.name, raw: m.raw_class! }))]}
          disabled={busy || stale} choices={selections} onPick={(choice, row, line) => {
            if (conflict.current || busy || !sameWorkVersion(advice.work, store.get("optimat-rough", null))) {
              setMessage("Bản khối lượng đã đổi. Tải lại trước khi chọn."); return;
            }
            setSelections(previous => [...previous.filter(c => c.lineId !== line || c.rowIndex !== row), ...(choice ? [choice] : [])]);
            setMessage(choice ? `Đã chọn ${choice.materialId} cho ${choice.originalName}. Bấm Lưu lựa chọn vật liệu để ghi vào dự án.` : "Đã bỏ lựa chọn trong bản nháp.");
            markDraft();
          }} assistant={(context, pick, open, onOpenChange) => busy || stale ? null : <MaterialAdvisor open={open} onOpenChange={onOpenChange} key={JSON.stringify([draftVersion,context.scope,context.binding,context.proposedMaterialIds])} context={context} onPropose={selection => {
            if ((selection.binding.materialRevision ?? null) === context.binding.materialRevision && selection.binding.projectUid === context.binding.projectUid &&
                selection.binding.drawingId === context.binding.drawingId && selection.binding.reviewId === context.binding.reviewId) pick(selection.lineId, selection.materialId);
          }} />} />
        <div className="flex flex-wrap items-center gap-3"><button type="button" className="btn primary" disabled={busy || stale} onClick={save}>{busy ? "Đang lưu…" : "Lưu phương án đã chọn"}</button>
          <span>{saved ? "Đã lưu vào dự án" : "Bản nháp"}</span></div>
      </Card>}
      {session.data.plans.map((plan, i) => session.states[i]?.scope === "count" && <Card key={i} title={`Chi tiết tường · ${plan.plan.name}`}>
        <Sheet rows={session.states[i].walls.filter(w => w.keep && w.masonry)} file={`vat-lieu-tuong-${i+1}.csv`} cols={[
          { key: "id", title: "Tường" }, { key: "cls", title: "Loại tường (mm)", num: true },
          { key: "mat", title: "Vật liệu", text: w => w.mat || "Chưa chọn", render: w => {
            const suggestions = session.data.materials.filter((m) => w.cand.some((id) => m.systems?.[w.cls] === id));
            const available = session.data.materials.filter((m) => m.systems?.[w.cls] || m.id === w.mat);
            return <select className="field" aria-label={`${plan.plan.name} vật liệu tường ${w.id}`} value={w.mat || ""} disabled={busy || stale} onChange={(e) => changeWall(i, w.id, e.target.value)}>
              <option value="">Chọn vật liệu…</option>
              {suggestions.length > 0 && <optgroup label="Đề xuất từ bản vẽ">{suggestions.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}</optgroup>}
              <optgroup label="Danh mục">{available.filter((m) => !suggestions.includes(m)).map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}</optgroup>
            </select>;
          } }
        ]} />
      </Card>)}
      <Card title="Vật liệu phần thô">
        {error && <p role="alert">{error}</p>}
        {roughFields(ref).flatMap(([, fields]) => fields).filter(([key]) => MATERIAL_PARAMS.has(key)).map(([key, label, type]) => {
          const options = Array.isArray(type) ? type : (grades[key] || []).map((v): [string, string] => [v, v]);
          const choices = options.some(([v]) => v === "") ? options : [["", "Chọn phương án…"], ...options];
          return <label key={key} className="flex flex-col gap-1">{label}<select className="field" value={params[key] || ""} disabled={busy} onChange={(e) => changeParam(key, e.target.value)}>
            {params[key] && !choices.some(([v]) => v === params[key]) && <option value={params[key]}>{params[key]} · đã lưu</option>}
            {choices.map(([v, text]) => <option key={v} value={v}>{text}</option>)}
          </select></label>;
        })}
        {!!ref?.raw_classes?.length && <fieldset><legend>Loại vật liệu cần bóc (bỏ trống để lấy mọi loại)</legend>
          {ref.raw_classes.map(c => {
            const picked = (params.material_classes || "").split(",").filter(Boolean);
            return <label key={c.code} className="mr-3"><input type="checkbox" disabled={busy} checked={picked.includes(c.code)}
              onChange={e => changeParam("material_classes", (e.target.checked ? [...picked, c.code] : picked.filter(x => x !== c.code)).join(","))} /> {c.name}</label>;
          })}
        </fieldset>}
      </Card>
      <div className="flex gap-2"><button className="btn primary" disabled={busy} onClick={save}>{busy ? "Đang lưu…" : "Lưu lựa chọn vật liệu"}</button>
        {saved && <Link className="btn primary" href="/vat-lieu">Tiếp: vật liệu và giá</Link>}</div>
      {!saved && <p className="text-muted">Lưu lựa chọn trước khi chuyển module; kích thước và khối lượng giữ theo bước xác nhận.</p>}
    </>}
  </>;
}
