# Kế hoạch kiểm độc lập và nhận xét — phiên14

Ngày 03/11/2026. Chỉ tạo CONTRACT.md và PLAN.md; không chuẩn bị/áp patch, không sửa source/tests/scripts/catalog/frontend, không import/probe/TestClient/full/CAD/DB, không commit/reset/deploy. Phiên03 sole writer backend dimensions; phiên01 giữ release/freeze/full. Source chưa được phiên14 sửa.

Đã đọc bổ sung `docs/KE_HOACH_UU_TIEN_HOAN_THIEN.md` và `docs/PHAN_VAI_CAC_PHIEN.md`. Ưu tiên lỗi sai lượng/mất nguồn trước; nhận xét đã gửi ngay cho01/03, không chờ triển khai hoặc báo cáo nghiệm thu lớn. Không bịa số đo thực, kết quả test hay lịch hoàn tất.

## Nhận xét từ mã đã đọc

| Mã | Vị trí quan sát | Nhận xét và ca cần chứng minh |
|---|---|---|
| D14-01, lỗi nhãn xác định | rough/beams.py:186–190 | length_m là net nhưng note “Dài sau trừ giao” in cut_mm. Trục4 m/cut0,2 m → length3,8 m, nhãn khoản trừ0,2 m; cut0 vẫn rõ. Chỉ sửa metadata, không đổi BT/CP. |
| D14-02, rủi ro cần focused | rough/models.py:176–192; beams.py:186–190 | Float optional chưa cấm số không hữu hạn. Width NaN, depth/slab thiếu có thể để quantity None nhưng metadata width NaN. Ca từng field với NaN/±inf phải bị chặn hoặc chuyển thiếu có lý do, strict JSON không phát token lỗi. Chưa quy đây là exact NaN của lượt full cũ. |
| D14-03, thiếu truy nguồn | rough/beams.py:168–190 | Nguồn ghi “tiết diện bản vẽ hoặc thông số” không chỉ ra cạnh nào lấy đâu. Ca b từ params, d từ Beam và ngược lại; giữ inputs/status, không nâng A. Việc `b.b_mm or params...` là hành vi cũ cần owner phân loại, không tự sửa công thức. |
| D14-04, thiếu cấu trúc | rough/foundations.py:143–149 | Đỉnh lớp vát chỉ nằm trong note mm. Ca hai lớp: hộp2×2×0,3 m và vát đáy2×2/đỉnh1×1/cao0,5 m phải giữ hai lớp và đỉnh số riêng. Nếu volume_m3 cùng tiers, lượng hiện ưu tiên volume nhưng metadata chưa nêu cơ sở override. Chỉ nhập volume không sinh kích thước. |
| D14-05, thiếu cấu trúc | rough/stairs.py:147–157,169–184 | Dài hiện là tổng chạy ngang, chiếu nghỉ/số bậc ở note; dài nghiêng/cao bậc chưa có field riêng. Ca H3 m, n20, b0,25 m → chạy5 m, nghiêng√34 m, cao bậc0,15 m; thêm hai thang khác kích thước và dầm thang, thang thiếu t/steps phải giữ missing. Không sửa công thức thang qua task metadata. |
| D14-06, rủi ro miền count | rough/takeoff.py:301–306 | `(d.count or 1)*n` gộp None/0 thành1. Với n3: count2→6; count0 không được thành3; countNone cần nghĩa rõ. Hiện beam producer count1 nên chưa chứng minh lỗi quantity thực; cần quyết định miền count trước sửa. |
| D14-07, giới hạn raw/net | rough/walls.py:107–127; secondary.py:185–188; takeoff.py:268–274 | Dimensions tường trước N03 và giằng trước hợp đoạn. Ca giằng chồng và N03 pending/None/D phải giữ quantity/status cuối, raw không thành net. CP/TRAT dùng chung metadata cần hiển thị khoản trừ/số mặt riêng, không tái tạo lượng. N03 thuộc03, reviewer không nhận ownership. |
| D14-08, thiếu thông tin áp dụng | rough/models.py:180–192; areas.py:218–227; steel.py:33–35 | None đang dùng cả thiếu và không áp dụng. Ca lỗ sànNone/0 và thép không có rộng/cao cần hiển thị khác nhau. Chốt backend/UI cách mã hóa tối thiểu, không parse note để suy số. |
| D14-09, khoảng trống export | rough/boq.py:35–38,57–77 | Công tác Excel không xuất danh sách dimensions; chỉ sheet thép giữ bảng thanh. Ca nhóm2 dầm khác dài và móng nhiều lớp cần đối chiếu đủ phần tử API/UI/BOQ nếu mục tiêu nghiệm thu yêu cầu. BOQ ngoài release10file phải qua01 trước khi writer sửa. |
| D14-10, giới hạn thép và nguồn | rough/steel.py:33–35,43–93 | Bảng có count/dài cắt, Ø nằm label; hàm lượng và tấn override không có dimensions là đúng về hình học thanh. Cần chứng minh bảng thiếu dòng giữ phần biết/missing, hàm lượng không giả thanh, manual override không mang nguồn bảng thành A. |

## Vùng ghi đề xuất cho điều phối, không phải yêu cầu mở writer14

- Phiên03: models/walls/columns/beams/foundations/areas/stairs/secondary/steel/takeoff trong release backend hiện có. Chỉ metadata và test trực tiếp được01 cấp; mọi đổi quantity/formula/status nêu riêng, không gộp ngầm.
- Owner API/test: route rough, rough/auto, strict JSON và payload cũ; phối hợp03 nếu release chưa bao phủ main.py/tests. Không tự mở main.py vì owner UI/khác đang dùng.
- Owner BOQ: boq.py và test export sau01 cấp phạm vi; giữ thứ tự/số lượng/số lượng đơn vị hiện có, thêm bằng chứng metadata nếu được chốt.
- Owner UI/session: WorkReview/model và review-session/materials; phân biệt ô thiếu/không áp dụng, nguồn từng đầu vào, kiểm lại sau đổi hình học/vật liệu, phản hồi cũ/lỗi lưu/reload. Phiên14 không ghi frontend.

## Ma trận nghiệm thu sau release/freeze

1. Producer nhỏ: payload cũ→[]; hai cấu kiện khác kích thước; None/0/nonfinite; nguồn trộn; beam cut/web/tie; cột hai cao độ âm nhưng chiều cao dương và CP hole; móng nhiều lớp/vát/volume override; hố đào/đắp; sàn không chữ nhật, lỗNone/0; thang nhiều loại; giằng raw/hợp; thép bảng/hàm lượng/manual.
2. Callers: count lặp3 tầng đúng một lần; quantity/missing/status/formula hồi quy; N03 raw-net và dòng trừ; API rough/auto + HTTP JSON, serialization/lưu/khôi phục, BOQ giữ đủ phần tử. Không cần CAD/full để chứng minh từng metadata producer.
3. Phiên01 chốt snapshot/hash các file liên quan và phân lịch focused; reviewer14 chỉ nhận log terminal và diff/hash để review độc lập. Không tính dấu chấm pytest là số passed; không nhận kết quả snapshot cũ cho delta mới.
4. Owner UI làm QA hồ sơ ACTUAL-build KT+KC sau quyền upload được giải quyết: `/do-boc` → `/phan-tho` → `/dieu-chinh` → `/vat-lieu` → `/toi-uu`, sửa/tính/lưu/quay lại/reload và đối chiếu API/BOQ. Chưa có browser evidence không ghi hoàn tất.

## Phụ thuộc và điều kiện kết thúc

Chờ03 chốt schema metadata nhỏ nhất và bàn giao delta/hash;01 chốt quyền API/BOQ/tests/UI và lịch freeze. Không chờ để làm patch vì reviewer14 không có nhiệm vụ triển khai. Nhận xét trên là đọc mã, các ca số là tính tay kỳ vọng, không phải kết quả chạy. Chưa xác nhận contract đã được owner chấp nhận, strict JSON đạt, DB round-trip đạt hoặc toàn luồng đã nghiệm thu.

## Review gói SOURCE-READY của03 — 03/11/2026, sau bàn giao

Đã đọc `reports/work_dimensions/CONTRACT.md`, `SOURCE_READY_HASH.json`, `backend_dimensions.patch`, snapshot WIP và `protected_N03.json`. Đối chiếu SHA256 bằng Get-FileHash trước/sau review: **11/11 khớp** manifest (10 source + tests/test_work_dimensions.py). Đây là gói trước focused, không gọi là hash nghiệm thu cuối. Phiên14 không chạy Python/import/test/AST runtime; protected_N03 là bằng chứng03 cung cấp, chưa được14 tái lập AST.

### Finding đã báo ngay01/03

