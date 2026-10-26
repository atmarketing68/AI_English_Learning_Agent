# Trạng thái lộ trình nâng cấp — AI AGENT ENGLISH

> File này là "bộ nhớ" giữa các phiên làm việc. Cập nhật mỗi khi xong một hạng mục.
> Kế hoạch gốc (đã được chủ dự án duyệt): Claude Doc "Kế hoạch nâng cấp AGEN — Audit & Lộ trình"
> https://claude.ai/artifact/7PHjES4CK5zB9i8rBxrCuT

Cập nhật lần cuối: 2026-10-26 (G2 + G3).

Web production: https://ai-english-learning-agent.atmarketing.vn · Backend: https://agen-api.onrender.com

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
| — | Sửa lỗi đăng ký/đăng nhập: báo lỗi rõ (mất kết nối, mật khẩu thiếu số, email trùng, sai mật khẩu), lỗi 500 vẫn có CORS, `APP_URL` tự vào CORS (`lib/apiError.ts`) | #12 |

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

**G2, G3, G4 và G5 hoàn tất (trên code).** Các phần cần khoá/đăng ký dịch vụ mới chạy thật — xem mục việc chủ dự án.

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
4. **`ALLOWED_ORIGINS` / `APP_URL` trên Render = `https://ai-english-learning-agent.atmarketing.vn`** (tên miền thật của web;
   trước đây để nhầm `agen-web.vercel.app` nên đăng ký bị chặn).
   Sai URL thì mọi lệnh gọi API bị chặn — đăng ký báo "Không kết nối được máy chủ".
5. Chạy thử: Actions → *Content Factory* → Run workflow (limit 10); Actions → *Learning reminders* → Run.

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

## G6 — gợi ý tiếp theo

Thử thách bạn bè · Thông báo đẩy khi con xuống hạng/giữ chuỗi cho phụ huynh · Trang landing làm mới theo giao diện mới ·
Bo nói bằng giọng neural · Báo cáo PDF cho phụ huynh.

## Câu hỏi còn mở với chủ dự án

- Số liệu trên landing ("1.247 học viên", "4,9 sao", lời đánh giá) là thật hay cần thay?
- Bảng giá trên landing: giữ hay ẩn cho tới khi có thanh toán thật? Giá 99K/tháng – 799K/năm?
- Dịch vụ chấm phát âm đến từng âm (G2 · hạng mục 9, xem `docs/G2_CHAM_PHAT_AM_SO_SANH.md`) và cổng thanh toán (G3).
- Thêm kênh nhắc qua Zalo OA? Có làm "học thử không cần đăng ký"?
