"use client";
// Trang kiểm tra gửi mọi mặt bằng lên /api/takeoff/rough và ghi kết quả gần nhất vào "optimat-rough"; ở đây chỉ hiển thị.
import Link from "next/link";
import { nf } from "@/lib/api";
import { useStored } from "@/lib/store";
import { Card, Empty, Head, Pill, Steps, Tile, Tiles } from "@/components/ui";
import type { Status } from "../do-boc/model";

type Qty = { name: string; quantity?: number | null; status?: Status; complete?: boolean };
type Total = Qty & { code: string; unit: string; complete: boolean };
type Mat = Qty & { material_id?: string; quantity_with_waste?: number | null; unit: string; missing: string[]; complete: boolean;
  best_price?: number | null; est_cost?: number | null; price_source?: string | null };
type Result = { works: { code: string; plan?: string; missing: string[] }[]; totals: Total[]; formwork?: Qty[]; materials: Mat[]; warnings: string[];
  missing_inputs?: { input: string; works: string[]; plans: string[]; count: number }[] };
type Saved = { file?: string; at?: string; result?: Result };

const STATUS: Record<string, string> = { A: "A đọc", B: "B suy", C: "C tạm tính", D: "D thiếu" };
const StatusPill = ({ status }: { status?: Status }) => status ? <Pill level={status === "C" || status === "D" ? "warn" : "info"}>{STATUS[status]}</Pill> : null;

export function Rough() {
  const saved = useStored<Saved | null>("optimat-rough", null), R = saved?.result;
  const plans = useStored<unknown[]>("optimat-confirmed", []);
  const why = (code: string) => [...new Set(R!.works.filter((w) => w.code === code).flatMap((w) => w.missing.map((m) => (w.plan ? w.plan + ": " : "") + m)))];
  const done = R ? R.materials.filter((m) => m.complete).length : 0;
  return (
    <>
      <Steps cur="/phan-tho" done={{ "/do-boc": plans.length > 0, "/phan-tho": !!saved }} />
      <Head title="Khối lượng phần thô" actions={<Link className="btn" href="/dieu-chinh">Điều chỉnh phần thô</Link>}>
        Xây, trát, lanh tô, cột, dầm, sàn, cầu thang, cán nền, chống thấm, nền, cốt thép, cốp pha và vật liệu mua về. Phần nào thiếu thông số
        hoặc định mức thì để trống và ghi rõ thiếu gì; hệ thống không tự điền số.
      </Head>
      {!R ? (
        <Empty>Chưa tính phần thô. Vào <Link href="/dieu-chinh">Điều chỉnh vật liệu và phần thô</Link>, mở bản vẽ, chọn tab &quot;Phần thô&quot;, nhập thông số rồi bấm &quot;Tính phần thô&quot;.</Empty>
      ) : (<>
        <Tiles>
          <Tile k="Bản vẽ" v={<span className="text-lg">{saved!.file}</span>} s={`tính lúc ${(saved!.at || "").replace("T", " ").slice(0, 16)}`} />
          <Tile tone={R.totals.every((t) => t.complete) ? "ok" : "warn"} k="Công tác đủ số" v={`${R.totals.filter((t) => t.complete).length}/${R.totals.length}`} />
          <Tile tone={done === R.materials.length ? "ok" : "warn"} k="Vật liệu đủ số" v={`${done}/${R.materials.length}`} s="Xem thông số và định mức còn thiếu trong từng dòng" />
        </Tiles>
        <div className="flex flex-wrap items-start gap-[18px] [&>*]:flex-[1_1_320px]">
          <Card title="Khối lượng công tác">
            <div className="tw"><table>
              <thead><tr><th>Công tác</th><th className="n">Khối lượng</th><th>ĐVT</th><th>Trạng thái</th><th></th></tr></thead>
              <tbody>{R.totals.map((t, i) => (
                <tr key={i}><td>{t.name}</td><td className="n">{nf(t.quantity)}</td><td>{t.unit}</td><td><StatusPill status={t.status} /></td>
                  <td>{!t.complete && <span title={why(t.code).join("; ")}><Pill level="warn">{t.quantity == null ? "còn thiếu" : "một phần"}</Pill></span>}</td></tr>
              ))}</tbody>
            </table></div>
          </Card>
          <Card title="Cốp pha theo cấu kiện">
            <div className="tw"><table><tbody>
              {R.formwork?.length ? R.formwork.map((f, i) => <tr key={i}><td>{f.name}</td><td className="n">{nf(f.quantity)}</td><td>m²</td>
                <td><StatusPill status={f.status} />{f.complete === false && <Pill level="warn">{f.quantity == null ? "còn thiếu" : "một phần"}</Pill>}</td></tr>)
                : <tr><td>Chưa có cốp pha.</td></tr>}
            </tbody></table></div>
          </Card>
        </div>
        <Card title="Vật liệu mua về">
          <div className="tw"><table>
            <thead><tr><th>Mã</th><th>Vật liệu</th><th className="n">Khối lượng</th><th className="n">Có hao hụt</th><th>ĐVT</th><th className="n">Đơn giá</th><th className="n">Thành tiền</th><th>Nguồn giá</th><th>Trạng thái</th><th>Thiếu</th></tr></thead>
            <tbody>{R.materials.map((m, i) => (
              <tr key={i}><td>{m.material_id || "—"}</td><td>{m.name}</td><td className="n">{m.quantity == null ? <Pill level="warn">thiếu</Pill> : <>{nf(m.quantity, 3)}{!m.complete && <> <Pill level="warn">một phần</Pill></>}</>}</td>
                <td className="n">{nf(m.quantity_with_waste, 3)}</td><td>{m.unit}</td>
                <td className="n">{m.best_price == null ? <Pill level="warn">chưa có giá</Pill> : nf(m.best_price)}</td>
                <td className="n">{nf(m.est_cost)}</td><td className="text-[12.5px] text-muted">{m.price_source || ""}</td>
                <td><StatusPill status={m.status} /></td><td className="text-[12.5px] text-muted">{m.missing.join("; ")}</td></tr>
            ))}</tbody>
          </table></div>
          <p className="mb-0 text-[12.5px] text-muted">Đơn giá và thành tiền lấy từ kết quả máy chủ, chưa gồm vận chuyển và nhân công. Nguồn giá giữ nguyên loại, đơn vị cung cấp và ngày khi có; giá công bố (BULLETIN) không phải báo giá mua đã xác nhận. Dòng ghi một phần chưa đủ khối lượng để kết luận tổng.</p>
        </Card>
        {(R.missing_inputs?.length ?? 0) > 0 && <Card title="Thông số còn thiếu">
          <p className="mt-0 text-[12.5px] text-muted">Hệ thống không tự điền số mặc định. Nhập các thông số dưới đây (theo bản vẽ, thuyết minh hoặc dự toán) để tính tiếp; thông số ảnh hưởng nhiều dòng nhất ở trên cùng.</p>
          <div className="tw"><table>
            <thead><tr><th>Thông số</th><th className="n">Số dòng trống</th><th>Công tác</th><th>Mặt bằng</th></tr></thead>
            <tbody>{R.missing_inputs!.map((m, i) => (
              <tr key={i}><td>{m.input}</td><td className="n">{m.count}</td><td>{m.works.join(", ")}</td><td className="text-[12.5px] text-muted">{m.plans.join("; ")}</td></tr>
            ))}</tbody>
          </table></div>
        </Card>}
        {R.warnings.length > 0 && <Card title="Cảnh báo"><ul className="m-0 pl-[18px] text-muted">{R.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></Card>}
      </>)}
    </>
  );
}
