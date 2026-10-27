# Bàn giao giữa các phiên làm việc (dành cho Claude)

> Đọc file này cùng `CLAUDE.md` và `docs/ROADMAP_STATUS.md` khi bắt đầu phiên mới.
> `ROADMAP_STATUS.md` = đã xong gì / tiếp theo là gì. File này = **cách làm việc và các bẫy đã gặp**, để không mất thời gian học lại.
> Cập nhật lần cuối: 2026-10-27, sau khi deploy G13 + SEO (PR #23, merge `968cd55`).

## 1. Trạng thái hiện tại

- `main` đã có G1 → G13 + SEO landing; tất cả đã deploy (merge = deploy production: Vercel cho `agen-web`, Render cho `agen-backend`).
- Migration mới nhất: `c6f7a8b9c0d1` (G13). Migration tiếp theo đặt `down_revision = "c6f7a8b9c0d1"`.
- Nhánh làm việc của Claude: `claude/sleepy-gates-m3mgxo`, đã đặt lại theo `main` sau mỗi lần merge.
- Việc chủ dự án còn phải làm (khoá, biến môi trường, xác minh Google…): `docs/VIEC_CAN_LAM.md`.
- Câu hỏi còn chờ chủ dự án: số liệu/đánh giá trên landing có thật không, bảng giá (cuối `ROADMAP_STATUS.md`).

## 2. Quy trình mỗi giai đoạn (chủ dự án đã quen)

1. Chủ dự án nhắn "làm gN" → tự lên kế hoạch 4–5 hạng mục, làm trọn gói, chỉ hỏi khi thật sự cần quyết định.
2. Code backend + migration + test `tests/test_gN_*.py` → web → kiểm tra (mục 4) → chạy app thật + Playwright, xem ảnh chụp.
3. Cập nhật tài liệu **cùng PR**: mục `## GN — …` trong `ROADMAP_STATUS.md` (+ "Chưa làm trong GN" + gợi ý giai đoạn sau),
   một gạch đầu dòng `GN:` trong phần "Quy ước quan trọng" của `CLAUDE.md`, biến/cấu hình mới vào `VIEC_CAN_LAM.md`, file này nếu có bẫy mới.
4. Commit (cuối message có `Co-Authored-By` + `Claude-Session`), push, tạo **PR nháp**, theo dõi CI. Không ghi tên mô hình vào repo.
5. Trả lời ngắn bằng tiếng Việt: làm gì, kiểm tra gì, chủ dự án cần làm gì.
6. **Chỉ merge khi chủ dự án nhắn "deploy"**: kiểm tra CI xanh → bỏ nháp → merge (kiểu `merge`, kèm SHA head đủ 40 ký tự) →
   `git fetch origin main && git checkout -B claude/sleepy-gates-m3mgxo origin/main && git push --force-with-lease`.

## 3. Môi trường (container cloud)

- Python 3.12 trong venv `/home/user/.venv-agen` (Python 3.13 không build được pydantic đã pin). Nếu venv chưa có:
  `python3.12 -m venv /home/user/.venv-agen && /home/user/.venv-agen/bin/pip install -r agen-backend/requirements.txt`.
- Node/npm có sẵn; `cd agen-web && npm ci` nếu chưa có `node_modules`.
- Playwright + Chromium có sẵn: chạy script `.cjs` bằng `NODE_PATH=/opt/node-tools/node_modules node x.cjs`. **Không** `playwright install`.
- Không có `sqlite3` CLI → đọc DB bằng Python. Font Inter có sẵn (dựng ảnh có tiếng Việt bằng HTML + Playwright, ví dụ `public/og.png`).

## 4. Lệnh kiểm tra (đúng thư mục, nếu không sẽ lỗi lạ)

```bash
# Backend — PHẢI chạy trong agen-backend, chỉ thư mục tests (agen-backend/test_reg.py là script tay, không phải test)
cd agen-backend && /home/user/.venv-agen/bin/python -m pytest -p no:cacheprovider -c pytest.ini tests -q
# chạy nền vì mất vài phút; xong thì xoá agen_dev.db lạc ở thư mục gốc nếu có

# Frontend
cd agen-web && npx eslint src && npx tsc --noEmit -p . && npm run build

# Migration kiểm tra offline (không cần Postgres)
cd agen-backend && DATABASE_URL=postgresql://u:p@localhost/x /home/user/.venv-agen/bin/alembic upgrade <cũ>:<mới> --sql
DATABASE_URL=postgresql://u:p@localhost/x /home/user/.venv-agen/bin/alembic downgrade <mới>:<cũ> --sql
```

## 5. Chạy app thật để chụp màn hình (smoke)

- Backend: tạo tạm `agen-backend/smoke_gN_main.py` (`from main import app` rồi thay handler agent bằng
  `dataclasses.replace(orchestrator.AGENT_SPECS[name], handler=...)` để khỏi gọi LLM thật), chạy nền:
  `DATABASE_URL=sqlite:////home/user/AI_English_Learning_Agent/agen-backend/smoke.db ADMIN_EMAILS=admin@x.com exec /home/user/.venv-agen/bin/uvicorn smoke_gN_main:app --port 8000`.
- Web: `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 npm run build` rồi `(nohup ./node_modules/.bin/next start -p 3000 > log 2>&1 &)`.
- Đăng nhập trong Playwright: `addInitScript` ghi `localStorage['agen-auth'] = {state:{token, refreshToken, isAuthenticated:true, userRole}, version:0}` (bọc try).
- Dữ liệu khó tạo qua API (bài viết có band, đơn hàng…) → script Python ghi thẳng vào `smoke.db`.
- Tắt server: `ps aux | grep -E "[n]ext-server|[u]vicorn smoke" | awk '{print $2}' | xargs -r kill`.
  **Không dùng `pkill -f`** (giết luôn shell đang chạy lệnh, exit 144).
- Trước khi commit: xoá `smoke.db`, `smoke_gN_main.py`, `agen_dev.db`. Ảnh chụp để ở thư mục scratchpad, không commit.

## 6. Bẫy đã gặp (đừng lặp lại)

**Backend**
- Thời gian DB là UTC naive; "ngày" của học viên luôn qua `local_today()` / `local_day_start_utc()` (trả về aware → `.replace(tzinfo=None)` khi so với cột DB).
  Test dùng `date.today()` sẽ đỏ sau 17:00 UTC.
- Fixture `client` chạy startup trên DB dev; seed bằng fixture `db_session`. Thay agent trong test bằng `monkeypatch` + `dataclasses.replace`.
- Danh sách đề có đề AI (`gen-…`) chỉ thấy khi truyền `db`: `mock_exams.list_exams(db)`, `speaking_exams.get_exam(id, db)`…
- Tính năng cần khoá phải tắt êm (`settings.xxx_enabled`); cảnh báo phụ huynh phải chạy khi chỉ có một kênh (FCM / web push / Zalo).
- LLM lỗi không được làm hỏng luồng học: luôn có fallback; lỗi giới hạn chi phí ném `LLMError(is_quota=True)`.

**Web (Next 16)**
- Đọc `node_modules/next/dist/docs/` trước khi dùng API lạ. Trang `'use client'` không export `metadata` được → bọc bằng server page/layout.
- Giá trị (mảng, object) export từ module `'use client'` **không** dùng được trong server component → để dữ liệu chung ở module thường (`lib/...`).
- Đọc query trên trang client bằng `new URLSearchParams(window.location.search)` trong effect, tránh `useSearchParams` (đòi Suspense khi prerender).
- ESLint React 19: không `setState` đồng bộ trong `useEffect`, không `Date.now()` khi render — đặt trong callback/handler.
- Hiển thị giờ học viên luôn ép `timeZone: 'Asia/Ho_Chi_Minh'`; ngày ISO `YYYY-MM-DD` → `new Date(\`${d}T00:00:00\`)`.
- Trang công khai/người lớn phải ở `ALWAYS_CLASSIC` (`SkinProvider`); trang app mới sau đăng nhập → thêm vào `SHELL_PREFIXES` (`navigation.ts`)
  và `PRIVATE` (`app/robots.ts`).
- CSS: dùng class sẵn trong `globals.css`; rule chỉ-classic dùng tiền tố `:root:not([data-skin="vivid"])`; không dùng `translate` 3 giá trị (Next bỏ mất).
- Lưới `grid-column: span 2` trong grid `auto-fit` làm tràn ngang trên điện thoại → dùng media query riêng. Luôn chụp 390px kiểm tra tràn.
- Biểu đồ: theo skill dataviz (bảng màu đã kiểm tra mù màu, có chú thích + nút "Xem bảng"), ví dụ `components/teacher/RubricChart.tsx`.
- App di động: web gọi plugin qua `window.Capacitor` (`lib/nativePush.ts`), không cài gói npm Capacitor vào web.

## 7. Hướng phát triển tiếp (đề xuất, chờ chủ dự án chọn)

Xem mục "G14 — gợi ý tiếp theo" trong `ROADMAP_STATUS.md` (thứ tự ưu tiên + lý do).
