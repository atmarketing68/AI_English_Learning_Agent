# AGEN Backend

Backend API cho **AI English Learning Agent (AGEN)** — xây dựng bằng Python FastAPI.

> 📄 Hướng dẫn khởi chạy đầy đủ (backend + frontend + pilot + deploy) nằm ở
> **[README gốc của dự án](../README.md)**. Hướng dẫn sử dụng cho người học ở
> **[docs/HUONG_DAN_SU_DUNG.md](../docs/HUONG_DAN_SU_DUNG.md)**.

## 🏗️ Cấu trúc

```
agen-backend/
├── app/
│   ├── api/          # API Routers (auth, learner, lessons, curriculum, parent, admin, ...)
│   ├── core/         # Config, Database, Security
│   ├── models/       # SQLAlchemy models (Learner Digital Twin, curriculum, ...)
│   ├── services/     # Business logic (adaptive engine, evaluation, content factory, ...)
│   └── agents/       # AI multi-agent + orchestrator
├── alembic/          # Database migrations
├── scripts/          # CLI tools (pregenerate_content.py, ...)
├── tests/            # pytest suite
├── main.py           # FastAPI entry point
└── requirements.txt
```

## 🚀 Khởi chạy nhanh (Development)

```bash
python -m venv venv
venv\Scripts\activate                 # Windows
pip install -r requirements.txt
copy .env.example .env                # điền GEMINI_API_KEY, SECRET_KEY, ADMIN_EMAILS...
python -m uvicorn main:app --port 8000
```

- Swagger UI: http://localhost:8000/docs (chỉ bật khi `APP_ENV=development`)
- Health: http://localhost:8000/health

## 🏭 Content Factory (sinh sẵn nội dung bài học)

Sinh + cache nội dung một lần để học viên không phải chờ AI:

```bash
python scripts/pregenerate_content.py --level A1 --auto-approve
python scripts/pregenerate_content.py --code A2-U01-L01 --auto-approve
```

Xem/duyệt nội dung tại **/admin → tab Kho nội dung** (yêu cầu email trong `ADMIN_EMAILS`).

## 🧪 Tests & Migrations

```bash
pytest -q                                    # chạy toàn bộ test
alembic upgrade head                         # áp migration mới nhất
alembic revision --autogenerate -m "msg"     # tạo migration sau khi đổi model
```

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Auth | JWT (python-jose) + bcrypt |
| AI | Google Gemini 3.6 Flash / OpenAI GPT-4o-mini (fallback) |
| Migrations | Alembic |
| Rate limiting | slowapi |

## 📍 Nhóm API chính (đều dưới tiền tố `/api/v1`)

| Nhóm | Tiền tố | Chức năng |
|------|---------|-----------|
| Auth | `/auth` | Đăng ký, đăng nhập, refresh, xác thực email |
| Learner | `/learner` | Hồ sơ học viên (Digital Twin) |
| Placement | `/placement` | Bài kiểm tra đầu vào adaptive |
| Lessons | `/lessons` | Tạo/lấy/hoàn thành bài học |
| Curriculum | `/curriculum` | Lộ trình học + bài tiếp theo |
| Speaking | `/speaking` | Roleplay + chấm phát âm |
| Writing | `/writing` | Đề bài + chấm bài viết |
| Analytics | `/analytics` | Tổng quan + báo cáo tiến bộ |
| Gamification | `/gamification` | XP, streak, huy hiệu, thử thách |
| Notifications | `/notifications` | Thông báo trong app |
| Billing | `/billing` | Gói + hạn mức (pilot) |
| Parent | `/parent` | Liên kết con + báo cáo tuần |
| Admin | `/admin` | Giám sát chất lượng AI + kho nội dung |
| Privacy | `/privacy` | Đồng ý, xuất/xóa dữ liệu |
