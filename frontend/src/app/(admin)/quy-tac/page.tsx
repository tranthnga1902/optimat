import type { Metadata } from "next";
import Link from "next/link";
import { Head, Card } from "@/components/ui";
import { Rules } from "./rules";
import { AiProposals } from "./ai-proposals";

export const metadata: Metadata = { title: "Quy tắc bóc tách" };

const groups = [
  ["Nhận diện và đơn vị", "Đọc đơn vị CAD trước khi quy đổi tọa độ sang mm. Layer và tên phòng lấy mẫu khớp đầu tiên trong bảng tương ứng. Với block, xét tiền tố dài trước. Bảng vật liệu sắp theo ưu tiên giảm dần rồi độ dài mẫu; khi chọn giữa các bằng chứng còn xét độ tin cậy của nguồn. Đối chiếu cả kiểu đối tượng, block và hình học; một layer có thể chứa nhiều cấu kiện.", "dxf_reader · match_layer", "drawing/dxf_reader.py, drawing/concepts.py, drawing/material_rules.py, rough/areas.py"],
  ["Phạm vi tầng và nguồn KT/KC", "Khi chưa xác nhận phạm vi, bộ tính rà các mặt bằng trùng tiêu đề. Trong nhánh mới của mã nguồn (chưa xác minh trên bản chạy), cột mặt bằng và bảng tổng cột chưa đối chiếu được giữ nguồn và đánh dấu thiếu để tránh cộng hai lần.", "compute_rough · duplicate_plans", "rough/takeoff.py"],
  ["XAY · Tường và lỗ mở", "Thể tích thô bằng tổng chiều dài × chiều cao xây × dày lõi (m³). Trừ diện tích cửa đủ ngưỡng × dày lõi, thể tích lanh tô và phần cột giao. Chiều cao cửa được giới hạn theo chiều cao xây.", "wall_works · lintel_under_beam", "rough/walls.py, rough/secondary.py"],
  ["MONG · Móng, đào và lót", "Đối chiếu số móng và kích thước từng lớp hoặc thể tích tham chiếu. Lót bằng số móng × diện tích đáy × chiều dày (m³). Khi có vị trí các hố đào, bộ tính xác định thể tích giao để trừ phần đếm lặp.", "foundation_works · pit_overlap_m3", "rough/foundations.py"],
  ["COT · Cột", "Với bảng cao độ, chiều cao đoạn cột bằng cốt trên trừ cốt dưới, không tự trừ sàn. Với cột mặt bằng, chiều cao tính theo tầng trừ chiều dày sàn khi có. Thể tích bằng số cột × tiết diện × chiều cao (m³). Nếu thiếu chiều dày sàn ở nhánh mặt bằng, bộ tính tạm dùng chiều cao tầng và cảnh báo. Nhánh cột vật lý mới phân biệt hai vị trí trục dù cùng mã cột. Thể tích thô lấy theo hai cao độ. Nếu yêu cầu trừ sàn đỉnh, phải có chiều dày và nguồn riêng cho sàn tại cột đó. Thiếu căn cứ thì lượng thuần để trống. Phép tính cho cột C2 khi đủ đầu vào chưa chứng minh bộ đọc đã nối đúng trục, tiết diện và vùng sàn trong VN002.", "schedule_column_works · column_works · instance_column_works", "rough/columns.py, rough/structural_column_instances.py"],
  ["DAM · Dầm và giằng", "Dùng chiều dài sau xử lý giao và kích thước tiết diện. Dầm sàn lấy chiều cao phần dưới sàn; giằng dùng đủ chiều cao. Giằng trên lớp lót không tính ván đáy. Thiếu tiết diện hoặc chiều dày sàn cần đối chiếu.", "beam_joints · beam_works", "rough/beams.py"],
  ["SAN / MAI · Sàn và mái", "Thể tích sàn (m³) bằng diện tích đường bao trừ diện tích ô trống, rồi nhân chiều dày. Chưa nhập ô trống thì mới biết lượng thô; chỉ dùng 0 khi đã xác nhận không có ô trống. Chỉ bỏ sàn và cốp pha sàn khi mái bê tông chỉ rõ mặt bằng thay thế (replaces_slab_of). Khoản trừ cốp pha đáy lấy diện tích dầm và đỉnh cột của mặt bằng đang xét (m²); cần đối chiếu đúng tầng và ô sàn vì bộ tính chưa tự dò giao với sàn tầng trên.", "area_works · drop_slab_under_roof · _slab_form_deduction", "rough/areas.py, rough/secondary.py, rough/takeoff.py"],
  ["CAU_THANG · Cầu thang", "Từ chiều cao, số bậc, mặt bậc và bề rộng vế, tính chiều dài nghiêng. Bê tông gồm bản nghiêng, phần bậc tam giác và chiếu nghỉ khi có kích thước. Đối chiếu riêng dầm thang.", "stair_works", "rough/stairs.py"],
  ["COT_THEP / COP_PHA · Thép và cốp pha", "Thép theo bảng thống kê: tổng số thanh × chiều dài cắt (m) × khối lượng đơn vị (kg/m). Kiểm tra phạm vi bảng trước khi cộng. Cốp pha dùng diện tích mặt tiếp xúc từng cấu kiện (m²), không suy từ khối lượng thép. Với từng cột vật lý, lượng cốp pha hiện để trống đến khi kiểm tra các mặt đỡ và giao dầm. Nhánh cột theo bảng cao độ chưa trừ diện tích đầu dầm.", "read_table · resolve_rebar_tables · beam_works", "rough/rebar.py, rough/beams.py"],
  ["Gộp khối lượng và lượng mua", "Gộp theo mã, đơn vị, nguồn, căn cứ và quy cách tương thích. Dòng thiếu quy cách được giữ riêng. Lượng sau hao hụt giữ phần đã bao gồm hao hụt và chỉ nhân tỷ lệ vào phần cần bổ sung. Tổng chỉ đủ khi phạm vi đã xác định, mọi đóng góp đều có lượng và không còn dữ kiện thiếu. Nếu công tác có trạng thái D hoặc còn thiếu, giữ phần biết được và để trống tổng chưa đủ. Chưa có lượng không mặc định là 0.", "build_quantity_summary · materials_for_works", "rough/quantity_details.py, rough/quantity_summary.py, rough/materials.py, rough/norms.py"],
];

