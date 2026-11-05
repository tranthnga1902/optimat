# QA hồ sơ dự án trước phân tích

## Ưu tiên đầu vào — criteria trước/sau chờmanifest00

00solewriterProjectFilesPanel.tsxrole/scope/missing/chặnchỉKC theoexistingprojectcontract;06/03readonlyđềxuấtKCđộc lập/file-tờ/sectionlinks,07đốichứngVN002. QA15chờexactmanifest/base/afterhash+scopeđượcgiao,khôngtựsửa00/sourcehoặctestfull/DB/CADactual/UIlive. Rootgiữdraft/runtimenotpromoted.

| ID | Trước/sau cần bằng chứng | Oracle |
|---|---|---|
| IN01 P0 | Cùngfile/version đổi role KT/KC/HO_SO/TIEN_LUONG/THAM_KHAO | Rolekhácformat;hist/sourcebyteshashgiữ,selectedrevisionđúng;khônggánrole từtênđểtựđủgate |
| IN02 P0 | Chọnsubsetfile/revision rồiđổiscope,thiếubắtbuộc | Missingtheoexistingcontract,khôngfakedata/role/confirmed;giữdraftngoàiscope vàtracekhireopen |
| IN03 P0 | ChỉKC,KT+KC,KT-only,PDF-only theo readercapability | Vớicontractprojecthiệncó,chỉKCkhôngđượcStartnhầmKTpipeline;hiệnlýdo/cầnthêmfile rõ. KhônglấychặnUI làmchứngminhbackendfailclosed,khôngđồngnhấtKCđộc lậpđềxuất vớisupportedđãáp |
| IN04 P0 | File/tờ/sectionlinks vànguồnmâu thuẫn | Chỉbindlocatorscónguồn/đúngfileversion,khôngglobalnearest/khôngtựbùslab/height/section;missing/ambiguousgiữđúngscope |
| IN05 P0 | Đổi project/version/roletronglúcpreview hoặcchuẩnbịStart | Stale/identityguard/P0draftkhôngregress;khônganalysisngoàiýđịnh/khôngreloaduserdraft |
| IN06 P1 | Mô tảnguồn/capability/missingtrướcStart | Đọcđược dữliệueffective sooriginal,táchmanual/design,khônggiấuKCpending hoặcclaimprojectaccepted |

Cầnsource/harnessreceiptbeforeaftercùngfixturemanifest,kếđóUIchỉsaulease01. QA36P0,worklistSSR/browserSYN,toolbarfixture làreceiptriêng,khônggộpclaimđầuvào/Projectaccepted/ACTUAL. Chưaartifact00thìIN01–06NOT_RUN.

## Toolbar-only staticreview tronglúcchờworklist

Đọc `reports/cad_fallback_ui/toolbar-3001.patch` vàtoolbar-3002.patch:cùnghunkBoard,bổsungnative details/summary“Hiển thị và thu phóng”,chỉchứaNền/checkboxNhậndạng+Nhãn/rangezoom;Vừakhungchuyểnra trướcdetails. Chọn/Vẽ/Thêm khôngbịhunkwrap,nênstaticgiữnguyênoutside. Handlerbackground/toggles/zoomref/minmax/fitSizekhôngđổi. Khôngcopyglobals.css/chưareviewcsscanonical.

KeyboardSTATIC:native summary cóngữnghĩatoggle,bêntrongselect/checkbox/rangecólabel/aria;khôngcustompreventDefaulthaytabIndexbấtthườngtrongpatch. **ChưakiểmTab/Enter/Space/arrow/focus/zoomoutputthực**,khônggọikeyboardPASS. Chờ17fixtureQAroute actualBoard+dữliệuSYN để01cấpbrowserlease;khônginjectstorage/no3002reload/TânBìnhreupload. Khôngfindingblockerstatictrongtoolbar-onlydelta;layout/focusoverlay/canvasavailableheight cầnảnhfixturethực,khôngtuyênbốđãhếtchồngviewer.

