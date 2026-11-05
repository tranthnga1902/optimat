# DATA20 · 05 — D05/D06

Ngày 04/11/2026. Chỉ kiểm kê tĩnh CSV, tài liệu và dự toán build; không chạy test/CAD, không kết nối hoặc nạp DB, không sửa source/dữ liệu canonical. Không train hoặc gọi AI trả phí.

## Phạm vi và phiên bản

Đã đọc CSDL_20_BANG.md và KE_HOACH_HOAN_THIEN_DU_LIEU_20_BANG.md. work_norms là bảng vật lý, rough_norms là view tương thích. Không suy việc có schema/SQL thành DB chính đã chuyển. Hai Word là bản trình bày đi kèm; lượt này dùng đặc tả Markdown, chưa kiểm nội dung/render hai Word.

GAP_DINH_MUC.csv bản đầu có 264 dòng báo cáo (không phải số định mức mới). Giữ nguyên hệ số, khoảng, đơn vị và nguồn CSV. Trống có nghĩa chưa xác minh/chưa có dữ liệu, không phải 0. Các trạng thái kiểm là mô tả bằng chứng, không tự cấp A/B/C/D hay dấu chuyên môn duyệt.

```json
{
  "data/catalog/materials.csv": {
    "rows": 98,
    "sha256": "9b644f3d83f4f525a3ddd9d62de7bda8761367ae4998bc7b809821e6a12a2bf6"
  },
  "data/catalog/wall_systems.csv": {
    "rows": 22,
    "sha256": "7b135b8ae2ee64db8530d098b6aea799fa537db4f0bb8dc79ebc1029aace2408"
  },
  "data/catalog/material_relations.csv": {
    "rows": 15,
    "sha256": "5b8233eae16c7e3edbe4b00147729241d6be83bdb10c5a842cd9fca9767793ef"
  },
  "data/rules/dinh_muc_phan_tho.csv": {
    "rows": 68,
    "sha256": "0e677eaa3cffeb4affd1fa3baaafb35c288f63e05ec39481e73c437cb092d542"
  }
}
```

## Năm ứng viên tường cần hoàn thiện trước

| Phương án | Căn cứ CSV hiện có | Khoảng thiếu trước phát hành |
|---|---|---|
| W-GN01-110 | AE.221, 643 viên + 0,23 m³ vữa/m³ xây | Trang nguồn, mác VU02, chiều cao/khối xây hồ sơ và kiểm hao hụt |
| W-GN01-220 | AE.222, 550 viên + 0,29 m³ vữa/m³ xây | Như trên; phải xác nhận dày khối xây khác lớp hoàn thiện |
| W-GO01-100 | AE.631, 682 viên + 0,17 m³ vữa/m³ xây; khối xây 80 mm | Kiểm nguồn và cấu tạo 100 mm gồm trát; không tự chọn thay thiết kế |
| W-GO01-200 | AE.632, 649 viên + 0,21 m³ vữa/m³ xây | 170 mm là giả định C (2 hàng 80 + mạch 10), cần D02/hồ sơ chốt |
| W-GK01-110 | AE.8226, 546 viên + 0,267 m³ vữa/m³ xây | Chuẩn hóa mã đầy đủ AE.82260, xóa mâu thuẫn ghi chú cũ sau duyệt; định mức trát gạch không nung riêng |

Đây là ứng viên có chuỗi gạch–vữa–cấp phối để kiểm tiếp, **chưa tuyên bố năm phương án đã đủ căn cứ nghiệm thu hoặc đủ mua/giá**. VU02 hiện có 307 kg XM01 + 1,13 m³ CA02/m³ vữa; cần mác và nguồn sản phẩm đúng dự án. GN02 giữ chờ chốt phạm vi gạch hai lỗ. AAC có AE.862/864/866 nhưng VU04 tính tấn và thiếu density đúng sản phẩm để đổi từ m³; lưới còn trống, trát AAC không dùng AK.212.