export default function Page() {
  return <>
    <Head title="Quy tắc bóc tách">Tra cách tính phần thô và đối chiếu quy tắc với công tác của dự án đang mở.</Head>
    <Card title="Cách bộ tính xử lý công tác">
      <p className="mb-3 text-sm">Đối chiếu mã nguồn ngày 04/11/2026. Đây là mô tả thuật toán. Mỗi nhóm dẫn tới tệp và hàm. Trang chưa liên kết từng quy tắc với phiên bản mã, dòng nguồn thiết kế hoặc dòng công tác cụ thể của dự án.</p>
      <div className="grid gap-2">{groups.map(([name, detail, source, files]) =>
        <details className="rounded-lg border border-slate-200 p-3" key={name}>
          <summary className="cursor-pointer font-semibold">{name}</summary>
          <p className="my-2">{detail}</p><small className="block break-words">Nguồn trong src/optimat: {files}. Hàm đối chiếu: {source}.</small>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {source.includes("match_layer") ? <Link className="btn" href="/nhan-dien">Tra quy tắc layer và block</Link> : <>
              <span className="text-sm">Xem đầu vào và kết quả của dự án tại bước tính khối lượng.</span>
              <Link className="btn" href="/phan-tho">Mở danh sách công tác (chưa định vị dòng)</Link>
            </>}
            {source.includes("materials_for_works") && <a className="btn" href="#rule-rough_norms">Mở bảng định mức phần thô</a>}
          </div>
        </details>)}</div>
      <div className="mt-4 flex flex-wrap gap-2"><Link className="btn primary" href="/phan-tho">Kiểm tra công tác và khối lượng</Link>
        <Link className="btn" href="/nhan-dien">Tra ký hiệu nhận diện</Link></div>
    </Card>
    <AiProposals />
    <h2>Bảng quy tắc và định mức</h2><p>Thao tác ghi cập nhật bảng đã chọn. Để xác nhận ảnh hưởng, tính lại trên dự án và đối chiếu nguồn quy tắc, phiên bản cùng kết quả của công tác.</p><Rules />
  </>;
}
