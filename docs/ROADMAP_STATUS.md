# Trạng thái lộ trình nâng cấp — AI AGENT ENGLISH

> File này là "bộ nhớ" giữa các phiên làm việc. Cập nhật mỗi khi xong một hạng mục.
> Kế hoạch gốc (đã được chủ dự án duyệt): Claude Doc "Kế hoạch nâng cấp AGEN — Audit & Lộ trình"
> https://claude.ai/artifact/7PHjES4CK5zB9i8rBxrCuT

Cập nhật lần cuối: 2026-10-26.

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
| — | Sửa lỗi đăng ký/đăng nhập: báo lỗi rõ (mất kết nối, mật khẩu thiếu số, email trùng, sai mật khẩu), lỗi 500 vẫn có CORS, `APP_URL` tự vào CORS (`lib/apiError.ts`) | #12 |

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
3. **Tài khoản admin:** đăng ký trên web bằng `atmarketing68@gmail.com`, rồi thêm `ADMIN_EMAILS=atmarketing68@gmail.com`
   trên Render → vào `/admin`.
4. **Kiểm tra `ALLOWED_ORIGINS` / `APP_URL` trên Render = đúng URL web đang dùng** (vd. `https://agen-web.vercel.app`).
   Sai URL thì mọi lệnh gọi API bị chặn — đăng ký báo "Không kết nối được máy chủ".
5. Chạy thử: Actions → *Content Factory* → Run workflow (limit 10); Actions → *Learning reminders* → Run.

Nếu khoá bị mất: tạo lại bằng `python agen-backend/scripts/generate_vapid_keys.py` (đổi khoá thì người
học phải bật lại thông báo).

## Tiếp theo: G2 — Nói & nghe (cần quyết định trước)

| # | Hạng mục | Ghi chú |
|---|---|---|
| 9 | Chấm phát âm đến từng âm | **Cần chủ dự án chọn:** dịch vụ trả phí theo lượng audio (vd. Azure Pronunciation Assessment, SpeechAce) hay tự chạy mô hình mã nguồn mở (cần GPU). Gửi bảng so sánh chi phí trước khi làm. Hiện `speak_repeat` chỉ so khớp transcript của Web Speech API. |
| 10 | Luyện nói 3 bước + AI Coach có nhân vật | Học cụm từ → nói lặp → roleplay; 20+ tình huống bối cảnh VN; đã có `practice/speaking` (roleplay) để mở rộng |
| 11 | Nghe hay hơn | Giọng neural tạo ở server + cache, nút 0,75×, transcript bấm từng từ để tra/thêm vào sổ, shadowing |
| 12 | Kiểm tra đầu vào đủ 4 kỹ năng | Thêm 3 câu nghe + 1 câu nói vào placement |

## G3 — Tăng trưởng (sau G2)

Học thử không cần đăng ký · Thanh toán thật (MoMo/VNPay/thẻ, webhook, dùng thử 7 ngày) · Giải đấu tuần ·
Phụ huynh chủ động (báo cáo tuần, cảnh báo nghỉ 2 ngày) · Khoá theo mục tiêu (IELTS/TOEIC/phỏng vấn).

## Câu hỏi còn mở với chủ dự án

- Số liệu trên landing ("1.247 học viên", "4,9 sao", lời đánh giá) là thật hay cần thay?
- Bảng giá trên landing: giữ hay ẩn cho tới khi có thanh toán thật? Giá 99K/tháng – 799K/năm?
- Dịch vụ chấm phát âm (G2) và cổng thanh toán (G3).
- Thêm kênh nhắc qua Zalo OA? Có làm "học thử không cần đăng ký"?
