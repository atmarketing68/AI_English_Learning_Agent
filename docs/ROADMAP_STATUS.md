# Trạng thái lộ trình nâng cấp — AI AGENT ENGLISH

> File này là "bộ nhớ" giữa các phiên làm việc. Cập nhật mỗi khi xong một hạng mục.
> Kế hoạch gốc (đã được chủ dự án duyệt): Claude Doc "Kế hoạch nâng cấp AGEN — Audit & Lộ trình"
> https://claude.ai/artifact/7PHjES4CK5zB9i8rBxrCuT

Cập nhật lần cuối: 2026-10-27 (G12).

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
| G2 | Chấm phát âm **đến từng âm** qua Azure Pronunciation Assessment (`services/pronunciation_azure.py`, `POST /speaking/pronunciation-audio`): web ghi âm → WAV 16 kHz → điểm từng từ, từng âm IPA, ngữ điệu; tự về chấm theo từ khi chưa có `AZURE_SPEECH_KEY`. Voicebox tự host làm nguồn giọng đọc miễn phí (`VOICEBOX_URL`) | #13 |
| G3 | Học thử không cần đăng ký (`POST /auth/guest`, `POST /auth/claim` giữ nguyên tiến bộ; nút trên landing/login, banner "Lưu tài khoản") | #13 |
| G3 | Thanh toán thật VNPay + MoMo (`services/payments.py`, IPN ký HMAC, `/billing/checkout`, `/billing/vnpay/*`, `/billing/momo/ipn`), dùng thử Premium 7 ngày (`POST /billing/trial`), trang Premium có nút theo cổng đã bật | #13 |
| G3 | Giải đấu tuần (`services/league.py`, `GET /engagement/league`, thưởng top 10 tuần trước, trang `/league`, thẻ trên trang chủ) | #13 |
| G3 | Phụ huynh chủ động: email báo cáo tuần Chủ nhật 18h + cảnh báo con nghỉ 2 ngày (`services/parent_digest.py`, chạy trong cron nhắc học), bật/tắt ở bảng phụ huynh | #13 |
| G3 | Khoá theo mục tiêu IELTS / TOEIC / phỏng vấn (`services/goal_tracks.py`, 33 bài theo thứ tự (IELTS 12 · TOEIC 12 · phỏng vấn 9), `GET /curriculum/tracks`, trang `/tracks`), bài tạo ở đúng trình độ của khoá | #13 |

| G4 | **Hai giao diện** (`ui_skin`): "Vui nhộn" (`data-skin="vivid"`: font Nunito, màu tươi, nút dày, mascot robot **Bo** có cảm xúc + bong bóng nói) mặc định cho học viên **dưới 16 tuổi**; "Chuyên nghiệp" (giao diện Apple-style hiện có) cho người đi làm và phụ huynh (trang phụ huynh/admin luôn chuyên nghiệp). Đổi ở Hồ sơ → Giao diện; lưu server + localStorage nên không nháy khi mở | — |
| G4 | **Đá quý & Cửa hàng avatar** (`services/shop.py`, `/gamification/shop`, trang `/shop`): 12 nhân vật emoji, 6 màu nền, 5 khung; đá quý nhận khi xong bài (3–15 theo hạng S–D), nhận thưởng nhiệm vụ (+3), mục tiêu tuần (+10), top 10 giải đấu (20–40), Blitz (tới 10). Avatar hiện ở sidebar, trang chủ, hồ sơ, bảng giải đấu | — |
| G4 | **Blitz 60 giây** (`GET /review/blitz`, `POST /review/blitz/result`, trang `/blitz`): 15 từ (ưu tiên Sổ từ vựng, bù từ lộ trình), chọn nghĩa đúng, combo, phím 1–4, +2 XP/câu đúng (trần 40 XP/ngày) + 1 đá quý/câu đúng (tối đa 10), ghi `LearningEvent` nên tính vào chuỗi/nhiệm vụ | — |
| G4 | **Giải đấu chia nhóm 30 người theo 4 hạng** Đồng → Bạc → Vàng → Kim cương (`LeagueMembership`, `services/league.py`): top 7 thăng hạng, 5 người cuối (nhóm ≥ 10) xuống hạng, nghỉ cả tuần tụt 1 hạng; trang `/league` hiện dải hạng, vùng thăng/xuống hạng, avatar, thưởng XP + đá quý | — |
| G4 | **Content Factory sinh sẵn bài khoá mục tiêu** (33 bài IELTS/TOEIC/phỏng vấn sau khi hết bài A1–B1; hàng `TRACKS` trong `content_coverage`); học viên mở bài khoá sẽ lấy bản đã duyệt từ cache, không tốn AI | — |