Cập nhật reviewSAMPLE04/11:QA15 đã đọc receiptproject23/file127rev1/profile3+3ảnh+accesslog và kiểm hashdownloadkhớp;review tại WEBUI_FOUR_MILESTONES.md. Có bằng chứng chức năng save/reopen/original/preview/Startkhôngtăngupload,nhưng chưa requestbody/analysismanifest mappingrevision độc lập đầy đủ và chưavisualpass viewerhẹp/overlay. Các ca dưới là danh sách đầyđủ,không tự đổi toàn bộPF sangPASS;không runtimeQA15,khônguploadlại hoặcQS.

Nguồn: mục Đích gần nhất của kế hoạch ưu tiên. Tất cả ca NOT_RUN; QA15 docs-only, chờ01 giao lượt sau freeze. Dùng fixture được phép, không thử lại upload Tân Bình đã bị từ chối bằng bất kỳ công cụ nào; không full/TestClient/browser/API restart trong lượt chuẩn bị.

## Ca ưu tiên

| ID | Dữ liệu / thao tác dự kiến | Oracle |
|---|---|---|
| PF01 P0 | Tải hai bản V1/V2 có bytes/hash khác nhau (có thể cùng tên), gán KT/KC/tham khảo theo dự án | Giữ nguyên từng tệp nguồn, định danh/phiên bản và vai trò; không ghi đè nhầm bản hoặc dự án; hiện tên, định dạng, dung lượng, thời điểm tải, phiên bản, trạng thái đúng nguồn |
| PF02 P0 | Mở từng bản, zoom/pan và đóng/mở preview trước phân tích | Preview CAD dựng từ đúng nguồn, ghi rõ định dạng gốc; **không chạy đo bóc** chỉ vì upload/mở preview/zoom/pan; không tạo kết quả phân tích giả |
| PF03 P0 | Tải nguyên bản V1/V2 về từ mục xem; so hash với fixture | Bytes/hash khớp bản chọn, không tải nhầm preview thay bản gốc hoặc bản mới nhất thay bản cũ |
| PF04 P0 | Sửa/kiểm thông tin dự án, địa điểm, số tầng nếu biết và vai trò file; reload/mở lại dự án | Giữ thông tin và phiên bản chọn; phân biệt nhập tay, chữ bản vẽ và chưa xác định; không điền mặc định thành thông tin đo được |
| PF05 P0 | Chọn V1 thay vì V2, chọn KT/KC; bấm Bắt đầu phân tích | Chỉ nút chủ động khởi chạy; chuyển đúng project/file/version/role sang /do-boc bằng định danh tệp đã lưu, không yêu cầu chooser/upload lần hai; provenance kết quả trỏ đúng bản chọn |
| PF06 P0 | Đổi bản chọn khi preview/request cũ đang chờ, đổi dự án hoặc reload | Response cũ không áp vào bản/dự án mới; preview và lệnh phân tích giữ đúng phiên bản; receipt khối lượng cũ hết hiệu lực khi đổi nguồn hình học |
| PF07 P0 | Tài khoản không có quyền, không đăng nhập, hoặc ID file thuộc dự án khác | Backend chặn đọc nguồn/preview/download và phân tích; không chỉ ẩn nút frontend; không lộ bytes/metadata riêng. Mã HTTP cụ thể theo contract01 chốt |
| PF08 P0 | Fixture hợp lệ nhưng preview không hỗ trợ/lỗi dựng; nguồn còn nguyên | Hiện lý do và trạng thái preview lỗi; không giả ảnh trống là đã xem thành công; vẫn tải đúng nguồn nếu có quyền, không tự chạy bóc tách để thay preview |
| PF09 P0 | Lưu/upload hoặc chuyển phiên bản thất bại; thao tác lại theo release | Không báo thành công khi chưa lưu, không mất bản gốc đã có; thông tin dự án và file/version không trộn; không khởi chạy phân tích ngoài ý định |
| PF10 P0 | CAD fixture có hình học phân biệt rõ giữa V1/V2; mở preview | Có nội dung dựng từ CAD đúng bản và điều khiển xem; tên file/placeholder/metadata/history không được tính là preview thật |
| PF11 P0 | Ghi trace upload/mở preview/zoom/pan; chưa bấm phân tích | Không POST takeoff/recognize, không gọi LLM hoặc save_result; chỉ lưu nguồn/dựng preview theo contract, không tạo kết quả đo bóc |
| PF12 P0 | Người dùng thường mở dự án của mình và thử ID thuộc SYN20/owner khác; unauth/crossproject/path traversal | Dùng route người dùng được cấp quyền, không mượn admin route; backend chặn truy cập chéo owner/project và đường dẫn không hợp lệ, không lộ nội dung; status theo contract06/01 |
| PF13 P0 | Chọn bản rồi đổi version/project hoặc reset trong khi preview/phân tích đang chờ | Vô hiệu request/context/receipt liên quan; response cũ không khôi phục lựa chọn hoặc kết quả đã reset; analysis chỉ chạy trên storedFileId và version đúng context hiện hành |
| PF14 P0 | Nhập/sửa thông tin công trình và nhu cầu vật liệu tùy chọn qua ProjectInfo/ProjectBar hiện có; lưu/reload/mở lại | Thông tin lưu đúng dự án, giữ dấu tiếng Việt, không tạo form trùng hoặc hai bản mâu thuẫn; nhu cầu tùy chọn để trống không thành lỗi/giả định; không tự chạy phân tích |
| PF15 P0 | Đối chiếu thông tin nhập tay và thông tin từ hồ sơ gốc; sửa một giá trị | Hiện nguồn nhập tay hoặc đúng file+version+vị trí khi có; chưa có vị trí ghi rõ, không bịa. Giá trị sửa giữ nguồn/lịch sử gốc theo contract, không ghi đè bytes tài liệu hoặc đánh thành dữ liệu đọc trực tiếp |
| PF16 P0 | Chọn bộ dữ liệu phân tích gồm thông tin công trình, nhu cầu, file/role/version; xem lại rồi phân tích | Trước nút Bắt đầu phân tích thấy rõ bộ dữ liệu được chọn, không lấy ngầm bản mới nhất/nguồn dự án khác; thay lựa chọn cập nhật context và invalidation đúng; chỉ nút chủ động mới chạy |
| PF17 P0 | Hai nguồn khác phiên bản có thông tin khác nhau hoặc nhập tay ghi đè; lưu lỗi | Giữ phân biệt nguồn gốc và hiệu chỉnh, hiển thị xung đột/phần chưa xác định; không tự chọn số thuận tiện hoặc mất bản gốc. Lưu lỗi không báo thành công hay áp dữ liệu chưa lưu vào phân tích |
| PF18 P0 | Mở /du-an-cua-toi, click dự án, bấm Sửa, thử Lưu/Hủy | Mặc định danh sách dự án; click mở VIEW read-only thông tin công trình+tệp kèm. Cuối detail đúng hai nút Sửa/Xóa. Chỉ Sửa mới mở edit inline không popup; Lưu/Hủy về VIEW. Trường/giá trị/đơn vị/nguồn và trạng thái lưu/lỗi rõ |
| PF19 P0 | Bấm Thêm dự án ở list để chủ động mở create; lưu rồi rời/mở lại dự án | Không tự mở form tạo/sửa mặc định. Reopen đúng VIEW read-only có đủ thông tin/tệp/nguồn/version; không cần Sửa để đọc. Giữ bộ dữ liệu hiệu lực và CTA phân tích đúng context, không upload lại |
| PF20 P1 | Desktop theo ảnh user17 mới nhất; chọn lần lượt card dự án | SPLIT: list dọc trái có search/Thêm/card/active; detail phải gồm thông tin gọn và bảng hồ sơ gốc. Không dùng bảng list full-width phía trên. Active card và detail cùng dự án; ảnh mẫu chỉ là bố cục, không là dữ liệu nguồn |
| PF21 P1 | Mobile ở viewport do owner chốt, chọn dự án và mở detail/edit | List rồi detail, không overflow ngang hoặc cắt thao tác chính; giữ VIEW sau click chọn, Sửa mới EDIT inline, Save/Cancel về VIEW; Sửa/Xóa cuối detail theo text, không lấy vị trí trong ảnh thay chỉ đạo chữ |
| PF22 P0 | Dự án PDF-only: tạo/lưu/rời/mở lại, xem và tải nguồn | Hoạt động đúng project/revision theo reader thực có; không ép phân tích CAD để lưu/xem/download; PDF unsupported phải nêu khả năng thực và giữ tải nguồn đúng hash |
| PF23 P0 | Bộ CAD+PDF/Word+XLS/XLSX, gán role rồi mở lại | Role độc lập định dạng; giữ từng file/version, không mặc định mọi PDF là tham khảo hoặc mọi XLS là khối lượng bóc; preview/extract theo capability reader thực, unsupported ghi rõ, không giả nội dung đã đọc |
| PF24 P0 | Đổi role của một file qua các bản, đối chiếu source/history | Giữ lịch sử role và bytes/hash gốc; đổi role không thay nội dung, không nhập nhầm dữ liệu nguồn đối chứng vào kết quả đo bóc; chênh khối lượng giữ riêng chờ duyệt, không tự cân bằng hoặc ghi đè |
| PF25 P0 | Mở “Xem nguồn” của thông tin từ PDF/Word hoặc bảng XLS/XLSX; đổi version/owner | Trỏ đúng project/ownership/revision và page/sheet/ô/vị trí có thật; nếu chỉ biết tệp ghi đúng giới hạn, không bịa page/sheet. Crossrevision không gắn nhầm vị trí; backend chặn crossowner, không lộ nguồn |

