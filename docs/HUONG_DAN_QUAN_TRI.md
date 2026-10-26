# 🛡️ Hướng dẫn vận hành cho Quản trị viên — AGEN

Tài liệu này dành cho **quản trị viên / người vận hành** AGEN trong giai đoạn pilot.
Bạn sẽ biết cách: cấp quyền admin, chuẩn bị nội dung bài học, giám sát chất lượng AI,
theo dõi hệ thống và xử lý sự cố thường gặp.

> 📄 Khởi chạy hệ thống: xem **[README gốc](../README.md)**.
> Hướng dẫn cho người học: xem **[HUONG_DAN_SU_DUNG.md](./HUONG_DAN_SU_DUNG.md)**.

---

## 1. Trở thành Quản trị viên

Quyền admin được cấp qua **danh sách email** trong biến môi trường, KHÔNG qua đăng ký.

1. Mở `agen-backend/.env`, thêm email của bạn vào `ADMIN_EMAILS` (phân tách bằng dấu phẩy):
   ```ini
   ADMIN_EMAILS=admin@example.com,quanly@example.com
   ```
2. Khởi động lại backend để nạp cấu hình.
3. Đăng ký một tài khoản học viên **bằng đúng email đó**, đăng nhập, rồi truy cập
   **`/admin`**.

Đặc điểm bảo mật:
- Danh sách rỗng = **không ai** truy cập được `/admin` (mặc định an toàn).
- So khớp email **không phân biệt hoa/thường**.
- Người ngoài danh sách gọi API admin sẽ nhận **403 Không có quyền**.

Kiểm tra quyền nhanh: gọi `GET /api/v1/admin/me` → trả `{ email, is_admin }`.

---

## 2. Trang Quản trị `/admin`

Có 2 tab:

| Tab | Mục đích |
|-----|----------|
| 🔍 **Chất lượng AI** | Giám sát điểm đánh giá nội dung do AI tạo + cảnh báo cần review |
| 📚 **Kho nội dung** | Sinh sẵn, duyệt, từ chối nội dung bài học theo lộ trình |

---

## 3. Chuẩn bị nội dung bài học (Content Factory)

AGEN sinh nội dung bài học bằng AI. Bạn nên **sinh sẵn + duyệt trước** để:
- Học viên nhận bài **tức thì** (không phải chờ AI 30–120 giây).
- **Tiết kiệm quota AI** (sinh 1 lần, mọi học viên dùng chung).
- **Kiểm soát chất lượng** trước khi phát hành.

### 3.1. Cách 1 — Dòng lệnh (CLI), khuyến nghị cho số lượng lớn

Từ thư mục `agen-backend` (đã kích hoạt venv):

```bash
# Sinh + tự duyệt toàn bộ một cấp độ:
python scripts/pregenerate_content.py --level A1 --auto-approve

# Sinh dạng nháp (chưa phát hành) để review thủ công sau:
python scripts/pregenerate_content.py --level A1

# Sinh một bài cụ thể:
python scripts/pregenerate_content.py --code A2-U01-L01 --auto-approve

# Giới hạn số bài mỗi lần (tránh chạm quota):
python scripts/pregenerate_content.py --level A2 --limit 5 --auto-approve

# Sinh lại đè lên bản cũ:
python scripts/pregenerate_content.py --code A1-U01-L01 --force --auto-approve
```

### 3.2. Cách 2 — Giao diện `/admin` → tab Kho nội dung

1. Chọn cấp độ (A1 / A2 / B1).
2. Bấm **"⚙️ Sinh (nháp)"** hoặc **"⚡ Sinh + duyệt tự động"** cho cả cấp.
3. Xem danh sách từng bài: mã, kỹ năng, chủ đề, **điểm đánh giá**, cờ cảnh báo, trạng thái.
4. Duyệt/từ chối từng bài bằng nút **✅ Duyệt** / **❌ Từ chối**.

### 3.3. Vòng đời trạng thái nội dung