| G5 | **Giao diện "Chuyên nghiệp" làm mới theo hướng cao cấp**: hero gradient xanh đậm có quầng sáng chuyển động, 4 vòng tròn kỹ năng (SVG animate), số đếm tăng (count-up), nút chính gradient có vệt sáng khi hover, sidebar có vạch chỉ mục đang chọn, nền ánh sáng dịu, thẻ "Luyện nhanh" có icon gradient. Skin Vui nhộn dùng cùng hero với màu tím-hồng | — |
| G5 | **Gói gia đình**: phụ huynh mua (179K/1 tháng, 1.490K/12 tháng), tối đa 4 con đã liên kết tự động Premium (`premium_source=family`); thẻ trên bảng phụ huynh, trang `/upgrade` tự chuyển sang gói gia đình với tài khoản phụ huynh; mua qua VNPay/MoMo hoặc demo | — |
| G5 | **Thống kê doanh thu & chuyển đổi cho admin** (`GET /admin/revenue/summary`, tab "Doanh thu" ở `/admin`): doanh thu 6 tháng, theo cổng, theo gói; Premium/gia đình đang hoạt động; dùng thử → trả phí; học thử → đăng ký (`users.claimed_at`) | — |
| G5 | **Chấm viết theo band IELTS/TOEIC**: 4 dạng đề thi thật (IELTS Task 2, Task 1 thư, TOEIC trả lời email, TOEIC essay) ở `/practice/writing`; AI trả thêm `exam_band` (IELTS 0–9 theo 4 tiêu chí hoặc TOEIC 0–200) + mẹo lên band; nhóm "Luyện thi" hiện trước với người có mục tiêu thi/đi làm | — |
| G5 | **Bo nói**: nút loa trên bong bóng mascot, đọc bằng giọng tiếng Việt của trình duyệt (tự ẩn nếu máy không có giọng vi-VN) | — |

| G6 | **Thử thách bạn bè** (`services/friends.py`, `/friends`, trang `/friends`, thẻ trên trang chủ): kết bạn bằng mã (cùng mã liên kết phụ huynh), mỗi tuần hai người cùng kiếm 200 XP (mỗi người ≥ 50) → mỗi bên nhận +30 XP, +10 đá quý; tối đa 10 bạn | — |
| G6 | **Trang landing làm mới** theo giao diện cao cấp: hero gradient có quầng sáng, khối "xem trước ứng dụng" với vòng tròn kỹ năng, bảng giá thêm gói Gia đình | — |
| G6 | **Bo nói bằng giọng neural**: `/audio/tts?lang=vi` (cache theo ngôn ngữ, prompt Gemini tiếng Việt, Voicebox `language=vi`); web `playVietnamese()` dùng giọng server trước, giọng vi-VN của trình duyệt khi không có | — |
| G6 | **Báo cáo PDF cho phụ huynh**: trang `/parent/report/<learnerId>` kiểu tài liệu in, nút "Tải PDF / In" mở hộp thoại in của trình duyệt (Lưu thành PDF); không cần thư viện PDF | — |
| G6 | **Gói gia đình tối đa 4 con**: chỉ 4 con liên kết sớm nhất được Premium; khi gói đang hoạt động, liên kết con thứ 5 bị từ chối với hướng dẫn huỷ liên kết | — |

| G7 | **Nhóm học cho giáo viên / doanh nghiệp** (vai trò `teacher`, `services/groups.py`, `/groups`, trang `/teacher`, `/teacher/<id>`): tạo lớp hoặc nhóm công ty, mã tham gia `LOP-XXXX` / `CTY-XXXX`, bảng tiến độ (XP tuần, chuỗi, trình độ, hôm nay đã học), giao bài theo tuần (kỹ năng + chủ đề + hạn), đếm ai đã làm; học viên có trang `/classes` + thẻ "Bài tập được giao" trên trang chủ; làm xong bài học cùng kỹ năng là bài tập được tính xong | — |
| G7 | **Gói doanh nghiệp / lớp học theo ghế** (`plan=team`, 79K/ghế/tháng, 690K/ghế/năm, 5–500 ghế): thành viên nhóm của chủ gói là Premium theo thứ tự tham gia (`premium_source=team`); `/upgrade` với tài khoản giáo viên chọn số ghế; mua qua VNPay/MoMo hoặc demo | — |
| G7 | **Thông báo đẩy cho phụ huynh** (`/parent/push-subscriptions`, `push_alerts`): con nghỉ 2 ngày, chuỗi ngày sắp mất (19–21h, chuỗi ≥ 3, một lần/ngày), báo cáo tuần sẵn sàng; chạy trong cron nhắc học, không cần email | — |
| G7 | **Bảng xếp hạng bạn bè** (`GET /friends/leaderboard`, trên trang `/friends`): XP tuần của tôi và các bạn học | — |
| G7 | **Ứng dụng di động gốc**: hướng dẫn đóng gói PWA bằng Capacitor (`docs/MOBILE_APP.md`, `docs/mobile/capacitor.config.ts.example`) — chủ dự án chạy ở máy có Android Studio / Xcode | — |

