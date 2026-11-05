"use client";
import Link from "next/link";
import { Sheet } from "@/components/Sheet";
import { useEffect, useState } from "react";
import { money, nf, post, ROLE } from "@/lib/api";
import { useStored, type ConfirmedPlan } from "@/lib/store";
import { currentPurchaseKey, usePurchaseSession } from "@/lib/purchase-session";
import { Card, Empty, Head, Loading, Note, Pill, Steps } from "@/components/ui";

type Plan = ConfirmedPlan & { file?: string; plan?: string; height_mm?: number; total_net_area_m2?: number; confirmed_at?: string; takeoff_id?: number };
type Offer = { price?: number | null; unit?: string; url?: string; supplier_name?: string; supplier_id?: string; price_level?: string; price_date?: string | null; valid_until?: string | null; source_detail?: string; is_reference?: boolean; rejection_reasons?: string[]; vat_included?: string | null; transport_included?: string | null };
type BillRow = {
  wall_type: string; role: string; wall_system_id?: string; kind?: string; material_id?: string; material_name?: string;
  quantity?: number | null; unit?: string; offers: Offer[]; best_offer?: Offer | null; price_note?: string; est_cost?: number | null; missing: string[];
};

export function Bill() {
  const plans = useStored<Plan[]>("optimat-confirmed", []);
  const { work: rough, key, ready: materialsReady } = usePurchaseSession();
  const groups = rough?.result.wall_groups;
  const issues = rough?.result?.wall_group_issues;
  const [res, setRes] = useState<{ for: string; bill?: BillRow[]; err?: string }>();
  useEffect(() => {
    if (!key || !groups?.length || issues?.length || currentPurchaseKey() !== key) return;
    let live = true;
    post<BillRow[]>("/api/price/bill", { groups, actual_only: true }).then(
      bill => live && currentPurchaseKey() === key && setRes({ for: key, bill }),
      e => live && currentPurchaseKey() === key && setRes({ for: key, err: e.message }));
    return () => { live = false; };
  }, [groups, issues, key]);

  if (!materialsReady) return <><Steps cur="/vat-lieu" done={{}} /><Head title="Vật liệu và giá" /><Empty>Hãy <Link href="/dieu-chinh">lưu lựa chọn vật liệu</Link> trước khi tra giá.</Empty></>;
  return (
    <>
      <Steps cur="/vat-lieu" done={{ "/do-boc": plans.length > 0, "/phan-tho": !!rough }} />
      <Head title="Vật liệu và giá theo thiết kế" actions={<>
        <Link className="btn primary" href="/toi-uu">Tiếp: tối ưu</Link>
      </>}>
        Lượng gạch và vữa lấy từ khối xây cuối cùng trong bảng phần thô của các mặt bằng được chọn tính. Đơn giá kèm ngày và nguồn.
      </Head>
      {groups && groups.length === 0 && !issues?.length ? <Empty>Phạm vi đã tính không phát sinh khối xây tường cần mua.</Empty> : !groups?.length || !!issues?.length ? (
        <Empty>Cần <Link href="/phan-tho">kiểm tra và tính lại phần thô</Link> để có đủ khối xây cho bảng vật tư. {issues?.join(" · ")}</Empty>
      ) : (
        <Card title="Gạch và vữa theo cấu tạo tường">
          {!res || res.for !== key ? <Loading>Đang tra giá…</Loading> : res.err ? <Note>{res.err}</Note> : <BillTable bill={res.bill || []} />}
        </Card>)}
        {rough?.result?.plan_scope_confirmed && <Card title="Vật tư mua cho phần thô (đã gồm vật tư xây tường)">
          <Sheet rows={rough.result.materials} file="vat-tu-mua-phan-tho.csv" cols={[
            {key:"name",title:"Vật tư"},
            {key:"quantity_with_waste",title:"Khối lượng có hao hụt",num:true,render:m=>nf(m.quantity_with_waste,3)},
            {key:"unit",title:"Đơn vị"},
            {key:"best_price",title:"Đơn giá",num:true,render:m=>money(m.best_price)},
            {key:"est_cost",title:"Thành tiền",num:true,render:m=>money(m.est_cost)},
            {key:"price_source",title:"Nguồn giá",text:m=>m.price_source || "Chưa có giá"}
          ]}/>
        </Card>}
    </>
  );
}

function terms(o: Offer) {
  const included = (v: string | null | undefined, item: string) => v === "YES" ? `đã gồm ${item}` : v === "NO" ? `chưa gồm ${item}` : `chưa rõ ${item}`;
  return [included(o.vat_included, "VAT"), included(o.transport_included, "cước giao hàng")].join(" · ");
}

