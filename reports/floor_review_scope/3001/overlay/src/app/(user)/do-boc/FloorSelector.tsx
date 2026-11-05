import { useMemo } from "react";
import type { Plan, PlanState } from "./model";
import { floorGroups, type ReviewScope } from "./floor-review";

export function FloorSelector({ plans, states, selected, disabled, onChange, onOpen }: {
  plans: Plan[]; states: Record<number, PlanState>; selected: ReviewScope; disabled: boolean;
  onChange: (next: ReviewScope) => void; onOpen: () => void;
}) {
  const groups = useMemo(() => floorGroups(plans, states), [plans, states]);
  const n = groups.filter(g => g.views.every(i => selected.includes(i))).length;
  return <fieldset className="min-w-0 rounded-md border border-rule bg-card px-3 py-2" disabled={disabled}>
    <legend className="px-1 font-semibold">Chọn tầng để kiểm tra</legend>
    <div className="flex flex-wrap items-center gap-2">
      <button className="btn" type="button" onClick={() => onChange(groups.flatMap(g => g.views))}>Chọn tất cả</button>
      <button className="btn" type="button" onClick={() => onChange([])}>Bỏ tất cả</button>
      <button className="btn" type="button" onClick={() => onChange(groups.filter(g => g.reasons.length).flatMap(g => g.views))}>Chỉ tầng cần kiểm tra</button>
    </div>
    <div className="my-2 max-h-44 overflow-auto divide-y divide-rule">
      {groups.map(g => <div key={g.key} className="py-1">
        <label className="flex items-baseline gap-2">
          <input type="checkbox" checked={g.views.every(i => selected.includes(i))}
            onChange={e => onChange(e.target.checked ? [...selected, ...g.views] : selected.filter(i => !g.views.includes(i)))} />
          <span><strong>{g.label}</strong>{g.reasons.length > 0 && <span className="ml-2 text-muted">{" · "}{g.reasons.join(" · ")}</span>}</span>
        </label>
        {(g.views.length > 1 || g.key.startsWith("view-")) && <ul className="ml-6 text-sm">
          {g.views.map(i => <li key={i}>Hình {i + 1} · {plans[i].plan.name} · {states[i]?.scope === "count" ? "Tính khối lượng" : states[i]?.scope === "reference" ? "Tham khảo" : "Chưa phân loại"}</li>)}
        </ul>}
      </div>)}
    </div>
    <div className="flex flex-wrap items-center gap-2"><span aria-live="polite">Đã chọn {n}/{groups.length}</span>
      <button className="btn primary" type="button" disabled={!n || disabled} onClick={onOpen}>Kiểm tra {n} tầng đã chọn</button>
    </div>
  </fieldset>;
}