| G8 | **Thư viện đề thi thử IELTS / TOEIC** (`services/mock_exams.py`, `/exams`, trang `/exams`, `/exams/<id>` chế độ tập trung): 4 mini test đúng định dạng thật — IELTS Listening (điền form, trắc nghiệm, hội thoại học thuật), IELTS Reading (T/F/NG, hoàn thành câu, trắc nghiệm), TOEIC Listening (Part 2–4), TOEIC Reading (Part 5–7); đồng hồ đếm ngược, phần nghe phát **một lần** bằng giọng server, nộp bài → band IELTS / điểm TOEIC ước tính theo bảng quy đổi chính thức, lời giải tiếng Việt từng câu, +3 XP/câu (trần 40), +8 đá quý khi ≥ 70 %; miễn phí 1 đề/ngày, Premium không giới hạn; lưu `ExamAttempt`, ghi `LearningEvent` | — |
| G8 | **Hỏi Bo — chatbot ngữ pháp tiếng Việt** (`agents/tutor_agent.py`, agent `tutor_answer`, `/tutor`, trang `/tutor`): trả lời bằng tiếng Việt kèm quy tắc, 2–3 ví dụ nghe được, lỗi người Việt hay mắc, gợi ý câu hỏi tiếp; nhớ 6 lượt gần nhất làm ngữ cảnh; miễn phí 5 câu/ngày (`TUTOR_FREE_DAILY_LIMIT`), Premium không giới hạn; LLM lỗi → câu trả lời dự phòng, không trừ lượt | — |
| G8 | **Báo cáo nhóm cho giáo viên / HR**: `GET /groups/<id>/report.csv` (UTF-8 BOM mở Excel được, cột theo từng bài tập) + trang in `/teacher/<id>/report` (KPI nhóm, bảng xếp hạng XP tuần, bài tập) với nút Tải CSV / Tải PDF | — |
| G8 | **Hoá đơn VAT cho doanh nghiệp**: tài khoản giáo viên / công ty điền tên đơn vị, MST, địa chỉ, email khi mua gói theo ghế (`PaymentOrder.invoice_info`, cả VNPay/MoMo lẫn demo); `GET /billing/orders`, `PUT /billing/orders/<id>/invoice`; admin xem danh sách đơn yêu cầu hoá đơn ở tab Doanh thu, đánh dấu "đã xuất", tải CSV (`GET /admin/revenue/orders`) | — |
| G8 | **Hero 3D trang landing** (`components/landing/HeroScene3D.tsx`, CSS 3D thuần): lõi tri thức + 3 vành quỹ đạo, 6 thẻ từ vựng bay quanh luôn hướng về người xem, bậc thang A1→C1 có điểm sáng leo lên, sàn lưới trôi, chữ cái lơ lửng, +XP, chip thành tích; nghiêng theo chuột; thu nhỏ trên điện thoại; tắt khi "giảm chuyển động". Đổi từ/thẻ: mảng `WORDS` trong file | — |
| G8 | **Kênh push gốc FCM cho app Capacitor** (`services/fcm.py`, `DeviceToken`, `POST/DELETE /notifications/device-tokens`, `GET /notifications/native-push`): FCM HTTP v1 với service account (token OAuth tự ký bằng python-jose, cache 55 phút), tự xoá token hết hiệu lực; nhắc học và cảnh báo phụ huynh gửi song song web push + FCM; tắt êm khi chưa có `FIREBASE_SERVICE_ACCOUNT_JSON` | — |

| G9 | **Thi thử Speaking có giám khảo AI** (`services/speaking_exams.py`, `/speaking-exams`, trang `/exams/speaking/<id>`): IELTS Speaking Part 1–3 (cue card 1 phút chuẩn bị, nói 2 phút) và TOEIC Speaking (Q1–2 đọc to chấm phát âm, Q5–7 trả lời, Q11 nêu ý kiến); giám khảo AI đọc câu hỏi, đếm giờ chuẩn bị/trả lời, ghi âm qua micro (tự nối lại khi trình duyệt ngắt vì im lặng); nộp bài → agent `speaking_exam_evaluation` cho band IELTS 4 tiêu chí / điểm TOEIC 0–200, nhận xét từng phần, câu sửa nghe được; LLM lỗi → ước tính theo độ dài; +6 XP/phần (trần 40), +8 đá quý khi ≥ 6.0 / ≥ 130; miễn phí 1 lần/ngày | — |
| G9 | **Ngân hàng đề thi thử sinh bằng AI, admin duyệt** (`agents/exam_agent.py`, `services/exam_generator.py`, `GeneratedExam`, `/admin/exams*`, tab "Đề thi" ở `/admin`): sinh IELTS/TOEIC Listening hoặc Reading đúng định dạng (`normalize_paper` kiểm tra đáp án, số câu, lời thoại), xem trước có đáp án, duyệt/từ chối/xoá; đề đã duyệt xuất hiện trong `/exams` với id `gen-…` và chấm như đề viết tay | — |
| G9 | **Kế hoạch ôn thi theo ngày thi + mục tiêu** (`services/study_plan.py`, `/study-plan`, trang `/plan`, thẻ trên trang chủ): điểm hiện tại từng kỹ năng từ thi thử/band viết, khoảng cách tới mục tiêu, dự kiến ngày thi, lộ trình theo tuần (kỹ năng yếu trước, chỉ tiêu bài/đề/viết/nói theo phút học mỗi ngày), trạng thái đúng/chậm/vượt tiến độ tính từ `LearningEvent` tuần này, lời khuyên tiếng Việt | — |
| G9 | **Nhắc học qua Zalo OA** (`services/zalo.py`, `/zalo/*`, khối Zalo trong Nhắc học và bảng Phụ huynh): học viên/phụ huynh quan tâm OA rồi gửi mã `ZL-XXXXX` (hoặc mã AGEN của học viên) → webhook liên kết; nhắc học hằng ngày, báo cáo tuần, cảnh báo nghỉ học, chuỗi sắp mất gửi thêm qua Zalo; gửi "TAT" để tắt; token OA tự làm mới và lưu trong `app_config`; tắt êm khi chưa có khoá | — |