| Trạng thái | Ý nghĩa | Học viên có nhận được? |
|-----------|---------|------------------------|
| `draft` (Nháp) | Đã sinh, chờ duyệt | ❌ Không |
| `approved` (Đã duyệt) | Đã kiểm duyệt, phát hành | ✅ Có |
| `rejected` (Từ chối) | Bị loại, sẽ sinh lại | ❌ Không |

> Chỉ nội dung **approved** mới được phục vụ cho học viên. Bài chưa có nội dung approved
> sẽ **tự động sinh live** khi học viên mở (fallback an toàn, không lỗi).

### 3.4. ⚠️ Lưu ý về quota AI (rất quan trọng)

- Mỗi bài = **1 lượt gọi AI**. Một cấp độ có ~24 bài sinh được.
- **Gemini free tier** giới hạn ~20 lượt/ngày → sinh cả một cấp sẽ hết quota trong ngày
  (báo lỗi *"Hệ thống AI đang bận hoặc đã hết giới hạn"*).
- Giải pháp: dùng **khóa API trả phí** để sinh toàn bộ một lần, hoặc **chia nhiều ngày**
  bằng `--limit`.

---

## 4. Giám sát chất lượng AI (tab Chất lượng AI)

Đây là **lớp gác cổng** đặc biệt quan trọng vì AGEN phục vụ cả trẻ em: mọi nội dung AI
sinh ra đều được chấm điểm tự động trước khi tới học viên.

### 4.1. Cơ chế chấm điểm (rule-based, không tốn AI)

Mỗi nội dung được chấm trên **4 chiều** (thang 0–100), tổng hợp theo trọng số:

| Chiều | Trọng số | Kiểm tra |
|-------|:--------:|----------|
| Độ chính xác tiếng Anh | 30% | rỗng, placeholder, ký tự lỗi, quá ngắn |
| Phù hợp lứa tuổi | 30% | danh sách từ cấm (bạo lực, người lớn, thô tục) |
| Tính đầy đủ | 25% | đủ số bài tập, câu trắc nghiệm có đáp án/lựa chọn |
| Bám chương trình | 15% | skill/level khớp yêu cầu |

- Điểm tổng **< 70** hoặc **có bất kỳ cảnh báo nào** → được **gắn cờ 🚩** để bạn review.
- **Fail-open:** nội dung bị gắn cờ **vẫn được giao** (không chặn học viên), nhưng luôn
  được ghi log để bạn xem lại. Triết lý: đánh dấu để review, không chặn trải nghiệm.

### 4.2. Đọc bảng giám sát

Trên tab **Chất lượng AI**, bạn thấy:
- **Thẻ tổng quan:** số bài đã đánh giá, điểm trung bình, số bị gắn cờ, % gắn cờ.
- **Theo từng agent:** thống kê điểm trung bình + số cảnh báo của từng loại AI.
- **Nhật ký đánh giá:** từng lần sinh, có bộ lọc **"Chỉ hiện bị gắn cờ 🚩"** và **theo agent**.

Màu điểm: **≥85 xanh (tốt)**, **70–84 vàng (khá)**, **<70 đỏ (cần xem)**.

### 4.3. Cảnh báo giả (false positive) thường gặp

Bộ lọc "ký tự lặp" đôi khi gắn cờ **phiên âm** (ví dụ `/həˈloʊ/`) là "ký tự lỗi". Đây là
cảnh báo vô hại — nội dung vẫn tốt. Bạn chỉ cần đọc lướt và duyệt nếu thấy ổn.

### 4.4. Quy trình review đề xuất

1. Vào tab Chất lượng AI, bật **"Chỉ hiện bị gắn cờ"**.
2. Với mỗi bài bị cờ: đọc lý do cảnh báo.
   - Nếu là false positive (phiên âm) → sang tab Kho nội dung **Duyệt**.
   - Nếu thật sự có vấn đề (từ không phù hợp, sai chủ đề) → **Từ chối** rồi **sinh lại**
     (`--force`), hoặc chỉnh chủ đề node curriculum nếu cần.

---

## 5. Cấu hình vận hành quan trọng

Trong `agen-backend/.env`:

