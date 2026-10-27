# Việc chủ dự án cần làm — AI AGENT ENGLISH

> Danh sách để đánh dấu dần. Mỗi việc ghi **làm ở đâu**, **từng bước**, **biến cần dán**, và **cách kiểm tra**.
> Khoá bí mật **không bao giờ** dán vào code hay gửi công khai — chỉ dán vào Render / Vercel / GitHub Secrets.
> Cập nhật: 2026-10-27 (sau G13). Mỗi giai đoạn mới Claude sẽ bổ sung vào file này.

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
- [ ] **1.2b Gắn tên miền chính `aiagentenglish.com`** (đã chốt; code đã dùng làm địa chỉ gốc cho SEO, sitemap, ảnh chia sẻ)
  1. Vercel → dự án web → **Settings → Domains** → Add `aiagentenglish.com` và `www.aiagentenglish.com` → chọn chuyển `www` về `aiagentenglish.com`.
  2. Ở nơi mua tên miền (DNS): bản ghi **A** `@` → `76.76.21.21`; bản ghi **CNAME** `www` → `cname.vercel-dns.com` (đúng giá trị Vercel hiển thị ở bước 1). Chờ Vercel báo "Valid" (vài phút đến vài giờ).
  3. (Nên làm) API riêng: Render → `agen-api` → **Settings → Custom Domains** → `api.aiagentenglish.com`; DNS thêm **CNAME** `api` → `agen-api.onrender.com`.
  4. Render → Environment: `APP_URL=https://aiagentenglish.com`; `ALLOWED_ORIGINS=https://aiagentenglish.com,https://www.aiagentenglish.com` (giữ thêm địa chỉ `*.vercel.app` cũ nếu còn dùng để thử);
     `API_PUBLIC_URL=https://api.aiagentenglish.com` (nếu làm bước 3).
  5. Vercel → Environment: `NEXT_PUBLIC_API_URL=https://api.aiagentenglish.com/api/v1` (nếu làm bước 3), `NEXT_PUBLIC_SITE_URL=https://aiagentenglish.com` → Redeploy.
  6. GitHub Secrets: `REMINDER_API_URL=https://api.aiagentenglish.com` (nếu đổi API).
  7. Đổi các địa chỉ đã khai báo ở bên ngoài cho khớp: URL trả về/IPN của VNPay, MoMo; webhook Stripe; webhook Zalo OA; tên miền gửi email Resend (xác minh `aiagentenglish.com` để gửi từ `no-reply@aiagentenglish.com`).
  Kiểm tra: mở `https://aiagentenglish.com` có khoá 🔒, đăng ký/đăng nhập không báo lỗi mạng, `https://aiagentenglish.com/sitemap.xml` hiện đúng tên miền.
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
- [ ] **3.6 Hoá đơn điện tử Viettel S-Invoice** (tự xuất HĐĐT cho đơn đã thanh toán)
  1. Ký hợp đồng HĐĐT với Viettel (đã đăng ký mẫu số + ký hiệu hoá đơn với cơ quan thuế), xin **tài khoản tích hợp API** (username/password — thường username là MST).
  2. Hỏi kế toán: dịch vụ học trực tuyến của bạn chịu **thuế suất bao nhiêu** (0/5/8/10 %) hay **không chịu thuế**.
  3. Render: `EINVOICE_PROVIDER=viettel`, `VIETTEL_SINVOICE_USERNAME`, `VIETTEL_SINVOICE_PASSWORD`, `VIETTEL_SINVOICE_TAX_CODE` (MST, trống thì dùng `SELLER_TAX_CODE`),
     `VIETTEL_SINVOICE_TEMPLATE_CODE` (mẫu số, vd. `1/001`), `VIETTEL_SINVOICE_SERIES` (ký hiệu, vd. `C26TAA`),
     `EINVOICE_TAX_PERCENT` (`-2` = không chịu thuế — mặc định; hoặc `8`, `10`…), tuỳ chọn `EINVOICE_UNIT_NAME` (mặc định "Gói"), `EINVOICE_LOOKUP_URL` (trang tra cứu hoá đơn in trên biên nhận).
  4. Thử trước với môi trường **demo** của Viettel: đặt `VIETTEL_SINVOICE_API_URL` và `VIETTEL_SINVOICE_LOGIN_URL` theo địa chỉ demo Viettel cấp; xuất thử 1 đơn ở `/admin` → Doanh thu → **Xuất HĐĐT**; kiểm tra trên cổng Viettel rồi mới chuyển sang địa chỉ thật (mặc định đã là địa chỉ thật).
  5. Muốn tự động: `EINVOICE_AUTO=business` (chỉ đơn yêu cầu hoá đơn công ty) hoặc `all` (mọi đơn). Mặc định `off`.
  - Kiểm tra: dòng "HĐĐT Viettel: mẫu… ký hiệu…" hiện trên bảng đơn hàng; sau khi xuất, số hoá đơn hiện ở cột "HĐ điện tử" và trên biên nhận của khách.

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
  **G13 — không cần sửa code trong app:** web tự nhận ra đang chạy trong app và dùng plugin `@capacitor/push-notifications` (chỉ cần cài plugin khi đóng gói, bước 1 của `docs/MOBILE_APP.md`).
  Kiểm tra: mở app → đăng nhập tài khoản phụ huynh → trang Phụ huynh → thẻ **Thông báo trên điện thoại** → **Bật thông báo** → cho phép → nút đổi thành "Đang bật". Học viên: đăng nhập là app tự đăng ký.