**G2 → G9 hoàn tất (trên code).** Các phần cần khoá/đăng ký dịch vụ mới chạy thật — xem mục việc chủ dự án.

**G1 hoàn tất.** Chưa làm trong G1: "sửa chuỗi trong 24 giờ" (streak repair) và mua bảo vệ chuỗi bằng XP —
hiện bảo vệ chuỗi nhận được khi đạt mục tiêu tuần (mỗi người tặng sẵn 1, tối đa 2).

## Việc chủ dự án còn phải làm (chưa xong, tính đến 2026-10-26)

> **Danh sách đầy đủ, theo thứ tự ưu tiên, có hướng dẫn từng bước: `docs/VIEC_CAN_LAM.md`** (cập nhật mỗi giai đoạn).

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

## G2 — Nói & nghe: hoàn tất (PR #11, #13)

| # | Hạng mục | Trạng thái |
|---|---|---|
| 9 | Chấm phát âm **đến từng âm** | ✅ #13 — Azure Pronunciation Assessment qua REST, bật khi có `AZURE_SPEECH_KEY` (+ `AZURE_SPEECH_REGION`, mặc định `southeastasia`). Chưa có khoá → chấm theo từ như cũ. **Chưa chạy thử với tài khoản Azure thật** (test bằng phản hồi mẫu) — lần đầu bật nên thử 1 câu và xem log Render. So sánh chi phí: `docs/G2_CHAM_PHAT_AM_SO_SANH.md`. |
| 10 | Luyện nói 3 bước + AI Coach có nhân vật | ✅ #11 — `/practice/speaking`: chọn tình huống → học cụm từ → nói lặp lại → hội thoại; vẫn có "tự chọn chủ đề" (AI dựng tình huống) |
| 11 | Nghe hay hơn | ✅ #11 — giọng neural server (cache đĩa, giới hạn ký tự/ngày `TTS_DAILY_CHAR_LIMIT`), 0,75×, bấm từ để tra/lưu, shadowing. #13 thêm Voicebox tự host. |
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

## G3 — Tăng trưởng: hoàn tất trên code (PR #13)

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

## G4 — Giao diện cho trẻ + lớp "vui" của sản phẩm: hoàn tất trên code

Nghiên cứu làm căn cứ (tóm tắt): Duolingo giữ chân người học bằng ba vòng — chuỗi ngày, giải đấu theo nhóm nhỏ có
thăng/xuống hạng, và tiền ảo (gems) chỉ để mua đồ trang trí nên không "mua được điểm"; thiết kế cho trẻ 6–12 cần nút to
(≥ 44 px), ít chữ, màu tươi nhưng nền dịu, phản hồi âm thanh + hình ảnh tức thì, một nhân vật dẫn dắt, và vòng chơi ngắn
(≤ 1–2 phút). Người lớn đi làm và phụ huynh lại cần giao diện gọn, trung tính, nhìn "đáng tin" → vì vậy làm **2 skin**
thay vì đổi toàn bộ.

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Hai giao diện + mascot Bo | Không cần gì. Học viên có tuổi < 16 mặc định "Vui nhộn"; không có tuổi → "Chuyên nghiệp". Tự đổi ở Hồ sơ. Muốn đổi ngưỡng tuổi: `VIVID_MAX_AGE` trong `agen-web/src/store/skinStore.ts`. |
| Đá quý & cửa hàng | Không cần gì. Chạy migration (`alembic upgrade head` tự chạy khi deploy). Thêm vật phẩm: sửa `CATALOGUE` trong `services/shop.py`. |
| Blitz 60 giây | Không cần gì (không dùng AI). |
| Giải đấu 4 hạng, nhóm 30 | Không cần gì. Thứ Hai đầu tuần ai mở giải đấu / học bài sẽ được xếp nhóm theo kết quả tuần trước. |
| Content Factory cho khoá mục tiêu | Không cần gì; workflow 2 giờ/lần sẵn có sẽ sinh tiếp 33 bài khoá sau khi xong A1–B1 (tốn lượt AI như bài thường). |

Chưa làm trong G4: âm thanh/giọng của Bo (hiện chỉ bong bóng chữ); vật phẩm theo mùa; "học cùng bạn" (friend streak).