1. **[P2] Dòng trừ thiếu metadata deduction.** `src/optimat/rough/foundations.py:116–119`: `_neg` chỉ tạo `_work(code,0,**kw)` rồi đổi quantity âm; dimensions vẫn []. Contract03 nói đã có record deduction. Ca `_neg('DAO_DAT',0.3,element='trừ giao',source='auto')` giữ quantity−0,3 nhưng không có record; ảnh hưởng dòng trừ hố chồng và CP sàn từ `takeoff.py:455–465`. `tests/test_work_dimensions.py:113–115` truy phần tử0 nên sẽ lỗi. Không yêu cầu đổi công thức hoặc lượng âm.
2. **[P2] Mất nhánh nguồn cao dầm dùng trừ tường.** `takeoff.py:257–260` đưa một depth duy nhất từ Beam/structural_beams vào wall_params khi params.beam_depth_mm gốc None; `walls.py:107–110` vẫn ghi field_sources.height_m là `PlanInput.height_mm − ProjectParams.beam_depth_mm`, source chỉ tầng/tường/dày. Ca H3300, params beam_depthNone, D1.d_mm400 structural: height2,9 m đúng, nhưng không giữ nhánh nguồn D1/structural, trỏ tham số gốc đang None. Cần truyền nguồn metadata đúng nhánh đã dùng; không đổi phép trừ/N03. Test mới chưa assert nguồn nhánh này.

Đã đọc log03 cung cấp sau khi phát finding: `focused.log` terminal **1 failed, 227 passed**, exit1; `result.json` ghi224dependency trước/sau không drift. Failure đúng `tests/test_work_dimensions.py:114`, IndexError dimensions[0] của `_neg`. Đây là kết quả lượt03, không phải14 chạy; chưa đạt focused toàn bộ. Chờ03 sửa có hash mới rồi kiểm lại, không nhận kết quả này cho delta sửa tiếp.

### Đối chiếu các gap trước

| Gap cũ | Nhận xét trên hash đã bàn giao |
|---|---|
| D14-01 nhãn/net/web | beams.py:186–200 đã tách gross/deducted/net và concrete_height, đổi nhãn đúng khoản trừ; không thấy đổi biểu thức BT/CP trong patch. |
| D14-02 finite | ConfigDict allow_inf_nan=False cho WorkDimensions; test finite trực tiếp và HTTP nằm trong lượt03. Không mở serializer; không coi là mọi đường dữ liệu khác đều được bao phủ. |
| D14-03 nguồn trộn dầm | field_sources b/d theo đúng nhánh truthy Beam hoặc params đã dùng trong engine. Còn finding nguồn chiều cao tường ở trên. |
| D14-04 lớp/vát/override | Giữ từng lớp, số đỉnh bằng m, volume override gắn reference/note; không suy hộp từ thể tích. |
| D14-05 thang | Có run/slope và record bậc/chiếu nghỉ/dầm riêng, đơn vị đúng biểu thức hiện có. Chưa chứng minh nhiều thang, cao0/steps0 hoặc nguồn thang sao chép bằng bộ focused này; không sửa công thức cũ. |
| D14-06 count/repetitions | takeoff.py:303–306 giữ count và kích thước, chỉ nhân repetitions×n; quantity vẫn nhân n một lần. Test mới kiểm n3/count1/dài4. Chưa có test đường caller với countNone/0; đọc biểu thức mới không còn `or1`, không thấy delta nhân đôi. |
| D14-07 raw-net | Giằng có reference từng raw + union riêng; length union None khi group thiếu, không thay normalize/deduct. Tường raw vẫn ở note, quantity/status cuối không bị metadata tính lại. |
| D14-08 None/0 | Validator tách field truyềnNone với không truyền, round-trip giữ danh sách, 0 không bị đổi. Hợp đồng tin producer; không có kiểm nhất quán danh sách do caller tự truyền hoặc cập nhật qua model_copy. Không kết luận UI đã hiển thị đúng. |
| D14-09 BOQ | **01 truyền quyết định00: sheet WorkDimensions ngoài deliverable MVP.** Chỉ yêu cầu parity quantity/source/status/missing trên cùng snapshot; không block MVP vì thiếu sheet dimensions. Giữ kiểm đầy đủ metadata qua API/UI. |
| D14-10 thép | Đã có diameter_m, dài cắt/count theo dòng bảng; hàm lượng/manual giữ[]; không giả thanh, không đổi lượng mua. |

Chưa thấy công thức quantity mới hoặc lỗi đếm đôi từ patch đã review; đây không phải chứng minh toàn bộ engine đúng. Nghiệm thu source-ready cuối thuộc01, còn full, DB round-trip, UI và QA ACTUAL-build phải có bằng chứng riêng.

## Review SOURCE-READY v2 sau hai finding

Đã đối chiếu11/11file khớp manifest v2. Hash mới: foundations.py `67d3ed107a29e544147c705b50238b67c43f4048b7a2504c6fea2f746cd08e93`; takeoff.py `3c8095c296b65adab96940b1a6091d6edbba2036aa7d057b25b21f96e349c20e`; test_work_dimensions.py `75bc5d57d8b76f55fea01de131b2c008dce03002dacde11057e84a2ee3ab7759`. Tám hash còn lại giữ như gói trước.

- `_neg` tại foundations.py:116–122 có record basis=deduction mặc định, không cạnh giả; lượng âm và round giữ nguyên. Finding1 đã khép ở mức đọc code.
- takeoff.py:265–279 chỉ annotate nguồn cho XAY/TRAT sau producer nếu caller inject depth. Giữ view, ID, b.source, d_mm và nhãn KC chưa liên kết/căn chỉnh O01; không đổi chọn depth hay quantity. Params depth0 không bị thay vì nhánh inject vẫn kiểm `is None`. Finding2 đã khép ở mức đọc code.
- Test bổ sung kiểm manual/structural D7 trên `p.beams`, H3300→cao2,9 và explicit0→cao3,3. Chưa có assert riêng fallback `req.structural_beams`; đây là giới hạn coverage, không tự mở O01. Dòng trừ hiện ghi nguồn tham chiếu chung, chưa liên kết vị trí cấu kiện; không coi là có vị trí bản vẽ.
- Chưa phát hiện blocker mới trên v2 khi đọc sửa. Lượt attempt2 đang chạy lúc ghi phần này; không dùng log attempt1 ở thư mục cha để kết luận v2 đạt. Phiên14 không sửa source hoặc chạy runtime.

Cập nhật terminal attempt2: đã đọc `reports/work_dimensions/attempt2/focused.log` (**231 passed in28,58s, EXIT=0**) và result.json (224dependency trước/sau, không added/removed/changed). Đối chiếu độc lập11/11hash manifest v2 với hash_after focused và byte checkout đều khớp. Hai finding đã khép trong phạm vi code + focused03 cung cấp. Không phát hiện blocker mới cho gói metadata đã review; chưa nghiệm thu full/BOQ parity/UI/DB/browser/độ chính xác thực. Các giới hạn coverage và nguồn chung của dòng trừ ở trên vẫn giữ. Root01 quyết định tiếp nhận cuối.

Đã nhận bàn giao cuối `reports/work_dimensions/BAN_GIAO.md` và `FINAL_HASH.json`: đối chiếu byte checkout11/11khớp FINAL_HASH, cùng mốc v2 đã review. Kết luận review độc lập giữ nguyên: hai finding đã khép, focused03 đạt trong phạm vi nêu trên, không blocker mới được xác định. Chủ đồ án yêu cầu tiếp tục review nếu có delta sau tích hợp UI/full; đã báo01/03 gửi diff/hash/log mới. Review này không bao phủ delta về sau, không mở quyền ghi source hoặc runtime cho14.

## Review delta attach_prices sau metadata v2

Đã nhận releasewindow01 và gói03 tại `reports/rough_price_source/attach_prices.patch`, `SOURCE_READY_HASH.json`. Hai hash khớp checkout: takeoff.py `2882a4e922d30d6a932022b06f04bf8bda5faa4e6e093ed0a443725a64eef90f`, test_rough_price_source.py `9c516e11055e860a0da3d508dafb2176a8838ecbb86b4daf9ee34d4c09daba19`. Base snapshot/takeoff.py SHA256 đúng `3c8095c296b65adab96940b1a6091d6edbba2036aa7d057b25b21f96e349c20e` của metadata v2 cuối. Đã đọc patch/test và selector pricing.py hiện có, không chạy runtime.

- takeoff.py:396–399 reset best_price/price_source/est_cost trước earlyreturn không ID và trước chọn lại; không còn giữ tiền cũ khi offer mới bị loại hoặc vật liệu mất mã.
- takeoff.py:409–423 gắn nguồn từ best được selector trả: mứcgiá, nhà cung cấp, ngày, loại dữ liệu, chứngtừ, tranggiá hợp lệ, VAT/cước và valid_until nguyên văn hoặc “chưa rõ hiệu lực”. Giá lịch sử và BULLETIN được ghi tham khảo. Không đổi selector eligibility/date hoặc gọi ngày giá là ngày hết hạn.
- est_cost chỉ tính khi quantity cơ sở có, complete và status khácD; ưu tiên quantity_with_waste kể cả0, không `or` làm mất0. Không ghi quantity/status/missing, count/repetitions, dimensions hoặc N03.
- Test mới dùng offers trong bộ nhớ: cùng đơn vị, reset sau expired/unknownterms/mất mã; partialD; SAMPLE/SYNTHETIC; validityNone/raw; lịch sử; D dù completeTrue. Đây là dữ liệu SYNTHETIC, không chứng minh giá mua ACTUAL hiện hành.
- Chưa phát hiện blocker mới trong hunk được giao. Không suy reviewmetadata231passed bao phủ hunkgiá mới. Chờ terminal/hashfocused riêng; BOQ/UI/dateeligibility/nguồn dữliệu thực ngoài kết luận này. Đã báo01/03 nhận xét tĩnh ngay, chỉ ghi docs riêng.

