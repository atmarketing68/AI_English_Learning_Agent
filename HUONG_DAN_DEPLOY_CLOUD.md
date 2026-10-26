# ☁️ HƯỚNG DẪN DEPLOY AGEN LÊN CLOUD

> **Mục tiêu:** Deploy toàn bộ hệ thống AGEN (Backend + Frontend + Database) lên cloud hoàn toàn miễn phí (hoặc chi phí rất thấp).
>
> **Kiến trúc đích:**
> ```
> [Người dùng] → [Vercel — Next.js Frontend]
>                        ↓ API calls (HTTPS)
>               [Render.com — FastAPI Backend]
>                        ↓
>               [Render.com — PostgreSQL DB]
> ```

---

## 📋 Tổng quan & Chi phí

| Dịch vụ | Mục đích | Gói miễn phí | Giá nâng cấp |
|---|---|---|---|
| **Render.com** | Backend (FastAPI) | ✅ 750h/tháng (ngủ sau 15 phút) | $7/tháng (always-on) |
| **Render.com** | PostgreSQL | ✅ 1GB, 90 ngày | $7/tháng (vĩnh viễn) |
| **Vercel** | Frontend (Next.js) | ✅ Không giới hạn | $20/tháng (Pro) |
| **Google AI Studio** | Gemini API | ✅ ~1500 req/ngày | Pay-as-you-go |

> ⚠️ **Lưu ý gói Free của Render:**
> - Backend **ngủ** sau 15 phút không có request → lần đầu vào sẽ chờ ~30 giây.
> - Database free **tự xóa sau 90 ngày** — hãy upgrade trước hạn hoặc backup dữ liệu.

---

## 🔑 Chuẩn bị trước khi deploy

### 1. Tài khoản cần có

- [ ] **GitHub** — lưu code: https://github.com
- [ ] **Render.com** — backend + database: https://render.com
- [ ] **Vercel** — frontend: https://vercel.com
- [ ] **Google AI Studio** — Gemini API key: https://aistudio.google.com

### 2. Lấy Gemini API Key

1. Truy cập https://aistudio.google.com/app/apikey
2. Nhấn **"Create API Key"**
3. Chọn project Google Cloud (hoặc tạo mới)
4. Sao chép key — lưu lại, sẽ cần ở bước sau

### 3. Đẩy code lên GitHub

Nếu chưa có repo GitHub, tạo repo mới và push:

```bash
# Tại thư mục gốc dự án (AI_English_Learning_Agent/)
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<username>/agen.git
git push -u origin main
```

> ✅ Đảm bảo file `.gitignore` đã loại trừ `.env`, `venv/`, `.next/`, `node_modules/`, `*.db`

---

## 🚀 BƯỚC 1 — Deploy Backend lên Render.com

Render hỗ trợ **Blueprint** — đọc file `render.yaml` và tự tạo toàn bộ hạ tầng.

### 1.1 — Tạo tài khoản & kết nối GitHub

1. Vào https://render.com → **"Get Started for Free"**
2. Đăng ký bằng GitHub (khuyến nghị — để Render có quyền đọc repo)
3. Sau khi đăng ký, vào **Dashboard**

### 1.2 — Tạo Blueprint (tự động tạo Backend + Database)

1. Nhấn **"New +"** → chọn **"Blueprint"**
2. Chọn GitHub repo của bạn (ví dụ: `username/agen`)
3. Render sẽ tìm thấy file `agen-backend/render.yaml` tự động
4. Xem lại danh sách services sẽ được tạo:
   - `agen-api` — Web Service (FastAPI, Docker)
   - `agen-db` — PostgreSQL database
5. Nhấn **"Apply"**

> 📌 **Nếu Render không tự tìm thấy `render.yaml`**, hãy chỉ định `rootDir = agen-backend` trong cài đặt.

### 1.3 — Cài đặt biến môi trường bí mật

Sau khi Blueprint được tạo, vào **Dashboard → agen-api → Environment**:

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `GEMINI_API_KEY` | `AIza...` | Key lấy từ Google AI Studio |
| `OPENAI_API_KEY` | *(bỏ trống)* | Không bắt buộc nếu dùng Gemini |
| `ADMIN_EMAILS` | `admin@email.com` | Email tài khoản quản trị |
| `SECRET_KEY` | *(tự sinh)* | Render tự generate — không cần sửa |
| `DATABASE_URL` | *(tự inject)* | Render tự kết nối — không cần sửa |

> 🔐 **Chỉ cần set `GEMINI_API_KEY` và `ADMIN_EMAILS`** — các biến khác đã được cấu hình sẵn trong `render.yaml`.