function knownTerms(o: Offer) {
  return [o.vat_included, o.transport_included].every(v => v === "YES" || v === "NO");
}

function quoteDates(o: Offer) {
  const dated = o.price_date ? `Ngày giá ${o.price_date}` : "Chưa có ngày giá";
  return `${dated} · ${o.valid_until ? `hạn theo nguồn ${o.valid_until}` : "chưa rõ hiệu lực"}`;
}

function BillTable({ bill }: { bill: BillRow[] }) {
  const subtotals = new Map<string, { amount: number; rows: number }>();
  for (const b of bill) {
    const o = b.best_offer;
    if (!o || !knownTerms(o) || b.est_cost == null || b.missing.length) continue;
    const basis = [o.is_reference ? "Tham khảo theo công bố" : "Vật liệu theo báo giá", terms(o)].join(" · ");
    const subtotal = subtotals.get(basis) || { amount: 0, rows: 0 };
    subtotals.set(basis, { amount: subtotal.amount + b.est_cost, rows: subtotal.rows + 1 });
  }
  const miss = bill.filter((b) => b.missing.length);
  return (
    <>
      <div className="tw"><table>
        <thead><tr><th>Nhóm tường</th><th>Vật liệu</th><th className="n">Khối lượng</th><th className="n">Đơn giá áp dụng</th><th>Nguồn và ngày giá</th><th className="n">Thành tiền</th></tr></thead>
        <tbody>{bill.map((b, i) => {
          const selected = b.best_offer;
          const o = selected && (selected.is_reference || knownTerms(selected)) ? selected : null;
          const rejected = b.offers.filter(x => x.rejection_reasons?.length);
          return (
            <tr key={i}>
              <td>{b.wall_type} {ROLE[b.role] || ""}<div className="text-[12.5px] text-muted">{b.wall_system_id}</div></td>
              <td>{b.kind === "mortar" ? "Vữa " : ""}{b.material_id ? <>{b.material_id}<div className="text-[12.5px] text-muted">{b.material_name}</div></> : <Pill level="warn">chưa chọn</Pill>}</td>
              <td className="n">{b.quantity == null ? <Pill level="warn">thiếu</Pill> : `${nf(b.quantity)} ${b.unit || ""}`}</td>
              <td className="n">{o ? money(o.price) : <Pill level="warn">chưa có giá</Pill>}</td>
              <td>{o && <>
                {o.supplier_name || o.supplier_id}
                {o.source_detail && o.source_detail !== o.url && <div>{o.source_detail}</div>}
                {o.url && <div><a href={o.url} target="_blank" rel="noopener">Liên kết từ nguồn</a></div>}
                <div>{o.is_reference ? "Công bố tham khảo" : "Báo giá mua"} · đ/{o.unit}</div>
                <div>{quoteDates(o)}</div>
                <div>{terms(o)}</div>
              </>}{b.price_note && <small>{b.price_note}</small>}
                {!!rejected.length && <details><summary>Xem giá chưa dùng ({rejected.length})</summary><ul>
                  {rejected.map((x, j) => <li key={j}>{x.supplier_name || x.supplier_id || x.price_level} · {x.price == null ? "chưa có giá" : `${money(x.price)} đ/${x.unit || "đơn vị chưa rõ"}`} · {quoteDates(x)} · {terms(x)}
                    {x.url && <> · <a href={x.url} target="_blank" rel="noopener">Liên kết</a></>}{x.source_detail && <> · {x.source_detail}</>} · {x.rejection_reasons?.join(". ")}</li>)}
                </ul></details>}</td>
              <td className="n">{o ? money(b.est_cost) : "—"}</td>
            </tr>
          );
        })}</tbody>
        <tfoot>{Array.from(subtotals, ([basis, t]) => <tr key={basis}><td colSpan={5}>{t.rows === bill.length ? "Tổng" : `Tạm tính ${t.rows}/${bill.length} dòng`} · {basis} · chưa gồm nhân công</td><td className="n">{money(t.amount)}</td></tr>)}
          {!subtotals.size && <tr><td colSpan={5}>Tổng tiền vật liệu</td><td className="n">Chưa đủ giá cùng điều kiện</td></tr>}</tfoot>
      </table></div>
      {miss.length > 0 && <ul className="m-0 pl-[18px] text-muted">{miss.map((b, i) => (
        <li key={i}>Tường {b.wall_type} {ROLE[b.role] || ""}, {b.kind === "mortar" ? "vữa" : "vật liệu"} {b.material_id || ""}: thiếu {b.missing.join(", ")}</li>
      ))}</ul>}
    </>
  );
}