## Đối chiếu DB 31 và CSV 68

- CSV hiện tại đếm độc lập: 68 dòng. Kiểm kê DB trước chuyển: 31 dòng, **chỉ kế thừa số kiểm kê**, không truy DB hoặc mở backup private. Không có export từng dòng DB được cung cấp trong phạm vi này, nên chưa thể xác nhận 31 dòng thực tế trùng những khóa/cột nào.
- J05C_TRAT_THIET_KE.md mục 9 ghi diff SQL lịch sử: bỏ TRAT/15, TRAT/20 và COP_PHA variant trống CP01 (3); thêm 4 khóa TRAT theo họ nền, 35 dòng GO theo cấu kiện và 1 dòng VAN_EP (40). 31−3+40=68; 28 dòng không đổi chỉ là suy ra từ diff đó, không phải đối chiếu DB độc lập.
- CSV hiện tại có đúng 4 TRAT, 35 COP_PHA/GO_* và 1 COP_PHA/VAN_EP. M150/M350/M400 đã có trong baseline SQL lịch sử, không gọi là phần tăng thêm J05c.
- CSV dùng material_name để phân biệt nhiều thành phần CP03 cùng work/variant/material_id. Không so chỉ ba trường rồi làm mất gỗ ván/đà nẹp/chống. Cần so toàn bộ cột, kiểu dữ liệu, NULL/trống, min/max, ngày/nguồn sau khi chủ DB cấp export sạch.
- Chưa reload rough_norms/work_norms, chưa sửa SQL hoặc áp hệ số mới. Đổi schema 20 không tự lấp chênh lệch dữ liệu.

## Ưu tiên công tác build và nguồn

Đọc metadata cases.csv và duy nhất dự toán build 46_nha_tan_binh.csv, không đọc CAD hay đáp án split test. Dự toán này mang nhãn ACTUAL nhưng quyền dùng/phien_ban chưa rõ, dap_an_trang_thai=chua_kiem. Các nhóm công tác được ghi D06_PHU_BUILD trong CSV; đây là phủ danh mục dự toán, không phải phủ nhận diện hình học. Không lấy số dự toán cũ làm hệ số 2026.

1. Chốt D02/phạm vi từng dòng, vật liệu/mác, chiều dày và cấu kiện; tách đào/đắp/cọc/chưa ánh xạ khỏi công tác có lượng mua vật liệu.
2. Kiểm năm phương án tường và cấp phối VU02; kiểm đúng TRAT theo nền/mác.
3. Kiểm cấp phối bê tông theo xi măng/Dmax/độ sụt và căn cứ 1,025 theo từng công tác; M350/M400 còn thiếu dòng phụ gia và nước, không dùng liều giữa khoảng hoặc đổi kg sang lít khi thiếu density.
4. AF.81 cần trang nguồn và phạm vi hao phí luân chuyển; AF.83 đã có phiếu nguồn J04 nhưng VAN_EP CSV còn ghi chú cũ. Chưa thêm J05b hoặc dùng hệ khung/chống khác thay thế.
5. Cán 50 mm giữ trống; chống thấm và dây buộc thép cần cấu tạo/đường kính/sản phẩm thực, không biến khoảng/giả định thành thiết kế.

Nguồn kế thừa: docs/research/J04_PHIEU_TRA_NGUON.md, J05C_TRAT_THIET_KE.md, J05B_VAN_EP_THIET_KE.md, J05D_PHU_GIA_THIET_KE.md và docs/review/J05BCD_CODEX_REVIEW_V2.md. Trang PDF chỉ điền nơi tài liệu nghiên cứu đã ghi rõ: PL II 589 (trát), 599 (cán); PL VII 4/15 (hướng dẫn và cấp phối M350/400). Các trang khác giữ trống; không mở lại PDF/web trong lượt này và không tuyên bố nguồn pháp lý đã được tái xác minh hiện hành.