## G5 — Giao diện cao cấp cho người lớn + gói gia đình + doanh thu + band thi: hoàn tất trên code

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Giao diện Chuyên nghiệp mới | Không cần gì. Toàn bộ nằm ở `globals.css` (khối "G5 — PRO LAYER"), `components/ui/SkillRing.tsx`, `CountUp.tsx`, hero ở `app/dashboard/page.tsx`. |
| Gói gia đình | Không cần gì ngoài cổng thanh toán đã bật ở G3 (demo vẫn hoạt động khi `ALLOW_DEMO_UPGRADE`). Giá ở `FAMILY_PRICES_VND` trong `services/payments.py`; số con tối đa `FAMILY_MAX_CHILDREN` (hiện chỉ hiển thị, chưa chặn liên kết con thứ 5). Migration `u8d9e0f1a2b3` tự chạy khi deploy. |
| Doanh thu admin | Không cần gì; cần email trong `ADMIN_EMAILS` để vào `/admin`. |
| Band IELTS/TOEIC | Không cần gì; dùng cùng agent chấm viết (tốn 1 lượt AI như bài viết thường). Band là ước tính của AI, có ghi chú trên màn hình. |
| Bo nói | Không cần gì; phụ thuộc giọng vi-VN của trình duyệt (Chrome/Edge máy tính và Android thường có; iOS có nếu người dùng đã cài giọng tiếng Việt). |

Chưa làm trong G5: thử thách bạn bè (friend quest); giọng neural cho Bo (có thể nối vào `/audio/tts` khi muốn); chặn liên kết quá 4 con cho gói gia đình.

## G6 — Bạn bè, landing mới, giọng Bo, PDF phụ huynh, giới hạn gia đình: hoàn tất trên code

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Thử thách bạn bè | Không cần gì. Migration `v9e0f1a2b3c4` tự chạy. Đổi mục tiêu/thưởng: hằng số đầu `services/friends.py`. |
| Landing mới | Không cần gì. Ảnh `public/hero-banner.webp` không còn dùng ở hero (có thể xoá hoặc giữ). |
| Bo nói giọng neural | Cần giọng server đã bật ở G2 (`GEMINI_API_KEY`/`OPENAI_API_KEY`/`VOICEBOX_URL`); không có thì dùng giọng vi-VN của trình duyệt; không có cả hai thì nút loa tự ẩn. Tiếng Việt tính vào ngân sách ký tự TTS hằng ngày. |
| Báo cáo PDF | Không cần gì; phụ huynh bấm "Tải PDF / In" → chọn "Lưu thành PDF" trong hộp thoại in. |
| Giới hạn 4 con | Không cần gì; đổi số: `FAMILY_MAX_CHILDREN` trong `services/payments.py`. |

## G7 — Lớp học / doanh nghiệp, push phụ huynh, bảng bạn bè, app di động: hoàn tất trên code

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Nhóm học + bài tập | Không cần gì. Migration `w0f1a2b3c4d5` tự chạy. Giáo viên/HR đăng ký với vai trò "Giáo viên / Công ty". |
| Gói theo ghế | Cần cổng thanh toán đã bật (G3) hoặc demo. Giá ở `TEAM_PRICES_VND`, ghế tối thiểu/tối đa `TEAM_MIN_SEATS`/`TEAM_MAX_SEATS` trong `services/payments.py`. |
| Push phụ huynh | Cần `VAPID_PUBLIC_KEY`/`VAPID_PRIVATE_KEY` (đã dùng cho nhắc học). Chạy trong cron hằng giờ sẵn có; cửa sổ "chuỗi sắp mất" 19–21h giờ VN. |
| Bảng xếp hạng bạn bè | Không cần gì. |
| App di động | Chủ dự án chạy các bước trong `docs/MOBILE_APP.md` ở máy có Android Studio (Android) / Xcode (iOS); cần tài khoản Google Play (25 USD) và Apple Developer (99 USD/năm). Push gốc trên iOS cần thêm kênh FCM/APNs (chưa làm). |

Chưa làm trong G7: kênh FCM/APNs cho push trên app gốc; giáo viên xem chi tiết từng bài làm của học viên; xuất báo cáo nhóm ra PDF/CSV.

## G8 — Thi thử, hỏi Bo, báo cáo nhóm, hoá đơn VAT, FCM: hoàn tất trên code

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Thi thử IELTS/TOEIC | Không cần gì (không dùng AI). Migration `x1a2b3c4d5e6` tự chạy. Phần nghe dùng giọng server đã bật ở G2 (không có thì trình duyệt tự đọc). Thêm đề: thêm phần tử vào `EXAMS` trong `services/mock_exams.py` (mỗi câu có `explanation_vi`). Đổi hạn mức miễn phí: `FREE_DAILY_ATTEMPTS`. |
| Hỏi Bo | Cần `GEMINI_API_KEY`/`OPENAI_API_KEY` (đã có). Mỗi câu hỏi = 1 lượt gọi LLM. Đổi hạn mức miễn phí: `TUTOR_FREE_DAILY_LIMIT` trên Render (mặc định 5). |
| Báo cáo nhóm | Không cần gì; giáo viên bấm "Báo cáo · PDF / CSV" ở trang nhóm. |
| Hoá đơn VAT | App chỉ **thu thông tin** và để admin đánh dấu đã xuất; việc xuất hoá đơn điện tử thật làm trên phần mềm HĐĐT của chủ dự án (Viettel/MISA/…). Admin xem ở `/admin` → Doanh thu → "Đơn hàng & hoá đơn VAT". |
| FCM | Firebase console → Project settings → Service accounts → Generate new private key → dán **nguyên file JSON** vào biến `FIREBASE_SERVICE_ACCOUNT_JSON` trên Render. App Capacitor đăng ký token theo `docs/MOBILE_APP.md` (mục Push gốc). Chưa có khoá thì web push vẫn chạy như cũ. |

