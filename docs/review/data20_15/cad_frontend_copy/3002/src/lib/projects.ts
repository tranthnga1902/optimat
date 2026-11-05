import { store } from "./store";

const KEYS = ["optimat-project-uid", "optimat-project-files-selected", "optimat-analysis-context", "optimat-work-review", "optimat-project", "optimat-confirmed", "optimat-rough", "optimat-review", "optimat-rough-params", "optimat-constraints", "optimat-optimization", "optimat-project-name", "optimat-project-info", "optimat-material-draft", "optimat-material-selection", "optimat-materials-ready"];
export function projectUid() {
  const saved = store.get<string>("optimat-project-uid", "");
  if (saved) return saved;
  const uid = crypto.randomUUID();
  localStorage.setItem("optimat-project-uid", JSON.stringify(uid));
  return uid;
}
export type ProjectInfo = { location: string; buildingType: string; floors: string; note: string;
  materialNeeds?: string; updatedAt?: string; profileVersion?: number;
};
export type ProjectHistory = { id: string; name: string; at: string; values: Record<string, string> };
export function switchProject(target?: ProjectHistory) {
  const values: Record<string, string> = {};
  for (const key of KEYS) {
    const value = localStorage.getItem(key);
    if (value !== null) values[key] = value;
  }
  const history = store.get<ProjectHistory[]>("optimat-project-history", []);
  const previousHistory = localStorage.getItem("optimat-project-history");
  const next = history.filter((p) => p.id !== target?.id);
  if (values["optimat-project-info"] || values["optimat-review"] || values["optimat-confirmed"] || values["optimat-optimization"]) {
    next.unshift({ id: crypto.randomUUID(), name: store.get("optimat-project-name", "Dự án đang làm"), at: new Date().toISOString(), values });
  }
  // Lưu lịch sử thành công trước khi thay đổi dữ liệu dự án đang mở.
  localStorage.setItem("optimat-project-history", JSON.stringify(next));
  try {
    for (const key of KEYS) {
      if (target?.values[key] !== undefined) localStorage.setItem(key, target.values[key]);
      else localStorage.removeItem(key);
    }
    if (!target?.values["optimat-project-uid"]) localStorage.setItem("optimat-project-uid", JSON.stringify(target?.id || crypto.randomUUID()));
  } catch (error) {
    if (previousHistory == null) localStorage.removeItem("optimat-project-history");
    else localStorage.setItem("optimat-project-history", previousHistory);
    for (const key of KEYS) {
      if (values[key] !== undefined) localStorage.setItem(key, values[key]);
      else localStorage.removeItem(key);
    }
    throw error;
  }
}
