import type { ProjectInfo } from "@/lib/projects";
import type { ProfileSource } from "@/lib/project-records";

export type SheetData = {sheet:number;sheet_name:string;sheets:string[];rows:(string|null)[][];truncated?:boolean};
const labels = {"địa điểm":"location","địa chỉ công trình":"location","loại công trình":"buildingType","số tầng":"floors","mô tả công trình":"note","nhu cầu vật liệu":"materialNeeds"} as const;
export function sheetFacts(table:SheetData) {
  return table.rows.flatMap((row,r)=>row.flatMap((label,c)=>{
    const key=(label || "").trim().toLocaleLowerCase("vi").replace(/[:：]$/,"").trim();
    const field=Object.hasOwn(labels,key) ? labels[key as keyof typeof labels] : null;
    const raw=row[c+1]?.trim();
    if(!field || !raw || (field==="floors" && !/^[1-9]\d*(?:\s+tầng)?$/iu.test(raw)))return [];
    const col=c+2;
    const cell=(col>26 ? String.fromCharCode(64+Math.floor((col-1)/26)) : "")+String.fromCharCode(65+(col-1)%26)+(r+1);
    return [{label,field,value:field==="floors"?parseInt(raw,10):raw,cell}];
  }));
}
export function estimateRows(table:SheetData) {
  const sheet=table.sheet_name.normalize("NFD").replace(/[\u0300-\u036f]/g,"").trim().toLowerCase();
  const rows:{kind:string;label:string;quantity:string;unit:string;cell:string;parent:string}[]=[];
  if(sheet!=="tien luong")return rows;
  let parent="",unit="";
  const numeric=(v:string|null|undefined)=>!!v?.trim() && /^-?\d+(?:[.,]\d+)?$/.test(v.trim());
  table.rows.forEach((r,i)=>{
    if(r[2]?.trim() || numeric(r[0])){
      parent="";unit="";
      if(!r[1]?.trim() || !numeric(r[0]) || !numeric(r[9]) || !r[2]?.trim())return;
      parent=r[1].trim();unit=r[2].trim();
      rows.push({kind:"Tổng công tác",label:parent,quantity:r[9]!,unit,cell:"J"+(i+1),parent:""});
    } else if(parent && r[1]?.trim() && numeric(r[8]) && numeric(r[3])){
      rows.push({kind:"Phần góp cấu kiện",label:r[1].trim(),quantity:r[8]!,unit,cell:"I"+(i+1),parent});
    }
  });
  return rows;
}
export function SheetFacts({table,draft,apply,changeSheet}:{table:SheetData;draft:ProjectInfo;apply:(field:ProfileSource["field"],value:string|number,cell:string)=>void;changeSheet:(sheet:number)=>void}) {
  const facts=sheetFacts(table);
  const estimates=estimateRows(table);
  return <section><label>Sheet nguồn <select className="field" value={table.sheet} onChange={e=>changeSheet(Number(e.target.value))}>{table.sheets.map((s,i)=><option key={s} value={i+1}>{s}</option>)}</select></label>
    <h3>Dữ kiện đề xuất từ bảng tính</h3>
    {facts.map(f=><div className="my-2 rounded border p-3" key={f.cell}><strong>{f.label}: {f.value}</strong><p>Nguồn: {table.sheet_name} · {f.cell}</p>
      {draft[f.field] && String(draft[f.field])!==String(f.value) && <p>Khác với thông tin hiện tại: {draft[f.field]}</p>}
      <button type="button" className="btn" onClick={()=>apply(f.field,f.value,f.cell)}>Đưa vào bản nháp</button></div>)}
    {!facts.length && <p>Chưa thấy nhãn thông tin công trình có giá trị ở ô liền bên phải.</p>}
    {!!estimates.length && <details><summary>Đối chiếu tiên lượng ({estimates.length} dòng)</summary>
      <p>Giá trị đọc từ bảng dự toán, chờ xác nhận phạm vi. Phần góp nằm trong tổng của công tác.</p>
      <div className="tw"><table><thead><tr><th>Loại dòng</th><th>Nội dung</th><th>Lượng</th><th>Nguồn</th></tr></thead><tbody>{estimates.map(r=><tr key={r.cell}><td>{r.kind}</td><td>{r.label}{r.parent && <small className="block">Thuộc: {r.parent}</small>}</td><td>{r.quantity} {r.unit}</td><td>{table.sheet_name} · {r.cell}</td></tr>)}</tbody></table></div>
    </details>}
    {table.truncated && <p>Đang đọc phần xem trước, tối đa 100 dòng và 30 cột.</p>}
  </section>;
}
