# Trạng thái lộ trình nâng cấp — AI AGENT ENGLISH

> File này là "bộ nhớ" giữa các phiên làm việc. Cập nhật mỗi khi xong một hạng mục.
> Kế hoạch gốc (đã được chủ dự án duyệt): Claude Doc "Kế hoạch nâng cấp AGEN — Audit & Lộ trình"
> https://claude.ai/artifact/7PHjES4CK5zB9i8rBxrCuT

Cập nhật lần cuối: 2026-10-26 (G2 + G3).

## Cách làm việc với chủ dự án

- Trao đổi bằng **tiếng Việt**, ngắn gọn, không thuật ngữ thừa. Chủ dự án làm SEO, bận — làm trọn gói, ít hỏi.
- Mỗi hạng mục: nhánh `claude/...` → PR → chờ CI xanh → **chỉ merge khi chủ dự án nhắn "deploy"**.
- Merge vào `main` = deploy production: Vercel (frontend, thư mục `agen-web`) và Render (backend, `agen-backend`)
  tự build; Render chạy `alembic upgrade head` khi khởi động (`scripts/start.sh`).
- Không bao giờ commit khoá/secret vào repo.

## Đã xong

| Giai đoạn | Hạng mục | PR |
|---|---|---|
| — | Giao diện Apple-style, logo, banner, landing có hiệu ứng | #1, #2 |
| G0 | Sửa 5 lỗi nền (giữ đăng nhập khi reload, email không phân biệt hoa/thường, ngày theo giờ VN, khoá nâng Premium giả lập, rate limit theo IP thật), PostHog analytics, giới hạn free 3 bài/ngày, đổi tên AI AGENT ENGLISH | #3 |
| G1 | Ôn tập thông minh FSRS + Sổ từ vựng + Sổ lỗi sai (`/review`, `/vocabulary`) | #4 |
| G1 | Màn bài học kiểu game, làm lại câu sai, AI "Vì sao sai?", hiện quy tắc ngữ pháp | #5 |
| G1 | Bảo vệ chuỗi (streak freeze), 3 nhiệm vụ/ngày, mục tiêu tuần (`/engagement`) | #6 |
| G1 | Nhắc học: web push (VAPID) + email (Resend), chọn giờ ở onboarding, cron GitHub Actions hằng giờ | #7 |
| G1 | PWA cài được + trang offline; Content Factory tự sinh bài A1–B1 (workflow 2 giờ/lần); luyện tập tự do lấy bài có sẵn | #8 |
| G1 | 6 dạng bài mới: ghép câu, nối cặp, nghe chọn, nghe-chép, nói lặp lại, sắp xếp hội thoại (dựng từ nội dung bài, không tốn AI) | #9 |
| G1 | App shell: sidebar máy tính + tab bar điện thoại thống nhất (`components/ui/navigation.ts`), trang Hồ sơ `/profile` | #10 |
| G2 | Luyện nói 3 bước + AI Coach có nhân vật: 24 tình huống bối cảnh VN (`services/speaking_scenarios.py`), học cụm từ → nói lặp lại chấm **từng từ** + mẹo âm khó cho người Việt → roleplay với nhân vật (câu sửa + gợi ý câu tiếp theo) | #11 |
| G2 | Nghe hay hơn: giọng neural tạo ở server + cache (`/audio/tts`, Gemini TTS → OpenAI TTS, tự tắt khi không có khoá), nút 0,75×, transcript bấm từng từ để tra (`/review/lookup`) và thêm vào Sổ từ (`POST /review/items`), chế độ shadowing | #11 |
| G2 | Kiểm tra đầu vào 4 kỹ năng: 14 câu = 10 câu chữ + 3 câu nghe (chỉ nghe audio) + 1 câu đọc to (chấm transcript; bỏ qua được nếu không có micro) | #11 |
| G2 | Chấm phát âm **đến từng âm** qua Azure Pronunciation Assessment (`services/pronunciation_azure.py`, `POST /speaking/pronunciation-audio`): web ghi âm → WAV 16 kHz → điểm từng từ, từng âm IPA, ngữ điệu; tự về chấm theo từ khi chưa có `AZURE_SPEECH_KEY`. Voicebox tự host làm nguồn giọng đọc miễn phí (`VOICEBOX_URL`) | #12 |
| G3 | Học thử không cần đăng ký (`POST /auth/guest`, `POST /auth/claim` giữ nguyên tiến bộ; nút trên landing/login, banner "Lưu tài khoản") | #12 |
| G3 | Thanh toán thật VNPay + MoMo (`services/payments.py`, IPN ký HMAC, `/billing/checkout`, `/billing/vnpay/*`, `/billing/momo/ipn`), dùng thử Premium 7 ngày (`POST /billing/trial`), trang Premium có nút theo cổng đã bật | #12 |
| G3 | Giải đấu tuần (`services/league.py`, `GET /engagement/league`, thưởng top 10 tuần trước, trang `/league`, thẻ trên trang chủ) | #12 |
| G3 | Phụ huynh chủ động: email báo cáo tuần Chủ nhật 18h + cảnh báo con nghỉ 2 ngày (`services/parent_digest.py`, chạy trong cron nhắc học), bật/tắt ở bảng phụ huynh | #12 |
| G3 | Khoá theo mục tiêu IELTS / TOEIC / phỏng vấn (`services/goal_tracks.py`, 36 bài theo thứ tự, `GET /curriculum/tracks`, trang `/tracks`), bài tạo ở đúng trình độ của khoá | #12 |

