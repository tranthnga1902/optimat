"""Ca âm hai đoạn hoàn toàn tổng hợp. Chạy bộ tính và hai bộ chọn UI, không lưu phiếu công trình."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from optimat.catalog.repository import Catalog
from optimat.db.session import get_database_url
from optimat.rough.models import ProjectParams
from optimat.rough.structural_column_instances import StructuralColumnInstance
from optimat.rough.takeoff import RoughRequest, compute_rough

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
assert not get_database_url() and os.environ.get("OPTIMAT_NO_DOTENV")
base = dict(code="C-TEST", floor_key="T2", z_from_mm=3000, z_to_mm=6000, b_mm=250, h_mm=400,
            grid_x="4", file="synthetic.dxf", sheet="SYN", evidence=["Nguồn thử tổng hợp"])
columns = [
    StructuralColumnInstance(**base, instance_id="synthetic-a", grid_y="A"),
    StructuralColumnInstance(**base, instance_id="synthetic-b", grid_y="B", top_slab_thickness_mm=100,
                             top_slab_source="Vùng sàn thử chỉ thuộc đỉnh cột B"),
]
ui = r"""
const fs=require('node:fs'),ts=require('./frontend/node_modules/typescript'),vm=require('node:vm');
const data=JSON.parse(fs.readFileSync(0,'utf8'));
function load(file){
    const js=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
    const ctx={exports:{}};vm.runInNewContext(js,ctx);return ctx.exports;
}
const unchecked=load('frontend/src/app/(user)/do-boc/row-advisory.ts').uncheckedRowAdvice;
const reviewed=load('frontend/src/app/(user)/dieu-chinh/advice-scope.ts').adviceScope;
const rows=data.result.works;
const report=rows.flatMap((w,i)=>{
    if(w.code!=='COT') return [];
    const local=unchecked(data,i,[]).context;
    // Phiếu này chỉ là tham số kiểm thử trên fixture tổng hợp để đi vào nhánh đã kiểm.
    const scoped=reviewed(data,{checked:[i],partial:true},i);
    const facts=m=>({id:m.material_id,quantity:m.quantity,after_waste:m.quantity_with_waste,missing:m.missing});
    return [{element:w.element,key:'w:'+i,net:w.quantity,missing:w.missing,
             unchecked:local.materials.map(facts),reviewed:scoped.materials.map(facts)}];
});
console.log(JSON.stringify(report));
"""
cases = []
for supply in ("ready_mix", "site_mix"):
    params = ProjectParams(concrete_grade="M250", concrete_supply=supply)
    req = RoughRequest(plans=[], structural_columns=columns, params=params)
    result = compute_rough(req, Catalog.from_csv())
    snapshot = {"request": req.model_dump(), "result": result.model_dump()}
    response = subprocess.run(["node", "-e", ui], input=json.dumps(snapshot), cwd=ROOT, capture_output=True,
                              encoding="utf-8", check=True)
    a,b = json.loads(response.stdout)
    assert a["element"].endswith("[synthetic-a]") and b["element"].endswith("[synthetic-b]")
    assert a["net"] is None and b["net"] == 0.29
    for mode in ("checked", "unchecked"):
        field = "reviewed" if mode == "checked" else mode
        assert all(m["quantity"] is None for m in a[field])
        assert all(m["quantity"] is not None and m["quantity"] > 0 for m in b[field])
        assert all(m["after_waste"] is None for m in a[field]+b[field])
        expected = {"BT03"} if supply=="ready_mix" else {"XM02","CA01","DA01"}
        assert {m["id"] for m in a[field]} == {m["id"] for m in b[field]} == expected
    foreign = sorted({g for m in b["reviewed"] for g in m["missing"] if g in a["missing"] and g not in b["missing"]})
    cases.append({"supply":supply,"installation_by_work":[a,b],"reasons_from_a_visible_on_b":foreign})
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [
    "src/optimat/rough/materials.py","src/optimat/rough/models.py",
    "frontend/src/app/(user)/do-boc/row-advisory.ts","frontend/src/app/(user)/dieu-chinh/advice-scope.ts"]}
out={"data_kind":"SYNTHETIC","browser":False,"database":False,"openai":False,"saved_receipts":0,
     "source_sha256":hashes,"quantity_scope_passed":True,
     "missing_scope_passed":all(not c["reasons_from_a_visible_on_b"] for c in cases),"cases":cases}
(OUT/"mixed_scope.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
for c in cases: print(c["supply"],c["reasons_from_a_visible_on_b"])
if not out["missing_scope_passed"]:
    raise SystemExit("FAIL: lý do thiếu của đoạn A xuất hiện khi chỉ chọn đoạn B.")
