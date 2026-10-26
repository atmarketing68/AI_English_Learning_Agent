# Việc chủ dự án cần làm — AI AGENT ENGLISH

> Danh sách để đánh dấu dần. Mỗi việc ghi **làm ở đâu**, **từng bước**, **biến cần dán**, và **cách kiểm tra**.
> Khoá bí mật **không bao giờ** dán vào code hay gửi công khai — chỉ dán vào Render / Vercel / GitHub Secrets.
> Cập nhật: 2026-10-27 (sau G11). Mỗi giai đoạn mới Claude sẽ bổ sung vào file này.

Ba nơi bạn sẽ dán cấu hình:

| Nơi | Đường đi | Dùng cho |
|---|---|---|
| **Render** (máy chủ API) | render.com → dịch vụ `agen-api` → **Environment** → Add Environment Variable → **Save, rebuild and deploy** | Hầu hết các khoá (AI, email, thanh toán, Zalo…) |
| **Vercel** (trang web) | vercel.com → dự án `ai-english-learning-agent` → **Settings → Environment Variables** → thêm cho *Production* → **Redeploy** | Các biến bắt đầu bằng `NEXT_PUBLIC_` |
| **GitHub Secrets** (lịch chạy tự động) | github.com → repo → **Settings → Secrets and variables → Actions → New repository secret** | Nhắc học, Content Factory, nhắc câu lạc bộ nói |

Thay `<api>` bằng địa chỉ backend Render thật (vd. `https://agen-api.onrender.com`) và `<web>` bằng địa chỉ web Vercel thật.

---

## Mức 1 — Bắt buộc để app chạy đủ cơ bản

- [ ] **1.1 Khoá AI** (bài học, chấm viết/nói, Hỏi Bo, podcast…) — Render:
  - `GEMINI_API_KEY` — lấy ở aistudio.google.com → Get API key. *(ưu tiên, rẻ)*
  - `OPENAI_API_KEY` — platform.openai.com → API keys. *(dự phòng khi Gemini lỗi; có thể bỏ trống)*
  - Kiểm tra: đăng nhập web → tạo 1 bài học mới; tab **Chi phí AI** ở `/admin` có lượt gọi.
- [ ] **1.2 Địa chỉ web/API khớp nhau**
  - Render: `APP_URL` = `<web>`; `ALLOWED_ORIGINS` = `<web>` (nhiều địa chỉ cách nhau bằng dấu phẩy); `API_PUBLIC_URL` = `<api>`.
  - Vercel: `NEXT_PUBLIC_API_URL` = `<api>/api/v1` → Redeploy.
  - Kiểm tra: mở `<web>`, đăng ký tài khoản mới không báo lỗi mạng.
- [ ] **1.3 Tài khoản quản trị** — Render: `ADMIN_EMAILS` = email của bạn (nhiều email cách nhau dấu phẩy).
  Kiểm tra: đăng nhập email đó → vào `<web>/admin` thấy các tab Doanh thu, Chi phí AI, Đề thi, Podcast AI.
- [ ] **1.4 Lịch chạy tự động (cron)**
  1. Render: `REMINDER_CRON_SECRET` = một chuỗi ngẫu nhiên dài (vd. tạo bằng `python -c "import secrets; print(secrets.token_hex(24))"`).
  2. GitHub Secrets: `REMINDER_API_URL` = `<api>`; `REMINDER_CRON_SECRET` = **cùng giá trị** ở bước 1.
  3. Kiểm tra: GitHub → **Actions** → *Learning reminders* → **Run workflow** → chạy xanh. Làm tương tự với *Content Factory* và *Speaking club reminders*.
  - Ba lịch dùng chung 2 secret này: nhắc học + email phụ huynh + cảnh báo chi phí AI (mỗi giờ), Content Factory (2 giờ/lần), nhắc câu lạc bộ nói (10 phút/lần, 6:00–23:00 giờ VN).
- [ ] **1.5 Nâng Premium thử (pilot)** — Render: `ALLOW_DEMO_UPGRADE=true` khi chưa có cổng thanh toán thật. **Đổi thành `false`** ngay khi bật VNPay/MoMo/Stripe.

## Mức 2 — Nên bật sớm (tăng giữ chân người học)

- [ ] **2.1 Thông báo đẩy trên web (nhắc học, phụ huynh, câu lạc bộ nói)**
  1. Tạo khoá: chạy `python agen-backend/scripts/generate_vapid_keys.py` (hoặc dùng khoá Claude đã gửi trong chat).
  2. Render: `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` = `mailto:atmarketing68@gmail.com`.
  - Kiểm tra: Hồ sơ → Nhắc học → bật thông báo → bấm "Gửi thử". *Đổi khoá về sau thì người học phải bật lại thông báo.*
