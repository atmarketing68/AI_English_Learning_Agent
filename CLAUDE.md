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
- Lỗi/LLM không được làm hỏng luồng học: luôn có fallback.

## Kiểm tra trước khi đẩy
- Backend (Python 3.12; 3.13 không build được pydantic đã pin):
  `cd agen-backend && python -m pytest -q`
- Frontend: `cd agen-web && npx eslint src && npx tsc --noEmit -p . && npm run build`
- Test chạy app thật: backend `DATABASE_URL=sqlite:///<file> uvicorn main:app --port 8000`, frontend
  `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 npm run build && npx next start`, rồi Playwright (Chromium có sẵn).
- Lưu ý test: fixture `client` vẫn chạy startup trên DB dev, và BackgroundTasks dùng `SessionLocal` thật — seed dữ liệu
  qua fixture `db_session`, patch job nền khi cần.