## Bằng chứng và điều kiện nhận lượt

Cập nhật04/11 từ01: role contract đang chuẩn bị `KT | KC | HO_SO | TIEN_LUONG | THAM_KHAO` (backcompat), **chưa coi là schema release**. Nhận enum/migration/capability cuối từ06/01 trước chạy PF22–25. Phân biệt vai trò hồ sơ với định dạng và khả năng reader; lượng nguồn đối chứng khác lượng bóc, mọi chênh lệch phải giữ để duyệt. Bằng chứng cần file hash, role history, reader capability/unsupported và locator page/sheet đúng revision. Không tạo/upload fixture mới hoặc chạy runtime trước release; CAD23 chỉ02 thực hiện; native Excel NOT_RUN gate vẫn riêng.

01 cấp nguồn freeze, contract project/file/version/role và route preview/download/analyze; owner cung cấp hai fixture có quyền sử dụng và hai tài khoản test cô lập phù hợp. Không tự tạo account/quyền hoặc sửa DB để chuẩn bị. Ghi hash nguồn trước/sau; ảnh route và phiên bản; request timeline đã loại bí mật, bao gồm bằng chứng **không có lần gọi/tác vụ takeoff** trong khoảng upload/preview. Phân biệt endpoint dựng preview với endpoint/tác vụ đo bóc, không suy từ tên route hoặc tốc độ phản hồi.