| Biến | Vai trò vận hành |
|------|------------------|
| `ADMIN_EMAILS` | Danh sách email quản trị (bắt buộc để dùng `/admin`) |
| `FREE_DAILY_LESSON_LIMIT` | Số bài/ngày cho gói free. Pilot nên để **cao (1000)** hoặc **0 (không giới hạn)** để không chặn người test |
| `GEMINI_API_KEY` | Khóa AI — **bắt buộc** để sinh nội dung. Không có = không tạo được bài |
| `OPENAI_API_KEY` | Khóa dự phòng (nếu Gemini lỗi, hệ thống tự chuyển sang OpenAI) |
| `ALLOWED_ORIGINS` | URL frontend được phép gọi API (CORS) |

> 🔐 **An ninh:** đừng commit khóa API vào git. Nếu khóa từng lộ (ví dụ trong file mẫu),
> hãy **thu hồi và tạo khóa mới** ngay.

---

## 6. Quản lý người dùng & dữ liệu

- **Xem dữ liệu:** dùng Swagger (`/docs`, chỉ bật ở `APP_ENV=development`) hoặc truy vấn DB.
- **Quyền riêng tư (API `/privacy`):** người dùng có thể tự **xuất dữ liệu** và **xóa tài
  khoản**. Đây là yêu cầu tuân thủ — không nên vô hiệu hóa.
- **Phụ huynh:** liên kết với con qua **mã mời** (`AGEN-XXXX`) của học viên; chỉ xem được
  báo cáo của con đã liên kết.

---

## 7. Theo dõi hệ thống

- **Health check:** `GET /health` → `{"status":"ok"}`. Dùng cho uptime monitor.
- **Log server:** backend ghi log theo định dạng `thời gian | mức độ | agen | thông điệp`,
  gồm thời gian xử lý mỗi request và cảnh báo khi AI bị gắn cờ.
- **Nhật ký AI (AgentTrace):** mọi lần gọi AI được lưu (agent, trạng thái, thời gian, điểm
  đánh giá) — xem qua tab Chất lượng AI.

---

## 8. Xử lý sự cố thường gặp

| Hiện tượng | Nguyên nhân & cách xử lý |
|-----------|--------------------------|
| Sinh bài báo *"AI đang bận / hết giới hạn"* | Hết quota AI trong ngày. Chờ reset, dùng khóa trả phí, hoặc `--limit` nhỏ hơn. |
| Học viên chờ lâu khi mở bài | Bài đó chưa được sinh sẵn → đang sinh live. Hãy pre-generate trước cho cấp độ đang test. |
| `/admin` báo "Không có quyền" | Email chưa nằm trong `ADMIN_EMAILS`, hoặc chưa khởi động lại backend sau khi sửa. |
| Học viên báo "hết lượt học hôm nay" | `FREE_DAILY_LESSON_LIMIT` đang thấp. Đặt cao hơn hoặc `0` cho pilot. |
| Nhiều bài bị gắn cờ do "ký tự lặp" | Thường là phiên âm — false positive, có thể duyệt bình thường. |
| Deploy production khởi động lỗi | Kiểm tra `WORKER_MODE`/`REDIS_URL` (nếu `distributed` phải có `REDIS_URL`); `SECRET_KEY` và `DATABASE_URL` (PostgreSQL) phải được cấu hình. |

---

## 9. Checklist chuẩn bị Pilot

- [ ] Điền `.env` backend: `SECRET_KEY`, `GEMINI_API_KEY`, `ADMIN_EMAILS`, `FREE_DAILY_LESSON_LIMIT` cao.
- [ ] Khởi động backend (`uvicorn`, KHÔNG `--reload`) + frontend (`npm run dev`).
- [ ] Đăng ký tài khoản admin (email trong `ADMIN_EMAILS`) và kiểm tra vào được `/admin`.
- [ ] Pre-generate nội dung cấp A1 (`--level A1 --auto-approve`); kiểm tra "24/24 đã duyệt".
- [ ] Review nhanh các bài bị gắn cờ trên tab Chất lượng AI.
- [ ] Tự trải nghiệm 1 vòng: đăng ký học viên → placement → học 1 bài → xem tiến bộ.
- [ ] Xác nhận `GET /health` trả `ok`.

Chúc buổi pilot thành công! 🚀
