# 📦 Bộ cài AGEN cho Windows

Thư mục này chứa toàn bộ script đóng gói AGEN thành ứng dụng desktop Windows để
**học viên tự cài trên máy** — kèm **biểu tượng ngoài màn hình desktop**.

Bộ cài gồm 2 phần chạy nội bộ trên máy học viên (không cần internet cho phần chạy,
trừ khi gọi AI):
- **backend** — `agen-api.exe` (FastAPI đóng gói bằng PyInstaller)
- **frontend** — `frontend/server.js` chạy bằng `node.exe` đi kèm (Next.js standalone)

---

## A. Dành cho người đóng gói (bạn)

### Yêu cầu
- Python venv của backend đã cài **PyInstaller** (`pip install pyinstaller`).
- **Node.js** trên PATH (dùng để build frontend + đóng gói `node.exe`).
- **Inno Setup 6** để tạo file cài 1-cú-nhấp. Cài nhanh: `winget install JRSoftware.InnoSetup`.

### Build

Chạy PowerShell từ thư mục gốc dự án:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\installer\build-installer.ps1
```

Script sẽ:
1. Build backend bằng `agen-backend/agen-api.spec` → `agen-api.exe`.
2. Build frontend standalone (`DESKTOP_BUILD=1`) → `frontend/server.js` + static.
3. Đóng gói `node.exe` và các script khởi chạy → thư mục **`installer\dist\AGEN`**.
4. Tự tìm Inno Setup và tạo **`installer\dist\AGEN-Setup.exe`** (file cài 1-cú-nhấp).

> Chỉ cần build lại `.exe` sau khi đã có sẵn thư mục portable? Chạy trực tiếp:
> `& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer\AGEN.iss`

**Gửi cho học viên: chỉ 1 file `AGEN-Setup.exe`.**

---

## B. Dành cho học viên (cài chỉ 1 cú nhấp)

1. Tải file **`AGEN-Setup.exe`** về máy.
2. **Nhấp đúp** để cài. Không cần quyền admin.
   - Trình cài tự chép ứng dụng và **tạo biểu tượng "AGEN English Learning Agent"
     trên màn hình Desktop**.
   - Sau khi cài xong, AGEN **tự khởi chạy**.
3. Những lần sau, mở AGEN bằng **biểu tượng trên Desktop**.

### Lần chạy đầu tiên (cấu hình khóa AI — làm một lần)
- Lần đầu mở, AGEN mở **Notepad** với file cấu hình.
- Điền **`GEMINI_API_KEY=<khóa AI của bạn>`**, **lưu lại (Ctrl+S)**, đóng Notepad,
  rồi mở lại biểu tượng AGEN trên Desktop.
- AGEN tự chạy và mở trình duyệt tại **http://127.0.0.1:3000**.

#### 🔑 Cấu hình dịch vụ AI

Người học không cần và không nên tự lấy hoặc nhập `GEMINI_API_KEY`. Người vận hành pilot
phải cấu hình dịch vụ AI trước khi phát hành bản cài đặt. Không đóng gói khóa dùng chung
vào installer và không gửi khóa qua chat, email hay tài liệu hướng dẫn người học.

### Dừng ứng dụng
- Mở menu Start → **"Dừng AGEN"**, hoặc chạy `Stop-AGEN.cmd` trong `%LOCALAPPDATA%\AGEN`.

### Gỡ cài đặt
- Vào **Cài đặt Windows → Ứng dụng → AGEN English Learning Agent → Gỡ**.

---

## C. Nội dung bài học trên máy học viên

Máy học viên khởi tạo cơ sở dữ liệu SQLite riêng tại `%LOCALAPPDATA%\AGEN`. Chương
trình học (khung A1/A2/B1) được **seed tự động** khi chạy lần đầu. Nội dung bài học
được **AI sinh khi học** (cần `GEMINI_API_KEY` của học viên).

> 💡 Nếu muốn học viên có nội dung **sẵn + không tốn quota**, hãy đóng gói kèm một
> file `agen_dev.db` đã pre-generate và đặt vào `%LOCALAPPDATA%\AGEN` trước khi chạy.

---

## D. Đã kiểm chứng

Bộ cài đã được build và chạy thử thành công trên Windows:
- **`AGEN-Setup.exe`** (63 MB) build từ Inno Setup; cài **im lặng (silent) không cần admin**,
  chép app vào `%LOCALAPPDATA%\AGEN` và **tạo biểu tượng Desktop** trỏ đúng `Start-AGEN.cmd`.
- Mở app từ biểu tượng đã cài: **backend `/health` = `ok`** (cổng 8000) và
  **frontend HTTP 200** (cổng 3000).
- `agen-api.exe` seed 90 bài chương trình khi chạy lần đầu.

---

## E. Ghi chú kỹ thuật

- **UPX tắt** trong `agen-api.spec` để tránh cảnh báo diệt virus và lỗi DLL.
- Backend chạy ở `APP_ENV=development` + SQLite (đơn giản, không cần PostgreSQL).
- Port mặc định: backend **8000**, frontend **3000** (đổi được qua biến môi trường
  `AGEN_BACKEND_PORT` / `PORT`).
- Nếu backend không lên: thường do **port 8000 đang bị chiếm** bởi tiến trình khác —
  đóng ứng dụng đang dùng cổng đó rồi chạy lại.
