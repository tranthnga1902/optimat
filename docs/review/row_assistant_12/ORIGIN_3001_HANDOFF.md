# Bàn giao sửa Origin demo — 04/11/2026

Đã thực hiện đúng release hai tệp và xác nhận trực tiếp của người dùng tại01 (“Cho phép hai tệp và HTTP mock”). Chỉ thêm Origin chính xác `http://127.0.0.1:3001` trong allowlist API; không mở localhost:3001, port khác, wildcard/regex hay bỏ auth/cookie/hash/rate/local-demo opt-in.

## Mã thay đổi và hash

| Tệp | SHA-256 trước | SHA-256 sau |
|---|---|---|
| src/optimat/api/material_advisor.py | 285BCC1C885C3D2F0CB82F19C08E3FFE16F3FB674B47831453E726800A47293C | 3873672E507B0F30B029A9F1A9A4D8E4659C833B67CF813009C0611C7F14901D |
| tests/test_material_advisor_api.py | DA8774E7D0C5CAD03673E8532A3955A7480F335C0CD52BAFACE9E425AF26E53E | EEF33C6213829F704F36243FDD9742183D70D5A74588979DDFD995018FDC22CD |

Đã so trước/sau: agent/material_advisor.py, api/auth.py, config.py, agent/llm.py, api/main.py, catalog/pricing.py **không đổi hash**. Agent vẫn 463E8F88…0210E; main vẫn A28A10E1…531F9. Không ghi source UI/DB/runtime/env.

## Terminal và phạm vi kiểm

`.venv/Scripts/python.exe -m pytest tests/test_material_advisor_api.py -q -p no:cacheprovider -o faulthandler_timeout=20`

**8 passed in 7.97s, exit0.** Chạy riêng HTTP mock ngoài sandbox bằng action exec require_escalated đã được duyệt để TestClient tạo socketpair Windows. Không OpenAI/DB/CAD/full/replay hay chạy lại 26 logic.

Ca mới kiểm Origin chính xác tạo session và request cùng cookie/hash; thiếu cookie vẫn401, đổi context vẫn409; missing/empty/evil/127.0.0.1:3002/localhost:3001 đều403 cho hai route; disabled local-demo vẫn403, DB mode thiếu user vẫn401. Spy mock chứng minh chỉ một lượt hợp lệ gọi hàm tư vấn giả, mọi nhánh bị chặn không gọi model. Các ca cũ giữ kiểm expiry/hash/principal/key/error/rate/nullable revision.

## Bằng chứng

- ORIGIN_3001_BEFORE.json / ORIGIN_3001_AFTER.json: exact hash tám tệp trước/sau.
- ORIGIN_3001.patch: diff hai tệp, dựng snapshot test trước sửa và kiểm SHA khớp DA8774… trước khi xuất diff.
- ORIGIN_3001_HTTP.log: stdout/stderr terminal thật.
- ORIGIN_3001_RECEIPT.json: lệnh, kết quả, hash, nguồn thay đổi và phụ thuộc không đổi.

Chưa restart/nạp runtime, chưa browser hoặc xác nhận user-flow thực. Kết quả mock không chứng minh server ownership của client_snapshot hay đủ điều kiện mua. HANDOFF.md là baseline backend trước bản Origin này; dùng hai hash sau ở trên cho kiểm tích hợp tiếp theo.