**G2 và G3 hoàn tất (trên code).** Các phần cần khoá/đăng ký dịch vụ mới chạy thật — xem mục việc chủ dự án.

**G1 hoàn tất.** Chưa làm trong G1: "sửa chuỗi trong 24 giờ" (streak repair) và mua bảo vệ chuỗi bằng XP —
hiện bảo vệ chuỗi nhận được khi đạt mục tiêu tuần (mỗi người tặng sẵn 1, tối đa 2).

## Việc chủ dự án còn phải làm (chưa xong, tính đến 2026-10-26)

Khoá đã được tạo và gửi cho chủ dự án trong chat (KHÔNG có trong repo). Cần dán:

1. **Render → agen-api → Environment:** `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`
   (`mailto:atmarketing68@gmail.com`), `REMINDER_CRON_SECRET`, `APP_URL` (URL Vercel thật).
   Tuỳ chọn email: `RESEND_API_KEY`, `EMAIL_FROM` (tên miền đã xác minh trên Resend).
   Bật analytics: `NEXT_PUBLIC_POSTHOG_KEY` trên **Vercel**.
   Giữ nâng Premium giả lập cho pilot: `ALLOW_DEMO_UPGRADE=true` trên Render.
2. **GitHub → Settings → Secrets → Actions:** `REMINDER_API_URL` (URL backend Render),
   `REMINDER_CRON_SECRET` (cùng giá trị Render). Dùng chung cho workflow nhắc học và Content Factory.
3. Chạy thử: Actions → *Content Factory* → Run workflow (limit 10); Actions → *Learning reminders* → Run.

Nếu khoá bị mất: tạo lại bằng `python agen-backend/scripts/generate_vapid_keys.py` (đổi khoá thì người
học phải bật lại thông báo).

## G2 — Nói & nghe: hoàn tất (PR #11, #12)

| # | Hạng mục | Trạng thái |
|---|---|---|
| 9 | Chấm phát âm **đến từng âm** | ✅ #12 — Azure Pronunciation Assessment qua REST, bật khi có `AZURE_SPEECH_KEY` (+ `AZURE_SPEECH_REGION`, mặc định `southeastasia`). Chưa có khoá → chấm theo từ như cũ. **Chưa chạy thử với tài khoản Azure thật** (test bằng phản hồi mẫu) — lần đầu bật nên thử 1 câu và xem log Render. So sánh chi phí: `docs/G2_CHAM_PHAT_AM_SO_SANH.md`. |
| 10 | Luyện nói 3 bước + AI Coach có nhân vật | ✅ #11 — `/practice/speaking`: chọn tình huống → học cụm từ → nói lặp lại → hội thoại; vẫn có "tự chọn chủ đề" (AI dựng tình huống) |
| 11 | Nghe hay hơn | ✅ #11 — giọng neural server (cache đĩa, giới hạn ký tự/ngày `TTS_DAILY_CHAR_LIMIT`), 0,75×, bấm từ để tra/lưu, shadowing. #12 thêm Voicebox tự host. |
| 12 | Kiểm tra đầu vào đủ 4 kỹ năng | ✅ #11 — 14 câu, có nghe và nói |

