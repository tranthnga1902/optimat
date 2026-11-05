"use client";
// Trang Kiểm tra bóc tách (thay iframe /ui/takeoff của app.html cũ): tải bản vẽ, kiểm tra, sửa, bổ sung rồi xác nhận từng mặt bằng.
// Kết quả chốt ghi vào optimat-confirmed, phần thô vào optimat-rough (store.set báo cho menu và các trang /vat-lieu, /phan-tho, /toi-uu).
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type MouseEvent, type ReactNode } from "react";
import { Empty, Head, Steps } from "@/components/ui";
import { store, useStored } from "@/lib/store";
import { projectUid } from "@/lib/projects";
import { projectPath, type AnalysisContext, type SelectedRevision } from "@/lib/project-records";
import { saveTogether, type ReviewSession } from "@/lib/review-session";
import { sameWorkVersion, type WorkSnapshot, type WorkReceipt, type DrawingVersion } from "@/lib/work-review";
import s from "./review.module.css";
import { Board, type Mode, type Pt } from "./Board";
import { ChangeInput } from "./ChangeInput";
import { ConfirmDialog, ConfirmedDialog, MaterialDialog, Msg } from "./Dialogs";
import { OpeningList, OverviewList, QtyTab, WallFilters, WallList, WarnTab, type Change } from "./Lists";
import { WorkReview } from "./WorkReview";
import { RoughTab } from "./Rough";
import {
  REASONS, RP_KEY, base, compute, convBad, csvText, fmt, initPlanParams, initState, nearestWall, payload, roughRequest, roughValues,
  type Confirmed, type Data, type PlanParams, type PlanState, type Rough, type Structural,
} from "./model";
import { useViewport } from "./viewport";
import { ReadPreview } from "./ReadPreview";
import { titleScale } from "./paper-scale";
import { readProgress, type ReadProgress } from "./read-progress";

const HINTS: Record<Mode, string> = {
  select: "Bấm vào tường hoặc dòng trong danh sách để chọn. Lăn chuột để phóng, kéo để di chuyển.",
  wall: "Bấm điểm đầu và điểm cuối theo trục tim tường; điểm tự hút vào đầu nét gần nhất. Esc để hủy.",
  open: "Chọn loại, nhập rộng × cao rồi bấm lên tường để thêm lỗ mở.",
};
const START = "Chọn \"Mở bản vẽ…\" để tải file .dxf hoặc .dwg. Hệ thống tách từng mặt bằng tầng, nhận dạng tường và lỗ mở; bạn kiểm tra, sửa, bổ sung rồi xác nhận.";
// Trang điều chỉnh chỉ nhận snapshot khớp kết quả xác nhận đang dùng ở các module.
export function reviewMatchesConfirmed(file: string, snapshot: Record<number, Confirmed>, published: Confirmed[]) {
  const fields = (p: Confirmed) => JSON.stringify([p.height_mm, p.total_net_area_m2, p.groups, p.confirmed_at, p.takeoff_id || null]);
  const saved = Object.values(snapshot);
  const current = published.filter((p) => p.file === file);
  return saved.length > 0 && saved.length === current.length && saved.every((p) =>
    current.some((c) => c.plan === p.plan && fields(c) === fields(p)));
}

type SheetState = { kind: "material" } | { kind: "confirm" } | { kind: "confirmed"; body: Confirmed; total: number }
  | { kind: "recover"; body: Confirmed }
  | { kind: "msg"; title: string; body?: ReactNode; primary?: boolean };
type ConfirmationStamp = DrawingVersion & { projectId: number | null; revision: number; planIndex: number; published?: boolean };
const storedProjectId = () => Number(store.get("optimat-project", "")) || null;

export function confirmationGuide(plans: Data["plans"], states: Record<number, PlanState>, confirmed: Record<number, Confirmed>, at: number) {
  if (!plans.length) return null;
  const unclassified = plans.flatMap((_, i) => states[i]?.scope === "count" || states[i]?.scope === "reference" ? [] : [i]);
  const counted = plans.flatMap((_, i) => states[i]?.scope === "count" ? [i] : []);
  if (unclassified.length || !counted.length) {
    const index = unclassified.includes(at) ? at : unclassified[0] ?? (plans[at] ? at : 0);
    return { index, field: "scope", action: `Phân loại hình ${index + 1}/${plans.length}`, message: unclassified.length
      ? `Còn ${unclassified.length}/${plans.length} hình chưa có phạm vi. Chọn tính khối lượng hoặc tham khảo cho “${plans[index].plan.name}”.`
      : "Tất cả hình đang là tham khảo. Chọn ít nhất một mặt bằng để tính khối lượng." };
  }
  if (!counted.includes(at)) {
    const index = counted.find(i => !confirmed[i]) ?? counted[0];
    return { index, field: "plan", action: `Mở hình ${index + 1}: ${plans[index].plan.name}`, message: "Mở một mặt bằng trong phạm vi tính để kiểm kích thước và khối lượng." };
  }
  if (!Number.isFinite(states[at]?.height_mm) || states[at].height_mm <= 0)
    return { index: at, field: "height", action: "Nhập chiều cao tầng", message: `Cần chiều cao có căn cứ cho “${plans[at].plan.name}” trước khi xác nhận.` };
  return null;
}