Chưa làm trong G8: ngân hàng đề lớn hơn (hiện 4 mini test, có thể thêm bằng tay hoặc sinh bằng Content Factory sau); Bo chưa đọc được ảnh/bài viết dài.

## G9 — Thi thử Speaking, đề AI sinh, kế hoạch ôn thi, Zalo OA: hoàn tất trên code

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Thi thử Speaking | Cần khoá LLM (đã có). Mỗi lần nộp = 1 lượt gọi AI. Trình duyệt cần Chrome/Edge/Safari có nhận diện giọng nói; đọc to chấm phát âm theo từ (Azure chưa nối vào đề thi, có thể thêm sau). Migration `y2b3c4d5e6f7` tự chạy. Thêm đề: `EXAMS` trong `services/speaking_exams.py`. |
| Đề thi AI sinh | Admin vào `/admin` → tab **Đề thi** → chọn kỳ thi/kỹ năng → "Sinh bản nháp" (30–60 giây, 1 lượt AI) → xem trước → **Duyệt**. Chỉ đề đã duyệt mới hiện với học viên. Nên đọc kỹ đáp án trước khi duyệt. |
| Kế hoạch ôn thi | Không cần gì. Học viên vào `/plan` (hoặc thẻ "Kế hoạch ôn thi" trên trang chủ) đặt kỳ thi, mục tiêu, ngày thi. |
| Zalo OA | 1) Tạo Zalo Official Account (loại Doanh nghiệp đã xác thực để gửi tin), 2) tạo ứng dụng tại developers.zalo.me, bật API OA, lấy **App ID**, **App Secret**; 3) cấp quyền OA cho app → lấy **refresh token** (công cụ OA → API → Lấy access token); 4) dán `ZALO_APP_ID`, `ZALO_APP_SECRET`, `ZALO_OA_ID`, `ZALO_OA_REFRESH_TOKEN`, `ZALO_OA_SECRET_KEY` (OA secret key, để xác thực webhook) lên Render; 5) khai báo webhook `https://<api>/api/v1/zalo/webhook` với các sự kiện `user_send_text`, `follow`, `unfollow`. Tin nhắn CS miễn phí trong cửa sổ 7 ngày sau khi người dùng nhắn OA; nhắc học hằng ngày giữ cửa sổ này mở. Chưa có khoá thì mục Zalo tự ẩn. |

Chưa làm trong G9: chấm phát âm Speaking bằng Azure (hiện theo từ); đề Speaking/Writing do AI sinh; gửi ZNS (tin theo mẫu, tính phí) khi hết cửa sổ 7 ngày.