Cập nhật kết thúc reviewgiá: so văn bản trước/sau sau khi loại đúng vùng `def attach_prices` đến comment nhóm vật liệu cho kết quả phần ngoài function bằng nhau. Đã đọc focused.log của03: **95passed in13,22s, EXIT0**, result.json225dependency trước/sau khôngdrift; hai hash gói khớp manifest, hash_before, hash_after và byte checkout. Không có finding mới được xác định trong phạm vi hunk này; báo01/03 để01 quyết định tiếp nhận. Không nghiệm thu API/UI/BOQ/DB hoặc giá thực, không chạy test bởi14.

## Review O01 theo release riêng01/BA đã duyệt

Đã đọc toàn bộ `docs/review/O01_CHUAN_BI.md`, đặc biệt phần chốt DTO BA cuối thay các đề xuất cũ; `reports/o01/TRANG_THAI.md`, O01.patch và source/tests. Manifest dạng object4path→hash, đã đối chiếu4/4byte khớp: takeoff.py `b7084eeee124931a9eec8efb66ed1d8bba189fc09ecee4ada09f5d87d1e0197b`, test_rough_beam_sources.py `ca241a6faf6f85070e8fbd78bef09a39b2ec4e77d04f9cba514d3f79e694cf0d`, test_rough_takeoff.py `09c52e34eba2d39bf1e0a5e15909f85ecd0e7b3f147a4bb68ec5fda9ca98b500`, test_work_dimensions.py `db65fe6ce2bc23f48748c247af694f63982e574eed73a387de4b1cdb2e80ea0d`. Không dùng metadata231/price95/core824 làm bằng chứng O01.

### Finding đã gửi ngay01/03

1. **[P1] Local toàn keepFalse bị bỏ mất phạm vi và tổng có thể giả đủ.** takeoff.py:379–396 chọn nguồn local, beam_works lọc kept trả[]; guard pending chỉ kiểm `p.beams == []`, bỏ sót danh sách có phần tử nhưng toàn keepFalse. Ca T2 localallFalse, T3 manual4m/b200/d400/slab100: T2 không có dòngDAM/CP; tổngDAM0,24/CP3,2 chỉT3 nhưng có thểcompleteTrue thay vì knownpart+pendingT2. Không inferbù, không chứng nhận thiết kế0.03 đã xác nhận blocker và sẽ sửa sau terminal attempt1, giữfreeze trong run.
2. **[P2] Trùng tên viewKC và plan làm mất geometry/nguồn trong result.beams.** takeoff.py:380 gán used_beams[p.name], sau đó dòng460 `used_beams.update(req.structural_beams)` và468 ghi theo view. DTO không cấm hai namespace trùng key. Ca plan.name='TẦNG 2' có manualDlocal4m, structural_beams key='TẦNG 2' nhưng scopeexplicitT3: lượng localT2/KCT3 có thể tính riêng đúng nhưng output chỉ còn KC T3 dưới key'TẦNG 2', geometrylocalT2 bị ghi đè. Ngay cả cùngtầng, mapping không chứng minh alignmentXY. Cần01 chốt báo lỗi/xử lý collision, không tự mở DTO/UI. Chưa khẳng định UI thực đã overlay vì chưa QA; đây là lỗi hợp đồng nguồn/output đọc mã.

### Các nhánh đã rà và giới hạn

- Resolver theo tầng giữ scope raw; chọn đúng một owner hoặc pending, count khai báo chỉ kiểm với rawscope trước allocation, không làm multiplier. Overlap A:T2/T3/T4 vàB:T4/T5 giữT4pending hoặc explicitowner; recordKC tách từngtầng/repetitions1, không nhân count thêm.
- KC có scope đúng chặn manual/suy chưa chọn; thiếu tiết diện/rỗngKC vẫn là nguồn được chọn và missing/pending, không fallback. None/[]local được phân biệt nhưng còn findingallFalse trên.
- Scope suy trầnB, mapping/choice trầnC qua priorstatus/inputs; assign_status giữ prior vàD, không thấy nângA chỉ vì structural. Test mới có validation/ref/scope, overlap đảo thứtự, countmismatch, knownpart/vật tư/BOQ, thiếuheight vànoKCdepthtransfer.
- KC không được đưa vào localbeams để cắt cột/tườngKT; depthwall chỉ lấylocal đã chọn hoặc paramtườngminh. GeometryKC xửlý bằng viewgốc, không dùng p.columns. Findingcollision vẫn cần khép trước nhận output giữnguồn.
- CPsàn/O02 và alignment chưa giải trong O01; không suy label view→tầng là đã căn chỉnh. Không sửa N03/beam_works/status/price. Chưa tái lập AST hoặc chạy test;03 đang focused attempt1, kết luận chờ fix/hash/terminal mới.

Chỉ ghi báo cáo riêng, không source/patch/test/runtime. Hai finding trên chưa được khép ở mốc hash này; quyết định release sửa và tiếp nhận thuộc01.

### O01 bản sửa1 — review độc lập sau chính sách collision được01 duyệt

Hash4/4khớp manifest mới: takeoff.py `aa1d00e565a9cd7344dde64f8d54c69793f3c8233cd47e6fc16419090da9f84b`; test_rough_beam_sources.py `dbe64198299a3d4d893f8e4c9f3e6cba79a16cae57828e2720b098ce2a8e746c`; hai filetest còn lại giữ hash O01 trước. Đã đọc gói sửa, không runtime.

- FindingP1 khép ở code: guard local `p.beams is not None and not any(b.keep...)` xử lý cả[]/allFalse, sinh pendingDAM/CP và khônginferbù. Regression giữknownT3 .24/3.2 nhưngcompleteFalse/statusD vàpendingT2.
- FindingP2 khép ở code theo releaseoutput01: RoughResult thêm plan_beams/structural_beams default{}, giữ riêngrawlocal/KC; legacybeams bỏ mọikeycollision và cảnh báo, không đổi owner/quantity/status vì tên trùng. Hai testscopeT2/T3 kiểm totals.24/.48 cùngCP, đủraw hai map vàabsentlegacy. Không suy rawmap thành nguồn đã chọn hoặc alignmentXY; UI02 cần dùng đúngmap, không cộng hai map làmkhối lượng.
- Caller thêmD/missing choXAY/TRAT khi cóKC mà khôngcólocal/userdepth; lượngraw đã biết giữ nguyên, không chứng nhận cao tường netđủ. Paramdepth0 vẫn làtườngminh; N03dùngcơsởđãchọnvàmissingkhôngbịxóa. Điều kiện này không tự giải alignment/O02.
- `_beam_trace` khôngprepend sourceinput vào dòng đãthiếu; vẫn giữstatuscap/evidence. Không sửastatus.py hoặcparseevidence để nângtrạngthái.
- Đã đọc attempt1_pure/result/log:268passed/2failed/4deselected,exit1,226hashkhôngdrift. Lỗi cũ noKCdepthstatus vàthứtựinputD được sửa trongbản này; không lấyattempt1làpassbản sửa. Attempt1HTTP bị ngắt/blocked, không kết luậnHTTPđạt. Chờattempt2_pureterminal/hash trướcchốt focusedbảnmới.

Chưa phát hiện blocker mới khi đọc bản sửa1. Không lấysource-readyhoặctestđượcviếtthànhbằngchứngđãpass; root01duyệtcuối, full/API/UI/BOQparity vàhồsơthậtgiữriêng.

Cập nhật terminalbản sửa1: reviewer14 đãđọc `reports/o01/attempt2_pure/focused.log` **273passed,4deselected in28,54s,EXIT0** vàresult.json226dependency0drift. Bốn hashmanifest khớp bytecheckout/hashbefore/hashafter củaattempt2. Hai findingP1/P2 đãkhép trongcodevàfocusedpuređượccungcấp; chưathấyblockermới tronggóinày. Đọc run_pure.py xác nhận4case bịdeselect gồm3HTTP và1CADthật; khôngđượccoiđạt.03 báoHTTPngoàisandbox bịautomaticapproval từchối;14khôngthửlách/chạy. Chưafull/API/UI/ACTUAL/DB. Đãbáo01/03 kếtluậnđúngsnapshotnày, khôngruntime14.

## G8 staging — review hợp đồng trước release canonical

Theo yêu cầu01, chỉ đọc bốn tệp trong `reports/g8_detail/SOURCE_READY_HASH.json`, FINAL_HASH.json, CONTRACT_DE_XUAT.md, staging model/test/M1 fixture và attempt1 log/result/process. Đã đối chiếu byte **4/4 khớp SOURCE_READY và FINAL**. Hash helper staging `f7eed3de5bdc4f71d2303f81cbdc5cafe79b70e830ba09b185acb97b80a32517`; test `dadf866de5992a7b491263db56036caa47734c90a1e5c541b088b8e7317d777c`; fixture `adaa9301a6906fe160fb6815b3cb7bd08d70a0603958ddb9f6fd793dbfae098f`; contract `8bb9d6b40ef43611a06f92a606d83b1a451502b789225e391b4865566ec8a88e`.