Khi bấm phân tích, ghi request nhận ID phiên bản đã lưu, provenance response và network trace không gửi lại bytes/upload; hash tải nguyên bản đối chiếu V1/V2. Việc backend tự đọc lại tệp đã lưu không phải upload lại từ người dùng. Nếu runtime/contract chưa có, ghi BLOCKED và owner, không thay bằng mock rồi tuyên bố E2E.

01 chốt phân vùng:06 contract/API audit;17 component props riêng;02 host/handoff/store;01 chốt file windows. Nhận exact contract `analysisByStoredFileId`/định danh version từ owner, không tự suy endpoint hoặc áp tên method này thành route. Existing100HTTP admin chưa đạt là gói riêng, không dùng kết quả admin metadata/History để chứng minh feature người dùng upload/xem trước phân tích. Không truy SYN20 của owner khác để lấy dữ liệu demo; chỉ kiểm từ chối bằng tài khoản/fixture và lượt được phép.

Kịch bản demo nhận thêm theo00: nhập thông tin công trình/nhu cầu tùy chọn → lưu → reload/mở lại dự án → đối chiếu tài liệu gốc và nguồn → chọn rõ file/role/version/bộ dữ liệu → Bắt đầu phân tích. Ghi trạng thái trước nút và trace chứng minh các thao tác trước đó không auto analyze. Tái dùng ProjectInfo/ProjectBar; QA không tạo form hoặc sửa source. Contract lưu nguồn/override cần01/owner bàn giao trước thực thi, không tự đặt schema.

