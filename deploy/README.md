# Đưa OptiMat AI lên Internet (Windows + DuckDNS + Caddy)

Chạy ngay trên máy Windows đang có dự án, không cần Docker, miễn phí.
Người dùng mở `https://<tên>.duckdns.org`. Đường đi như sau:

```
Internet ──> router (mở port 80, 443) ──> máy này
             Caddy :80/:443 (HTTPS tự động, Let's Encrypt)
               └─> Next.js 127.0.0.1:3000 (giao diện)
                     └─ /api, /docs ─> FastAPI 127.0.0.1:8000 ─> PostgreSQL :5432
```

DuckDNS chỉ trỏ tên miền về IP nhà bạn. Tác vụ `OptiMat DuckDNS` báo lại IP 5 phút một lần khi nhà mạng đổi IP.

## Các file

| File | Việc |
|---|---|
| `duckdns.env` | tên miền + token DuckDNS (chép từ `duckdns.env.example`, không vào Git) |
| `duckdns.ps1` | báo IP hiện tại cho DuckDNS, ghi `duckdns.log` (`OK` là được, `KO` là sai tên/token) |
| `Caddyfile` | cấu hình Caddy: HTTPS cho `<tên>.duckdns.org`, chuyển vào cổng 3000 |
| `install.ps1` | chạy 1 lần (admin): cài Caddy, mở tường lửa, tạo 2 tác vụ Task Scheduler |
| `start.ps1` | chạy API + giao diện + Caddy ở chế độ ẩn; `-Build` để build lại giao diện |
| `stop.ps1` | tắt cả ba |
| `logs/` | nhật ký `api`, `web`, `caddy` (`*.err.log` là lỗi) |

## Cần có sẵn

- Dự án chạy được trên máy: `.venv` đã `pip install -r requirements.txt`, `frontend` đã `npm install`,
  `.env` có `DATABASE_URL`, PostgreSQL đang chạy.