- [ ] **2.2 Email (nhắc học, báo cáo phụ huynh, cảnh báo chi phí AI)**
  1. resend.com → thêm và xác minh tên miền (thêm bản ghi DNS theo hướng dẫn của Resend).
  2. Render: `RESEND_API_KEY`, `EMAIL_FROM` = vd. `AI AGENT ENGLISH <hoc@tenmiencuaban.vn>`.
  - Kiểm tra: Hồ sơ → Nhắc học → bật email → "Gửi thử".
- [ ] **2.3 Analytics PostHog** — posthog.com → Project settings → Project API key. Vercel: `NEXT_PUBLIC_POSTHOG_KEY` (tuỳ chọn `NEXT_PUBLIC_POSTHOG_HOST`, mặc định máy chủ US) → Redeploy.

## Mức 3 — Thu tiền

- [ ] **3.1 VNPay** (thẻ ATM / QR trong nước)
  1. Đăng ký merchant VNPay → nhận `TMN code` và `Hash secret`.
  2. Render: `VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET`, `VNPAY_URL` = `https://pay.vnpay.vn/vpcpay.html` (bỏ trống = sandbox thử).
  3. Khai báo với VNPay địa chỉ IPN: `<api>/api/v1/billing/vnpay/ipn`.
- [ ] **3.2 MoMo**
  1. Đăng ký doanh nghiệp MoMo → `Partner code`, `Access key`, `Secret key`.
  2. Render: `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY`, `MOMO_SECRET_KEY`, `MOMO_ENDPOINT` = `https://payment.momo.vn` (bỏ trống = môi trường test).
- [ ] **3.3 Stripe** (thẻ quốc tế, giá USD)
  1. stripe.com → Developers → API keys → **Secret key** (`sk_live_…`).
  2. Developers → Webhooks → Add endpoint `<api>/api/v1/billing/stripe/webhook`, chọn các sự kiện:
     `checkout.session.completed`, `checkout.session.expired`, `checkout.session.async_payment_succeeded`,
     `checkout.session.async_payment_failed`, **`charge.refunded`** → lấy **Signing secret** (`whsec_…`).
  3. Render: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`; tuỳ chọn `USD_TO_VND` (mặc định 25000, chỉ để thống kê).
  - Kiểm tra: trang `/upgrade` hiện nút "Thẻ quốc tế".
- [ ] **3.4 Sau khi bật cổng thật:** Render `ALLOW_DEMO_UPGRADE=false`.
- [ ] **3.5 Thông tin người bán in trên biên nhận** — Render: `SELLER_NAME` (mặc định "AI AGENT ENGLISH"), `SELLER_TAX_CODE`, `SELLER_ADDRESS`, `SELLER_EMAIL`.

## Mức 4 — Bật khi cần (tính năng nâng cao)

- [ ] **4.1 Chấm phát âm đến từng âm (Azure)** — portal.azure.com → tạo *Speech service* (vùng Southeast Asia) → Keys and Endpoint.
  Render: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` = `southeastasia`. Lần đầu bật: thử 1 câu ở Luyện nói và xem log Render.
- [ ] **4.2 Zalo OA (nhắc học qua Zalo)**
  1. Tạo Zalo Official Account (loại Doanh nghiệp, đã xác thực).
  2. developers.zalo.me → tạo ứng dụng → bật API Official Account → lấy **App ID**, **App Secret**.
  3. Cấp quyền OA cho ứng dụng → lấy **refresh token** (Công cụ OA → API → Lấy access token).
  4. Render: `ZALO_APP_ID`, `ZALO_APP_SECRET`, `ZALO_OA_ID`, `ZALO_OA_REFRESH_TOKEN`, `ZALO_OA_SECRET_KEY`.
  5. Khai báo webhook `<api>/api/v1/zalo/webhook` với sự kiện `user_send_text`, `follow`, `unfollow`.
- [ ] **4.3 App di động (Android / iOS)** — làm theo `docs/MOBILE_APP.md` trên máy có Android Studio / Xcode. Tài khoản Google Play (25 USD một lần), Apple Developer (99 USD/năm).
  Push trên app: Firebase console → Project settings → Service accounts → Generate new private key → dán **nguyên nội dung file JSON** vào Render `FIREBASE_SERVICE_ACCOUNT_JSON`.