## Hao hụt và kiểm bàn giao

Code hiện coi mã AE là đã gồm hao hụt cho xây, và bool(norm_code) cho dòng định mức phần thô. Đây là hành vi mã, không đủ chứng minh mọi định mức có cùng phạm vi hao hụt. Cột hao_hut_da_gom để trống nếu chưa có căn cứ riêng; không cộng lại phần đã bao gồm. unit_factor AAC là đổi viên sang m³, không phải hao hụt. Các quan hệ REQUIRES vữa AAC trùng ý nghĩa suất vữa wall_systems, không cộng hai lần.

Đã kiểm cấu trúc CSV và đếm dòng bằng thư viện chuẩn, không chạy pytest/check_data có ghi báo cáo. Không sửa nguồn/CSV canonical; chưa phát hành/import hay nghiệm thu hồ sơ. Bước tiếp theo cần điều phối 01 cấp quyền cụ thể cùng export DB sạch, D02 và người kiểm nguồn độc lập.


## Delta theo BOARD01 — Pioneer VN002 BUILD

Bản cập nhật có **286 dòng**, thêm 22 dòng `D06_VN002_PIONEER` truy work_id và trang/bảng/hàng tiên lượng. Giữ 14 nhóm Tân Bình ở bản đầu làm đối chiếu lịch sử, không dùng chúng thay danh mục VN002. VN002 là `nha_sang_hai_duong_4x15`, BUILD, chưa chốt sẵn sàng; 07 ghi 249 source works, 5 nhãn DEV và 244 cách ly, human_approval=false. Chưa đủ nguyên hồ sơ/GT và quyền dùng.

### Receipt DB được phép đọc

`reports/schema20_migration_trial.json`: `legacy_rows.rough_norms=31`, `physical_rows.work_norms=31`, `tables=20`, `changed=true`; receipt ghi đã đối chiếu đầy đủ từng cột/dòng qua view tương thích trên **bản sao thử**. Vì vậy có bằng chứng artifact cho việc chuyển 31→31, không chỉ lời bàn giao. Không suy đây là main DB đã chuyển hoặc CSV68 đã được nạp. Receipt không xuất nội dung 31 dòng, nên đối chiếu 31 DB với 68 CSV từng khóa/cột vẫn chưa hoàn thành. Không truy DB, không mở backup/private hoặc thông tin kết nối.

### Thứ tự VN002 và delta canonical xin 01 cấp phạm vi

