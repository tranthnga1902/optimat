"use client";
import { useState } from "react";
import { DrawingWorkList } from "@/app/(user)/do-boc/DrawingWorkList";
import type { Data, Plan, Structural } from "@/app/(user)/do-boc/model";

function floor(name: string, walls: number): Plan {
  return { plan:{name}, height_mm:3300,size:[2000,3000],layers:[],segs:[],openings:[],
    walls:Array.from({length:walls},(_,i)=>({id:"W"+(i+1),cls:"110",role:"partition",x1:0,y1:i*1000,x2:2000,y2:i*1000,masonry:true,conf:1})) };
}
const drawing: Data={file:"mau-kiem-thu-kt.dxf",plans:[floor("Trệt",2),floor("Lầu 1",1)],materials:[],families:[]};
const kc: Data={file:"mau-kiem-thu-kc.dxf",plans:[],materials:[],families:[],drawing_work_signals:{FOUNDATION:["Móng M1"],REBAR:["Bảng thống kê thép"]}};
const structural: Structural={file:"mau-ket-cau.dxf",foundations:[{}],notes:[],lintel_height_mm:null,structural_beams:{},structural_floors:{},
  column_schedule:[],column_sections:{},rebar:[{}],members:[],sheets:[]};
export default function WorkListFixture() {
  const [view,setView]=useState("preview");
  return <main className="p-5"><h1>Kiểm thử danh sách công tác dưới bản vẽ</h1>
    <p>Dữ liệu tổng hợp · chỉ dùng trên bản QA.</p>
    <label>Trạng thái <select value={view} onChange={e=>setView(e.target.value)}>
      <option value="preview">Vừa nhận diện · mọi hình</option><option value="ground">Đang mở trệt</option>
      <option value="upper">Đang mở lầu 1</option><option value="kc">Chỉ có hồ sơ kết cấu</option>
      <option value="empty">Chưa có bằng chứng công tác</option></select></label>
    <DrawingWorkList data={view==="kc"?kc:view==="empty"?{...kc,drawing_work_signals:{}}:drawing}
      index={view==="ground"?0:view==="upper"?1:-1} structural={view==="kc"?structural:null} />
  </main>;
}