Đã đọc terminal03: **33 passed in0,49s, EXIT0**, result226 canonical dependency không drift. Không chạy lại, không coi staging là production/API/UI/Excel đã đạt.

- Contribution mới cộng; reference không cộng, kể cả khác đơn vị. raw_quantity là magnitude không âm hữu hạn, sign tách±1, tổng âm không clamp. Count/repetitions/factors/conversion là diễn giải đã áp dụng, helper không nhân lại.
- Conversion có đơn vị/nguồn không trống, factor dương hữu hạn, to_unit khớp row.unit. Factor có tên/value/unit/meaning/source, không nhận extra keys; value không âm hữu hạn. Không giả hệ số1 khi nguồn trống.
- Model tổng kiểm signed sum, đơn vị contribution, duplicate row_id, known_part_raw, total_raw, complete, scope_complete, legacy_delta ngay cả khi gọi constructor trực tiếp. Unknown giữ None/missing, known0 giữ0. ScopeComplete do producer khai báo, validator không chứng minh phạm vi bản vẽ thực sự đủ.
- `_amounts` tính sum và delta trong cùng localcontext đủ khoảng exponent/digits và carry; không thấy còn rơi delta về precision28. Tests có số hơn28 chữ số và round-trip; chưa exhaustive mọi scale/cancellation/khối dữ liệu lớn. Không tự thực thi expression hoặc tính lại từ dimensions.
- Helper nhận q trước round3, không ghi WorkItem.quantity; staging chưa nối producer/net mutations. M1 giữ9 dòng source_quantity, nhóm không góp, raw3.2515; fixture không nhận là groundtruth độc lập, không audit công thức XLS. Reviewer đọc fixture/evidence JSON, không mở hoặc xác minh lại file XLS trong lượt này. Số vật tư chỉ thuộc reference, không được dùng để đổi catalog hoặc precision engine legacy.

### Import canonical và lưu ý validation

**Chưa thấy blocker số học trong staging đã đọc.** Có nguy cơ circular import nếu canonical copy module đang `from optimat.rough.models import WorkDimensions` rồi models.py lại import WorkQuantityDetail từ module đó. Hunk đề xuất cho01/03, không viết patch: đặt DTO DetailConversion/DetailFactor/QuantityDetailRow/WorkQuantityDetail sau WorkDimensions và trước WorkItem trong models.py; pure decimal_text/_amounts dùng bởi validators nằm cùng models, không import helper ngược. Module quantity_details.py mới chỉ import DTO/pure helpers và chứa summarize. WorkItem.quantity_detail optional giữ tương thích. Có thể chọn cấu trúc tương đương nhưng dependency phải một chiều; không tách bộ WorkDimensions mới hoặc thêm model_rebuild/wrapper không cần thiết.

Lưu ý nhỏ, không block phép tính: QuantityDetailRow._source_and_missing hiện chỉ kiểm truthiness missing, nên `raw_quantity=None, missing=[' ']` qua validation dù không có lý do thực. Nên reject reason rỗng khi đưa validation canonical; không biến unknown thành0. DetailLevel là nhãn producer, chưa là bằng chứng từng cấu kiện đủ. Hook lót staging chỉ minh họa, nguồn/hệ số/quy đổi thực và cập nhật sauN03/L1 cần review ở release producer riêng.

Đã gửi01/03 kết luận/hash và đề xuất import. Không sửa canonical hoặc runtime/test; O01HTTP/full chưa đạt vẫn giữ,33staging không bao phủ toànrough/UI/Excel. Canonical DTO/helper sau release cần hash/test riêng; việc này chưa mở producer/takeoff.

## G8 canonical DTO — review độc lập trước producer lót

Đã đọc `reports/g8_detail/canonical_dto/DTO.patch`, SOURCE_READY_HASH/FINAL_HASH, snapshot/models.py, ba canonical file và attempt2/result/log. Bytecheckout cùnghashbefore/hashafter **3/3 khớp**: models.py `56a507cf9cc4841756258415aa80a8fa3c9293cfc93ae306304d58cc85d5c841`; quantity_details.py `ecf62f7e8aee229cdbfb8228c35d64e187964370b215e06590cdb1288f7b7ad2`; test_rough_quantity_details.py `600a5538d6cc9930c1c2e04df8aa861d980d89eae5db1f33ed37aa358e545e28`. Log03: **78 passed,3 deselected in5,43s,EXIT0**;229dependency0drift. Attempt1runnererror/exit4 không được coi là testđạt.

- Dependency đúng một chiều: models chứa pureDecimal+DTO sau WorkDimensions/trướcWorkItem, không import quantity_details. Helper import DTO/purefunctions từmodels; chưacallerproducer/takeoff. Đối chiếu text nguyên class WorkDimensions giữa snapshot vàcheckout bằng nhau; reviewer không chạyAST/runtime. Không thấy sửaquantity/statusO01 trong patchDTO.
- Optional quantity_detail=None giữ payloadcũ quantityNone/0/1,25 vàstatus. Parentvalidator kiểmđúng unit vàlegacyquantity (kểcảNone khác0); test round-trip khôngghiđèquantity. Missingreason whitespace đãreject cho cảknown/unknown. Precision/signedsum/factors/conversion giữinvariant nhưstaging, khôngnhâncount/lặp lần2.

### Finding mới đã báo01/03 — [P2] Complete detail chưa ràng dependency của WorkItem cha

`src/optimat/rough/models.py:416–428`: `_quantity_detail_matches_work` chỉ kiểmunit/legacy. Ca đọc mã: detail có một contributionraw1,legacy1,scope_completeTrue→completeTrue,total_raw1; gắn vào WorkItem quantity1,statusD,missing=['chưa xác nhận phạm vi'] vẫnđượcnhận. ContractG8 địnhnghĩa complete gồm phạmvi/dependency côngtác, khôngchỉ đủsốrows; consumer cóthểhiểunhầm detail làtổngđủ trongkhi parent đangthiếu.

Đề nghị01chốt trướcproducer: khôngcho detail.completeTrue khi parentD/missing, vẫngiữknownpart/totalNone; releaseproducer sau cần finalize sauN03/L1/status, vì model_copy/in-place mutation hiệnkhôngđượctrìnhvalidatornàybảovệ. Không sửaquantity hoặcstatusparent để làmkhớpdetail. Nếu chủđồánđịnhnghĩa detail.complete chỉlàđủsốhọc thìcầnđổicontract/consumer rõ, hiệncontractkhôngnóivậy. Đây làfindingtĩnh, chưa runtime; 78testchưacócase parentD/missingvớidetailcompleteTrue.

Chưachốt canonicalDTO khôngblocker vìP2trên chờ01/03 xửlý. Chưanối emitters/producer/takeoff; không lấy78testchoO01HTTP/full/UI/Excel. Reviewer14 chỉghi docsriêng, khôngsource/runtime/test.

### G8 canonical parent fix — P2 đã khép theo BA01

Đã đọc `canonical_dto/review1/parent_invariant.patch`: chỉ thêm guard parentvalidator và4case test. Guard reject khi parent.statusD hoặc parent.missingkhôngrỗng đồng thời detail.completeTrue hoặc total_rawkhácNone, kểcảtotal0. Không ghiđèquantity/status/missing, khôngglobalvalidate_assignment/status.py. Test cóDkhôngmissing, Ccómissing, Nonecómissing vàpartialknownroundtrip. `_quantity_detail_amounts`/helper/importkhôngđổi; chưa thêmemitter/finalize.

NewSOURCE_READY/FINAL cùng bytecheckout/hashbefore/hashafter attempt3_parent_fix **3/3khớp**: models.py `5cfb8b6344775a17a02f9b50b11c07fb6927bb19e583a1d06266356a2c3142ad`; helpergiữ `ecf62f7e8aee229cdbfb8228c35d64e187964370b215e06590cdb1288f7b7ad2`; test `e244042b48632fa88a3b72b19512740c3776bb72f20413ba1c9e46785a9e18de`. Đãđọc log03: **82passed,3deselected in5,19s,EXIT0**,229dependency0drift.

FindingP2 parent scope đãkhép ởcodevàfocusedđượccungcấp. Chưathấyblockermới trongDTO/helpertrênhashnày; root01quyếtđịnhtiếpnhận. Giớihạn:3HTTPchưakiểm, O01full/API/UI/Excelchưađạt; in-placemutation/model_copykhôngtựvalidate, nênreleaseproducer sau vẫn phải finalize saunet/status/scope.82testkhôngchứngminhđãphủemitter.14khôngsource/runtime/test.

## G8 lean producer — review theo release4file