## G10 — Podcast, câu lạc bộ nói, giáo viên xem bài, Stripe + chứng nhận, chi phí AI: hoàn tất trên code

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Podcast / video (`/listen`) | Không cần gì. 6 tập tĩnh A2–B2 trong `services/media_library.py` (lời thoại song ngữ, từ khoá, câu hỏi). Âm thanh là giọng đọc server theo từng nhân vật, chạm từ để tra + lưu sổ từ. Muốn kèm video: điền `youtube_id` (+ `start`/`end` giây) cho tập có lời thoại khớp video. XP chỉ lần đầu và khi cải thiện điểm; 100% được đá quý. |
| Câu lạc bộ nói (`/club`) | Cần khoá LLM (đã có); AI lỗi thì vẫn chạy bằng câu hỏi soạn sẵn. Phòng 2–4 người (tự luyện 1 người cũng được), 8 chủ đề trong `services/speaking_club.py`, mỗi người 3 lượt. Trình duyệt hỏi đáp bằng polling 2,5 giây, không cần dịch vụ realtime. Phòng riêng chỉ vào bằng mã. |
| Giáo viên xem bài + nhận xét | Không cần gì. Trong `/teacher/<nhóm>` bấm tên học viên → bài học, bài viết (đọc toàn văn + lỗi AI chỉ ra), thi thử, thi nói, bài tập; gửi nhận xét chung hoặc theo từng bài → học viên nhận thông báo và xem ở `/classes`. Giáo viên cũng cấp chứng nhận từ trang này. |
| Stripe (thẻ quốc tế, USD) | 1) Tạo tài khoản Stripe, lấy **Secret key** (`sk_live_…`); 2) Developers → Webhooks → Add endpoint `https://<api>/api/v1/billing/stripe/webhook`, chọn sự kiện `checkout.session.completed`, `checkout.session.expired`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed` → lấy **Signing secret** (`whsec_…`); 3) dán `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` lên Render (tuỳ chọn `USD_TO_VND`, mặc định 25.000 để thống kê doanh thu). Giá USD trong `services/payments.py` (Premium $4.99/tháng · $11.99/3 tháng · $39/năm; gia đình $8.99 · $74; theo ghế $3.99 · $34 mỗi ghế). Chỉ webhook có chữ ký đúng + đúng số tiền mới cộng Premium. Chưa có khoá thì nút thẻ quốc tế tự ẩn. |
| Chứng nhận hoàn thành | Không cần gì. Học viên xong 1 lộ trình mục tiêu → nhận ở **Hồ sơ**; giáo viên/doanh nghiệp cấp cho thành viên. Trang công khai `/certificate/<mã>` để nhà tuyển dụng kiểm tra, nút **In / Lưu PDF** (khổ A4 ngang). |
| Chi phí AI theo người dùng | Mặc định đã ghi (bảng `ai_usage`): mỗi lượt gọi LLM và mỗi lần tạo giọng đọc mới, ước tính theo ký tự. Xem ở `/admin` → tab **Chi phí AI**. Tuỳ chọn trên Render: đơn giá `AI_PRICE_GEMINI_IN/OUT`, `AI_PRICE_OPENAI_IN/OUT` (USD/1 triệu token), `TTS_PRICE_PER_MCHAR`; giới hạn mỗi người mỗi ngày `AI_DAILY_LIMIT_USD_FREE`, `AI_DAILY_LIMIT_USD_PREMIUM` (0 = không giới hạn; vượt thì tính năng AI trả lời bằng phương án dự phòng tới hôm sau). |

Migration `z3c4d5e6f7a8` tự chạy khi deploy.

Chưa làm trong G10: thêm video thật có bản quyền/khớp lời thoại; câu lạc bộ nói bằng giọng thật (WebRTC) thay cho nhận diện giọng nói + đọc to; hoàn tiền Stripe tự động; chứng nhận xuất file PDF phía server.

## G11 — Podcast AI, câu lạc bộ nói hẹn giờ, giáo viên chấm lại bài viết, hoàn tiền + biên nhận, cảnh báo chi phí AI: hoàn tất trên code

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Podcast do AI sinh | Admin vào `/admin` → tab **Podcast AI** → chọn trình độ, dạng (hội thoại / một người dẫn), chủ đề → "Sinh bản nháp" (1 lượt AI) → đọc lời thoại + đáp án → **Duyệt**. Tập đã duyệt hiện ở mục Podcast cho mọi học viên. Muốn có video: dán link YouTube có lời nói **khớp đúng** lời thoại và cho phép nhúng (tuỳ chọn giây bắt đầu/kết thúc). Không tự lấy video có bản quyền của người khác. |
| Câu lạc bộ nói hẹn giờ | 1) Workflow mới `.github/workflows/club-reminders.yml` chạy 10 phút/lần từ 6:00 đến 22:59 giờ VN, dùng **chung** 2 secret `REMINDER_API_URL` + `REMINDER_CRON_SECRET` đã có — không cần thêm gì. 2) Học viên tick "Hẹn giờ", chọn ngày giờ (10 phút → 14 ngày tới), chọn chủ đề; người khác bấm **Đăng ký** ở mục "Buổi nói sắp diễn ra" hoặc vào bằng mã. Trước ~15 phút mọi người nhận thông báo trong app + push (+ Zalo nếu đã liên kết). Chủ phòng mở được từ 10 phút trước giờ hẹn; phòng không ai mở tự đóng sau 2 giờ. Lưu ý: gọi 10 phút/lần giữ máy chủ Render gói free luôn thức trong khung giờ đó (vẫn trong hạn mức 750 giờ/tháng nếu chỉ có 1 dịch vụ free). |
| Giáo viên chấm lại bài viết | Không cần gì. Trong trang học viên (`/teacher/<nhóm>` → bấm tên) → tab Bài viết → mở bài → nhập điểm /100 (và band IELTS/TOEIC với đề thi) + nhận xét → học viên nhận thông báo, thấy điểm giáo viên ở **Luyện viết → Bài viết gần đây**. |
| Hoàn tiền + biên nhận | Admin → tab **Doanh thu** → bảng đơn hàng: **Biên nhận** (in/lưu PDF) và **Hoàn tiền**. Đơn Stripe hoàn qua API ngay; đơn VNPay/MoMo phải hoàn trên cổng trước rồi bấm để ghi nhận. Hoàn tiền trừ lại thời hạn Premium đã mua. Hoàn tiền trực tiếp trên trang Stripe cũng tự ghi nhận nếu webhook Stripe có thêm sự kiện **`charge.refunded`**. Người mua xem "Lịch sử thanh toán" + biên nhận ở `/upgrade`. Tuỳ chọn trên Render để in thông tin người bán: `SELLER_NAME`, `SELLER_TAX_CODE`, `SELLER_ADDRESS`, `SELLER_EMAIL`. Biên nhận **không** thay hoá đơn GTGT. |
| Cảnh báo chi phí AI | Đặt trên Render: `AI_ALERT_DAILY_USD` (tổng cả app/ngày) và/hoặc `AI_ALERT_USER_DAILY_USD` (một tài khoản/ngày); 0 = tắt. Job nhắc học hằng giờ kiểm tra và email cho `ADMIN_EMAILS` (cần `RESEND_API_KEY`), mỗi ngưỡng tối đa 1 lần/ngày; tab **Chi phí AI** hiện băng cảnh báo đỏ. |

Migration `a4d5e6f7a8b9` tự chạy khi deploy. Sửa kèm: 3 test thử thách hằng ngày từng đỏ khi chạy CI sau 17:00 UTC (test dùng ngày UTC, code dùng ngày giờ VN).

Chưa làm trong G11: thư viện video có bản quyền (cần hợp đồng với nhà sản xuất); câu lạc bộ nói bằng giọng thật (WebRTC); hoàn tiền một phần; hoá đơn điện tử tự động.

## G12 — Podcast tự động, câu lạc bộ nói hằng tuần của lớp, rubric IELTS, hoá đơn điện tử Viettel, chế độ tiết kiệm AI: hoàn tất trên code

| Hạng mục | Cần chủ dự án làm để chạy thật |
|---|---|
| Podcast tự sinh theo lịch | Render: `PODCAST_AUTO_DRAFTS` = số bản nháp chờ duyệt muốn giữ cho mỗi trình độ (vd. `2`; `0` = tắt), tuỳ chọn `PODCAST_AUTO_LEVELS` (mặc định `A2,B1,B2`). Content Factory (2 giờ/lần) tạo tối đa 1 tập mỗi lần chạy, mỗi trình độ ≤ 1 tập/ngày, chủ đề luân phiên; vẫn phải **duyệt** ở `/admin` → Podcast AI (tập tự động có nhãn "Tự động"); admin nhận email khi có tập mới (nếu đã bật email). |
| Câu lạc bộ nói hằng tuần của lớp | Không cần gì thêm (dùng lịch 10 phút/lần của G11). Giáo viên vào trang lớp → "Câu lạc bộ nói hằng tuần" → chọn thứ, giờ (giờ VN), chủ đề hoặc luân phiên. Phòng buổi kế tiếp tự mở, cả lớp nhận thông báo; học viên đăng ký ở **Lớp học** hoặc **Câu lạc bộ nói**; người đăng ký đầu tiên làm chủ phòng; trước 15 phút: người đăng ký được nhắc (push/Zalo), cả lớp nhận thông báo trong app. Phòng chỉ thành viên lớp vào được. |
| Rubric IELTS 4 tiêu chí | Không cần gì. Với bài IELTS, giáo viên chấm Đáp ứng đề · Mạch lạc · Từ vựng · Ngữ pháp (0–9, bước 0,5); band tổng làm tròn theo luật IELTS, điểm /100 mặc định = band/9; học viên thấy từng tiêu chí ở **Luyện viết → Bài viết gần đây**. |
| Hoá đơn điện tử Viettel S-Invoice | Xem mục 3.6 trong `docs/VIEC_CAN_LAM.md` (tài khoản API, mẫu số, ký hiệu, thuế suất). Admin → Doanh thu → nút **Xuất HĐĐT** từng đơn; hoặc `EINVOICE_AUTO=business` (đơn có yêu cầu hoá đơn) / `all` (mọi đơn) để job hằng giờ tự xuất cho đơn đã trả trong 3 ngày. Số hoá đơn + mã tra cứu hiện trên biên nhận. Lần đầu nên thử với tài khoản **demo** của Viettel (đặt `VIETTEL_SINVOICE_API_URL`/`LOGIN_URL` theo hướng dẫn Viettel). Hoàn tiền đơn đã có HĐĐT: lập hoá đơn điều chỉnh/huỷ trên trang Viettel. |
| Chế độ tiết kiệm AI | Render: `AI_ECONOMY_AT_USD` (vd. `3` = từ khi cả app tốn 3 USD/ngày) + `AI_ECONOMY_GEMINI_MODEL` / `AI_ECONOMY_OPENAI_MODEL` (tên mô hình rẻ hơn, lấy từ trang giá của Google/OpenAI). Mô hình thường: `GEMINI_MODEL`, `OPENAI_MODEL`. Nếu mô hình tiết kiệm lỗi (sai tên…) hệ thống tự gọi lại bằng mô hình thường. Tab Chi phí AI hiện băng khi đang tiết kiệm. |

Migration `b5e6f7a8b9c0` tự chạy khi deploy.

Chưa làm trong G12: tích hợp VNPT/MISA (chỉ Viettel); tải file PDF hoá đơn từ Viettel về app; lập hoá đơn điều chỉnh tự động khi hoàn tiền; podcast tự sinh có giọng đọc riêng từng nhân vật bằng nhiều giọng neural.

## G13 — gợi ý tiếp theo

Bảng điều khiển phụ huynh trên ứng dụng di động (push gốc) · Bài kiểm tra định kỳ hằng tháng tự chấm cho lớp · Báo cáo tiến bộ theo rubric cho giáo viên (biểu đồ 4 tiêu chí theo thời gian) · Hoá đơn VNPT/MISA · Đề Speaking/Writing do AI sinh có duyệt.

## Câu hỏi còn mở với chủ dự án

- Số liệu trên landing ("1.247 học viên", "4,9 sao", lời đánh giá) là thật hay cần thay?
- Bảng giá trên landing: giữ hay ẩn cho tới khi có thanh toán thật? Giá 99K/tháng – 799K/năm?
- Dịch vụ chấm phát âm đến từng âm (G2 · hạng mục 9, xem `docs/G2_CHAM_PHAT_AM_SO_SANH.md`) và cổng thanh toán (G3).
- Thêm kênh nhắc qua Zalo OA? Có làm "học thử không cần đăng ký"?
