"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { money, nf, post, ROLE } from "@/lib/api";
import { mergedGroups, store, useStored, type ConfirmedPlan, type WallGroup } from "@/lib/store";
import { Card, Empty, Head, Loading, Note, Pill, Steps } from "@/components/ui";

type Plan = ConfirmedPlan & { file?: string; plan?: string; height_mm?: number; total_net_area_m2?: number; confirmed_at?: string; takeoff_id?: number };
type Offer = { price?: number | null; url?: string; supplier_name?: string; supplier_id?: string; price_level?: string; data_kind?: string };
type BillRow = {
  wall_type: string; role: string; wall_system_id?: string; kind?: string; material_id?: string; material_name?: string;
  quantity?: number | null; unit?: string; offers: Offer[]; est_cost?: number | null; missing: string[];
};

export function Bill() {
  const plans = useStored<Plan[]>("optimat-confirmed", []);
  const rough = useStored("optimat-rough", null);
  const groups = useMemo(() => mergedGroups(plans), [plans]);
  // kết quả gắn với đúng bộ groups đã gửi, để biết khi nào đang tra giá lại
  const [res, setRes] = useState<{ for: WallGroup[]; bill?: BillRow[]; err?: string }>();
  useEffect(() => {
    if (!groups.length) return;
    post<BillRow[]>("/api/price/bill", { groups }).then((bill) => setRes({ for: groups, bill }), (e) => setRes({ for: groups, err: e.message }));
  }, [groups]);

  const save = (l: Plan[]) => store.set("optimat-confirmed", l);
  return (
    <>
      <Steps cur="/vat-lieu" done={{ "/do-boc": plans.length > 0, "/phan-tho": !!rough }} />
      <Head title="Vật liệu và giá theo thiết kế" actions={<>
        <button className="btn" type="button" disabled={!plans.length} onClick={() => save([])}>Xóa kết quả đã lưu</button>
        <Link className="btn primary" href="/toi-uu">Tiếp: tối ưu</Link>
      </>}>
        Gộp {plans.length} mặt bằng đã xác nhận. Mã vật liệu là mã danh mục, giá lấy nguyên từ cơ sở dữ liệu; dòng thiếu số liệu để trống và ghi rõ thiếu gì.
      </Head>
      {!groups.length ? (
        <Empty>Chưa có mặt bằng nào được xác nhận. Vào <Link href="/do-boc">Hồ sơ và đo bóc</Link>, mở bản vẽ, kiểm tra rồi bấm &quot;Xác nhận bản vẽ&quot;.</Empty>
      ) : (<>
        <Card title="Mặt bằng đã xác nhận">
          <div className="tw"><table>
            <thead><tr><th>Bản vẽ</th><th>Mặt bằng</th><th className="n">Cao tầng m</th><th className="n">Tường thực m²</th><th>Xác nhận lúc</th><th></th></tr></thead>
            <tbody>{plans.map((p, i) => (
              <tr key={i}>
                <td>{p.file}</td><td>{p.plan}</td><td className="n">{nf((p.height_mm ?? NaN) / 1000)}</td><td className="n">{nf(p.total_net_area_m2)}</td>
                <td className="text-[12.5px] text-muted">{(p.confirmed_at || "").replace("T", " ").slice(0, 16)}{p.takeoff_id ? " · lưu DB #" + p.takeoff_id : ""}</td>
                <td><button className="btn" type="button" aria-label={`Bỏ mặt bằng ${p.plan}`} onClick={() => save(plans.filter((_, j) => j !== i))}>Bỏ</button></td>
              </tr>
            ))}</tbody>
          </table></div>
        </Card>
        <Card title="Khối lượng tường gộp các tầng">
          <div className="tw"><table>
            <thead><tr><th>Loại</th><th>Vai trò</th><th>Phương án theo thiết kế</th><th className="n">Dài m</th><th className="n">Lỗ mở m²</th><th className="n">Thực m²</th></tr></thead>
            <tbody>{groups.map((g, i) => (
              <tr key={i}>
                <td>{g.wall_type}</td><td>{ROLE[g.role] || g.role}</td>
                <td>{g.design_wall_system_id || (g.design_material_id ? <>{g.design_material_id} <Pill level="warn">chưa có phương án</Pill></> : <Pill level="warn">chưa chọn vật liệu</Pill>)}</td>
                <td className="n">{nf(g.length_m)}</td><td className="n">{nf(g.opening_area_m2)}</td><td className="n"><b>{nf(g.net_area_m2)}</b></td>
              </tr>
            ))}</tbody>
          </table></div>
        </Card>
        <Card title="Vật liệu cần mua và giá">
          {res?.for !== groups ? <Loading>Đang tra giá…</Loading> : res.err ? <Note>{res.err}</Note> : <BillTable bill={res.bill || []} />}
        </Card>
      </>)}
    </>
  );
}

function BillTable({ bill }: { bill: BillRow[] }) {
  const costs = bill.map((b) => b.est_cost), total = costs.length && costs.every((c) => c != null) ? (costs as number[]).reduce((a, b) => a + b, 0) : null;
  const miss = bill.filter((b) => b.missing.length);
  return (
    <>
      <div className="tw"><table>
        <thead><tr><th>Nhóm tường</th><th>Vật liệu</th><th className="n">Khối lượng</th><th className="n">Giá thấp nhất</th><th>Nguồn giá</th><th className="n">Thành tiền</th></tr></thead>
        <tbody>{bill.map((b, i) => {
          const o = b.offers.find((x) => x.price != null);
          return (
            <tr key={i}>
              <td>{b.wall_type} {ROLE[b.role] || ""}<div className="text-[12.5px] text-muted">{b.wall_system_id}</div></td>
              <td>{b.kind === "mortar" ? "Vữa " : ""}{b.material_id ? <>{b.material_id}<div className="text-[12.5px] text-muted">{b.material_name}</div></> : <Pill level="warn">chưa chọn</Pill>}</td>
              <td className="n">{b.quantity == null ? <Pill level="warn">thiếu</Pill> : `${nf(b.quantity)} ${b.unit || ""}`}</td>
              <td className="n">{o ? money(o.price) : <Pill level="warn">chưa có giá</Pill>}</td>
              <td>{o && <>
                {o.url ? <a href={o.url} target="_blank" rel="noopener">{o.supplier_name || o.supplier_id}</a> : o.supplier_name || o.price_level}
                {o.data_kind && o.data_kind !== "ACTUAL" && <> <Pill level="info">{o.data_kind}</Pill></>}
              </>}</td>
              <td className="n">{money(b.est_cost)}</td>
            </tr>
          );
        })}</tbody>
        <tfoot><tr><td colSpan={5}>Tổng tiền vật liệu (chưa gồm vận chuyển, nhân công)</td><td className="n">{total == null ? "chưa đủ giá" : money(total)}</td></tr></tfoot>
      </table></div>
      {miss.length > 0 && <ul className="m-0 pl-[18px] text-muted">{miss.map((b, i) => (
        <li key={i}>Tường {b.wall_type} {ROLE[b.role] || ""}, {b.kind === "mortar" ? "vữa" : "vật liệu"} {b.material_id || ""}: thiếu {b.missing.join(", ")}</li>
      ))}</ul>}
    </>
  );
}