Đã đọc LEAN.patch/source/test và SOURCE_READY_HASH tại reports/g8_detail/lean_producer. Bốn byte khớp manifest: foundations.py `18660eabb927549a12c7ae52e85321a37b0f6b41a2e8a297ae77c4859b47848a`; quantity_details.py `2b026826413c388c70e5ee4645cad7b9a18da29d83ebc88f8d65cd9936104af2`; takeoff.py `2ede81021e619e7ff152e3fc2edc0231613d141ff390066b8314e5a3c9c61d0d`; test_rough_quantity_details.py `216d656620e001bda689c2a798e8f5d77f45e3a64ae969af2de8f40a8a6e0d3b`.

- Lean q đưa nguyên biểu thức cũ ra biến lean_q tínhmộtlần, dùng cùngq cho_work vàdetail, khôngsuy từround3. Detail giữf.source/count/lớpđáy/dàylót; raw0khôngthànhNone. Thiếubase giữNone/missing; chưa nhậpdàylót thìkhôngsinh emittermới, nhưlegacy.
- Rawâm đượcgiữreference/sign−1/magnitude dương cómissing/detailunavailable, khôngsinhđónggópgiả; legacy clamp0giữnguyên. Không thay status/hìnhhọc chỉđểđủdetail.
- Finalize sauassign_status vàmọinetmutationhiệncó, trướcmaterials. Dump→model_validate táikiểm nestedDTO; khôngmodel_copybypass. So legacy/unit trước khi summarize, mismatchraiseValueError thayvìgánrawgrosslàmnet; scopechỉhạkhiparentD/missing, khôngtựnângscopefalse. WorkItemđượctáivalidate, giữparentknown/quantity/status/missing; dòngchưaphủdetailgiữnguyên.
- Patchtakeoff chỉimport vàcallfinalize; O01resolver/attach_priceskhôngcóhunkđổi. Không sửamodels/walls/N03/BOQ/địnhmức tronggóinày. Testparityso payloadlegacy cólean vàstripdetail giữtotals/materials/status/giá, nhưngchưađạtterminaltoànbộ.

Đãđọc attempt1/focused.log/result: **141passed,1failed,3deselected,EXIT1**. Failure tại test_lean_hook_receives_pre_round_quantity: fixtureSimpleNamespacecũkhôngsource, helpernayđọcf.source; FoundationItemproductioncófieldsource. Owner03cầnsửafixturecónguồnhợp lệ, khôngnớihelperđểnétest. Hash231deps phát hiện drift tests/test_project_files.py; chưakếtluậnsnapshotfocusedổnđịnhhoặcthànhcông. Đãbáo01/03ngay,khôngtựsửa.

Giớihạn quantrọng chogóiproducersau: soquantitylegacyround3 chỉpháthiệnmutations làmđổisốlegacy, khôngchứngminhrawnetkhôngđổi nếu netmớivẫncùnground3. Leanhiệnkhôngcónetmutationnênkhôngxácđịnhblockerởđây; khi mởN03/L1/côngtáckhác bắtbuộcdựnglạiledger bằngqnetthực, khôngdựafinalizeđểtựpháthiệnmọigrossnet. ChưaG8toànproducer/API/UI/Excel/O01HTTP/full.14chỉdocs,khôngsource/runtime/test.

### Lean attempt2 — chốt review độc lập

Fixturecũ đã thay SimpleNamespace bằng FoundationItem thật cósource default; không nới helper hoặc thay productionđểnétest. Hash ba productionfile giữ nguyên soattempt1 đãreview; hash test mới `fae4effed89231d3aa2921ddfdeec10eb97b02821ca236f776c1d6143b1eaf6a`. SOURCE_READY=FINAL=bytecheckout=hashbefore/hashafter **4/4khớp**.

Đãđọc attempt2/focused.log/result: **142passed,3deselected in10,52s,EXIT0**;231dependencykhôngadded/removed/changed. Lỗi fixture và thiếu bằng chứng snapshotổnđịnh ởattempt1 đãkhép bằnglượt2; giữ logattempt1 làm lịch sử, khônggọidrifttests_projectfileslàthấtbạiproduction. AST_PARITY.json của03 báo rawexpr/_work/ngoàiemittergiữnguyên; reviewerđãđọcpatchđểđốichiếu, khôngtựchạyAST/runtime.

Không phát hiện blocker mới trong phạm vi emitterlót/finalize đãreview; đãbáo01/03 để01tiếpnhận. Giới hạn3HTTPdeselected,khôngfull/DB/CAD/UI/Excel vàkhôngG8mọiproducer giữ nguyên. Giới hạnrawnetcùnground3 ởtrênvẫnápdụng choreleaseproducerkhác.14khôngsource/runtime/test.

## P02 area producer — review ngày04/11/2026

Đã đọc SOURCE_READY_HASH, AREA.patch, ba canonical file, snapshot/helper, AST_LEGACY_PARITY_STAGED và attempt1 process/log/result. **3/3hash khớp checkout/hashbefore/hashafter**: areas.py `5c2a517b2dbf1979755e5a8db31390aaaafbfaeb79fae0172b264c43b7c9b0a4`; quantity_details.py `784df5be1a5479462a9eb711e6cce73a3905064eb90546055310cbcc4316c0f7`; test_rough_area_details.py `0ff11ccb1b26e148e11043d76832421e388e11a5a1a0445cc738d3d32521ca11`.

Đọc terminal03 attempt1: **132passed in12,97s, EXIT0**,241dependency0drift. Năm file focusedpure, khôngHTTP/DB/CAD/full;14khôngtựchạy. AST_LEGACY_PARITY_STAGED.json ghi canonical_appliedFalse làbằngchứngstagingcũ, khônggọilàchứngminhASTcanonical; reviewerđọcpatchlegacyvàđốichiếutexthelpercũ nguyênprefix trước2hàmarea mới.

- SAN contributiongrossm³ vàvoidsign−1m³; CPpositive dùngm². Khônglấyarea×thickness choCP. raw producer aggregate làmreference riêng, khôngcộngvàkhôngbùdư đểép khớpfloat. Workquantitylegacy/clamp/formula/missing/statusgiữnguyên tronghunk; testparity cóvàstripdetailkhôngphảikiểmCADđộchínhxác.
- VoidNone tạo rowunknown cómissing vàscopeFalse; biết0giữ0. ParentSANcóthểvẫnCvàquantitygross theolegacy, nhưngdetailpartial/totalNone, khônggọiđólànetđủ. Voidâm/vượtgross chỉra thiếu/invalid; khônggọiclamp0làđápánđủ. TNone/0 giữnhánhlegacyquantityNone, dimension0khácNone.
- Groundlayers cùngmã vẫn cólabeltheolớp riêng; row_id chỉnộibộWorkItemkhôngdeduptoàncục. CAN_NENunitm² dùdàylớpthiếuvẫngiữknownarea/totalNone. Layerthiếu cấu tạo giữunknownrow. BanconyNone/0khôngsinhdòngmới nhưlegacy, khôngtuyênbốthiết kếkhôngchốngthấm.
- WCđáy+upturn đónggóp riêng; thiếuupturn giữknownfloor, khônglấymặcđịnh0đểđủ. Ca2,1+0,8 códetailDecimal2,9, rawfloatproducer2,9000000000000004reference, legacy2,9; đãđượcBA01chốtgiữkhácbiệt này, khôngsửaquantityhoặcthêmdòngresidual. SourcegiữfieldPlanParams/PlanGeometryvàtham sốcổtường;khôngtạovịtríbảnvẽgiả.
- area_quantity_rowâmgiữreference/magnitude/sign vàreason; area_detaildùngsumcanonical, scopekhôngđủnếureferenceunknown/missing. Finalizer/leanhelpers cũgiữnguyêntext; khôngđổitakeoff/O01/N03 trongP02. Quantitydetailđượcdumpvalidate, khôngmodel_copybypass.

Khôngxácđịnhblockermới trongP02trênhashđãreview; đãbáo01/03. Giớihạn: CPsànâm/_slab_form_deduction vẫnquantity_detailNone ngoàiP02; khôngđượcgộpchỉledgerpositiveđểtuyênbốtoànCPsànđãdiễngiảiđủ. Hạnchếgeom.hull/khépkín/ôtrốnglegacyvẫnphảiđọcwarning; P02khôngchứngminhđúngdiệntíchthực. RuntimeAPIvẫnbaselineLEANchưareloadP02 theo03báo; khôngAPI/UI/Excel/DB/fullacceptance.14khôngsource/runtime/test;01duyệtcuối.

## G8 quantity summary — review ngày04/11/2026

Đã đọc SUMMARY.patch, sáu file canonical trong SOURCE_READY_HASH, snapshot và SYNTHETIC_EXAMPLE.json; đọc attempt1 process/log/result. **6/6hash khớp bytecheckout/hashbefore/hashafter**: models.py `69f12ffb9ee6e4250d8569f80281d076f461e1252e353cbb8e8a297ac9a06ac2`; quantity_summary.py `2ba36d8a4a9ede72e239856f94ffe7e9bb98462cba0a252ead90f847de16bb6f`; takeoff.py `96677ab2bcf42331911a2c486f3ecbe1cc00b2d58a152e1dfa8509f6886d42e4`; testsummary `3b97941d2eaddb20c9951f27fb2782665b8fdcdfc475ec6e2c2b45494d23de53`; testdetail `012eefaffc397763ddbfa97137552428f34157557491b1c334e82e603ee3810d`; testarea `615017f0d4e2e083b0c3d33e200e1c8c867cd5a647deeaf2eb05f4ae488e0946`.

