"use client";
import {useState,useLayoutEffect} from "react";
import {Board,type Mode} from "../(user)/do-boc/Board";
import {initState,type Data,type Plan} from "../(user)/do-boc/model";
import {useViewport} from "../(user)/do-boc/viewport";
import s from "../(user)/do-boc/review.module.css";

const plan:Plan={plan:{name:"Mặt bằng thử"},height_mm:3000,size:[6000,4000],layers:[{name:"Wall",role:"WALL"}],wall_layers:["Wall"],
  segs:[[0,0,6000,0,0,0],[6000,0,6000,4000,0,0],[6000,4000,0,4000,0,0],[0,4000,0,0,0,0],[3000,0,3000,4000,0,0]],
  walls:[{id:"W1",cls:"110",role:"partition",x1:3000,y1:0,x2:3000,y2:4000,masonry:true,conf:1}],openings:[]};
const data:Data={file:"Mặt bằng thử",plans:[plan],families:[],materials:[]};
const state=initState(plan);
export default function ToolbarQA(){
  const vp=useViewport(),[mode,setMode]=useState<Mode>("select"),[rec,setRec]=useState(true),[labels,setLabels]=useState(true);
  const [cls,setCls]=useState("110"),[kind,setKind]=useState("door"),[w,setW]=useState("900"),[h,setH]=useState("2100");
  useLayoutEffect(()=>{vp.fitSize(plan.size);},[vp.fitSize]);
  return <section className={s.app} style={{height:"85dvh"}}><header className={s.head}>Bóc tách bản vẽ · Mặt bằng thử</header>
    <Board {...vp} data={data} pi={0} P={plan} S={state} selected={null} mode={mode} onMode={setMode} hint="Bản vẽ tổng hợp để kiểm tra thanh công cụ" draft={null} snap={p=>p} unit={60}
      bg="lines" hasCad={false} onBg={()=>{}} showRec={rec} onShowRec={setRec} showLabels={labels} onShowLabels={setLabels}
      newCls={cls} onNewCls={setCls} newKind={kind} onNewKind={setKind} newW={w} onNewW={setW} newH={h} onNewH={setH}
      cols={[]} onToggleCol={()=>{}} onSvgClick={()=>{}} onSelect={()=>{}} onOpenPlan={()=>{}}/></section>;
}

