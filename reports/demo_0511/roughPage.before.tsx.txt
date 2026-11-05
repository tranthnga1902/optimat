"use client";
// Trang kiểm tra gửi mọi mặt bằng lên /api/takeoff/rough và ghi kết quả gần nhất vào "optimat-rough"; ở đây chỉ hiển thị.
import Link from "next/link";
import { nf } from "@/lib/api";
import { useStored } from "@/lib/store";
import { Card, Empty, Head, Pill, Steps, Tile, Tiles } from "@/components/ui";

type Qty = { name: string; quantity?: number | null };
type Total = Qty & { code: string; unit: string; complete: boolean };
type Mat = Qty & { material_id?: string; quantity_with_waste?: number | null; unit: string; missing: string[]; complete: boolean };
type Result = { works: { code: string; plan?: string; missing: string[] }[]; totals: Total[]; formwork?: Qty[]; materials: Mat[]; warnings: string[] };
type Saved = { file?: string; at?: string; result?: Result };

export function Rough() {
  const saved = useStored<Saved | null>("optimat-rough", null), R = saved?.result;
  const plans = useStored<unknown[]>("optimat-confirmed", []);
  const why = (code: string) => [...new Set(R!.works.filter((w) => w.code === code).flatMap((w) => w.missing.map((m) => (w.plan ? w.plan + ": " : "") + m)))];
  const done = R ? R.materials.filter((m) => m.complete).length : 0;
  return (
    <>
      <Steps cur="/phan-tho" done={{ "/do-boc": plans.length > 0, "/phan-tho": !!saved }} />
      <Head title="Khối lượng phần thô" actions={<Link className="btn" href="/do-boc">Sửa trên trang kiểm tra</Link>}>
        Xây, trát, lanh tô, cột, dầm, sàn, cầu thang, cán nền, chống thấm, nền, cốt thép, cốp pha và vật liệu mua về. Phần nào thiếu thông số
        hoặc định mức thì để trống và ghi rõ thiếu gì; hệ thống không tự điền số.
      </Head>
      {!R ? (
        <Empty>Chưa tính phần thô. Vào <Link href="/do-boc">Hồ sơ và đo bóc</Link>, mở bản vẽ, chọn tab &quot;Phần thô&quot;, nhập thông số rồi bấm &quot;Tính phần thô&quot;.</Empty>
      ) : (<>
        <Tiles>
          <Tile k="Bản vẽ" v={<span className="text-lg">{saved!.file}</span>} s={`tính lúc ${(saved!.at || "").replace("T", " ").slice(0, 16)}`} />
          <Tile tone={R.totals.every((t) => t.complete) ? "ok" : "warn"} k="Công tác đủ số" v={`${R.totals.filter((t) => t.complete).length}/${R.totals.length}`} />
          <Tile tone={done === R.materials.length ? "ok" : "warn"} k="Vật liệu đủ số" v={`${done}/${R.materials.length}`} s="thiếu chủ yếu do định mức chưa tra TT 38" />
        </Tiles>
        <div className="flex flex-wrap items-start gap-[18px] [&>*]:flex-[1_1_320px]">
          <Card title="Khối lượng công tác">
            <div className="tw"><table>
              <thead><tr><th>Công tác</th><th className="n">Khối lượng</th><th>ĐVT</th><th></th></tr></thead>
              <tbody>{R.totals.map((t, i) => (
                <tr key={i}><td>{t.name}</td><td className="n">{nf(t.quantity)}</td><td>{t.unit}</td>
                  <td>{!t.complete && <span title={why(t.code).join("; ")}><Pill level="warn">còn thiếu</Pill></span>}</td></tr>
              ))}</tbody>
            </table></div>
          </Card>
          <Card title="Cốp pha theo cấu kiện">
            <div className="tw"><table><tbody>
              {R.formwork?.length ? R.formwork.map((f, i) => <tr key={i}><td>{f.name}</td><td className="n">{nf(f.quantity)}</td><td>m²</td></tr>)
                : <tr><td>Chưa có cốp pha.</td></tr>}
            </tbody></table></div>
          </Card>
        </div>
        <Card title="Vật liệu mua về">
          <div className="tw"><table>
            <thead><tr><th>Mã</th><th>Vật liệu</th><th className="n">Khối lượng</th><th className="n">Có hao hụt</th><th>ĐVT</th><th>Thiếu</th></tr></thead>
            <tbody>{R.materials.map((m, i) => (
              <tr key={i}><td>{m.material_id || "—"}</td><td>{m.name}</td><td className="n">{m.quantity == null ? <Pill level="warn">thiếu</Pill> : nf(m.quantity, 3)}</td>
                <td className="n">{nf(m.quantity_with_waste, 3)}</td><td>{m.unit}</td><td className="text-[12.5px] text-muted">{m.missing.join("; ")}</td></tr>
            ))}</tbody>
          </table></div>
        </Card>
        {R.warnings.length > 0 && <Card title="Cảnh báo"><ul className="m-0 pl-[18px] text-muted">{R.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></Card>}
      </>)}
    </>
  );
}
