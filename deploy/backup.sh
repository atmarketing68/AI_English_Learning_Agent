#!/bin/sh
# Sao lưu PostgreSQL hằng đêm (giữ 14 ngày). Chạy tay: ./backup.sh
# Cron (2 giờ sáng):  0 2 * * * /đường/dẫn/deploy/backup.sh >> /đường/dẫn/deploy/backups/backup.log 2>&1
# Nhớ chép thư mục backups/ sang nơi khác (máy thứ hai, ổ ngoài, Google Drive) — ổ cứng hỏng là mất cả bản sao lưu.
set -eu
cd "$(dirname "$0")"
mkdir -p backups
ts=$(date +%F_%H%M)
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > "backups/agen_$ts.dump"
find backups -name 'agen_*.dump' -mtime +14 -delete
echo "$(date -Iseconds) saved backups/agen_$ts.dump ($(du -h "backups/agen_$ts.dump" | cut -f1))"