- Quyền đăng nhập router (mật khẩu in trên tem dưới modem, không phải mật khẩu wifi), hoặc nhờ tổng đài nhà mạng mở port.
- IP WAN trên router trùng IP public (xem ở https://api.ipify.org). Khác (thường `100.x`, `10.x`) là CGNAT: cách này
  không dùng được, xem mục cuối.

## Các bước

### 1. Tạo tên miền DuckDNS

1. Vào https://www.duckdns.org, đăng nhập bằng Google/GitHub.
2. Gõ tên vào ô **sub domain** (vd. `optimat`), bấm **add domain**. Ô *current ip* tự điền IP nhà bạn.
3. Chép **token** ở đầu trang.

### 2. Điền `duckdns.env`

Chép `duckdns.env.example` thành `duckdns.env`, sửa:

```
DUCKDNS_DOMAIN=optimat
DUCKDNS_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Chỉ ghi phần trước `.duckdns.org`. Ghi cả `optimat.duckdns.org` thì Caddy xin chứng chỉ cho `optimat.duckdns.org.duckdns.org`.

### 3. Tạo tài khoản quản trị TRƯỚC khi mở ra Internet

Khi database chưa có admin, ai mở `/dang-nhap` cũng tạo được admin. Tạo ngay trên máy:

```powershell
cd C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai
.venv\Scripts\python.exe scripts\create_admin.py --email <email-cua-ban>
```

### 4. Cài đặt (1 lần, quyền admin)

Trong PowerShell thường, chạy lệnh dưới, bấm **Yes** ở hộp thoại UAC:

```powershell
Start-Process powershell -Verb RunAs -ArgumentList '-NoExit -ExecutionPolicy Bypass -File "C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai\deploy\install.ps1"'
```

Script cài Caddy (winget), mở tường lửa Windows cổng 80/443, tạo tác vụ `OptiMat DuckDNS` (5 phút/lần) và
`OptiMat Start` (tự chạy ứng dụng khi đăng nhập Windows), rồi gọi DuckDNS một lần. Cuối cùng phải in dòng có `OK`.
Đã chạy bản cũ của `install.ps1` thì chạy lại: tác vụ được ghi đè, thêm thiết lập chạy cả khi dùng pin và chạy bù khi máy thức dậy.

### 5. Mở port trên router

Vào `http://192.168.1.1` (địa chỉ ở dòng *Default Gateway* của `ipconfig`), tìm mục:

- ZTE (modem Viettel F670Y, H196A…): *Internet* → *Security* → *Port Forwarding*
- Huawei (HG8045, EG8145…): *Forward Rules* → *Port Mapping Configuration*
- TP-Link: *Forwarding* / *NAT* → *Virtual Servers*
- VNPT, FPT: *Advanced* → *NAT* → *Port Forwarding* / *Virtual Server*

Thêm 2 dòng, giao thức TCP, IP trong là IP LAN của máy này (dòng *IPv4 Address* của `ipconfig`, vd. `192.168.1.35`):

| Cổng ngoài | Cổng trong |
|---|---|
| 80 | 80 |
| 443 | 443 |

Có ô *WAN Connection* thì chọn kết nối có chữ INTERNET. Bấm Apply/Save.

Nên đặt IP cố định cho máy (mục *LAN* → *DHCP* → *Static IP* / *Address Reservation*, gán IP trên cho MAC của máy;
MAC xem bằng `getmac`), nếu không router có thể cấp IP khác sau khi khởi động lại và port trỏ nhầm máy.

Không vào được router: gọi tổng đài (Viettel 18008168), nhờ "mở port 80 và 443 về IP 192.168.1.35". Không reset modem.
Modem nhà mạng cắm thêm một router wifi: phải mở port trên cả hai (modem trỏ về IP WAN của router wifi).

### 6. Chạy

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Admin\Downloads\optimat-ai_6\optimat-ai\deploy\start.ps1
```

Lần đầu `start.ps1` thêm `OPTIMAT_SECRET_KEY` vào `.env` (khóa cố định để người dùng không bị đăng xuất mỗi lần khởi động)
và build giao diện nếu chưa có. Từ lần sau, tác vụ `OptiMat Start` tự chạy khi bạn đăng nhập Windows.

### 7. Kiểm tra

1. `nslookup <tên>.duckdns.org` ra đúng IP public.
2. Trên máy: http://127.0.0.1:3000/api/health trả `"status": "ok"`.
3. `logs\caddy.err.log` có dòng `certificate obtained successfully`. Còn `Timeout during connect` là từ ngoài chưa vào được
   (port router, tường lửa, nhà mạng chặn). Caddy tự thử lại, không cần chạy lại gì.
4. Mở `https://<tên>.duckdns.org` bằng **4G** trên điện thoại. Thử bằng wifi nhà có thể không vào được dù từ ngoài vẫn vào
   được (router không hỗ trợ NAT loopback).

## Vận hành hằng ngày

| Việc | Lệnh (thư mục `optimat-ai`) |
|---|---|
| Tắt | `powershell -ExecutionPolicy Bypass -File deploy\stop.ps1` |
| Bật | `powershell -ExecutionPolicy Bypass -File deploy\start.ps1` |
| Sửa mã Python | tắt rồi bật |
| Sửa mã giao diện | tắt rồi bật với `-Build` |
| Xem lỗi | `Get-Content deploy\logs\api.err.log -Tail 50` (thay `web`, `caddy`) |
| Xem DuckDNS | `Get-Content deploy\duckdns.log` |

Máy phải bật và không ngủ thì trang mới chạy: *Settings* → *System* → *Power* → *Screen and sleep* → **Sleep: Never**
khi cắm điện. Ứng dụng chỉ tự chạy sau khi bạn đăng nhập Windows (bật máy mà chưa đăng nhập thì chưa có trang).

## Lỗi thường gặp

| Hiện tượng | Nguyên nhân, cách sửa |
|---|---|
| `install.ps1` báo `#requires ... Administrator` | chưa chạy quyền admin, dùng lệnh ở bước 4 |
| `duckdns.log` ghi `KO` | sai tên miền hoặc token trong `duckdns.env` |
| Caddy `Timeout during connect` | chưa mở port router / nhà mạng chặn port 80, 443 (gọi tổng đài) |
| Caddy `too many failed authorizations` | Let's Encrypt khóa tạm sau ~5 lần hỏng/giờ, chờ 1 giờ |
| `502 Bad Gateway` | giao diện chưa chạy: xem `logs\web.err.log`, chạy lại `start.ps1` |
| Trang mở được nhưng báo lỗi API | xem `logs\api.err.log` (thường do PostgreSQL chưa chạy hoặc sai `DATABASE_URL`) |
| `start.ps1` báo cổng đang dùng | đang chạy sẵn: `stop.ps1` rồi `start.ps1` |
| Chữ tiếng Việt trong script bị lỗi font | file `.ps1` phải lưu UTF-8 có BOM (PowerShell 5.1) |

## Bảo mật khi mở ra Internet

- Tạo admin trước khi mở port (bước 3).
- API của người dùng thường chưa bắt đăng nhập (`api/auth.py` chỉ chặn `/api/admin/*`): ai có địa chỉ cũng dùng được
  đo bóc, tối ưu, tải bản vẽ lên (giới hạn 50 MB x 20 file một lần). Chỉ gửi địa chỉ cho người cần dùng.
- `/docs` (tài liệu API) mở công khai.
- `.env`, `duckdns.env` chứa mật khẩu và token: không gửi, không đưa lên Git (đã có trong `.gitignore`).

## Không mở được port (CGNAT, không có quyền router)

Dùng **Tailscale Funnel** (miễn phí, không cần mở port): địa chỉ dạng `https://<máy>.<tên>.ts.net`, không dùng DuckDNS và Caddy.
Cài Tailscale, đăng nhập, bật Funnel trong trang quản trị Tailscale, rồi chạy `start.ps1` (Caddy báo lỗi cổng thì bỏ qua) và:

```powershell
tailscale funnel --bg 3000
```
