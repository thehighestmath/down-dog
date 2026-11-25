#!/usr/bin/env bash
# shellcheck disable=SC2016
# SC2016 отключён намеренно: $POSTGRES_USER и $POSTGRES_DB в одинарных кавычках должен
# раскрыть shell внутри контейнера БД, а не локальный shell.
# Восстановление Postgres из дампа, сделанного scripts/backup.sh.
#   scripts/restore.sh check ДАМП   проверка: восстановить во временную БД, показать
#                                   число строк в таблицах и удалить временную БД
#   scripts/restore.sh apply ДАМП   заменить данные в рабочей БД (необратимо!)
# Необязательные переменные окружения:
#   DB_SERVICE     имя сервиса Postgres в compose (по умолчанию db)
#   APP_SERVICES   сервисы, которые пишут в БД, через пробел (по умолчанию backend)
set -euo pipefail

cd "$(dirname "$0")/.."

DB_SERVICE="${DB_SERVICE:-db}"
APP_SERVICES="${APP_SERVICES:-backend}"

mode="${1:-}"
file="${2:-}"
if [ -z "$mode" ] || [ ! -f "$file" ]; then
  echo "Использование: $0 check|apply ДАМП.dump" >&2
  exit 2
fi

db() { docker compose exec -T "$DB_SERVICE" "$@"; }

case "$mode" in
  check)
    db sh -c 'dropdb -U "$POSTGRES_USER" --if-exists restore_check && createdb -U "$POSTGRES_USER" restore_check'
    db sh -c 'pg_restore -U "$POSTGRES_USER" -d restore_check --no-owner --exit-on-error' < "$file"
    echo "Число строк в таблицах восстановленной копии:"
    db sh -c 'psql -U "$POSTGRES_USER" -d restore_check -At' <<'SQL'
select table_name || ': ' || (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text
from information_schema.tables
where table_schema = 'public' and table_type = 'BASE TABLE'
order by table_name;
SQL
    db sh -c 'dropdb -U "$POSTGRES_USER" restore_check'
    echo "Проверка пройдена: дамп $file восстанавливается"
    ;;
  apply)
    read -r -p "Данные в рабочей БД будут перезаписаны. Продолжить? (yes/no) " answer
    [ "$answer" = "yes" ] || { echo "Отменено"; exit 1; }
    read -r -a apps <<< "$APP_SERVICES"
    docker compose stop "${apps[@]}"
    db sh -c 'pg_restore -U "$POSTGRES_USER" -d "${POSTGRES_DB:-$POSTGRES_USER}" --clean --if-exists --no-owner --single-transaction' < "$file"
    docker compose start "${apps[@]}"
    echo "Готово: данные восстановлены из $file"
    ;;
  *)
    echo "Использование: $0 check|apply ДАМП.dump" >&2
    exit 2
    ;;
esac
