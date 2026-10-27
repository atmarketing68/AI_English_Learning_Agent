# AI AGENT ENGLISH (AGEN) — ghi chú cho Claude

App học tiếng Anh bằng AI cho người Việt. **Đọc `docs/ROADMAP_STATUS.md` trước** — nó ghi việc đã xong,
việc chủ dự án còn phải làm và hạng mục tiếp theo. Cập nhật file đó khi xong mỗi hạng mục.
Mọi cấu hình / việc chủ dự án phải tự làm (khoá, biến môi trường, webhook, vận hành) ghi vào checklist
`docs/VIEC_CAN_LAM.md` (theo mức ưu tiên, có bước + cách kiểm tra) — bổ sung file này ở mỗi giai đoạn có biến mới.

## Làm việc với chủ dự án
- Trả lời bằng tiếng Việt, gọn. Chủ dự án bận: tự làm trọn gói, chỉ hỏi khi thật sự cần quyết định.
- Mỗi việc: nhánh `claude/...` → PR → CI xanh → **merge chỉ khi chủ dự án nhắn "deploy"** (merge = deploy production).
- Không commit secret. Tính năng cần khoá (PostHog, web push, email, cron) phải tự tắt êm khi chưa cấu hình.

## Cấu trúc
- `agen-backend/` — FastAPI + SQLAlchemy + Alembic (Postgres trên Render, SQLite khi dev/test). API dưới `/api/v1`.
  - `app/api/` router · `app/services/` nghiệp vụ · `app/agents/` gọi LLM (Gemini → OpenAI dự phòng) · `app/models/`
  - Migration mới: `alembic/versions/`, `down_revision` = revision mới nhất. Render tự chạy `alembic upgrade head`.
- `agen-web/` — Next.js 16 (App Router), React 19, zustand, framer-motion, lucide-react. **Đọc `agen-web/AGENTS.md`**:
  Next 16 khác bản cũ, xem docs trong `node_modules/next/dist/docs/` trước khi dùng API lạ.
  - Giao diện: token màu/khoảng cách trong `src/app/globals.css` (phong cách Apple, sáng/tối tự động). Dùng class sẵn
    (`card`, `btn`, `choice`, `segmented`, `review-feedback`…) thay vì style mới.
  - Điều hướng: `src/components/ui/navigation.ts` (sidebar + tab bar, trang nào hiện shell).
- `.github/workflows/`: `ci.yml` (pytest + lint/build), `reminders.yml` (hằng giờ), `content-factory.yml` (2 giờ/lần).

## Quy ước quan trọng
- Thời gian lưu DB là **UTC naive**; "ngày" của người học theo giờ VN qua `app/core/timeutil.py`.
- Hoạt động học ghi `LearningEvent`; nhiệm vụ ngày & mục tiêu tuần tính từ đó (không cần hook mới).
- Bài học: bài tập mới dựng từ nội dung bài trong `app/services/exercise_builder.py`; ôn tập FSRS ở `app/services/srs.py`.
- Nói & nghe (G2): tình huống + nhân vật ở `app/services/speaking_scenarios.py` (không cần LLM cho bước 1–2); chấm theo
  từ ở `pronunciation_service.py`; giọng đọc server ở `tts_service.py` (`/audio/tts`, tự tắt khi không có khoá). Web:
  mọi nút nghe đi qua `playText()` trong `lib/speechService.ts` (server → trình duyệt), micro qua `lib/useSpeechRecorder.ts`.
  Chấm từng âm: `pronunciation_azure.py` (bật khi có `AZURE_SPEECH_KEY`); web gửi WAV qua `scoreAttempt()`.
- Tăng trưởng (G3): khách `is_guest` (`/auth/guest`, `/auth/claim`); thanh toán `services/payments.py` (chỉ IPN ký
  đúng mới cộng Premium); giải đấu `services/league.py`; email phụ huynh `services/parent_digest.py` (cron nhắc học);
  khoá mục tiêu `services/goal_tracks.py` + `GoalTrackProgress` (bài tạo qua `/lessons/generate` với `track_code`).
- Lớp "vui" (G4): đá quý/cửa hàng `services/shop.py` (`award_gems` ở bài học, nhiệm vụ, mục tiêu tuần, giải đấu, Blitz);
  Blitz `GET/POST /review/blitz*`; giải đấu nhóm 30 + 4 hạng `services/league.py` (`LeagueMembership`, 1 dòng/người/tuần).
  Web: 2 skin qua `<html data-skin="vivid|classic">` (`store/skinStore.ts`, `components/ui/SkinProvider.tsx`; token CSS
  trong `globals.css` dưới `:root[data-skin="vivid"]`); mascot `components/ui/Mascot.tsx` **tự ẩn ở skin classic** —
  người lớn/phụ huynh phải luôn thấy giao diện chuyên nghiệp; avatar `components/ui/Avatar.tsx`.
