#!/usr/bin/env bash
# $COMPOSE is intentionally unquoted: it is a command with arguments
# shellcheck disable=SC2086

# Смоук-тест: каждый сервис поднятого стека отвечает и делает свою работу.
#
# Локально:
#   docker compose up -d --wait backend frontend db minio adminer
#   bash scripts/smoke_test.sh
#
# Адреса можно переопределить, если порты на машине заняты:
#   BACKEND_URL=http://localhost:18000 bash scripts/smoke_test.sh
set -u

BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
FRONTEND_URL=${FRONTEND_URL:-http://localhost:3000}
MINIO_URL=${MINIO_URL:-http://localhost:9000}
ADMINER_URL=${ADMINER_URL:-http://localhost:8080}
# Команда compose целиком: локально можно добавить -f override.yml
COMPOSE=${COMPOSE:-docker compose}

failed=0

ok() { echo "OK    $1"; }
fail() {
  echo "FAIL  $1"
  echo "      $2"
  failed=1
}

# check <название> <ожидаемая подстрока в ответе> <подсказка> <аргументы curl...>
check() {
  local name=$1 expect=$2 hint=$3
  shift 3
  local out
  if ! out=$(curl --fail --silent --show-error --max-time 10 \
    --retry 5 --retry-delay 2 --retry-all-errors "$@" 2>&1); then
    # curl печатает ошибку на каждую попытку, достаточно последней
    fail "$name" "$hint (${out##*$'\n'})"
  elif [[ $out != *"$expect"* ]]; then
    fail "$name" "$hint (в ответе нет '$expect')"
  else
    ok "$name"
  fi
}

echo "--- Бэкенд"
check "backend: /docs" "swagger" \
  "FastAPI не отвечает - смотри логи backend" \
  "$BACKEND_URL/docs"
check "backend: GET /api/poses (БД, миграции, сиды)" '"name_en"' \
  "нет поз - не подключилась БД или не применились backend/sql/*.sql" \
  "$BACKEND_URL/api/poses"
check "backend: POST /api/workouts/generate" '"poses"' \
  "генерация тренировки не работает" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"duration_min": 10, "level": "beginner", "focus": "full_body"}' \
  "$BACKEND_URL/api/workouts/generate"

echo "--- Фронтенд"
check "frontend: главная страница" 'id="root"' \
  "nginx не отдаёт собранный фронт - смотри frontend/Dockerfile и nginx.conf" \
  "$FRONTEND_URL/"
check "frontend: /api/poses через nginx" '"name_en"' \
  "nginx не проксирует /api/ на бэкенд - смотри location /api/ в frontend/nginx.conf" \
  "$FRONTEND_URL/api/poses"

echo "--- Инфраструктура"
if $COMPOSE exec -T db pg_isready -U postgres -d app_db > /dev/null; then
  ok "postgres: pg_isready"
else
  fail "postgres: pg_isready" "Postgres не принимает подключения - смотри логи db"
fi
check "minio: health" "" \
  "MinIO не отвечает - смотри логи minio" \
  "$MINIO_URL/minio/health/live"
check "adminer" "Adminer" \
  "Adminer не отвечает - смотри логи adminer" \
  "$ADMINER_URL/"

echo "--- Загрузка картинок в MinIO (s3)"
# s3.py ловит ошибки загрузки и печатает их с ❌, не меняя код выхода,
# поэтому проверяем и код выхода, и вывод
if ! s3_out=$($COMPOSE run --rm s3 2>&1); then
  fail "s3: загрузка картинок" "скрипт упал: $s3_out"
elif [[ $s3_out == *"❌"* ]]; then
  fail "s3: загрузка картинок" "часть файлов не загрузилась: $(grep '❌' <<< "$s3_out")"
else
  ok "s3: загрузка картинок ($(grep -c '✅ Загружено' <<< "$s3_out") файлов)"
fi

if [ "$failed" -ne 0 ]; then
  echo
  echo "Смоук-тест не пройден: см. строки FAIL выше."
  exit 1
fi
echo
echo "Смоук-тест пройден."