- [ ] **4.4 Giọng đọc miễn phí tự host (Voicebox)** — chỉ khi có máy chạy 24/7: `VOICEBOX_URL`, `VOICEBOX_PROFILE_ID` (+ `VOICEBOX_PROFILE_ID_MALE`, `VOICEBOX_API_KEY`). Chi tiết ở `docs/ROADMAP_STATUS.md` mục G2.
- [ ] **4.5 Podcast tự sinh theo lịch** — Render: `PODCAST_AUTO_DRAFTS=2` (giữ 2 bản nháp chờ duyệt mỗi trình độ; `0` = tắt), tuỳ chọn `PODCAST_AUTO_LEVELS` (mặc định `A2,B1,B2`). Mỗi ngày vào `/admin` → **Podcast AI** nghe thử và duyệt các tập có nhãn "Tự động".

## Mức 4b — SEO (để Google lập chỉ mục đúng tên miền)

- [x] **4.6 Địa chỉ chính thức của web** — mặc định đã là `https://aiagentenglish.com` trong code; chỉ đặt `NEXT_PUBLIC_SITE_URL` trên Vercel nếu muốn tạm dùng tên miền khác.
  Kiểm tra sau khi gắn tên miền (1.2b): `https://aiagentenglish.com/robots.txt` và `/sitemap.xml` hiện đúng tên miền.
- [ ] **4.7 Google Search Console** — search.google.com/search-console → Thêm tài sản (*Tiền tố URL* = tên miền ở 4.6) → chọn xác minh bằng **Thẻ HTML** → chép giá trị `content="…"` →
  Vercel: `NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION` = giá trị đó → Redeploy → bấm Xác minh. Sau đó: **Sơ đồ trang web** → gửi `sitemap.xml`; **Kiểm tra URL** từng trang ở 4.8 → Yêu cầu lập chỉ mục.
  (Nếu xác minh bằng DNS ở nhà cung cấp tên miền thì bỏ qua biến này.)