Để set biến:
1. Vào **Environment** tab của service `agen-api`
2. Tìm `GEMINI_API_KEY` → nhấn biểu tượng bút chì (edit)
3. Nhập giá trị → **Save Changes**

### 1.4 — Trigger Deploy lần đầu

1. Vào **Dashboard → agen-api → Deploys**
2. Nhấn **"Deploy latest commit"**
3. Xem log deploy — quá trình gồm:
   - Build Docker image (~3-5 phút)
   - Chạy `alembic upgrade head` (tạo bảng database)
   - Khởi động uvicorn server

### 1.5 — Kiểm tra Backend hoạt động

Sau khi deploy xong, URL backend sẽ có dạng: `https://agen-api.onrender.com`

Kiểm tra:
```bash
# Health check (chạy trên terminal)
curl https://agen-api.onrender.com/health

# Kết quả mong đợi:
# {"status": "ok", "version": "1.0.0"}
```

Hoặc mở trình duyệt: `https://agen-api.onrender.com/health`

> ⚠️ Lần đầu có thể mất 1-2 phút để service khởi động hoàn toàn.

### 1.6 — Ghi lại URL Backend

**Lưu URL này lại** — sẽ cần ở Bước 2:
```
https://agen-api.onrender.com
```

---

## 🌐 BƯỚC 2 — Deploy Frontend lên Vercel

### 2.1 — Tạo tài khoản Vercel

1. Vào https://vercel.com → **"Start Deploying"**
2. Đăng ký bằng GitHub
3. Authorize Vercel truy cập repo

### 2.2 — Import Project

1. Nhấn **"Add New..."** → **"Project"**
2. Tìm repo `agen` → nhấn **"Import"**
3. Cấu hình:

| Cài đặt | Giá trị |
|---|---|
| **Root Directory** | `agen-web` |
| **Framework Preset** | Next.js (tự động phát hiện) |
| **Build Command** | `npm run build` |
| **Output Directory** | `.next` |

### 2.3 — Cài đặt biến môi trường

Trong phần **"Environment Variables"** của project mới:

| Tên biến | Giá trị |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://agen-api.onrender.com/api/v1` |

> ⚠️ **Quan trọng:** Điền đúng URL backend từ Bước 1, bao gồm `/api/v1` ở cuối.

### 2.4 — Deploy

Nhấn **"Deploy"** → Vercel sẽ:
1. Clone repo
2. `npm install`
3. `npm run build`
4. Deploy lên CDN toàn cầu

Quá trình mất ~2-3 phút. Sau khi xong, URL frontend sẽ có dạng:
```
https://agen-web.vercel.app
```
hoặc URL tùy chỉnh nếu bạn có domain riêng.

### 2.5 — Ghi lại URL Frontend

**Lưu URL frontend lại** — cần dùng ở Bước 3.

---

## 🔗 BƯỚC 3 — Cập nhật CORS (kết nối hai chiều)

Backend cần biết URL frontend để cho phép request (CORS policy).

### 3.1 — Cập nhật ALLOWED_ORIGINS trên Render

1. Vào **Render Dashboard → agen-api → Environment**
2. Tìm biến `ALLOWED_ORIGINS`
3. Sửa giá trị thành URL Vercel của bạn:
   ```
   https://agen-web.vercel.app
   ```
   Nếu có nhiều URL (ví dụ domain riêng), cách nhau bằng dấu phẩy:
   ```
   https://agen-web.vercel.app,https://agen.yourdomain.com
   ```
4. Nhấn **"Save Changes"** → Render tự động redeploy

---

## ✅ BƯỚC 4 — Kiểm tra toàn hệ thống

### 4.1 — Kiểm tra kết nối API

```bash
# Test đăng ký tài khoản qua API
curl -X POST https://agen-api.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@gmail.com\",\"password\":\"Test1234!\",\"full_name\":\"Test User\",\"display_name\":\"TestUser\"}"

# Kết quả mong đợi: {"access_token": "...", "token_type": "bearer"}
```

### 4.2 — Kiểm tra Frontend

1. Mở `https://agen-web.vercel.app` trong trình duyệt
2. Đăng ký tài khoản mới
3. Đăng nhập và thử làm 1 bài học
4. Kiểm tra Console (F12) — không được có lỗi CORS

### 4.3 — Checklist xác nhận

- [ ] `https://agen-api.onrender.com/health` trả về `{"status":"ok"}`
- [ ] Frontend load được tại URL Vercel
- [ ] Đăng ký / Đăng nhập hoạt động
- [ ] Bài học AI sinh ra nội dung (có thể chậm lần đầu)
- [ ] Không có lỗi CORS trong Console trình duyệt