Đọc terminal03: **189passed in12,18s,EXIT0**,243dependency0drift;7purefiles,khôngHTTP/DB/CAD/full.14khôngchạytest. Không lấy30case summary riêng thànhbằngchứngcảrough/UI/Excelđãđạt.

- Import một chiều takeoff→quantity_summary→models, models không importtakeoff/helper. DTOgroup/context/coverageappendcuối, WorkItem thêmguardquantityNone khôngthểclaimdetailfull; quantitylegacykhôngđượcđổichođủguard.
- Builder dump→validate works/context trướcđọc; hash gồmđúngworksđãfinalize+context/schema. work_key ordinalw:index vàrow_id chỉsnapshotlocal,đảothứtựhoặcsửaidentity/rawlàmhashđổi;khônggọi hash làngườidùngđãkiểm.
- Key cóstage/code/variant/unit/source/basis/formwork_of/steel_element/wall_system_id/spec. Methodhìnhhọc chỉtrace,khôngtáchquycách hoặc gộp saiđơnvị. Quy cách dùng7paramsđãkhai báo,khôngverified; thiếuquycáchisolatemỗiwork,khôngsuytừformula/evidence/AF. Đất/thép/đệmcát chưa cóclassificationcấutrúc giữisolatedunknown. Đủquantityvàđủcompatibility làhaiýnghĩakhácnhau: groupisolatedunknownvẫncóthểcótotalrawcủariêngwork; UIkhôngđượccoicomplete_componentslàđãxácminhquycách.
- Knownraw chỉcộngdetail.known_part_raw; totalchỉkhi mọi thànhviênquantitycomplete,khôngdùnglegacyhoặc0bùdòngnodetail. Reference/unionđãphânvaiởledgerkhôngbịsummarycộnglại; count/repetitionskhôngnhânlần2. Sốâm/kếtquả0giữDecimal,precisiontínhđủdigit/exponent/carry. Fixture4worksđúngknown.6450,totalNone;2dòng.3225rawkháclegacy.323×2,khôngcộngreference100hoặcnodetaillegacy1.
- Countsphânbốđủcomponents/aggregate/unavailable/nodetail; quantitycomplete/incomplete vàknown/unknowncontribution; referencecount riêng. Aggregatequantitycompletekhôngđượccoiđủcomponentcoverage;emptykhônggiảđủ/total0. Missingrefs giữwork+row, khôngdeduprow_idcùngr1ởkhácwork.
- RoughResultoptionalquantity_summaryNonegiữpayloadcũ; cósummarythìvalidate_quantity_summary xâyexpected từworks/contextcủasummaryvàsofullpayload,khôngghiđè đểsửasaihash/membership/key/raw/count/ref. Context tựkhai báo khôngchứngminhkhớptham sốthiếtkếđộclập;snapshotnàyđượctạoởcompute bằnggrouping_context(params).
- Hai testparitycũ chỉexcludequantity_summaryởCẢHAI phía,giữstripquantity_detailvàmọiasserlegacy. Testmới riêngchứngminhcompute thêmsummarymàlegacytotals/materials/status/giákhôngđổi;khôngnélegacyasserthidden.

Khôngxácđịnhblockermới tronggóiSUMtrênhashnày; đãbáo01/03. Giới hạn: SummaryDTOđứngriêngkhôngcóworksđểchứngminhsignedsum,phảiquaRoughResultparentvalidator; inplacemutation/model_copyvẫncầnrevalidatedump trước consumer. Sourcecontextđãkhaibáokhôngverified,khôngđổiđịnhmức/catalog. CPâmchưacóledgergiữnodetail/incomplete,khôngfilltừlegacy. ChưaAPIreload/HTTP/DB/CAD/full/UI/Excel;14chỉdocs/readonlysource,01duyệtcuối.

## Exporter09 sau user release — review chỉ đọc 04/11/2026

Theo yêu cầu01, chỉ review hai source mới; không review lại SUM unchanged. Hash byte khớp receipt và chỉ đạo: boq.py `7e090cdee04752bacea7c935da35d425ef4eb1b413e982c3ac973bb7d87137a5`; test_rough_boq_detail.py `b68090c72bf3fb4728bf1910c64271253f546ce73aeb7dcb2f5e36671724cad9`. Artifact/receipt ở `C:/Users/Admin/Downloads/optimat-ai_6/tmp/g8_summary_09_receipt`. Đã đọc source/test/receipt/final.log và đề xuất exporter09/QA15; áp dụng skill Spreadsheets cho review artifact. Không author workbook, không native Excel, không import code hoặc chạy pytest.

### Finding và gap trình bày

1. **[P2] Số nhỏ khác0 có thể hiện thành0 không cảnh báo.** boq.py:56–69 `_detail_number` nhận raw1e-16 (một chữ số có nghĩa, trong range) và trả numeric1e-16. Nhưng dòng79 `_detail_append` đặt format `0.###############;-0.###############;0`, chỉ15 chữ số thập phân cố định; số đó hiển thị0, sốâm tương tự. Dòng192 chỉ cảnh báo khi `_detail_number` trảNone nên ca này không cówarning. Raw text bên trace vẫn đúng; đây là lỗi hiển thị lượng/knownzero, chưa phải mất raw hoặc sai phép cộng backend. Cần format scientific/phù hợp scale hoặc blank numeric+cảnh báo raw, không sửa giá trị/quantize/residual. Testprecision hiện bao1e-308 bịblank nhưng chưabao1e-16 numeric đượcnhận. Chưa kiểm Excel native; kết luận từ codeformat.
2. **[P2, gap deliverable/truy vết cần01 chốt] Nhóm summary chỉ ởĐối soát, main/trace chưa biểu diễn quan hệ nhóm.** boq.py:148–170 main lặp nguyên từngWorkItem, nhãn chứaname/code/variant/position nhưng không có blocktổngnhóm/quycách/stage→group; dòng213 chỉ gọi `_group_block(compare,...)`. Trace:154–158,197–200 không cóquantity_summary.group_id/member refs; cột'Nhóm' chỉrow.group, không phải nhómsummary. Liên kết nhóm→main có ởĐối soát, nhưng người đọc dòngmain/trace không lần ngược đượcnhómresolved/isolated vàrawtổngliênquan ngaytạiđó. Không phát hiện sai raw/groupmembership dođiềunày; là thiếu lớp trìnhbày/truyvết của G8 tiênlượng, không lýdo mở thêm12sheet hoặc đổi backend.01 chốt owner09 khép trong cácsheet đãcó trước nghiệmthu deliverable.
3. **[P2, usability] Coverage/quycách còn là JSON/khóa kỹ thuật.** boq.py:123,128–138 ghi `coverage.model_dump_json()` và ghépkhóa `stage/code/source/concrete_supply/lean_concrete_grade...`, tươngthích `resolved/isolated_unknown` nguyênmã. Có n/m côngtácđủ lượng nhưng chưa trình bày tiếng Việt rõ số códetail/aggregate/unavailable/nodetail, unknowncontribution/reference/compatibilitypending và ýnghĩa'đủ lượng'khác'quycách đã xácminh'. Dữliệu gốc không mất, không phải lỗi phép tính; chưa đủ dễkiểm cho người dùng G8 và nguy cơ đọccompatibilityresolvedlàđãduyệtthiếtkế. Giữmã/rawtruyvết, bổ sungnhãnViệt ởvùng đọcchính, không đổi grouping.

### Những điểm correctness đã đối chiếu

- boq.py:162 dùng enumerate(result.works), keyw:index không dựa thứtựsort sheetlegacy; locationsworkheading trước detailNonecontinue; rowlocations theo(key,row_id). Group member vàmissingrefs dùng trực tiếp summary, không định tuyến bằngrow_idtoàncục. Testmới cóđảoplan/sortkhác,2workcùngr1 vàmissingref đúngw:1. Chưa thấy lỗi original-index trongsnapshotđãđọc.
- Group rawknown/total/unit/compatibility dùngpayload, không gọi producer/builder/pricing, không sum lạiExcel. Signed Decimal dùngcopy_negate giữprecision; referenceblankđónggóp;0khácNone; partialtotalblank; no_detail không dựngfakecontributiontừdimensions. Numeric vượt15significantdigits/rangeblank+cảnhbáovàrawtextcòn nguyên. Caseformat sốnhỏ ởfinding1 là khoảnghở riêng.
- Legacy9sheet/export_for_optimizer không có hunk thayđổi nghiệpvụ, thêm consumer mới. Stringdetail ép celltype's' tránhformula; raw precision text và factor/conversion/dimension JSON đượcgiữtrace. Không tuyênbốgloballegacyformulasafe vì legacy_sheetwriter ngoài hunk.
- Đọc ZIP/XML của workbook SYNTHETIC bằng .NET chỉ đọc, không chạy app/renderer: sheet10/11 cósnapshothash nhưng0token g:index; sheet12 có7token g:index và'Tổng raw theo nhóm'. Xácnhậnartifact phù hợp code về vịtrínhóm; không thay visual/nativeQA. Rowheight cốđịnh48/60/72 vàspecnhiềudòng cầnkiểmrender/native riêng, chưa khẳngđịnhclipthực tế.

