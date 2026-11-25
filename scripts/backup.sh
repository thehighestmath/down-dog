#!/usr/bin/env bash
# Бэкап Postgres в сжатый дамп (pg_dump -Fc). Запускать из cron на сервере.
# Необязательные переменные окружения:
#   DB_SERVICE          имя сервиса Postgres в compose (по умолчанию db)
#   BACKUP_DIR          куда класть дампы (по умолчанию ~/backups/down-dog)
#   BACKUP_KEEP_DAYS    сколько дней хранить (по умолчанию 14)
#   BACKUP_RSYNC_TARGET куда копировать за пределы сервера, например user@host:/backups/down-dog/
set -euo pipefail

cd "$(dirname "$0")/.."

DB_SERVICE="${DB_SERVICE:-db}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/down-dog}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
file="$BACKUP_DIR/db_$(date +%F_%H%M%S).dump"
trap 'rm -f "$file.tmp"' EXIT

# -T: без псевдотерминала, иначе в cron падает.
# Пользователя и имя БД берём из окружения контейнера, в скрипте секретов нет.
docker compose exec -T "$DB_SERVICE" \
  sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "${POSTGRES_DB:-$POSTGRES_USER}"' > "$file.tmp"

# Дамп должен читаться: битый файл не оставляем
if ! docker compose exec -T "$DB_SERVICE" pg_restore --list < "$file.tmp" > /dev/null; then
  echo "Бэкап повреждён, файл удалён" >&2
  exit 1
fi
mv "$file.tmp" "$file"
echo "Бэкап: $file ($(du -h "$file" | cut -f1))"

find "$BACKUP_DIR" -name 'db_*.dump' -mtime "+$KEEP_DAYS" -delete

# Копия вне сервера: бэкап рядом с БД не спасёт, если пропадёт сам сервер
if [ -n "${BACKUP_RSYNC_TARGET:-}" ]; then
  rsync -a "$file" "$BACKUP_RSYNC_TARGET"
fi