- G5: gói gia đình = `Subscription.plan == "family"` trên tài khoản phụ huynh, con được Premium qua
  `subscription_service.premium_source()` (luôn dùng `is_premium()`/`premium_source()`, đừng đọc `sub.plan` trực tiếp);
  doanh thu `GET /admin/revenue/summary`; band thi: `writing_agent.EXAM_GENRES` + `exam_band` chỉ với genre thi.
  Web: lớp "pro" cho skin classic ở cuối `globals.css` (`.pro-hero`, `.stat-card`, `.quick-tile`, `SkillRing`, `CountUp`) —
  mọi rule chỉ-classic dùng tiền tố `:root:not([data-skin="vivid"])`.
- G6: bạn học `services/friends.py` (1 dòng/cặp, `a_id < b_id`, thử thách đôi tính từ `league.weekly_xp`); giọng Bo
  `/audio/tts?lang=vi` → web `playVietnamese()` trong `lib/speechService.ts`; báo cáo in `app/parent/report/[learnerId]`
  (CSS `@media print` ở cuối `globals.css`); gói gia đình chỉ phủ `subscription_service.covered_children()` (4 con đầu).
- G7: vai trò `teacher` (không có learner/parent profile) sở hữu `Group` (`services/groups.py`); bài tập hoàn thành khi
  `lessons.finish_lesson` gọi `groups.mark_done_on_finish` (bài tập đã start, cùng kỹ năng, cũ nhất trước). Gói theo ghế
  `plan=team` + `Subscription.seats`, phủ `subscription_service.team_covered_learners()`. Push phụ huynh:
  `PushSubscription.user_id` (learner_id có thể null), gửi trong `parent_digest.run_parent_digests` qua `reminders.push_to_user`.
  Web: trang chủ nhóm `app/teacher`, học viên `app/classes`, `/learn?assignment=<id>`.
- G8: đề thi thử tĩnh trong `services/mock_exams.py` (`grade()` chấm xác định, `estimate_score()` quy đổi band/điểm), lưu `ExamAttempt`;
  Bo hỏi đáp `agents/tutor_agent.py` qua orchestrator `tutor_answer` + `TutorMessage` (fallback không trừ lượt miễn phí); CSV nhóm
  `groups.report_csv`; hoá đơn VAT `PaymentOrder.invoice_info`/`invoice_issued_at`; FCM `services/fcm.py` (gọi trong
  `reminders.push_to_learner/push_to_user`, tắt khi không có `FIREBASE_SERVICE_ACCOUNT_JSON`). Web: `/exams/<id>` là chế độ tập trung
  (không shell), chat Bo dùng class `chat-*`, báo cáo nhóm in `app/teacher/[groupId]/report`. Hero 3D landing:
  `components/landing/HeroScene3D.tsx` + CSS `.h3d-*` — vị trí chiều sâu phải dùng `transform`/`--z` trong keyframes, **không** dùng
  thuộc tính `translate` 3 giá trị (trình nén CSS của Next bỏ mất).
- G9: thi thử Speaking `services/speaking_exams.py` + `SpeakingExamAttempt` (start → answer từng task → finish gọi agent
  `speaking_exam_evaluation`, fallback `heuristic_estimate`); đề AI sinh `agents/exam_agent.py` → `exam_generator.normalize_paper`
  → `GeneratedExam` (chỉ `approved` mới vào `mock_exams.list_exams(db)`, id `gen-<uuid>`); kế hoạch ôn thi `services/study_plan.py`
  (`LearnerProfile.exam_target/exam_target_score/exam_date`, không LLM); Zalo OA `services/zalo.py` (token trong `AppConfig`,
  webhook `/zalo/webhook` liên kết bằng `User.zalo_link_code`, kênh gửi trong `reminders.zalo_to_user` + `parent_digest._alert`).
  Web: `/exams/speaking/<id>` dùng `SpeechRecognizer` trực tiếp (gộp transcript, tự nối lại), `/plan`, tab "Đề thi" ở admin.
- G10: podcast tĩnh `services/media_library.py` (`MediaProgress`, `/media`, web `/listen` dùng `AudioPlayerTTS`); câu lạc bộ nói
  `services/speaking_club.py` + agent `club_moderator` (`SpeakingRoom`/`RoomMember`/`RoomMessage`, web `/club/<id>` polling `after=seq`);
  giáo viên xem bài `groups.member_detail` + `TeacherFeedback` (web `app/teacher/[groupId]/member/[learnerId]`); chứng nhận
  `services/certificates.py` (trang công khai `/certificate/<mã>`, trong ALWAYS_CLASSIC, CSS `.cert-*`, `@page cert` khổ ngang);
  Stripe trong `services/payments.py` (`PaymentOrder.currency/amount_foreign`, chỉ webhook ký đúng + đúng số tiền mới cộng).
  Chi phí AI: `core/usage_context.py` (middleware ASGI đặt user + feature, orchestrator đặt feature = tên agent) →
  `services/ai_usage.py` ghi `AiUsage` trong `llm_client.get_llm_response` và `tts_service.synthesize`; test đổi
  `ai_usage._session_factory` sang engine test. Giới hạn ngày ném `LLMError(is_quota=True)` → các luồng dùng fallback sẵn có.