### Bằng chứng và giới hạn

Receipt/final.log ghi **18passed in8,26s,exit0** (17case BOQ và1legacyrebar assertion). Sourceafter2hash khớpbyte, nhưng receipt không cung cấp tậpdependency/hashbefore-after toànbackend như các lượt03; không gọi đây là243dependency0drift. Testbao serialization/reopen openpyxl, signed/reference/partial/precision/source/links/legacy, khôngtestmaingroupdeliverable/tracegroupid/coverageViệthoặcformat1e-16. ChưanativeExcel/render/print/ACTUAL/UIcùngsnapshot/HTTP/DB/full. Không dùng18test đểnghiệmthu trọnG8 hoặc giảđãđủtấtcảproducer/CPâm.

Đãbáofindingcho01, giữ09solewriter, khôngnhắn09ngoàiphạmviủyquyềnhiệncó.14chỉghidocsriêng, khôngsource/runtime/test. Chưađềnghịnghiệmthu exporter hoàn chỉnh khifindinghiểnthị vàgapdeliverablechưachốt.

Cập nhật01 xác nhận sau review: findingnumeric1e-16 phảiđóng trước nghiệmthu.09 xácnhận tựchuyển toàngroupblock sangĐốisoát chưađược01chốt; thiếukhốinhóm ởTiênlượng,group_id/member/missingrefs ởTruyvết vànhãnquycách/coverageđọctiếngViệt là **deliverable chưađủ**, khôngcònchỉđềxuấtusabilitytùychọn. Giữkếtluậnraw/groupmembershipđãxuấtkhôngthấysaitínhtronghunk. Báocáo này chốt trênđúng2hash7e090.../b68090...;01sẽrelease09sửacùng2file đãđượcuserduyệt,14khôngtựmởwriter/test/Excelnative.

### Exporter09 review2 — chốt đúng snapshot mới

Đã đối chiếu source và receipt `tmp/g8_summary_09_review2`: boq.py `7f23bd7aeb27a0747bb5c97c48430e73a5f353c4d3a6592f5ad1505c876ca4c5`; test `c0b85044a0714a749056b78d96d1a51c0c832d87c02b18aa72d7192c1e665156`. Hai hash vẫn khớp khi kết thúc review. Tám dependency liệt kê trong receipt trước=sau=checkout đều khớp; không tuyên bố toàn repo không drift.

Đã đọc final.log/receipt: **143passed in14,81s, exit0**. Attemptđầu140passed+3setupErrors/tmpdir là lỗi, không được nhận đạt. Chỉ đọc test/source/log, không tự chạy test hoặc mở Excel native.

- Findingnumeric đã khép: boq.py:79 chọn scientific cho0<abs(value)<1e-14; ±1e-16 giữ khác0/None. Testmới kiểmcellvalue,number_format vàrawtext. Chưavisualnative nhưng codeformat không còn fixed15decimal cho ca này.
- Main group đã có block nhóm/quycách/tổngraw vàmember links, không tự tính lại. boq.py:154–181 giữworkheading→group, groupmember→heading, trace→group vàmemberheading; originalw:indexkhôngsortlại. Trace18/19 cósummarygroupid vàmissingreason theo(key,row_id); row.group vẫnriêng, khônggánlẫnsummarygroupid. Cácgapmain/trace/refshai chiều đãkhép ởcode/testđãđọc.
- Nhãnfieldquycách vàresolved/isolatedunknown đãViệthóa trong136–159, giữmãgiátrịgốc. Legacywriter/optimizer không có hunk đổi trongchanges.diff review2; không thấy thêmphéptínhraw/residual hoặcđổi backendSUM.
- **Gap coverage còn lại,01 xác nhận phải khép:** boq.py:130–133 `_coverage_text` chỉ đủ/chưađủlượng,known/unknowncontribution,reference,nodetail. Chưa cócomponents/aggregate/unavailable/complete_components/compatibility_pending_works bằngtiếngViệt; các count chỉ cònJSONở139/169, perworkscope252 vẫncomponents/aggregate rawcode. Ca1workaggregatecomplete hiện'1/1côngtácđủlượng;0côngtácchưacódiễngiải' nhưng khôngnóichỉcótổng/chưađủchi tiếtcấukiện; dễnhầmquantitycomplete thànhcomponentcoverage. Đây làthiếu trìnhbàycoverage, không sai raw/model. Chỉ cầnhelpertext vàtesttrongcùng2file,khôngbackend/sheetmới.

Đãbáo01chốtreview2: numeric/main/trace đãkhép; chưanghiệmthucoveragehoànchỉnh.01sẽrelease09sửahelpertext+testvàfocusedBOQnhỏ,khôngyêucầulặp143chỉvìnhãntext. Lượtsau14chỉreviewgapcoverage trênhash/logmới,khôngreviewSUM/sourcecũlặp. Giữgiớihạn nativeExcel/render/print/ACTUAL/UIcùngsnapshot/API/DB/full chưakiểm.14khôngsource/runtime/test.

### Coverage cuối — chỉ review gap còn lại, 04/11/2026

Đã đối chiếu đúng hai hash mới với receipt/checkout: boq.py `d5240bf248a204e3be266acd673a06d2c0fa685491d19fabf63d957cae5c9007`; test_rough_boq_detail.py `b394a0f70d4b5024760f99f644adc80ca760f7ffd74b2f5e654bd9316caba4c5`. Artifact ở `tmp/g8_summary_09_coverage_final`. Đã đọc changes.diff, helpertext/perworklabel và4case test mới; không rà lại các mục numeric/main/trace đã khép hoặc SUM unchanged.

- boq.py:137–145 lấy nguyên coverage payload để diễn giải components/aggregate/unavailable/no_detail, complete_components vàcompatibility_pending_works bằng tiếng Việt. Scope rỗng ghi'Không có công tác để đánh giá'; không biến0/0thànhđủ cấukiện.
- Cùng helpertext xuất ở vùngchínhTiênlượng dòngnhóm tổng vàĐốisoát toànphạmvi/từngnhóm; perworkdetail_level tại264 đã dịch thành'Chi tiết theo cấu kiện'/'Chỉ có tổng'/'Chưa có chi tiết khả dụng', tách nhãnđủlượngtoànphạmvi.
- Caseaggregate1/1 đủlượng đồng thời'Chưa đủ chi tiết cấu kiện'; mixed2/4 hiểnthị đủbốncount và4côngtácchờquycách; componentfull1/1 vàempty0/0 cólabelđúng. Testkiểmmain/comparetextvàperworklabel, khôngthêmtínhtoáncoveragehoặctổngmới.

Gapcoverage đã khép ởcodevàpureconsumer evidence: final.log **25passed in9,97s**,receipt exit0;8dependency before/after trongreceipt khôngdrift. Không tìmfindingmới trongdeltahelpertext/testđượcgiao. Kếtluậnchỉtrênhashnày, khôngcoi25testlànativeExcel/render/runtime/ACTUAL/UIcùngsnapshotđãđạt.14khôngsource/test/nativeExcel; đãbáo01đểtiếpnhận code+pureconsumer theoquyền01.

## Bill _masonry — review 04/11/2026 theo yêu cầu01

Chỉ đọc materials.py/test_rough_materials.py, callers liên quan và receipt/log tại `reports/demo_0511/masonry_mortar_0411`; không rà SUM/Excel unchanged. Hai hash byte khớp tested/after trong receipt: materials.py `fc29185e25e80f9c90d0542d30d8e949fc501860d4cc74c9d30ae8a52830de63`; test `85ebbbfe1143298fa737966509b41561302a2505293b676ff5aa4743eb7161cfd`. Receipt không kèm isolated diff/basebytes; reviewer không dùng HEAD để quy toàn diff cho04.

Đã đọc focused.log **95passed in19,38s**,receipt exit0;6target gồm materials/takeoff/plaster/wallprocurement/finalwallgroups/price_source. Red12failed trướcfix giữ làred, không đạt. Chỉ có2file tested/afterhash, không tuyên bố dependency toànrepo0drift hoặcfullđãpass.

