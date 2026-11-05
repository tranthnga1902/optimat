# Bàn giao giao diện hồ sơ và cửa sổ AI

## Phạm vi đã triển khai

17 sở hữu bốn tệp component: ProjectFilesPanel.tsx/.module.css và AssistantWindow.tsx/.module.css trong frontend/src/components. 02 sở hữu host inline/ProjectWorkspace/ProjectDossier/store/router;06 sở hữu API/DDL. Không sửa chồng host hoặc dùng admin API cho người dùng.

ProjectFilesPanel đã có DTO/props và bằng chứng lint/type/harness trong AUDIT_GIAO_DIEN_20261103.md. Hai tệp này giữ nguyên hash sau bàn giao để02 dùng adapter.

AssistantWindow là khung trình bày controlled:

```tsx
<AssistantWindow
  open={assistantOpen}
  onOpenChange={setAssistantOpen}
  title="AI hỗ trợ"
  context={/* tên dự án và bản kiểm đang dùng từ host */}
>
  {/* Nội dung hội thoại do owner AI cung cấp */}
</AssistantWindow>
```

Props export: open:boolean, onOpenChange:(open:boolean)=>void, title?:string, context?:ReactNode, children:ReactNode. Native dialog cung cấp cơ chế modal/focus; Escape và nút thu gọn gọi callback false; effect cleanup đóng dialog và trả focus cho nút đã mở nếu còn trong DOM. Nội dung vẫn được mount khi đóng; host quản lý hội thoại, phiên bản và vòng đời network. Component không tự gọi API, không lưu store, không tạo câu trả lời mẫu.

Khung desktop bên phải, lề16px; mobile lề12px theo 100dvh; header cố định trong khung và body cuộn riêng. Phần composer/lịch sử hội thoại do children của02/12 cung cấp; không gọi việc bọc một form hỏi đáp hiện tại là đã có hội thoại nhiều lượt.

Kiểm: ESLint AssistantWindow.tsx và TypeScript toàn frontend exit0/session5448. Harness tmp/ui17/check-assistant.cjs exit0 cho controlled/title/Escape/cleanup/returnfocus/closed state. Đây là kiểm với fake DOM refs; focus trap thật và viewport cửa sổ cần kiểm sau khi host ghép.

| Tệp | SHA256 |
|---|---|
| AssistantWindow.tsx | 27d7019d95f01a3e21c313cefdf7a819473d5690dc29fddd488199d59591b551 |
| AssistantWindow.module.css | e407c7c0af757c0daec162e17ba7da522c52062108ce7ae7041f794a430608de |

Đã gửi bàn giao props/paths/hash/check tới02 và01 bằng công cụ nhắn của dự án.

## Kiểm giao diện thực tế hiện tại

Theo release01: chỉ đọc tab Chrome riêng; không upload, save, Start, compute, DB, đổi đăng nhập hoặc gọi AI. Không dùng hồ sơ Tân Bình bị từ chối. Không dùng fixture làm bằng chứng E2E.

- Desktop1440×1000: form Thông tin công trình xuất hiện inline, không có dialog mở, không tràn ngang toàn trang. Trạng thái Hồ sơ gốc hiện “Máy chủ chưa cung cấp hồ sơ hoặc chức năng này”. API chưa E2E.
- Mobile390×844: có tràn ngang. Đã xác định label và select “Dự án đã lưu trên trình duyệt” rộng810px. Đã gửi02 sửa host theo yêu cầu danh sách mới; không dùng overflow-x:hidden che lỗi. Thanh menu mobile hiện chiếm phần đầu trang khá dài; chưa sửa shared Shell.
- Ảnh chụp thật tại reports/ui_17/ho-so-desktop-current.jpg, ho-so-mobile-current.jpg và ho-so-mobile-form-current.jpg. Ảnh là trạng thái đang tích hợp, không phải nghiệm thu hồ sơ đã xem đúng revision. Đã reset viewport sau chụp.
- Chưa có ảnh cửa sổ AI ghép trong sản phẩm; chưa kiểm upload/lưu server/mở đúng CAD revision/Start không reupload.06 báo migration chưa áp và adapter chưa hook runtime.02 giữ E2E sau readiness.

## Steering mới cần host/API thực hiện