- [ ] **4.8 Các trang nội dung đã có** (có trong sitemap): `/luyen-thi-ielts`, `/luyen-thi-toeic`, `/tieng-anh-cho-tre-em`, `/tieng-anh-giao-tiep`, `/lop-hoc-va-doanh-nghiep`.
  Sửa chữ: `agen-web/src/lib/seo/pages.ts` (tiêu đề, mô tả, nội dung, hỏi đáp). Ảnh chia sẻ mạng xã hội: `agen-web/public/og.png` (1200×630) — thay bằng ảnh thương hiệu nếu muốn.
  Khu vực sau đăng nhập đã chặn trong `robots.txt`; trang Đăng nhập/Đăng ký đặt `noindex`.
- [ ] **4.9 Gửi trang mới cho Google** (sau 4.7): trong Search Console → Kiểm tra URL → Yêu cầu lập chỉ mục cho `/cam-nang`, `/huong-dan-su-dung`
  và 4 trang con `/huong-dan-su-dung/nguoi-hoc|hoc-sinh|phu-huynh|giao-vien` (sitemap đã có sẵn). Kiểm tra: trang hiện ảnh chụp, không lỗi 404.
- [ ] **4.10 Gắn nguồn cho link quảng cáo** để bảng "Giữ chân" (admin) biết người dùng đến từ đâu: thêm `?utm_source=<tên>` vào link chia sẻ,
  ví dụ `https://aiagentenglish.com/?utm_source=facebook`, `…?utm_source=zalo`, `…?utm_source=tiktok`. Kiểm tra: đăng ký thử qua link → admin → tab Giữ chân → bảng Nguồn.
- Landing đã bỏ các số liệu/lời đánh giá chưa có thật. Khi có đánh giá thật của học viên (có đồng ý), sửa `agen-web/src/components/landing/LandingPage.tsx`.
- Ảnh hướng dẫn (`agen-web/public/guides/*.webp`) chụp từ dữ liệu mẫu; khi giao diện đổi nhiều, nhờ Claude chụp lại (xem `docs/HANDOFF.md` mục 6).

## Mức 5 — Kiểm soát chi phí AI (khuyên đặt khi có người dùng thật)

- [ ] **5.1 Cảnh báo chi phí** — Render: `AI_ALERT_DAILY_USD` (vd. `5` = báo khi cả app tốn quá 5 USD/ngày), `AI_ALERT_USER_DAILY_USD` (vd. `0.5` = báo khi 1 tài khoản tốn quá 0,5 USD/ngày). Email gửi tới `ADMIN_EMAILS` (cần mục 2.2), tối đa 1 lần/ngày mỗi ngưỡng.
- [ ] **5.2 Giới hạn cứng mỗi người/ngày** — Render: `AI_DAILY_LIMIT_USD_FREE` (vd. `0.2`), `AI_DAILY_LIMIT_USD_PREMIUM` (vd. `1`). Vượt mức thì tính năng AI dùng phương án dự phòng tới hôm sau. `0` = không giới hạn.
- [ ] **5.3 Đơn giá để ước tính đúng** (tuỳ chọn, USD / 1 triệu token): `AI_PRICE_GEMINI_IN`, `AI_PRICE_GEMINI_OUT`, `AI_PRICE_OPENAI_IN`, `AI_PRICE_OPENAI_OUT`, `TTS_PRICE_PER_MCHAR`.
- [ ] **5.4 Chế độ tiết kiệm (tự đổi mô hình rẻ hơn)** — Render: `AI_ECONOMY_AT_USD` (vd. `3`), `AI_ECONOMY_GEMINI_MODEL` và/hoặc `AI_ECONOMY_OPENAI_MODEL` = tên mô hình rẻ hơn (xem trang giá Google AI / OpenAI). Đổi mô hình thường bằng `GEMINI_MODEL`, `OPENAI_MODEL`. Sai tên mô hình tiết kiệm thì hệ thống tự quay về mô hình thường.
- Giọng đọc: `TTS_DAILY_CHAR_LIMIT` (mặc định 150.000 ký tự mới/ngày); tắt hẳn bằng `TTS_PROVIDER=off`.
- Hạn mức miễn phí: `FREE_DAILY_LESSON_LIMIT` (bài/ngày), `TUTOR_FREE_DAILY_LIMIT` (câu hỏi Bo/ngày, mặc định 5).