- materials.py:54–62 mortar_material fullmatch đầu vào mác duy nhất, không lấy số đầu từM75/M100 hoặcM75.5; tìm vật liệuMORTARunitm³ với boundary mác, khôngsubstring75→750/75.5. Inputkhôngkhớp không tự dùngmácmặcđịnh. Chưa xácminhđộđúngquycáchcủa catalogthực hoặc giải quyết mọi trườnghợp tênmácmơhồngoàidữliệuhiệncó.
- `_masonry`: thiếu wall_system_id hoặcIDkhôngcótrongview giữ2dòng nhu cầu gạch/liênkết chưa cósố, khôngdropbinder. Hệtườngcóratevữa nhưng thiếuid hoặcidkhôngởcatalog: giữq×rate m³ nếubiết,grade tronglabel/missing vàcompleteFalse/statusD,khônggiảlàvậtliệumua. Q0giữ0khácQNone;rateNonegiữunknown,khôngtựđổi0.
- Paramgradeđượctrim; khôngnhậpyêucầumác thìgiữvữatheohệđãchọn. Cógradevàvữahệunitm³thìchọnmácđúng bằnghelper;khôngtìmđượcgiữnhucầuD/thểtíchđãbiết,chứkhôngfallbackmãhệ. AAC/vữachuyên dụngunitkhácm³cógrade yêu cầu thìgiữpendingcompatibility,khôngtựđổiqualitésangvữatrộntạichỗ.
- Per_mâm/nonfiniteđượccoilàthiếu. Per_m0chỉbỏbinderkhinorm_codehoặcnorm_sourcecótext;0khôngnguồngiữunknownvàmissing. Đây làkiểmnguồnđượckhaibáo,khôngđộc lậpchứngminhnguồnthựcsựxácnhậnhệsố0.
- Knownpart/via/uses còn; w.missing/D đi quaBill.addlàincomplete,khôngthànhmualượngđủ. NhánhAE giữwaste_included truyềnđếnplaceholder hoặcBill.mortar;khôngnhânhaohụtlần2. Khôngsửaratevữa/địnhmứcAE/cấpphối hoặcđổiunitđểlàmmácđúng. Khiđịnhmứcthiếuvàmãvữahợplệ,lines_missinggiữmissingchooutputs;khônglấycấpphốiđủlàmchứngminhthểtíchvữađủ.
- Testmới cómácM50,unknown/malformedM999/M75-M100dạngslash/M75.5,thiếuid/unknownid/rate/Q0/QNone,0có/khôngnguồn,AACgradepending; khôngchạytestbởi14.

Không xác định blocker mới trong phạm vi Bill _masonry/matcher đã đọc; đãbáo01đểchốtgatecode. **Gapđườngkhácriêng giữnguyên:** final_wall_groups chỉ overridegradekhimãvữahệunitm³;AACunitkhácvẫncóthểgiữmãliênkếtmặcđịnhvớiyêucầumácchưaxácminh. Không nhận muavậtliệuAAC/optimizerđãđủchỉvìBillđãsửa hoặc95focusedpass;cầngatecompatibilityđườngđótheophâncông01. ChưaAPI/runtime/DB/OpenAI/nativeExcel/ACTUAL hoặcfull.14chỉreadonlysource/docsriêng,khôngsửa/chạytest.

## Guard AAC final_wall_groups — review gate hẹp 04/11/2026

Đã đọc wall_groups.py, test_final_wall_groups_ui.py, base .before.txt, receipt/red/focusedlog tại `reports/demo_0511/aac_guard_0411` và caller trả kếtquả takeoff. Hai hash exact khớp tested/after/bytecheckout: wall_groups.py `1197c1eda5d94812cbfc3a9b0893c47660c94925afe787926291a3d906d8395b`; test `7f4f24e2f29754f39ad3d68c48f90d7eb6237dcb153f1edd87d90615622b8979`. Mười hai dependency ngoài2file sửa before=tested=after=checkout đều khớp; không suy toànrepo0drift.

Đọc terminal04: **30passed in6,71s,exit0**; red9failed4passed giữ làred. Ba targetedfiles finalgroups/wallprocurement/roughpricesource; không dùngBill95/SUM/Excel cũ thaybằngchứngguardnày.14khôngchạytest.

- `_design_mortar` thêmguard rateNone/âm/nonfinite; rate0chỉreturnnooverride/noissue khi cónorm_codehoặcnorm_sourcekhôngtrống.0khôngnguồn giữissue,khônggiảunknownlà0. Cónguồnởđâylàcăn cứđãkhai báo,khôngđộc lậpkiểmđịnhmứcthật.
- Basebinderkhôngcómã/đơnvịhợplệ giữissue. Gradeđượctrim; vậtliệuliênkếtunitkhácm³(cóAAC/VU04) kèmgradeyêucầuchưaxácminh bịchặn,khôngfallbackmãmua. M³vớigradehợp lệvẫndùngmatcherđúngmác; malformed/khôngtìmđượcgiữissue. Vắnggradegiữmãthiếtkếhệtheohợpđồngcũ,nếurate/baseunitđủ.
- Issue tạiworkgiữplan/element/wall_system_id,helpergiữmãliênkết/mác. Khôngđổisystem/masonry_geometry/work.quantity; codeonlykiểmeligibilitytrướctạogroup. TestAAC+gạchcùngrequestxácnhậnwork/geometrygiữnguyênvàissueAACcóT1/W-AAC01-100/VU04/M75.
- Helperfinal_wall_groupscóthểgiữgroupvalidkháctrongkhiAACissue, nhưng caller takeoff.py:570–571 xuấtwall_groups=[]nếubấtkỳscopeissue/wallgroupissue; khôngxuấtmua một phần nhưtoànphạmviđủ. Work/totalsđãbiếtvẫnởpayload,khôngbịgatexóa.
- Rate0cónguồnkhôngcầnmãmua ởgate này; nhánhq0workkhôngsinhnhucầumuamới. Không sửa source/norm hoặcđổiquantity đểquaeligibility. Chưa testmọiunitđồngnghĩahoặcdữliệuthực; gate exactunit dùngcataloghiệncó.

**Không xác định blocker mới trongguardeligibility trênhashnày. GapAACmácởfinal_wall_groupscũđãkhép trongphạmvi này**, cócode+purefocusedđượccungcấp. Gatecodecuốithuộc01. Giữgapconsumerngoàiscope04đãbàn giao: advisoryUIchưađọcissuesđầyđủtrongnhánhworknull/reviewedcódata; pricing/problemvẫncóthểđòimortarởzero-source. KhôngnhậnAACtoànchuỗi/muathậtchỉvìguardđãkhép30test;khôngmởrộngsửaBill/SUM/Excel. Khôngruntime/DB/OpenAI/nativeExcel/full/ACTUALQA;14chỉdocsriêng/readonlysource.

## Chọn mác bê tông — review delta nhỏ 04/11/2026

Đã đọc đúng `reports/demo_0511/concrete_grade_0411/change.diff`, basehai file, receipt/red/focused và haihunk canonical. Hash materials.py `ae1f83bd9503788bf568ccb7482e8164fd8e7f7cc2624cd8fcedbc40fc5a4567`; test_rough_materials.py `47ceb93ce8a6a57ea60b129abd2e9f1bb904ddf384713753816d678ca5b48642` khớp tested=after=checkout. Mười bốn dependencyngoài2file sửa before=tested=after=checkoutđềukhớp. So textsource saukhiloạihaihàm `_grade_number`/`ready_mix_material` bằngbase; khôngràlạivữa/AAC/Excel/SUM unchanged.

Đọc focused.log **103passed in16,05s**,receipt exit0. Red13failed15passed46deselected làred, khôngnhậnđạt. Targetmaterials/takeoff/plaster; khôngfull/HTTP/DB/runtime.14khôngchạytest.

- `_grade_number` đổi searchlấysốđầusangfullmatchnguyêninput; chấpnhậnmácsốnguyên đơn(ví dụM250/250/mác250), khôngM250/M300,M250.5,M250,5,M250chốngthấmW8hoặcB250. KhôngB↔Mconversion.
- `ready_mix_material` fullmatchtên'Bê tông thương phẩm [mác] M250' vàchỉchophépchúthíchcấpBtrongngoặc. CatalogM250.5/M250,5/M250-M300dạngslash hoặcđiềukiệnthêmtênkhônglọtM250bằngtokenđầu. Bchỉlàchúthíchcatalogđãcó,khônglàcơsởsuyđổimácinput.
- Khôngkhớpready_mix→None; Billconcretehiệncógiữnhucầum³/grade/missing/knownquantity,khônggộplượngpendingvàoBT03. TestmớitáchCOTvàBE_TONG_LOTcảhaihướngmácxungđột,ready_mix/site_mix: workmácchưarõgiữ3m³D/khônggiá,workmácM250rõgiữ2m³riêng. Site_mixvẫnnorms_forexactvariantCSVhiệncó,khôngsửarate/cấpphốihoặcđổinormđểnhậninputmơhồ.
- HaihunkkhôngsửaBill/mortar/waste/AAC; helperđượcgọiởready_mix,khôngđổilogicnhánhsite_mix. Khôngtuyênbốđãxácminhcatalogquycách/mácchấtlượngthựchoặcmọicáchghitênngoàipatternđượcduyệt.

Khôngxácđịnhblockermới trongdeltađúnghashnày; đãbáo01đểchốtgatecodehẹp. Package `package_01_20261104T015156Z` làbaselineTRƯỚCfix,nênkhôngdùngđểchứngminhcómãmớihoặcruntime/fullđãkiểmfix. Rootfull05/appmetadata06vẫnchờuserduyệt;14khôngchạyhộ. Khôngsource/test/runtime/DB/OpenAI; giớihạnACTUAL/báogiámua/fullvẫnriêng.