---

## 👑 BƯỚC 5 — Thiết lập tài khoản Admin

### 5.1 — Tạo tài khoản Admin

1. Mở frontend tại `https://agen-web.vercel.app`
2. **Đăng ký** bằng đúng email đã set trong `ADMIN_EMAILS` trên Render
3. Sau khi đăng nhập, truy cập: `https://agen-web.vercel.app/admin`

### 5.2 — Trang Admin có gì

- **Dashboard**: Thống kê học viên, bài học, tỷ lệ hoàn thành
- **Kho nội dung**: Xem / duyệt / xóa nội dung AI sinh ra
- **Quality Review**: Review chất lượng câu trả lời AI

---

## 📦 BƯỚC 6 (Tùy chọn) — Sinh sẵn nội dung bài học

Nếu muốn học viên vào là có bài ngay (không chờ AI sinh live):

### 6.1 — Kết nối với Production Database

Lấy DATABASE_URL từ **Render Dashboard → agen-db → Connection → External URL**.

### 6.2 — Chạy script sinh nội dung

```bash
# Tại máy local, thư mục agen-backend
cd agen-backend

# Activate venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Set DATABASE_URL trỏ tới production (PowerShell)
$env:DATABASE_URL="postgresql://agen_user:password@host:5432/agen_production"
$env:GEMINI_API_KEY="AIza..."

# Sinh nội dung A1 (24 bài)
python scripts/pregenerate_content.py --level A1 --auto-approve

# Tùy chọn: sinh thêm A2, B1
python scripts/pregenerate_content.py --level A2 --auto-approve
python scripts/pregenerate_content.py --level B1 --auto-approve
```

> ⚠️ Gemini free tier giới hạn ~1500 req/ngày. Sinh cả một level (~24 bài) tốn ~24-48 lượt gọi. Có thể chia nhiều ngày nếu cần.

---

## 🔄 Quy trình Deploy cập nhật code (sau này)

Khi có thay đổi code, chỉ cần:

```bash
git add .
git commit -m "feat: mô tả thay đổi"
git push origin main
```

- **Render** tự động detect push → build lại Docker → deploy (~3-5 phút)
- **Vercel** tự động detect push → build lại → deploy (~1-2 phút)

> 💡 **Zero downtime:** Render và Vercel đều dùng rolling deploy — service không bị gián đoạn.

---

## 🗄️ Quản lý Database Migration

Khi thay đổi model database (thêm bảng, thêm cột):

```bash
# Local: tạo migration mới
cd agen-backend
alembic revision --autogenerate -m "them_cot_moi"

# Commit và push lên GitHub
git add alembic/
git commit -m "db: them_cot_moi"
git push
```

Render tự chạy `alembic upgrade head` mỗi lần deploy (xem `scripts/start.sh`) → database tự cập nhật.

---

## 🔒 Bảo mật Production

### Những việc BẮT BUỘC phải làm

| Hành động | Lý do |
|---|---|
| Không commit `.env` lên GitHub | Lộ API key → bị hack, mất tiền |
| Dùng HTTPS (Render & Vercel tự cấp) | Bảo vệ dữ liệu người dùng |
| Set `SECRET_KEY` ngẫu nhiên đủ mạnh | Bảo vệ JWT token |
| Giới hạn `ALLOWED_ORIGINS` đúng URL | Chặn CSRF attack |
| Không bật Swagger UI trên production | `APP_ENV=production` tự tắt `/docs` |

### Kiểm tra bảo mật nhanh

```bash
# Swagger phải bị tắt trên production
curl https://agen-api.onrender.com/docs
# Kết quả mong đợi: 404 Not Found

# Health check phải hoạt động
curl https://agen-api.onrender.com/health
# Kết quả mong đợi: {"status":"ok","version":"1.0.0"}
```

---

## 💰 Nâng cấp lên Production trả phí (khi có người dùng thật)

### Khi nào cần nâng cấp?

| Dấu hiệu | Giải pháp |
|---|---|
| User phàn nàn load chậm (backend ngủ) | Upgrade Render Web Service → **Starter ($7/tháng)** |
| Database sắp đến 90 ngày | Upgrade Render DB → **Starter ($7/tháng)** |
| Nhiều user truy cập đồng thời | Tăng `WORKERS` hoặc dùng **Celery + Redis** |

### Cách upgrade Render service

1. Vào **Render Dashboard → agen-api → Settings**
2. Phần **"Instance Type"** → chọn **"Starter"**
3. Nhấn **"Save Changes"** → apply ngay, không downtime

---

## 🆘 Xử lý sự cố thường gặp