### Thứ tự bằng chứng inline bắt buộc theo chỉ đạo mới

**Chốt mới nhất từ01 theo user17 thay yêu cầu form luôn hiện trước đây:** LIST → click project → VIEW read-only; cuối detail đúng hai nút Sửa/Xóa; Sửa mới EDIT inline, Lưu/Hủy về VIEW. Thêm dự án ở LIST mở CREATE chủ động. Không thực hiện Xóa trong lượt chuẩn bị hoặc khi API chưa ready; kiểm vị trí/nút không đồng nghĩa được phép xóa. Native Excel NOT_RUN do permission timeout là gói riêng, không retry đường khác.

**Cập nhật 04/11/2026, ảnh user17 đúng thay ảnh gửi nhầm:** desktop SPLIT list trái/detail phải, mobile list→detail, theo PF20–21. Ảnh bằng chứng phải đủ thấy cấu trúc split và active card/detail tương ứng, thêm ảnh mobile có viewport và trạng thái VIEW/EDIT. Không sao chép tên file/số liệu trong ảnh mẫu thành nguồn thật. Hiện chỉ02 thực hiện ca server23; QA15 chưa được upload/Start/delete, chỉ chờ receipt/timeline để review độc lập. Không lấy tài liệu ca dự kiến thành bằng chứng đã thao tác.

Chỉ thực thi sau release01, với CAD mẫu được phép, không Tân Bình denied. Ghi cùng project ID và file/version xuyên các ảnh thực, không dựng mockup làm bằng chứng.

1. Chụp LIST mặc định; chủ động Thêm dự án nếu tạo mới hoặc click dự án để vào VIEW. Upload CAD fixture được phép trong luồng được owner triển khai; ảnh file/version và preview thật, chưa phân tích.
2. Chủ động CREATE hoặc bấm Sửa từ VIEW để EDIT inline không popup; chụp nhãn/giá trị/đơn vị/nguồn, lưu thành công và trở VIEW. Kiểm Hủy trở VIEW không áp draft; ca lỗi lưu riêng phải có trạng thái lỗi.
3. Rời trang rồi mở lại LIST → đúng dự án → VIEW read-only đầy đủ thông tin/tệp, không form always-open và không cần bấm Sửa để đọc; chụp đúng hai nút Sửa/Xóa cuối detail.
4. Đối chiếu tệp gốc đúng version, nguồn và dữ liệu hiệu lực đã chọn trên cùng trang; lưu hash download và trace chưa auto analyze.
5. Bấm Bắt đầu phân tích; ảnh/trace /do-boc nhận đúng file/version qua stored ID, không chooser/upload lại và không gửi lại bytes từ người dùng.

Thiếu một bước ghi riêng NOT_RUN/BLOCKED/FAIL, không gộp ảnh popup existing hoặc metadata/History thành demo inline đạt.

PF01–25 chưa kiểm sản phẩm bởi QA15. Chức năng hồ sơ trước phân tích không gỡ gate upload Tân Bình; mọi thử fixture chờ lượt được01 giao.