**Đính chính ảnh của người dùng ngày04/11:** ảnh bảng danh sách phía trên gửi nhầm. Mẫu chính mới là bố cục desktop hai cột: danh sách dự án dọc bên trái (tìm kiếm/tạo/chọn), thông tin và hồ sơ nguồn của dự án được chọn bên phải. Mobile xếp dọc. Giảm biểu tượng và nội dung minh họa; không sao chép các tệp mẫu PDF/DWG/XLSX trong ảnh vào dữ liệu thật. Nội dung mô tả bố cục bảng trên/chi tiết dưới bên dưới đây là lịch sử đã bị thay thế.

01 đã release và17 đã hoàn tất `frontend/src/components/ProjectInfoSummary.tsx` cùng `.module.css`, read-only. Props: name:string,info:ProjectInfo,storageLabel?:string,sources?:Partial<Record<location|buildingType|floors|note|materialNeeds,ReactNode>>. Host02 cung cấp đúng nguồn hiệu lực cho từng trường; component không suy nguồn nhập tay. Trường chính có dữ liệu hiển thị gọn và đơn vị tầng; missing gom một nhãn; mô tả/nhu cầu dài dùng details native với preview2dòng, giữ nguyên toàn bộ nội dung. Không sửa host/API/store hoặc tạo dữ liệu minh họa. Đã bàn giao02/01 ghép pane phải theo ảnh mới, sau ca demo hoặc hunk trình bày độc lập.

ESLint riêng component và tsc toàn frontend exit0/session65407. Harness tmp/ui17/check-summary.cjs exit0: missing/no-default/read-only/unit/long-text/source-link/storage/input-unchanged. Chưa kiểm component này trong trang thực.

Hash TSX: `1b39758e4b03e344637993b3cd5ef029f2d361b0a3e7a9a2f5d98207174c8812`; CSS: `1ab3db36dd09dc5e560955d721b4154853ebfa37b4749279ca2e535e5570664d`.

Ngày04/11 người dùng gửi ảnh bảng công trình và phần thông tin phía dưới, yêu cầu giữ kiểu này nhưng giảm phần thông tin/minh họa. Hướng trình bày đã chuyển02/01: giữ bảng và trạng thái xem mặc định; thông tin chính gọn theo tên, địa điểm, loại công trình, số tầng; mô tả/nhu cầu dài chỉ mở rộng khi cần, không xóa dữ liệu gốc hoặc thay dữ liệu QA bằng số minh họa. Cột mô tả trong danh sách nên tóm tắt khoảng hai dòng, xem đủ tại chi tiết. Không thêm ảnh/card minh họa trang trí hoặc nhiều khoảng trống chỉ để lấp trang. Đây là cách hiểu đang áp dụng từ câu chữ và ảnh, không suy thành yêu cầu thay dữ liệu nghiệp vụ.

**Chỉ đạo người dùng mới nhất thay thế việc luôn hiện form edit:** mặc định hiển thị danh sách dự án theo chiều dọc. Bấm dự án mở chế độ xem thông tin và các tệp đi kèm. Cuối chi tiết có hai nút Sửa và Xóa. Chỉ khi bấm Sửa mới mở form inline; Lưu/Hủy quay về chế độ xem. Thêm dự án là hành động chủ động ở danh sách. Slot projectInfo của panel nhận nội dung chỉ đọc trong chế độ xem, không truyền form thường trực. Đã chuyển yêu cầu mới tới02/01;02 giữ sole writer host.

Người dùng yêu cầu Dự án của tôi hiển thị danh sách công trình; click công trình mở chi tiết/thông tin/hồ sơ đúng dự án, có Thêm/Sửa/Xóa. Form create/edit inline, không popup. Dùng bảng kiểu Excel, đường kẻ mờ và STT gọn. Đã chuyển yêu cầu này tới01/02/06.

Thao tác xóa chưa có hợp đồng server chốt về lịch sử, kết quả và tệp liên quan;06 đã ghi nhận giữ nguyên list/view/create/edit, chưa triển khai hoặc thử xóa. Không ghi xóa thành công khi chỉ xóa khỏi giao diện. Cần phản hồi/confirm rõ công trình bị xóa và không tự thử xóa dữ liệu trong QA chỉ đọc.
