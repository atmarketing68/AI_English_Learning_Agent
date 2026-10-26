# AI AGENT ENGLISH (AGEN) — ghi chú cho Claude

App học tiếng Anh bằng AI cho người Việt. **Đọc `docs/ROADMAP_STATUS.md` trước** — nó ghi việc đã xong,
việc chủ dự án còn phải làm và hạng mục tiếp theo. Cập nhật file đó khi xong mỗi hạng mục.

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
  (không shell), chat Bo dùng class `chat-*`, báo cáo nhóm in `app/teacher/[groupId]/report`.
- Lỗi/LLM không được làm hỏng luồng học: luôn có fallback.

## Kiểm tra trước khi đẩy
- Backend (Python 3.12; 3.13 không build được pydantic đã pin):
  `cd agen-backend && python -m pytest -q`
- Frontend: `cd agen-web && npx eslint src && npx tsc --noEmit -p . && npm run build`
- Test chạy app thật: backend `DATABASE_URL=sqlite:///<file> uvicorn main:app --port 8000`, frontend
  `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 npm run build && npx next start`, rồi Playwright (Chromium có sẵn).
- Lưu ý test: fixture `client` vẫn chạy startup trên DB dev, và BackgroundTasks dùng `SessionLocal` thật — seed dữ liệu
  qua fixture `db_session`, patch job nền khi cần.