| ID đề nghị | Dòng nguồn VN002 / trang PDF tiên lượng | Canonical dự kiến, chưa sửa | Căn cứ cần bổ sung / điều kiện mở |
|---|---|---|---|
| C05-01 | W009 p7; W026 p13; W028 p14, gạch đặc 60×105×220, M75 | data/catalog/wall_systems.csv: W-GN01-110/220; materials.csv: GN01 | GN01 đúng cao60 nhưng ghi chú AE.22 viện viên65. Tra bảng đúng quy cách/trang và kiểm độc lập trước đổi 643/550 hoặc suất vữa. Không tự coi sai lệch chiều cao là tương đương |
| C05-02 | W027 p14: tường55 gạch đặc | wall_systems.csv: chưa có ID được duyệt | Cần cấu tạo, chiều xây viên/mạch và định mức đúng dày55. Không tạo ID/hệ số mới hoặc chia đôi phương án110 |
| C05-03 | W030 p16: trát15 M75 gộp tường/cột/dầm/sàn/thang | dinh_muc_phan_tho.csv TRAT; material_relations.csv VU02 | J04 PL II PDF589 chỉ hỗ trợ phần tường theo nền. D02 tách nền/phạm vi và công thức; tìm định mức riêng cho cột/dầm/trần/thang trước mở rộng |
| C05-04 | W006 p4: M100 đá4×6; W013/W015/W017/W019/W021 p9–12: M250 đá1×2 | dinh_muc_phan_tho.csv BE_TONG_TRON/M100,M250 | Không dùng cấp phối Dmax20 cho đá4×6; cần nguồn PL VII đúng đá/xi măng/độ sụt, cấp phối thiết kế, nước và phạm vi1,025. M250 có nguồn mã11.12323 trong CSV nhưng chưa chứng minh đủ điều kiện VN002 |
| C05-05 | W008 p6: móng/giằng/bể gộp đang map DAM; W002 p3: mét cọc map COT_THEP | normalized_20261103/...estimate.json / mapping ingestion (owner07/S20) | Chỉnh ánh xạ chỉ sau review nguồn; tách phạm vi và đơn vị, không đổi công tác ép cọc thành thép; 05 không own sửa GT/mapping |
| C05-06 | W007/12/14/16/18/20: thép theo cấu kiện | dinh_muc_phan_tho.csv COT_THEP/TH10, snapshot đo bóc của07 | Cần bảng thống kê/đường kính đã kiểm; dây buộc không thay thép chịu lực; không lấy giữa khoảng7,85–16,07 làm thiết kế |
| C05-07 | W033 p19: Sika Proof Membrane3lớp; W010 p8: trát/láng/thử tải bể | dinh_muc_phan_tho.csv CHONG_THAM; materials.csv mã sản phẩm chưa chốt | TDS chính hãng đúng sản phẩm/phiên bản, suất dùng từng lớp/nền và hao hụt; không mượn CT01/02/03 khác hệ; tách W010 trước định mức |
| C05-08 | W037 p20: láng30mm M75 | dinh_muc_phan_tho.csv CAN_NEN/30; material_relations.csv VU02 | J04 PL II PDF599 AK.41120 có0,035; CSV ghi mã nhómAK.41100. Có thể chuẩn hóa mã đầy đủ sau cấp quyền/review; chưa thay quantity |
| C05-09 | Không có dòng cốp pha độc lập trong 249 tên tiên lượng đã rà từ JSON | dinh_muc_phan_tho.csv COP_PHA/GO_* và VAN_EP | Không kết luận hồ sơ không cần cốp pha. D02 xác định diện tích mặt khuôn/hệ khung, cấu kiện, luân chuyển; AF.81/83 giữ pending theo hệ thực |

**3–5 tường:** giữ năm ID ứng viên của bản đầu để thu nguồn, không tuyên bố năm phương án đủ nguồn. VN002 ưu tiên GN01-110/220 nhưng đang bị chặn bởi cao viên60/65; phương án55 chưa có. GO01-100/200 và GK01-110 chỉ là phương án so sánh cần người dùng chọn, không phải vật liệu VN002 được chỉ định. Hiện **chưa chứng minh đủ 3 phương án tường đạt G3**, phải báo thiếu thay vì áp phương án khác để đủ chỉ tiêu.

M350/M400/phụ gia tiếp tục là gap chung J05d, chưa có căn cứ ưu tiên hơn M100/M250 trong Pioneer này. Các URL chính thức đã ghi trong phiếu J04/J05 là nguồn cần mở/kiểm ở lượt được cấp; delta này không bổ sung hệ số hoặc tuyên bố đã tái kiểm pháp lý.

Đề nghị 01 cấp bước nhỏ đầu tiên C05-01/C05-03/C05-08 (review nguồn và phạm vi trước; chưa import DB). Các thay đổi source, SQL, GT/mapping và canonical khác vẫn chờ phân quyền owner. Không chạy suite do S20 sole-runner.

Hash bằng chứng delta: receipt `c334aa3c1a2cbb90ce36545f7907cce01bc3d15cf5914fe238cc2ddf4175de47`; estimate JSON VN002 `b5485677036543ef6590e121299aeea0aef5be94b88feddb692e86f55bcc72a2`. Đã đọc lại CSV:286 dòng/22 dòng VN002, đủ cột; bốn hash canonical vẫn khớp bản đầu.
