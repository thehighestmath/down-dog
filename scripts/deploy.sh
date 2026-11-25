#!/usr/bin/env bash
# Выкатка актуального master на сервер. Запускать на сервере: ./scripts/deploy.sh
set -euo pipefail

cd "$(dirname "$0")/.."

# 1. Бэкап перед обновлением: миграции необратимы, откат кода данные не вернёт
./scripts/backup.sh

# 2. Свежий код
git fetch origin master
git checkout master
git pull --ff-only origin master

# 3. Пересборка и запуск (COMPOSE_FILE с prod-конфигурацией задан в .env)
docker compose up -d --build --remove-orphans
docker compose ps

# 4. Проверка, что сайт отвечает по HTTPS (домен: переменная DOMAIN или строка DOMAIN= в .env)
domain="${DOMAIN:-$(grep -E '^DOMAIN=' .env | head -n1 | cut -d= -f2- || true)}"
if [ -z "$domain" ]; then
  echo "Готово. Домен не задан (DOMAIN в .env), проверку сайта пропускаем"
  exit 0
fi
for _ in 1 2 3 4 5 6; do
  if curl -fsS -o /dev/null "https://$domain/"; then
    echo "Готово: https://$domain/ отвечает"
    exit 0
  fi
  sleep 5
done
echo "Сайт не отвечает после выкатки, смотри: docker compose logs --tail=100" >&2
exit 1