export function Review({ adjustment = false, roughOnly = false }: { adjustment?: boolean; roughOnly?: boolean }) {
  const router = useRouter();
  const [restored, setRestored] = useState(false);
  const [saveError, setSaveError] = useState("");
  const publishPending = useRef<ConfirmationStamp | null>(null);
  const stampByBody = useRef(new WeakMap<Confirmed, ConfirmationStamp>());
  const sessionProject = useRef<number | null>(null);
  const lastStoredReview = useRef<string | null>(null);
  const revision = useRef(0);
  const activePlan = useRef(-1);
  const confirmRequest = useRef<AbortController | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const scopeInput = useRef<HTMLSelectElement>(null);
  const heightLabel = useRef<HTMLLabelElement>(null);
  const drawing = useRef<DrawingVersion & { materialRevision?: string } | null>(null);
  const [externalChange, setExternalChange] = useState(false);
  const [saveNotice, setSaveNotice] = useState("");
  const [reading, setReading] = useState<ReadProgress | null>(null);
  const [showReadPreview, setShowReadPreview] = useState(false);
  const readController = useRef<AbortController | null>(null);
  const { svgRef, scaleRef, zoomRef, zoomLabel, zoomTo, vbRef, movedRef, fitSize, focusOn, toWorld, onPointerDown } = useViewport();
  const listRef = useRef<HTMLDivElement>(null), scrollTo = useRef<string | null>(null);
  const [data, setData] = useState<Data | null>(null);
  const [msg, setMsg] = useState<string | null>(START);      // thông báo chiếm danh sách: chưa mở bản vẽ, đang đọc, lỗi đọc
  const [pi, setPi] = useState(0);
  const [states, setStates] = useState<Record<number, PlanState>>({});   // trạng thái sửa theo từng mặt bằng (giữ khi đổi mặt bằng)
  const [hist, setHist] = useState<string[]>([]);
  const [tab, setTab] = useState("walls");
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState<string | null>(null);
  const [mode, setModeState] = useState<Mode>("select");
  const [hint, setHint] = useState(HINTS.select);
  const [draft, setDraft] = useState<Pt | null>(null);
  const [confirmed, setConfirmed] = useState<Record<number, Confirmed>>({});
  const [planP, setPlanP] = useState<Record<number, PlanParams>>({});
  const [rough, setRough] = useState<Rough>(null);
  const [roughBusy, setRoughBusy] = useState(false);
  const [structural, setStructural] = useState<Structural | { error: string } | { busy: string } | null>(null);
  const [roughVals, setRoughVals] = useState<Record<string, string>>({});
  const [bgPref, setBgPref] = useState("cad");
  const [showRec, setShowRec] = useState(true);
  const [showLabels, setShowLabels] = useState(false);
  const [newCls, setNewCls] = useState("220");
  const [newKind, setNewKind] = useState("door");
  const [newW, setNewW] = useState("900");
  const [newH, setNewH] = useState("2200");
  const [sheet, setSheet] = useState<SheetState | null>(null);

  // ?project=12 trên địa chỉ trang hoặc ô Mã dự án: kết quả chốt được lưu vào dự án (bảng takeoff_results) khi máy chủ có PostgreSQL
  const projectName = useStored("optimat-project-name", "");
  const projectInfo = useStored<unknown>("optimat-project-info", null);
  const projectReady = !!projectName.trim() && !!projectInfo;
  const projectRaw = useStored<string | number>("optimat-project", "");
  const project = Number(projectRaw) || null;
  const confirmedList = useStored<unknown[]>("optimat-confirmed", []);
  const roughStored = useStored<WorkSnapshot | null>("optimat-rough", null);
  const receipt = useStored<WorkReceipt | null>("optimat-work-review", null);
  useLayoutEffect(() => { activePlan.current = pi; }, [pi]);
  // storage không phát sự kiện trong chính tab đã ghi. So với bản cuối do phiên này đọc/ghi,
  // kể cả khi bản khác trùng tên tệp, tên tầng và drawingId.
  const ownsReview = useCallback(() => {
    try {
      return !!drawing.current && drawing.current.projectUid === store.get("optimat-project-uid", "") &&
        storedProjectId() === sessionProject.current && localStorage.getItem("optimat-review") === lastStoredReview.current;
    } catch { return false; }
  }, []);
  const stampIsCurrent = useCallback((stamp?: ConfirmationStamp | null) => !!stamp && ownsReview() &&
    stamp.projectUid === drawing.current?.projectUid && stamp.projectId === sessionProject.current &&
    stamp.drawingId === drawing.current?.drawingId && stamp.revision === revision.current && stamp.planIndex === activePlan.current, [ownsReview]);
  useEffect(() => {
    const q = new URLSearchParams(location.search).get("project");
    if (q) store.set("optimat-project", q);
    setRoughVals(roughValues());
    try { const m = localStorage.getItem("optimat-bg"); if (m) setBgPref(m); } catch { /* chế độ riêng tư */ }
  }, []);

  useEffect(() => {
    let saved: (ReviewSession & { projectId?: number | null }) | null;
    try {
      lastStoredReview.current = localStorage.getItem("optimat-review");
      saved = lastStoredReview.current ? JSON.parse(lastStoredReview.current) : null;
      sessionProject.current = storedProjectId();
      if (saved?.projectId !== undefined && saved.projectId !== sessionProject.current) { setExternalChange(true); return; }
      const uid = projectUid();
      if (saved?.projectUid && saved.projectUid !== uid) { setMsg("Bản vẽ thuộc phiên dự án khác. Hãy mở lại dự án từ lịch sử."); return; }
      drawing.current = { projectUid: uid, drawingId: saved?.drawingId || crypto.randomUUID(), materialRevision: saved?.materialRevision };
    } catch { setSaveError("Chưa lưu được mã phiên dự án trên trình duyệt."); return; }
    if (saved && saved.data.plans.some((_, i) => !saved.states[i]?.scope)) {
      saved.confirmed = {};
      store.set("optimat-confirmed", store.get<Confirmed[]>("optimat-confirmed", []).filter((p) => p.file !== saved.data.file));
      store.set("optimat-rough", null); store.set("optimat-materials-ready", false);
      if (adjustment || roughOnly) {
        setMsg("Hồ sơ cũ chưa xác nhận hình tính khối lượng và hình tham khảo. Về Bóc tách để phân loại từng mặt bằng.");
        setRestored(true); return;
      }
    }
    if (saved && (adjustment || roughOnly) && (saved.data.plans.some((_, i) => saved.states[i]?.scope === "count" && !saved.confirmed[i]) ||
      !reviewMatchesConfirmed(saved.data.file, saved.confirmed, store.get<Confirmed[]>("optimat-confirmed", [])))) {
      setMsg("Bản vẽ đã lưu chưa khớp kết quả xác nhận hiện tại. Không mở bản cũ để điều chỉnh. Hãy quay lại trang đo bóc đang mở và lưu thành công trước khi tiếp tục.");
      setRestored(true);
      return;
    }
    if (saved) {
      if (saved.data.plans.some((_, i) => !saved.states[i]?.scope)) {
        saved.confirmed = {};
        store.set("optimat-confirmed", store.get<Confirmed[]>("optimat-confirmed", []).filter((p) => p.file !== saved.data.file));
        store.set("optimat-rough", null); store.set("optimat-materials-ready", false);
      }
      const restoredPi = saved.pi < 0 && (roughOnly || !saved.data.overview?.cad) ? 0 : saved.pi;
      setData(saved.data);
      setStates(Object.fromEntries(saved.data.plans.map((p, i) => [i, saved.states[i] || initState(p)])));
      const published = store.get<Confirmed[]>("optimat-confirmed", []);
      for (const [key, body] of Object.entries(saved.confirmed)) {
        const index = Number(key);
        if (body.file === saved.data.file && body.plan === saved.data.plans[index]?.plan.name &&
            saved.states[index]?.scope === "count" && reviewMatchesConfirmed(body.file, { [index]: body }, published.filter(p => p.plan === body.plan)))
          stampByBody.current.set(body, { ...drawing.current!, projectId: sessionProject.current, revision: revision.current, planIndex: index, published: true });
      }
      setPlanP(saved.planP); setConfirmed(saved.confirmed);
      setStructural(saved.structural); setPi(restoredPi); setMsg(null);
      setTab(roughOnly ? "rough" : "qty");
      if (roughOnly) {
        const result = store.get<WorkSnapshot | null>("optimat-rough", null);
        const valid = result?.file === saved.data.file && result?.drawingId === drawing.current.drawingId && result.projectUid === drawing.current.projectUid;
        setRough(valid ? result.result : null);
        roughStarted.current = valid;
      }
      const size = saved.data.plans[restoredPi]?.size || saved.data.overview?.size;
      if (size) fitSize(size);
    }
    setRestored(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- khôi phục một lần khi mở trang
  }, []);
  const persistReview = useCallback((nextConfirmed = confirmed) => {
    if (!data) return true;
    if (externalChange || !ownsReview() || (publishPending.current && !stampIsCurrent(publishPending.current))) {
      setSaveError("Phiên dự án đã thay đổi. Tải phiên hiện tại để tiếp tục.");
      return false;
    }
    const snapshot = { ...drawing.current, projectId: sessionProject.current, data, states, planP, confirmed: nextConfirmed, pi,
      structural: structural && "file" in structural ? structural : null };
    const writeSnapshot = (value: string) => {
      if (!publishPending.current) {
        localStorage.setItem("optimat-review", value); lastStoredReview.current = value; return;
      }
      const previous = store.get<Confirmed[]>("optimat-confirmed", []).filter(p => p.file !== data.file);
      const summaries = Object.values(nextConfirmed).map(({file, plan, height_mm, groups, total_net_area_m2, confirmed_at, takeoff_id}) =>
        ({file, plan, height_mm, groups, total_net_area_m2, confirmed_at, takeoff_id: takeoff_id || null}));
      saveTogether({ "optimat-review": value, "optimat-confirmed": JSON.stringify([...previous, ...summaries]) });
      publishPending.current.published = true;
      lastStoredReview.current = value; publishPending.current = null;
    };
    try {
      if (roughOnly) localStorage.setItem(RP_KEY, JSON.stringify(roughVals));
      writeSnapshot(JSON.stringify(snapshot));
      setSaveError(""); setSaveNotice("");
      return true;
    } catch {
      // SVG nền CAD có thể rất lớn; hình học đo bóc vẫn đủ để khôi phục và tính tiếp.
      try {
        if (roughOnly) localStorage.setItem(RP_KEY, JSON.stringify(roughVals));
        writeSnapshot(JSON.stringify(snapshot, (key, value) => key === "cad" ? undefined : value));
        setSaveError("");
        setSaveNotice("Đã lưu bản gọn để tiếp tục: giữ hình học, kích thước và khối lượng; khi mở lại dùng nền nét đã đọc thay cho ảnh CAD gốc.");
        return true;
      } catch {
        setSaveNotice("");
        setSaveError("Chưa lưu được bản vẽ hiện tại. Bộ nhớ có thể đã đầy; chưa thể chuyển trang. Hãy giữ trang này mở và thử lại sau khi giải phóng bộ nhớ.");
        return false;
      }
    }
  }, [data, states, planP, confirmed, pi, structural, roughOnly, roughVals, externalChange, ownsReview, stampIsCurrent]);
  useEffect(() => {
    if (restored) persistReview();
  }, [restored, persistReview]);
  useEffect(() => {
    // Kiểm tra lại ngay lúc điều hướng, kể cả liên kết ở thanh bước và menu chung.
    const beforeNavigate = (event: globalThis.MouseEvent) => {
      const link = event.target instanceof Element ? event.target.closest("a[href]") : null;
      if (!(link instanceof HTMLAnchorElement) || link.origin !== location.origin || link.pathname === location.pathname) return;
      if (reading || confirmRequest.current || !persistReview()) {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    document.addEventListener("click", beforeNavigate, true);
    return () => document.removeEventListener("click", beforeNavigate, true);
  }, [persistReview, reading]);

  const P = data && pi >= 0 ? data.plans[pi] || null : null;
  const S = P ? states[pi] || null : null;
  const paper = useMemo(() => P && titleScale(P.plan.name, P.texts), [P]);
  const c = useMemo(() => (S ? compute(S) : null), [S]);
  const pp = P ? planP[pi] || initPlanParams(P) : null;
  const scopeReady = !!data?.plans.length && data.plans.every((_, i) => !!states[i]?.scope) && data.plans.some((_, i) => states[i]?.scope === "count");
  const allCountedConfirmed = scopeReady && data!.plans.every((_, i) => states[i]?.scope === "reference" || !!confirmed[i]);
  const guide = data ? confirmationGuide(data.plans, states, confirmed, pi) : null;
  const hasOverview = !!(data && data.overview && data.overview.cad);
  const hasCad = !!data && (pi < 0 ? !!(data.overview && data.overview.cad) : !!(P && P.cad));
  let bg = bgPref;
  if (!hasCad && bg !== "lines") bg = "lines";
  if (pi < 0 && bg === "lines") bg = "cad";
  useEffect(() => { if (data) try { localStorage.setItem("optimat-bg", bg); } catch { /* chế độ riêng tư */ } }, [data, bg]);
  const unit = P ? Math.max(...P.size) / 100 : data?.overview ? Math.max(...data.overview.size) / 100 : 100;

  // ---------------------------------------------------------------- phần thô: tự tính lại sau khi sửa, chỉ khi đã bấm "Tính phần thô" ít nhất một lần
  const latest = useRef({ data, states, planP, project, rough, structural, roughVals });
  useLayoutEffect(() => { latest.current = { data, states, planP, project, rough, structural, roughVals }; });
  const roughTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined), busyRef = useRef(false);
  const roughStarted = useRef(false), uploadRevision = useRef(0), structuralRevision = useRef(0);
  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if (event.key && !["optimat-project-uid","optimat-project","optimat-project-info","optimat-project-files-selected", "optimat-review", "optimat-work-review", "optimat-rough", RP_KEY].includes(event.key)) return;
      revision.current++; uploadRevision.current++; structuralRevision.current++;
      confirmRequest.current?.abort();
      clearTimeout(roughTimer.current); readController.current?.abort(); setExternalChange(true);
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, []);
  useEffect(() => () => { revision.current++; uploadRevision.current++; structuralRevision.current++; clearTimeout(roughTimer.current); readController.current?.abort(); confirmRequest.current?.abort(); }, []);
  const computeRough = useCallback(async function runRough() {
    const L = latest.current;
    if (!L.data || !drawing.current) return;
    const version = { projectUid: drawing.current.projectUid, drawingId: drawing.current.drawingId };
    if (L.structural && !("file" in L.structural)) {
      setRough({ error: "Chờ đọc bản vẽ kết cấu thành công rồi tính phần thô." });
      return;
    }
    if (busyRef.current) { roughTimer.current = setTimeout(runRough, 100); return; }
    const atRevision = revision.current;
    roughStarted.current = true;
    busyRef.current = true; setRoughBusy(true);
    store.set("optimat-rough", null);
    store.set("optimat-work-review", null);
    store.set("optimat-materials-ready", false);
    store.set("optimat-optimization", null);
    try {
      const request = roughRequest(L.data, L.states, L.planP, L.project, L.structural && "file" in L.structural ? L.structural : null, L.roughVals);
      const r = await fetch("/api/takeoff/rough", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request) });
      const body = await r.json();
      if (!r.ok) throw new Error(typeof body.detail === "string" ? body.detail
        : "Máy chủ từ chối dữ liệu phần thô: " + ((body.detail || []) as { loc?: string[]; msg: string }[]).map((d) => (d.loc || []).slice(-1)[0] + " " + d.msg).join("; "));
      if (revision.current !== atRevision || version.projectUid !== store.get("optimat-project-uid", "")) return;
      const snapshot: WorkSnapshot = { ...version, file: L.data.file, reviewId: crypto.randomUUID(), at: new Date().toISOString(), request, result: body };
      saveTogether({ "optimat-rough": JSON.stringify(snapshot) });
      setRough(body);
    } catch (err) {
      if (revision.current === atRevision) setRough({ error: (err as Error).message });
    } finally { busyRef.current = false; setRoughBusy(false); }
  }, []);
  const scheduleRough = useCallback(() => {
    if (drawing.current) drawing.current = { projectUid: drawing.current.projectUid, drawingId: crypto.randomUUID() };
    store.set("optimat-materials-ready", false);
    store.set("optimat-optimization", null);
    revision.current++;
    store.set("optimat-work-review", null);
    setRough(null);
    store.set("optimat-rough", null);
    clearTimeout(roughTimer.current);
    if (roughStarted.current) roughTimer.current = setTimeout(computeRough, 700);
  }, [computeRough]);

  // ---------------------------------------------------------------- sửa: mỗi lần sửa lưu một bước hoàn tác, bỏ trạng thái đã xác nhận
  const markDirty = () => {
    confirmRequest.current?.abort();
    if (publishPending.current?.planIndex === pi) publishPending.current = null;
    store.set("optimat-work-review", null);
    store.set("optimat-materials-ready", false);
    store.set("optimat-material-draft", null);
    store.set("optimat-materials-ready", false);
    store.set("optimat-material-draft", null);
    store.set("optimat-optimization", null);
    setConfirmed((x) => { const r = { ...x }; delete r[pi]; return r; });
    if (data && P) store.set("optimat-confirmed", store.get<Confirmed[]>("optimat-confirmed", [])
      .filter((p) => !(p.file === data.file && p.plan === P.plan.name)));
    setSheet(null);
    scheduleRough();
    // Sửa một tầng giữ nguyên biên nhận đã lưu của các tầng còn lại.
    if (drawing.current && ownsReview()) for (const [key, body] of Object.entries(confirmed)) {
      const stamp = stampByBody.current.get(body);
      if (Number(key) !== pi && stamp?.published)
        stampByBody.current.set(body, { ...stamp, drawingId: drawing.current.drawingId, revision: revision.current });
    }
  };
  const edit = (fn: (n: PlanState) => void) => {
    if (!S) return;
    setHist((h) => [...h, JSON.stringify(S)].slice(-100));
    const n: PlanState = structuredClone(S);
    fn(n);
    setStates((st) => ({ ...st, [pi]: n }));
    setMsg(null);
    markDirty();
  };
  const undo = () => {
    if (!hist.length) return;
    const prev: PlanState = JSON.parse(hist[hist.length - 1]);
    setHist(hist.slice(0, -1));
    setStates((st) => ({ ...st, [pi]: prev }));
    markDirty();
  };
  const undoRef = useRef(undo);
  useLayoutEffect(() => { undoRef.current = undo; });
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") setDraft(null);
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !(e.target as Element).closest?.("input,select")) { e.preventDefault(); undoRef.current(); }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);

  const change: Change = (id, f, v) => edit((n) => {
    const item = (n.walls.find((w) => w.id === id) || n.openings.find((o) => o.id === id)) as Record<string, unknown> | undefined;
    if (!item) return;
    if (f === "keep") { item.keep = v; if (!item.keep && !item.reason) item.reason = REASONS[0]; }
    else if (f === "w" || f === "h") item[f] = Math.max(100, Number(v) || (item[f] as number));
    else item[f] = v || null;
    if (f !== "keep" && f !== "reason") item.edited = true;
  });

  // ---------------------------------------------------------------- chọn, chế độ, mặt bằng
  const setMode = (m: Mode) => { setModeState(m); setDraft(null); setHint(HINTS[m]); };
  const select = (id: string, fromDrawing: boolean) => {
    if (!S) return;
    const sel = selected === id ? null : id;
    const isOpen = S.openings.some((o) => o.id === id);
    if (sel && (tab === "walls" && isOpen || tab === "open" && !isOpen || tab === "qty" || tab === "warn")) setTab(isOpen ? "open" : "walls");
    if (sel && filter !== "all" && !isOpen) setFilter("all");
    setSelected(sel); setMsg(null);
    if (!sel) return;
    if (fromDrawing) scrollTo.current = sel;
    else {
      const w = S.walls.find((x) => x.id === sel) || S.walls.find((x) => x.id === (S.openings.find((o) => o.id === sel) || { wall: "" }).wall);
      if (w) focusOn(w);
    }
  };
  useEffect(() => {
    const id = scrollTo.current;
    scrollTo.current = null;
    if (id) listRef.current?.querySelector(`[data-id="${CSS.escape(id)}"]`)?.scrollIntoView({ block: "nearest" });
  });

  const loadPlan = (i: number, D: Data = data!, st = states) => {
    confirmRequest.current?.abort();
    setStates({ ...st, [i]: st[i] || initState(D.plans[i]) });
    setPi(i); setHist([]); setSelected(null); setMsg(null);
    setMode(mode);
    fitSize(D.plans[i].size);
  };
  const showOverview = (D: Data = data!) => {
    confirmRequest.current?.abort();
    setPi(-1); setSelected(null); setHist([]); setMsg(null);
    setMode("select");
    fitSize(D.overview!.size);
  };
  const start = (D: Data) => {
    confirmRequest.current?.abort(); publishPending.current = null;
    store.set("optimat-material-selection", null);
    drawing.current = { projectUid: projectUid(), drawingId: crypto.randomUUID() };
    store.set("optimat-work-review", null);
    store.set("optimat-material-draft", null);
    store.set("optimat-materials-ready", false);
    store.set("optimat-optimization", null);
    D.materials = D.materials || [];
    D.families = D.families || [];
    clearTimeout(roughTimer.current);
    revision.current++; structuralRevision.current++; roughStarted.current = false;
    store.set("optimat-rough", null);
    store.set("optimat-materials-ready", false); store.set("optimat-material-draft", null); store.set("optimat-optimization", null);
    store.set("optimat-confirmed", store.get<Confirmed[]>("optimat-confirmed", []).filter((p) => p.file !== D.file));
    setSheet(null);
    setData(D); setStates({}); setPlanP({}); setConfirmed({}); setRough(null); setStructural(null); setMsg(null);
    if (D.overview && D.overview.cad) return showOverview(D);
    if (!D.plans.length) { setPi(-1); setMsg("Bản vẽ không có mặt bằng kiến trúc để đo tường (chỉ có mặt bằng kết cấu, móng hoặc điện nước)."); return; }
    loadPlan(0, D, {});
  };
  const cancelReading = () => {
    uploadRevision.current++;
    readController.current?.abort();
    readController.current = null;
    setReading(null); setShowReadPreview(false); setMsg(data ? null : START);
  };
  const readFile = async (name: string, url: string, request: RequestInit, context?: AnalysisContext) => {
    confirmRequest.current?.abort();
    if (!projectReady) { setMsg("Lưu tên và thông tin ở trang Dự án của tôi trước khi mở bản vẽ."); return; }
    readController.current?.abort();
    const controller = new AbortController(); readController.current = controller;
    const atUpload = ++uploadRevision.current;
    setShowReadPreview(true);
    setReading({ file: name, stage: "reading", message: context ? "Đang đọc bản gốc đã chọn trong hồ sơ dự án…" : "Đang gửi file và đọc nét bản vẽ…" });
    try {
      const r = await fetch(url, { ...request, method: "POST", signal: controller.signal });
      if (!r.ok) { const body = await r.json().catch(()=>null); throw new Error(typeof body?.detail === "string" && body.detail !== "Not Found" ? body.detail : "Không phân tích được bộ phiên bản đã chọn. Hãy kiểm tra lại hồ sơ."); }
      const body = r.headers.get("content-type")?.includes("application/x-ndjson")
        ? await readProgress(r, (event) => {
          if (uploadRevision.current !== atUpload) return;
          if (event.type === "preview") setReading((old) => old ? { ...old, preview: event.preview } : old);
          else if (event.type === "recognized") setReading((old) => old ? { ...old, recognized: event.data } : old);
          else if (event.type === "status") setReading((old) => old ? { ...old, stage: event.stage, message: event.message } : old);
        }) : await r.json();
      if (uploadRevision.current !== atUpload) return;
      if (context && (projectUid() !== context.projectUid || Number(store.get("optimat-project","")) !== context.projectId)) throw Error("Phiên dự án đã thay đổi.");
      if (context) {
        const proof=body.provenance, expected=context.revisions.filter(f=>f.role!=="THAM_KHAO");
        if (proof?.project_id!==context.projectId || proof.profile_version!==context.profile.profileVersion ||
          !Array.isArray(proof.files) || proof.files.length!==expected.length ||
          !expected.every(f=>proof.files.some((p:SelectedRevision)=>p.revision_id===f.revision_id && p.file_id===f.file_id && p.role===f.role && p.sha256===f.sha256)))
          throw Error("Kết quả không khớp bộ tệp hoặc phiên bản hồ sơ đã chọn.");
      }
      const result = context ? body.view : body;
      if (!result || !Array.isArray(result.plans) || typeof result.file !== "string") throw Error("Máy chủ chưa trả kết quả mặt bằng cho bộ hồ sơ này.");
      localStorage.setItem("optimat-analysis-context", JSON.stringify(context || null));
      start(result);
      if (context && body.structural?.file) setStructural(body.structural);
      setReading(null);
    } catch (err) {
      if (uploadRevision.current !== atUpload || controller.signal.aborted) return;
      setReading((old) => old ? { ...old, error: (err as Error).message, message: "Chưa đọc xong bản vẽ" } : old);
    }
  };
  const upload = (f: File | undefined) => {
    if (!f) return;
    const form = new FormData(); form.append("file", f); form.append("progressive","true");
    if (project) form.append("project_id", String(project));
    return readFile(f.name, "/api/takeoff/view", {body:form});
  };
  useEffect(() => {
    if (!restored || !projectReady || roughOnly || adjustment) return;
    const token=new URLSearchParams(location.search).get("analysis");
    if (!token) return;
    const timer=window.setTimeout(()=>{
      try {
        const handoff=JSON.parse(sessionStorage.getItem("optimat-analysis-start") || "null") as {token:string;context:AnalysisContext} | null;
        if(!handoff || token!==handoff.token) return;
        sessionStorage.removeItem("optimat-analysis-start");
        const c=handoff.context;
        if (projectUid()!==c.projectUid || project!==c.projectId || !c.revisions.length || c.revisions.some(f=>f.project_id!==c.projectId)) throw Error("Bộ hồ sơ không còn khớp dự án. Hãy chọn lại trên trang Dự án của tôi.");
        void readFile(c.revisions.map(f=>f.name).join(", "), projectPath(c.projectId)+"/analysis", {
          headers:{"Content-Type":"application/json"},
          body: JSON.stringify({files:c.revisions.filter(f=>f.role!=="THAM_KHAO").map(({file_id,revision_id,sha256,role})=>({file_id,revision_id,sha256,role})), profile_version:c.profile.profileVersion, progressive:true}),
        }, c);
      } catch(e) { setSaveError(e instanceof Error?e.message:"Không mở được bộ hồ sơ đã chọn."); }
    },0);
    return ()=>window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- token dùng một lần từ đúng thao tác Bắt đầu phân tích.
  },[restored,projectReady,project,roughOnly,adjustment]);

  // ---------------------------------------------------------------- vẽ thêm tường, thêm cửa
  const snapGrid = useMemo(() => {
    const g = new Map<string, Pt[]>();
    if (!P) return g;
    const add = (x: number, y: number) => { const k = Math.floor(x / 500) + ":" + Math.floor(y / 500); (g.get(k) || g.set(k, []).get(k)!).push([x, y]); };
    for (const [x1, y1, x2, y2, , isH] of P.segs) if (!isH) { add(x1, y1); add(x2, y2); }
    return g;
  }, [P]);
  const walls = S?.walls;
  const snap = ([x, y]: Pt): Pt => {
    const tol = 10 * vbRef.current.w / (svgRef.current?.getBoundingClientRect().width || 1);
    let best: Pt | null = null, bd = tol;
    const cx = Math.floor(x / 500), cy = Math.floor(y / 500);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) for (const p of snapGrid.get((cx + i) + ":" + (cy + j)) || []) {
      const d = Math.hypot(p[0] - x, p[1] - y);
      if (d < bd) { bd = d; best = p; }
    }
    for (const w of walls || []) for (const p of [[w.x1, w.y1], [w.x2, w.y2]] as Pt[]) { const d = Math.hypot(p[0] - x, p[1] - y); if (d < bd) { bd = d; best = p; } }
    return best ? [best[0], best[1]] : [x, y];
  };

  const onSvgClick = (e: MouseEvent<SVGSVGElement>) => {
    if (movedRef.current || !S) return;
    if (mode === "select") { if (selected) setSelected(null); return; }
    const p = toWorld(e);
    if (mode === "wall") {
      const q = snap(p);
      if (!draft) { setDraft(q); return; }
      if (Math.hypot(q[0] - draft[0], q[1] - draft[1]) < 200) return;
      const id = "M" + (S.seq + 1);
      edit((n) => {
        n.seq += 1;
        n.walls.push({ id, cls: newCls, role: "partition", x1: draft[0], y1: draft[1], x2: q[0], y2: q[1], reason: null,
          mat: null, fam: null, cand: [], masonry: true, conf: 1, keep: true, src: "manual", edited: false });
      });
      setDraft(null);
      setSelected(id); setTab("walls"); setFilter("all");
    } else if (mode === "open") {
      const w = nearestWall(S, p[0], p[1]);
      if (!w) { setHint("Không có tường đang giữ trong vòng 0,6 m quanh điểm bấm."); return; }
      const id = "N" + (S.seq + 1);
      edit((n) => {
        n.seq += 1;
        n.openings.push({ id, wall: w.id, kind: newKind, w: Number(newW) || 900, h: Number(newH) || 2200, x: p[0], y: p[1], keep: true, src: "manual" });
      });
      setSelected(id); setTab("open");
    }
  };
  const toggleCol = (j: number) => {
    if (!P || !pp) return;
    setPlanP({ ...planP, [pi]: { ...pp, cols: pp.cols.map((c, k) => (k === j ? { ...c, keep: !c.keep } : c)) } });
    scheduleRough();
  };

  // ---------------------------------------------------------------- xác nhận, xuất
  // Ghi mặt bằng đã chốt cho giao diện chung (Vật liệu và giá, Phương án tối ưu). Lưu trên trình duyệt;
  // kết quả chính thức nằm trong takeoff_results khi có mã dự án. Một bản vẽ + mặt bằng chỉ giữ lần xác nhận mới nhất.
  const focusField = (field: string) => {
    if (field === "scope") scopeInput.current?.focus();
    else if (field === "height") heightLabel.current?.querySelector("input")?.focus();
  };
  const focusAfterSwitch = useRef("");
  useLayoutEffect(() => { focusField(focusAfterSwitch.current); focusAfterSwitch.current = ""; }, [pi]);
  const guideToPlan = () => {
    setSheet(null);
    if (!guide) return;
    if (guide.index === pi) focusField(guide.field);
    else { focusAfterSwitch.current = guide.field; loadPlan(guide.index); }
  };
  const publishConfirmation = (body: Confirmed) => {
    const stamp = stampByBody.current.get(body);
    if (externalChange || !stamp || !stampIsCurrent(stamp)) { setSheet(null); setExternalChange(true); return; }
    if (!data || !P || body.plan !== P.plan.name || body.file !== data.file) {
      setSheet(null); setSaveError("Bản xác nhận không khớp mặt bằng đang mở."); return;
    }
    const next = { ...confirmed, [pi]: body };
    if (stamp.published) {
      const summaries = store.get<Confirmed[]>("optimat-confirmed", []).filter(p => p.plan === body.plan);
      if (!reviewMatchesConfirmed(body.file, { [pi]: body }, summaries)) { setSheet(null); setExternalChange(true); return; }
    } else {
      publishPending.current = stamp;
      setConfirmed(next);
      if (!persistReview(next)) { setSheet({ kind: "recover", body }); return; }
    }
    if (adjustment) {
      setSheet({ kind: "msg", title: "Đã lưu điều chỉnh", body: <p>Phương án vật liệu của mặt bằng đã được cập nhật cho bước tra giá và tối ưu.</p> });
    } else if (data.plans.every((_, i) => states[i]?.scope === "reference" || next[i])) {
      setSheet(null); router.push("/phan-tho");
    } else {
      setSheet({ kind: "confirmed", body, total: c?.total ?? body.total_net_area_m2 });
    }
  };
  const sendConfirm = async () => {
    if (confirmRequest.current) return;
    if (externalChange || !ownsReview() || (publishPending.current && !stampIsCurrent(publishPending.current))) {
      setSheet(null); setExternalChange(true); return;
    }
    if (guide) { guideToPlan(); return; }
    if (reading || !data || !P || !S || !c) { setSheet(null); setSaveError("Chờ đọc xong và mở một mặt bằng để xác nhận."); return; }
    if (confirmed[pi]) { publishConfirmation(confirmed[pi]); return; }
    const version = drawing.current;
    if (!version || project !== sessionProject.current || pi !== activePlan.current) { setSheet(null); setExternalChange(true); return; }
    const stamp: ConfirmationStamp = { ...version, projectId: project, revision: revision.current, planIndex: pi };
    const controller = new AbortController();
    confirmRequest.current = controller; setConfirmBusy(true);
    const atRevision = revision.current;
    let timedOut = false;
    const timeout = setTimeout(() => { timedOut = true; controller.abort(); }, 120_000);
    try {
      const response = await fetch("/api/takeoff/confirm", { method: "POST", headers: { "Content-Type":"application/json" },
        body: JSON.stringify(payload(data, P, S, project)), signal: controller.signal });
      const body = await response.json();
      if (controller.signal.aborted || revision.current !== atRevision) return;
      if (!stampIsCurrent(stamp)) { setExternalChange(true); return; }
      if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : `Máy chủ từ chối kết quả (HTTP ${response.status}).`);
      stampByBody.current.set(body, stamp);
      publishConfirmation(body);
    } catch (err) {
      if ((timedOut || !controller.signal.aborted) && stampIsCurrent(stamp))
        setSheet({ kind: "msg", title: "Chưa nhận được kết quả xác nhận", body: <p>{timedOut ? "Máy chủ chưa phản hồi sau hai phút. Kiểm tra kết quả đã lưu của dự án trước khi gửi lại." : (err as Error).message}</p> });
    } finally {
      clearTimeout(timeout);
      if (confirmRequest.current === controller) {
        confirmRequest.current = null; setConfirmBusy(false);
        if (controller.signal.aborted || revision.current !== atRevision) setSheet(prev => prev?.kind === "confirm" ? null : prev);
      }
    }
  };
  const openConfirmation = () => {
    if (guide) guideToPlan();
    else if (confirmed[pi]) publishConfirmation(confirmed[pi]);
    else if (S && !reading) setSheet({ kind: "confirm" });
  };
  const download = (name: string, text: string, type: string) => {
    try {
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([text], { type }));
      a.download = name; document.body.appendChild(a); a.click(); a.remove();
    } catch (e) { setSheet({ kind: "msg", title: "Không tải được file", body: <p>{(e as Error).message}</p> }); }
  };
  // ---------------------------------------------------------------- thông số phần thô
  const onParam = (k: string, v: string) => {
    const vals = { ...roughVals, [k]: v };
    setRoughVals(vals);
    scheduleRough();
  };
  // bản vẽ kết cấu tách file: máy chủ đọc dầm, cột, móng, bảng thép; ghép vào yêu cầu phần thô rồi tính lại
  const onStructural = async (f: File | undefined) => {
    if (!f) return;
    const atStructural = ++structuralRevision.current;
    const rerun = roughStarted.current;
    scheduleRough(); clearTimeout(roughTimer.current);
    latest.current.structural = null;
    setStructural({ busy: `Đang đọc ${f.name}…` });
    const form = new FormData(); form.append("file", f);
    try {
      const r = await fetch("/api/takeoff/structural", { method: "POST", body: form });
      const body = await r.json();
      if (structuralRevision.current !== atStructural) return;
      if (!r.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Không đọc được bản vẽ kết cấu.");
      setStructural(body); latest.current.structural = body;
      revision.current++;
      computeRough();
    } catch (err) {
      if (structuralRevision.current === atStructural) {
        setStructural({ error: (err as Error).message });
        if (rerun) setRough({ error: "Chưa tính lại: không đọc được bản vẽ kết cấu. Mở lại file kết cấu rồi tính phần thô." });
      }
    }
  };
  const onPlanParam = (k: string, v: string | boolean) => {
    if (!pp) return;
    setPlanP({ ...planP, [pi]: { ...pp, [k]: v } });
    scheduleRough();
  };

  // ---------------------------------------------------------------- bố cục
  const overview = !!data && pi < 0 && hasOverview;
  const status = overview ? ["", "Xem toàn bộ"] : confirmed[pi] ? [s.done, "Đã xác nhận"] : [s.edit, "Đang kiểm tra"];
  const showTab = (t: string) => { setTab(t); setMsg(null); };
  const tabs: [string, string, ReactNode][] = [["walls", "Tường", S ? S.walls.filter((w) => w.keep).length : ""], ["open", "Lỗ mở", S ? S.openings.filter((o) => o.keep).length : ""],
    ["qty", "Khối lượng", null], ...(adjustment ? [["rough", "Phần thô", null] as [string, string, ReactNode]] : []), ["warn", "Cảnh báo", P && S ? (P.warnings || []).length + convBad(data).length : ""]];
  let filters: ReactNode = null, body: ReactNode = null;
  if (msg != null || !data) body = <div className={s.empty}>{msg}</div>;
  else if (overview) body = <OverviewList D={data} onOpen={(i) => loadPlan(i)} />;
  else if (P && S && c && pp) {
    if (tab === "walls") {
      filters = <WallFilters S={S} filter={filter} onFilter={setFilter} onAllMat={adjustment ? () => setSheet({ kind: "material" }) : undefined} />;
      body = <WallList materials={adjustment} D={data} S={S} c={c} filter={filter} selected={selected} onSelect={(id) => select(id, false)} change={change} />;
    } else if (tab === "open") {
      filters = <span>Rộng × cao theo mm. Cửa nhận từ khe tường lấy cao mặc định: kiểm tra lại theo bảng thống kê cửa.</span>;
      body = <OpeningList S={S} selected={selected} onSelect={(id) => select(id, false)} change={change} onDelete={(id) => edit((n) => { n.openings = n.openings.filter((o) => o.id !== id); })} />;
    } else if (tab === "qty") body = <QtyTab materials={adjustment} D={data} S={S} c={c} confirmed={confirmed[pi]} />;
    else if (tab === "rough") {
      filters = <span>Phần thô cả công trình: mọi mặt bằng trong file, theo tường, cửa đã sửa ở các tab khác.
        {(P.stairs?.length || 0) > 1 && <> Mặt bằng có {P.stairs!.length} thang: biểu mẫu sửa thang đầu tiên; các thang còn lại giữ nguyên dữ liệu nhận dạng.</>}</span>;
      body = <RoughTab P={P} pp={pp} values={roughVals} rough={rough} busy={roughBusy} onParam={onParam} onPlanParam={onPlanParam} onRun={computeRough}
        structural={structural} onStructural={onStructural} />;
    } else body = <WarnTab D={data} P={P} />;
  }
  const closeSheet = () => setSheet(null);
  if (externalChange) return <Empty>Dự án đã thay đổi trong tab khác. <button className="btn" onClick={() => location.reload()}>Tải phiên hiện tại</button></Empty>;

  if (roughOnly) return <div className="flex flex-col gap-4 p-5">
    <Steps cur="/phan-tho" done={{ "/do-boc": allCountedConfirmed, "/phan-tho": !!receipt?.confirmed && sameWorkVersion(receipt, roughStored) }} />
    <Head title="Kiểm tra công tác và khối lượng" actions={<Link className="btn" href="/do-boc">Về bóc tách bản vẽ</Link>}>Kiểm khối lượng theo tầng trước khi chọn vật liệu. Bổ sung kích thước còn thiếu, tính lại và kiểm từng dòng.</Head>
    {saveError && <p role="alert">{saveError}</p>}{saveNotice && <p role="status">{saveNotice}</p>}
    {!data || !P || !pp ? <Empty>{msg || "Chưa có bản vẽ đã xác nhận."} <Link href="/do-boc">Về bóc tách</Link></Empty> : <>
      <label>Mặt bằng <select className="field" value={pi} onChange={(e) => loadPlan(Number(e.target.value))}>{data.plans.map((p, i) => <option key={i} value={i}>{p.plan.name}</option>)}</select></label>
      {rough && !("error" in rough) && roughStored && !roughBusy && <WorkReview key={roughStored.reviewId} snapshot={roughStored}
        initial={sameWorkVersion(roughStored, receipt) ? receipt : null} onSave={(next, destination) => {
        if (!persistReview() || !sameWorkVersion(roughStored, store.get("optimat-rough", null)) || drawing.current?.drawingId !== roughStored.drawingId)
          throw new Error("Chưa lưu được hoặc khối lượng đã đổi. Hãy kiểm tra lại phiên hiện tại.");
        const updates: Record<string, string> = { "optimat-work-review": JSON.stringify(next) };
        if (!next.confirmed) Object.assign(updates, { "optimat-materials-ready": "false", "optimat-optimization": "null" });
        saveTogether(updates);
        if (next.confirmed && destination) router.push(destination);
      }} />}
      <RoughTab P={P} pp={pp} values={roughVals} rough={rough} busy={roughBusy} onParam={onParam} onPlanParam={onPlanParam} onRun={computeRough} structural={structural} onStructural={onStructural} />

    </>}
  </div>;

  return (
    <div className="flex h-screen min-h-0 flex-col max-[900px]:h-auto">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2.5 border-b border-rule bg-card px-5 py-3">
        <div className="mr-auto"><Steps cur={adjustment ? "/dieu-chinh" : "/do-boc"} done={{ "/do-boc": confirmedList.length > 0, "/phan-tho": !!roughStored }} /></div>
        {adjustment ? (allCountedConfirmed
          ? <Link className="btn primary" href="/vat-lieu">Tiếp: vật liệu và giá</Link>
          : <span className="text-muted">Lưu điều chỉnh từng mặt bằng để tiếp tục</span>)
          : allCountedConfirmed
            ? <Link className="btn primary" href="/phan-tho">Tiếp: kiểm tra công tác và khối lượng</Link>
            : <span className="text-muted">Xác nhận khối lượng từng mặt bằng để tiếp tục</span>}
      </div>
      {saveError && <p role="alert">{saveError}</p>}
      {saveNotice && <p role="status">{saveNotice}</p>}
      <div className={`${s.app} min-h-0 flex-1`}>
        <header className={s.head}>
          <h1>{adjustment ? "Điều chỉnh vật liệu và phần thô" : "Xác nhận kích thước và khối lượng"}</h1>
          <span className={s.file}>{data?.file || ""}</span>
          {P && S && <span className={s.field}>{paper ? <span title={paper.source}>Tỷ lệ in 1:{paper.denominator} · từ tiêu đề hình</span> :
            <label>Tỷ lệ in · {S.paperScale ? "người dùng nhập" : "chưa xác định"} · 1:
              <ChangeInput key={pi} aria-label="Mẫu số tỷ lệ in tham chiếu" type="number" min={0.01} step="any" placeholder="Nhập"
                value={S.paperScale == null ? "" : String(S.paperScale)} onCommit={el => {
                  const v = el.valueAsNumber;
                  if (el.value && !(Number.isFinite(v) && v > 0)) return S.paperScale == null ? "" : String(S.paperScale);
                  setStates(st => ({ ...st, [pi]: { ...st[pi], paperScale: el.value ? v : undefined } }));
                }} /></label>}</span>}
          {data && !P && <span className={s.field}>Tỷ lệ in: chọn từng hình để xem</span>}
          {S && <label>Phạm vi hình <select ref={scopeInput} value={S.scope || ""} onChange={(e) => {
            edit((n) => { n.scope = e.target.value as "count" | "reference" | null; });
            store.set("optimat-materials-ready", false);
          }}><option value="">Chưa xác nhận tầng/phạm vi</option><option value="count">Tính khối lượng tầng này</option><option value="reference">Hình tham khảo / bản sao, không cộng</option></select></label>}
          {guide && <span role="status">{guide.message}</span>}
          {data && (data.plans.length > 1 || hasOverview) && <label className={s.field}>Mặt bằng{" "}
            <select value={String(pi)} onChange={(e) => { const v = Number(e.target.value); if (v < 0) showOverview(); else loadPlan(v); }}>
              {hasOverview && <option value="-1">Toàn bộ bản vẽ</option>}
              {data.plans.map((p, i) => <option key={i} value={i}>{i + 1}. {p.plan.name}</option>)}
            </select></label>}
          <label className={s.field} ref={heightLabel}>Chiều cao tầng (m){" "}
            <ChangeInput type="number" step={0.05} min={1} max={10} value={S ? (S.height_mm / 1000).toFixed(2) : ""} onCommit={(el) => {
              if (!S) return;
              const v = Number(el.value);
              if (!(v >= 1 && v <= 10)) return (S.height_mm / 1000).toFixed(2);
              edit((n) => { n.height_mm = Math.round(v * 1000); n.height_source = "nhập tay"; });
              return (Math.round(v * 1000) / 1000).toFixed(2);
            }} /></label>
          <label className={s.field}>Chiều dài{" "}
            <select value={S?.length_rule || "tim"} onChange={(e) => edit((n) => { n.length_rule = e.target.value; })}>
              <option value="tim">theo trục tim</option><option value="thong_thuy">thông thủy</option></select></label>
          <span className={`${s.status} ${status[0]}`}>{status[1]}</span>
          <span className={s.grow} />
          <label className={s.btn} title={projectReady ? "Mở bản vẽ cho dự án hiện tại" : "Nhập thông tin dự án ở đầu trang trước"}>Mở bản vẽ… <input disabled={!projectReady} type="file" accept=".dxf,.dwg" hidden onChange={(e) => {
            const file = e.currentTarget.files?.[0];
            e.currentTarget.value = "";
            void upload(file);
          }} /></label>
          <button className={s.btn} type="button" disabled={!hist.length} onClick={undo}>Hoàn tác</button>
          <button className={`${s.btn} ${s.primary}`} type="button" disabled={!!reading || confirmBusy || !data?.plans.length} onClick={openConfirmation}>
            {guide?.action || (confirmed[pi] ? "Tiếp tục từ bản đã xác nhận" : adjustment ? "Lưu điều chỉnh mặt bằng" : "Xác nhận kích thước, khối lượng")}</button>
        </header>
        <div className={s.main}>
          <Board svgRef={svgRef} scaleRef={scaleRef} zoomRef={zoomRef} zoomLabel={zoomLabel} zoomTo={zoomTo} movedRef={movedRef} toWorld={toWorld} onPointerDown={onPointerDown} fitSize={fitSize} data={data} pi={pi} P={P} S={S} selected={selected} mode={mode} onMode={setMode} draft={draft} snap={snap} unit={unit}
            preview={showReadPreview && reading?.preview && !reading.error && <ReadPreview preview={reading.preview} recognized={reading.recognized} />}
            hint={reading ? <div className="flex flex-wrap items-center gap-2">
              <span className="break-words" role={reading.error ? "alert" : "status"}>{reading.file} · {reading.error || reading.message}
                {reading.preview && !reading.error && ` · ${reading.preview.shown.toLocaleString("vi-VN")}/${reading.preview.total.toLocaleString("vi-VN")} nét`}</span>
              {reading.preview && !reading.error && <button className={s.btn} aria-pressed={showReadPreview} onClick={() => setShowReadPreview(!showReadPreview)}>
                {showReadPreview ? "Ẩn nét đang nhận diện" : "Xem nét đang nhận diện"}</button>}
              <button className={s.btn} onClick={cancelReading}>{reading.error ? "Đóng thông báo" : "Hủy đọc"}</button>
            </div> : hint}
            bg={bg} hasCad={hasCad} onBg={setBgPref} showRec={showRec} onShowRec={setShowRec} showLabels={showLabels} onShowLabels={setShowLabels}
            newCls={newCls} onNewCls={setNewCls} newKind={newKind}
            onNewKind={(v) => { setNewKind(v); setNewH(v === "door" ? "2200" : "1400"); setNewW(v === "door" ? "900" : "1200"); }}
            newW={newW} onNewW={setNewW} newH={newH} onNewH={setNewH}
            cols={pp ? pp.cols : []} onToggleCol={toggleCol} onSvgClick={onSvgClick} onSelect={(id) => select(id, true)} onOpenPlan={(i) => loadPlan(i)} />
          <aside className={s.aside}>
            <div className={s.tabs} role="tablist">
              {tabs.map(([k, t, n]) => (
                <button key={k} className={s.tab} role="tab" type="button" aria-selected={tab === k} onClick={() => showTab(k)}>{t}{n != null && <span className={s.n}>{n}</span>}</button>
              ))}
            </div>
            {filters && <div className={s.filters}>{filters}</div>}
            <div className={s.list} ref={listRef}>{body}</div>
            <div className={s.foot}>
              <span className={s.total}>Diện tích tường thực <b>{overview ? "–" : fmt(c ? c.total : 0)}</b> m²</span>
              <span className={s.grow} />
              <button className={s.btn} type="button" onClick={() => data && P && S && download(base(data, P) + ".csv", csvText(data, S), "text/csv")}>Xuất CSV</button>
              <button className={s.btn} type="button" onClick={() => data && P && S && download(base(data, P) + ".json",
                JSON.stringify({ ...payload(data, P, S, project), confirmed: confirmed[pi] || null }, null, 2), "application/json")}>Xuất JSON</button>
            </div>
          </aside>
        </div>
        {sheet?.kind === "material" && data && S && <MaterialDialog data={data} n={S.walls.filter((w) => w.keep && w.masonry && !w.mat).length} onClose={closeSheet}
          onApply={(m, cl) => { edit((n) => n.walls.forEach((w) => { if (w.keep && w.masonry && !w.mat && (!cl || w.cls === cl)) { w.mat = m; w.edited = true; } })); closeSheet(); }} />}
        {sheet?.kind === "confirm" && P && S && c && <ConfirmDialog P={P} S={S} c={c} send={sendConfirm} busy={confirmBusy} onClose={() => { if (!confirmRequest.current) closeSheet(); }} />}
        {sheet?.kind === "recover" && <Msg title="Máy chủ đã xác nhận mặt bằng" onClose={closeSheet}><p>{saveError || "Chưa hoàn tất lưu phiên trên trình duyệt."} Giữ trang này mở để tiếp tục từ kết quả đã nhận.</p>
          <button className={s.btn} type="button" onClick={() => publishConfirmation(sheet.body)}>Thử lưu phiên và tiếp tục</button></Msg>}
        {sheet?.kind === "confirmed" && <ConfirmedDialog body={sheet.body} total={sheet.total} onClose={closeSheet} onNext={() => {
          const next = data?.plans.findIndex((_, i) => states[i]?.scope === "count" && !confirmed[i]) ?? -1;
          closeSheet(); if (next >= 0) loadPlan(next);
        }} />}
        {sheet?.kind === "msg" && <Msg title={sheet.title} primary={sheet.primary} onClose={closeSheet}>{sheet.body}</Msg>}
      </div>
    </div>
  );
}
