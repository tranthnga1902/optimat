"use client";
import { Sheet } from "@/components/Sheet";

const rows=[
  {code:"QA-02",name:"Gạch xây",unit:"viên",amount:1200,price:1500,source:"Báo giá thử A"},
  {code:"QA-01",name:"Gạch lát",unit:"m²",amount:24,price:180000,source:"Báo giá thử B"},
  {code:"QA-03",name:"Cát vàng",unit:"m³",amount:3,price:null,source:"Chưa có giá"}
];
export default function Page(){
  return <main className="mx-auto max-w-5xl p-4 sm:p-8">
    <h1 className="mb-4 text-2xl font-semibold">Bảng vật tư thử nghiệm</h1>
    <Sheet rows={rows} cols={[
      {key:"code",title:"Mã vật tư"},{key:"name",title:"Vật tư"},
      {key:"unit",title:"Đơn vị"},{key:"amount",title:"Số lượng",num:true}, {key:"price",title:"Đơn giá (đồng)",num:true}, {key:"source",title:"Nguồn giá"}
    ]} file="vat-tu-thu.csv"/>
  </main>;
}