---

## Việc vận hành định kỳ (không cần cấu hình)

| Việc | Ở đâu | Bao lâu một lần |
|---|---|---|
| Duyệt đề thi AI sinh | `/admin` → **Đề thi** → Sinh bản nháp → đọc đáp án → Duyệt | Khi muốn thêm đề |
| Duyệt tập podcast AI sinh (+ gắn video YouTube khớp lời thoại nếu có) | `/admin` → **Podcast AI** | Khi muốn thêm tập |
| Xuất hoá đơn VAT cho doanh nghiệp | `/admin` → **Doanh thu** → "Đơn hàng & hoá đơn VAT": bấm **Xuất HĐĐT** (khi đã cấu hình Viettel, mục 3.6) — hoặc xuất trên phần mềm HĐĐT khác rồi bấm "Đánh dấu đã xuất" | Khi có đơn yêu cầu (hoặc để chế độ tự động) |
| Hoàn tiền đơn đã có HĐĐT | Lập hoá đơn điều chỉnh / huỷ trên cổng Viettel S-Invoice | Khi hoàn tiền |
| Hoá đơn VNPT / MISA | Chưa tích hợp (hai bên không công bố API). Nếu dùng VNPT/MISA: xin nhà cung cấp tài liệu API + tài khoản thử, gửi cho Claude để tích hợp như Viettel; trước đó xuất tay rồi bấm "Đánh dấu đã xuất" | Khi chọn nhà cung cấp |
| Hoàn tiền | `/admin` → **Doanh thu** → **Hoàn tiền**. Stripe hoàn tự động; VNPay/MoMo: hoàn trên cổng trước rồi bấm để ghi nhận | Khi khách yêu cầu |
| Xem chi phí AI, người dùng tốn nhiều | `/admin` → **Chi phí AI** | Hằng tuần |
| Xem chất lượng AI (bài bị gắn cờ) | `/admin` → **Chất lượng AI** | Hằng tuần |
| Duyệt đề Speaking AI sinh | `/admin` → **Đề thi** → "Sinh đề thi thử Speaking bằng AI" → xem trước → Duyệt | Khi muốn thêm đề nói |
| Hướng dẫn giáo viên giao bài kiểm tra lớp hằng tháng | Trang lớp của giáo viên → **Bài kiểm tra lớp** (chọn đề, ngày mở, hạn nộp) | Đầu mỗi tháng / khi mở lớp |
| Nhắc giáo viên đặt lịch câu lạc bộ nói cho lớp | Trang lớp của giáo viên → "Câu lạc bộ nói hằng tuần" | Khi mở lớp mới |
| Kiểm tra lịch tự động còn chạy | GitHub → **Actions** (3 lịch: nhắc học, Content Factory, nhắc câu lạc bộ nói) | Hằng tuần |

## Lưu ý khi deploy

- Merge PR = deploy production (Vercel + Render tự build). Render tự chạy migration cơ sở dữ liệu khi khởi động.
- Render gói **free** ngủ sau 15 phút không có truy cập; lịch nhắc câu lạc bộ nói (10 phút/lần ban ngày) giữ máy thức trong khung 6:00–23:00 — vẫn nằm trong 750 giờ miễn phí/tháng nếu chỉ có 1 dịch vụ free. Muốn luôn nhanh: nâng Render lên gói Starter (~7 USD/tháng).
- Mất khoá VAPID: tạo lại bằng script ở 2.1 (người học phải bật lại thông báo).

## Câu hỏi còn chờ bạn quyết định

- Số liệu trên landing ("1.247 học viên", "4,9 sao", lời đánh giá) là thật hay cần thay?
- Bảng giá trên landing: giữ hay ẩn tới khi có thanh toán thật? Giá 99K/tháng – 799K/năm có giữ không?