- [ ] **4.4 Giọng đọc miễn phí tự host (Voicebox)** — chỉ khi có máy chạy 24/7: `VOICEBOX_URL`, `VOICEBOX_PROFILE_ID` (+ `VOICEBOX_PROFILE_ID_MALE`, `VOICEBOX_API_KEY`). Chi tiết ở `docs/ROADMAP_STATUS.md` mục G2.

## Mức 5 — Kiểm soát chi phí AI (khuyên đặt khi có người dùng thật)

- [ ] **5.1 Cảnh báo chi phí** — Render: `AI_ALERT_DAILY_USD` (vd. `5` = báo khi cả app tốn quá 5 USD/ngày), `AI_ALERT_USER_DAILY_USD` (vd. `0.5` = báo khi 1 tài khoản tốn quá 0,5 USD/ngày). Email gửi tới `ADMIN_EMAILS` (cần mục 2.2), tối đa 1 lần/ngày mỗi ngưỡng.
- [ ] **5.2 Giới hạn cứng mỗi người/ngày** — Render: `AI_DAILY_LIMIT_USD_FREE` (vd. `0.2`), `AI_DAILY_LIMIT_USD_PREMIUM` (vd. `1`). Vượt mức thì tính năng AI dùng phương án dự phòng tới hôm sau. `0` = không giới hạn.
- [ ] **5.3 Đơn giá để ước tính đúng** (tuỳ chọn, USD / 1 triệu token): `AI_PRICE_GEMINI_IN`, `AI_PRICE_GEMINI_OUT`, `AI_PRICE_OPENAI_IN`, `AI_PRICE_OPENAI_OUT`, `TTS_PRICE_PER_MCHAR`.
- Giọng đọc: `TTS_DAILY_CHAR_LIMIT` (mặc định 150.000 ký tự mới/ngày); tắt hẳn bằng `TTS_PROVIDER=off`.
- Hạn mức miễn phí: `FREE_DAILY_LESSON_LIMIT` (bài/ngày), `TUTOR_FREE_DAILY_LIMIT` (câu hỏi Bo/ngày, mặc định 5).

---

## Việc vận hành định kỳ (không cần cấu hình)

| Việc | Ở đâu | Bao lâu một lần |
|---|---|---|
| Duyệt đề thi AI sinh | `/admin` → **Đề thi** → Sinh bản nháp → đọc đáp án → Duyệt | Khi muốn thêm đề |
| Duyệt tập podcast AI sinh (+ gắn video YouTube khớp lời thoại nếu có) | `/admin` → **Podcast AI** | Khi muốn thêm tập |
| Xuất hoá đơn VAT cho doanh nghiệp | `/admin` → **Doanh thu** → "Đơn hàng & hoá đơn VAT": xuất trên phần mềm HĐĐT của bạn (Viettel/MISA…) rồi bấm "Đánh dấu đã xuất" | Khi có đơn yêu cầu |
| Hoàn tiền | `/admin` → **Doanh thu** → **Hoàn tiền**. Stripe hoàn tự động; VNPay/MoMo: hoàn trên cổng trước rồi bấm để ghi nhận | Khi khách yêu cầu |
| Xem chi phí AI, người dùng tốn nhiều | `/admin` → **Chi phí AI** | Hằng tuần |
| Xem chất lượng AI (bài bị gắn cờ) | `/admin` → **Chất lượng AI** | Hằng tuần |
| Kiểm tra lịch tự động còn chạy | GitHub → **Actions** (3 lịch: nhắc học, Content Factory, nhắc câu lạc bộ nói) | Hằng tuần |

## Lưu ý khi deploy

- Merge PR = deploy production (Vercel + Render tự build). Render tự chạy migration cơ sở dữ liệu khi khởi động.
- Render gói **free** ngủ sau 15 phút không có truy cập; lịch nhắc câu lạc bộ nói (10 phút/lần ban ngày) giữ máy thức trong khung 6:00–23:00 — vẫn nằm trong 750 giờ miễn phí/tháng nếu chỉ có 1 dịch vụ free. Muốn luôn nhanh: nâng Render lên gói Starter (~7 USD/tháng).
- Mất khoá VAPID: tạo lại bằng script ở 2.1 (người học phải bật lại thông báo).

## Câu hỏi còn chờ bạn quyết định

- Số liệu trên landing ("1.247 học viên", "4,9 sao", lời đánh giá) là thật hay cần thay?
- Bảng giá trên landing: giữ hay ẩn tới khi có thanh toán thật? Giá 99K/tháng – 799K/năm có giữ không?