### ❌ Backend trả về 502 Bad Gateway

**Nguyên nhân:** Service đang khởi động (lần đầu hoặc sau khi ngủ)

**Giải pháp:** Đợi 30-60 giây rồi thử lại

---

### ❌ CORS Error trên trình duyệt

**Nguyên nhân:** `ALLOWED_ORIGINS` chưa có URL frontend

**Giải pháp:**
1. Render Dashboard → agen-api → Environment
2. Sửa `ALLOWED_ORIGINS` → thêm URL Vercel
3. Save → chờ redeploy (~2 phút)

---

### ❌ Frontend lỗi "Cannot connect to API"

**Nguyên nhân:** `NEXT_PUBLIC_API_URL` sai hoặc chưa set

**Giải pháp:**
1. Vercel Dashboard → Project → Settings → Environment Variables
2. Kiểm tra `NEXT_PUBLIC_API_URL` = `https://agen-api.onrender.com/api/v1`
3. Redeploy: Deployments → chọn deployment mới nhất → Redeploy

---

### ❌ Database migration lỗi khi deploy

**Nguyên nhân:** Migration conflict hoặc DB chưa kết nối được

**Giải pháp:**
1. Render Dashboard → agen-api → **Logs**
2. Tìm dòng chứa `alembic upgrade head` để xem lỗi cụ thể
3. Nếu DB chưa sẵn sàng: chờ 1-2 phút rồi trigger redeploy lại

---

### ❌ Gemini API lỗi quota

**Nguyên nhân:** Đã dùng hết free tier

**Giải pháp:**
1. Kiểm tra quota tại https://aistudio.google.com
2. Bật billing (Pay-as-you-go) — chi phí ~$0.001/bài học
3. Hoặc đợi quota reset vào ngày hôm sau

---

### ❌ Render database bị xóa sau 90 ngày

**Phòng tránh (làm trước khi hết hạn):**

```bash
# Backup database trước khi hết hạn (chạy tại máy local)
pg_dump "postgresql://agen_user:pass@host:5432/agen_production" > backup.sql
```

**Khôi phục sau khi tạo DB mới:**
```bash
# Restore data vào DB mới
psql "postgresql://agen_user:pass@newhost:5432/agen_production" < backup.sql
```

---

## 📊 Monitoring & Logs

### Xem logs Backend (Render)

1. **Render Dashboard → agen-api → Logs**
2. Logs hiển thị real-time — có thể filter theo từ khóa
3. Các log quan trọng cần chú ý: `ERROR`, `CRITICAL`, `alembic`

### Xem logs Frontend (Vercel)

1. **Vercel Dashboard → Project → Deployments**
2. Chọn deployment → xem **Build Logs** và **Runtime Logs**

### URLs quan trọng để bookmark

```
Backend Health:    https://agen-api.onrender.com/health
Frontend App:      https://agen-web.vercel.app
Admin Panel:       https://agen-web.vercel.app/admin
Render Dashboard:  https://dashboard.render.com
Vercel Dashboard:  https://vercel.com/dashboard
Gemini Quota:      https://aistudio.google.com/app/apikey
```

---

## 🗺️ Tóm tắt nhanh (Quick Reference)

```
CHUẨN BỊ
├── Tạo tài khoản: GitHub · Render · Vercel · Google AI Studio
├── Lấy GEMINI_API_KEY từ aistudio.google.com
└── Push code lên GitHub

BƯỚC 1 — BACKEND (Render.com)
├── New → Blueprint → chọn repo → Apply
├── Đặt biến: GEMINI_API_KEY, ADMIN_EMAILS
├── Deploy → chờ 3-5 phút
└── Kiểm tra: curl https://agen-api.onrender.com/health

BƯỚC 2 — FRONTEND (Vercel)
├── New Project → Import repo → Root Dir = agen-web
├── Đặt biến: NEXT_PUBLIC_API_URL = https://agen-api.onrender.com/api/v1
├── Deploy → chờ 2-3 phút
└── Ghi lại URL Vercel (vd: https://agen-web.vercel.app)

BƯỚC 3 — KẾT NỐI CORS
└── Render → agen-api → ALLOWED_ORIGINS = <URL Vercel>

BƯỚC 4 — KIỂM TRA
├── Mở URL Vercel → đăng ký → đăng nhập → thử bài học
└── Không có lỗi CORS trong Console (F12)

BƯỚC 5 — ADMIN
└── Đăng ký bằng email trong ADMIN_EMAILS → vào /admin
```

---

*Tài liệu: HƯỚNG DẪN DEPLOY CLOUD — Dự án AGEN AI English Learning Agent*
*Cập nhật: 09/2026*