Voicebox (github.com/jamiepine/voicebox) thay API TTS được không? **Được, nếu có máy chạy 24/7**: Voicebox là app
chạy máy cục bộ (REST API ở `127.0.0.1:17493`, engine Qwen3-TTS/Kokoro, CPU chạy được nhưng chậm, không có xác thực).
Render không chạy được nó. Cách dùng: chạy Voicebox trên PC/VPS, mở ra ngoài bằng Cloudflare Tunnel (có bật
Access), rồi đặt `VOICEBOX_URL` + `VOICEBOX_PROFILE_ID` (id giọng nữ, lấy từ `GET /profiles`), tuỳ chọn
`VOICEBOX_PROFILE_ID_MALE`, `VOICEBOX_API_KEY` (gửi dạng Bearer nếu tunnel yêu cầu). Khi đặt, Voicebox được thử trước
Gemini/OpenAI; lỗi thì tự chuyển sang nguồn sau. Lưu ý: giọng tạo trên CPU mất vài giây/câu; cache đĩa giúp câu đã tạo
phát ngay.

Ghi chú vận hành G2:
- Giọng neural **tự bật** khi Render có `GEMINI_API_KEY` hoặc `OPENAI_API_KEY` (thứ tự Gemini → OpenAI). Tắt bằng
  `TTS_PROVIDER=off`; ghim một bên bằng `TTS_PROVIDER=gemini|openai`. Mặc định tối đa 150.000 ký tự mới/ngày
  (≈ 2 USD/ngày với OpenAI tts-1; cache nên thực tế thấp hơn nhiều). Không có khoá → trình duyệt tự đọc như trước.
- Model TTS đổi được bằng `GEMINI_TTS_MODEL` (mặc định `gemini-2.5-flash-preview-tts`) và `OPENAI_TTS_MODEL` (`tts-1`).
  Nếu Gemini TTS báo lỗi (đổi tên model, hết quota), server tự chuyển sang OpenAI rồi trình duyệt.
- Tra từ khi bấm transcript dùng 1 lần gọi LLM mỗi từ (cache trong tiến trình).

## G3 — Tăng trưởng: hoàn tất trên code (PR #12)

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Học thử không đăng ký | Không cần gì. Tài khoản khách có email `guest-…@guest.agen.local`, cùng hạn mức gói miễn phí. |
| Thanh toán VNPay / MoMo | Đăng ký merchant rồi dán khoá vào Render: **VNPay** `VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET`, `VNPAY_URL` (sandbox mặc định; production `https://pay.vnpay.vn/vpcpay.html`); **MoMo** `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY`, `MOMO_SECRET_KEY`, `MOMO_ENDPOINT` (test mặc định; production `https://payment.momo.vn`). Đặt `API_PUBLIC_URL` = URL backend Render. Khai báo IPN với cổng: VNPay `…/api/v1/billing/vnpay/ipn`, MoMo tự lấy từ request. Khi đã bật cổng thật, đặt `ALLOW_DEMO_UPGRADE=false`. Giá: 99K/249K/799K (`services/payments.py`). |
| Dùng thử 7 ngày | Không cần gì (mỗi tài khoản một lần, khách phải lưu tài khoản trước). |
| Giải đấu tuần | Không cần gì. |
| Email phụ huynh | Cần email đã bật (`RESEND_API_KEY`, `EMAIL_FROM`); chạy trong cron nhắc học hằng giờ sẵn có. |
| Khoá mục tiêu | Không cần gì; bài tạo bằng AI khi học viên mở (tốn 1 lượt AI/bài như bài tự do). |

Chưa làm trong G3: "giải đấu" chia bảng 30 người theo nhóm (hiện 1 bảng chung, top 30 hiển thị); thẻ quốc tế đi qua
VNPay (chưa có Stripe); Zalo OA.

## G4 — gợi ý tiếp theo

Chia bảng giải đấu theo nhóm + hạ/thăng hạng · Nội dung Content Factory cho khoá mục tiêu (tạo sẵn 36 bài) ·
Gói gia đình (1 phụ huynh – nhiều con, thanh toán chung) · Thống kê admin cho doanh thu/chuyển đổi học thử → trả phí ·
Chấm viết theo band IELTS/TOEIC.

## Câu hỏi còn mở với chủ dự án

- Số liệu trên landing ("1.247 học viên", "4,9 sao", lời đánh giá) là thật hay cần thay?
- Bảng giá trên landing: giữ hay ẩn cho tới khi có thanh toán thật? Giá 99K/tháng – 799K/năm?
- Dịch vụ chấm phát âm đến từng âm (G2 · hạng mục 9, xem `docs/G2_CHAM_PHAT_AM_SO_SANH.md`) và cổng thanh toán (G3).
- Thêm kênh nhắc qua Zalo OA? Có làm "học thử không cần đăng ký"?