- G11: podcast AI `agents/podcast_agent.py` → `podcast_generator.normalize_episode` → `GeneratedEpisode` (chỉ `approved` vào
  `media_library.list_episodes(db)`, id `gen-<uuid>`, `youtube_id` → kind video); phòng nói hẹn giờ `SpeakingRoom.scheduled_at` +
  `RoomMember.reminded_at`, `speaking_club.run_reminders` (cron `/club/cron/remind` 10 phút/lần + fallback trong `/reminders/cron/run`);
  giáo viên chấm lại `WritingSubmission.teacher_*` qua `groups.grade_writing` (tạo `TeacherFeedback` + thông báo); hoàn tiền
  `payments.refund_order`/`record_refund` (trạng thái `refunded`, trừ lại thời hạn Premium; Stripe `charge.refunded` tìm đơn theo
  `provider_txn`), biên nhận `/billing/orders/<id>/receipt` + web `/receipt/<id>` (ALWAYS_CLASSIC); cảnh báo chi phí
  `ai_usage.check_alerts` (cờ ngày trong `AppConfig`, chạy trong cron hằng giờ). Ngày của học viên luôn theo `local_today()` — cả trong test.
- G12: podcast tự động `podcast_generator.run_auto_drafts` (gọi trong `/admin/content/cron`, tối đa 1 lượt AI/lần chạy,
  `GeneratedEpisode.auto`); lịch câu lạc bộ lớp `GroupClubSchedule` → `speaking_club.ensure_group_rooms` (chạy trong `run_reminders`),
  phòng lớp có `group_id`/`schedule_id`, `host_learner_id` có thể null (người đăng ký đầu làm chủ), chỉ thành viên lớp vào được;
  rubric IELTS `WritingSubmission.teacher_rubric` + `groups.ielts_overall` (làm tròn kiểu IELTS); HĐĐT Viettel `services/einvoice.py`
  (token cookie `access_token`, `createInvoice/{MST}`, `transactionUuid` lưu trước khi gọi để không xuất trùng), cron hằng giờ `run_auto`;
  chế độ tiết kiệm `ai_usage.economy_active()` (cache 60 giây) + `llm_client.economy_model()`, mô hình tiết kiệm lỗi → gọi lại mô hình thường.
- G13: bài kiểm tra lớp `GroupTest` (`kind` mock|speaking, `opens_on`/`due_on`) trong `services/groups.py` (`create_test`, `test_results`,
  `open_test_for` = điều kiện miễn lượt miễn phí, `remind_due_tests` trong cron nhắc học); lần làm tính điểm gắn `ExamAttempt.group_test_id` /
  `SpeakingExamAttempt.group_test_id` (web truyền `?test=<id>`; `_attempts_today` bỏ qua bài có `group_test_id`). Biểu đồ rubric
  `groups.rubric_history` → web `components/teacher/RubricChart.tsx`. Đề Speaking AI: agent `speaking_exam_generation` →
  `speaking_exam_generator.normalize_exam` (thời gian do server đặt) → `GeneratedSpeakingExam`; `speaking_exams.list_exams(db)/get_exam(id, db)`
  phải truyền `db` để thấy đề `gen-…`. Push gốc trên web: `lib/nativePush.ts` dùng `window.Capacitor` (không cài npm), `NativePushBridge`
  trong AppShell, `authStore.logout` gỡ token; cảnh báo phụ huynh chạy cả khi chỉ có FCM (`parent_digest.can_alert`).
- SEO: `app/page.tsx` là server (metadata + JSON-LD), giao diện landing ở `components/landing/LandingPage.tsx` (client); FAQ dùng chung
  `lib/seo/landingFaqs.ts`. Trang nội dung: dữ liệu `lib/seo/pages.ts` → `components/seo/SeoLanding.tsx`, thêm trang = thêm mục + thư mục
  `app/<slug>/page.tsx` + thêm slug vào `ALWAYS_CLASSIC` (SkinProvider). Trang app mới sau đăng nhập → thêm vào `PRIVATE` trong `app/robots.ts`.
  Không ghi số liệu/đánh giá không có thật vào nội dung SEO; URL gốc qua `lib/seo/site.ts` (`NEXT_PUBLIC_SITE_URL`).
- Lỗi/LLM không được làm hỏng luồng học: luôn có fallback.

## Kiểm tra trước khi đẩy
- Backend (Python 3.12; 3.13 không build được pydantic đã pin):
  `cd agen-backend && python -m pytest -q`
- Frontend: `cd agen-web && npx eslint src && npx tsc --noEmit -p . && npm run build`
- Test chạy app thật: backend `DATABASE_URL=sqlite:///<file> uvicorn main:app --port 8000`, frontend
  `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 npm run build && npx next start`, rồi Playwright (Chromium có sẵn).
- Lưu ý test: fixture `client` vẫn chạy startup trên DB dev, và BackgroundTasks dùng `SessionLocal` thật — seed dữ liệu
  qua fixture `db_session`, patch job nền khi cần.
