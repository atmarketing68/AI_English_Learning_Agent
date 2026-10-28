# Chạy AI AGENT ENGLISH trên máy chủ Linux bằng Docker

Mô hình: **web trên Vercel** (như hiện tại) + **API và PostgreSQL trên máy Linux của bạn**.
Yêu cầu: Docker Engine + plugin Compose (`docker compose version`), ~2 GB RAM trống, ổ trống ≥ 5 GB.

> Các file trong thư mục này **chưa được chạy thử trên máy Linux thật** (máy dựng sẵn không có Docker). Hãy làm theo thứ tự và kiểm tra từng bước; gặp lỗi thì gửi lại phần log để sửa.

## 1. Chuẩn bị
```bash
unzip agen-backup-*.zip -d ~/agen-backup          # gói sao lưu
mkdir -p ~/agen && cd ~/agen
unzip ~/agen-backup/source-code.zip               # tạo thư mục AI_English_Learning_Agent/
cd AI_English_Learning_Agent/deploy
cp .env.example .env && nano .env                  # điền theo ~/agen-backup/render-env.txt
```
- `POSTGRES_PASSWORD`: mật khẩu mạnh mới (database mới, **không** dùng mật khẩu Render).
- `SECRET_KEY`, `GEMINI_API_KEY`, `REMINDER_CRON_SECRET`, `ADMIN_EMAILS`… chép đúng từ `render-env.txt`. Giữ nguyên `SECRET_KEY` để người dùng không bị đăng xuất.
- `ALLOWED_ORIGINS` phải có `https://aiagentenglish.com` và `https://www.aiagentenglish.com`.

## 2. Khởi động database và API (API tự chạy migration tạo bảng)
```bash
docker compose up -d --build db api
docker compose logs -f api            # chờ tới khi thấy "Application startup complete" (Ctrl+C để thoát xem log)
curl -s http://127.0.0.1:8000/health  # → {"status":"ok"}
```

## 3. Nạp dữ liệu từ bản sao lưu
```bash
cp -r ~/agen-backup/db_data migrate/ && cp ~/agen-backup/restore_db.py migrate/ 2>/dev/null || true
docker compose run --rm -v "$PWD/migrate:/migrate:ro" api sh -c 'python /migrate/restore_db.py "$DATABASE_URL" /migrate/db_data'
# cuối cùng phải in:  restore OK: all row counts match
docker compose restart api
```
(Nếu muốn lấy dữ liệu **mới nhất** ngay trước khi chuyển: chạy lại `dump_db.py` ở máy có mạng ra Render — xem `HUONG_DAN_KHOI_PHUC.md` trong gói sao lưu.)

## 4. Mở API ra internet (chọn một cách)
**Cách A — Cloudflare Tunnel (khuyên dùng, không cần mở cổng):**
1. Cloudflare → Zero Trust → Networks → Tunnels → Create tunnel → copy **token**, dán vào `CLOUDFLARE_TUNNEL_TOKEN` trong `.env`.
2. Public hostname: `api.<tên miền của bạn trên Cloudflare>` → Service `HTTP` → `api:8000`.
3. `docker compose --profile tunnel up -d`

   *Lưu ý:* tên miền dùng cho tunnel phải nằm trên Cloudflare DNS. `aiagentenglish.com` đang dùng DNS của zonedns.vn; hoặc chuyển DNS sang Cloudflare, hoặc dùng một tên miền khác đã ở Cloudflare (vd. `agen-api.atmarketing.vn`).

**Cách B — Caddy (cần IP công khai, mở cổng 80/443 trên router/tường lửa):**
1. Tạo bản ghi `A`: `api.aiagentenglish.com` → IP công khai của máy (ở zonedns.vn).
2. Đặt `API_DOMAIN=api.aiagentenglish.com` trong `.env`, rồi `docker compose --profile caddy up -d` (Caddy tự lấy chứng chỉ HTTPS).

Kiểm tra: `curl https://api.aiagentenglish.com/health`.

## 5. Trỏ web sang API mới
1. Vercel → dự án `ai-english-learning-agent` → Settings → Environment Variables: sửa `NEXT_PUBLIC_API_URL` = `https://api.aiagentenglish.com/api/v1` → **Redeploy**.
2. GitHub → Settings → Secrets → Actions: `REMINDER_API_URL` = `https://api.aiagentenglish.com` (các lịch nhắc học, Content Factory chạy qua đây).
3. Sau khi chạy ổn vài ngày: tắt dịch vụ `agen-api` và database trên Render.

## 6. Sao lưu hằng đêm (bắt buộc)
```bash
chmod +x backup.sh && ./backup.sh                  # thử một lần → backups/agen_<ngày>.dump
crontab -e   # thêm:  0 2 * * * /đường/dẫn/AI_English_Learning_Agent/deploy/backup.sh >> /đường/dẫn/AI_English_Learning_Agent/deploy/backups/backup.log 2>&1
```
Hãy chép thư mục `backups/` sang nơi khác (máy thứ hai / ổ ngoài / Google Drive).

Khôi phục từ bản `.dump`:
```bash
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' < backups/agen_<ngày>.dump
```

## 7. Cập nhật phiên bản mới
```bash
cd ~/agen/AI_English_Learning_Agent && git pull        # nếu dùng git clone từ source-history.bundle / GitHub
cd deploy && docker compose up -d --build api
```
(Migration tự chạy khi API khởi động.)

## Lệnh hay dùng
`docker compose ps` · `docker compose logs -f api` · `docker compose restart api` · `docker compose down` (giữ dữ liệu) · `docker compose down -v` (**xoá cả dữ liệu — cẩn thận**).

## An toàn
- Cổng 5432 và 8000 chỉ mở trên `127.0.0.1`; ra internet qua tunnel/Caddy.
- Bật tường lửa (`ufw allow 22,80,443/tcp` nếu dùng Caddy), tự cập nhật bảo mật hệ điều hành, đổi mật khẩu SSH/dùng khoá SSH.
- `.env` và `render-env.txt` chứa khoá bí mật: `chmod 600`, không đưa lên GitHub.
