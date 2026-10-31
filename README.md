# Down Dog

Веб-приложение для йога-тренировок: выбираешь длительность, уровень и фокус, получаешь сгенерированную последовательность поз и проходишь её с таймером. Сейчас делаем MVP, чтобы проверить, нужен ли такой сервис.

- [MVP.md](MVP.md) — что входит в MVP, что уже сделано, API и логика генератора
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) — куда проект развивается после MVP
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — подробно про MinIO, FastAPI и виртуальное окружение
- [Доска задач](https://github.com/users/thehighestmath/projects/5) и майлстоуны: [v0.0.1a (MVP)](https://github.com/thehighestmath/down-dog/milestone/1), [v1.0.0](https://github.com/thehighestmath/down-dog/milestone/2)

## Быстрый старт (Docker)

Нужен только [Docker Desktop](https://www.docker.com/products/docker-desktop/) (на Windows — с WSL 2, это настройка по умолчанию). Запустите его и дождитесь иконки на панели задач.

```bash
git clone git@github.com:thehighestmath/down-dog.git
cd down-dog
docker compose up -d --build
```

Первый запуск занимает несколько минут. Когда всё поднимется:

| Что                  | Адрес                      | Доступ                                 |
| -------------------- | -------------------------- | -------------------------------------- |
| Приложение           | http://localhost:3000      |                                        |
| API (Swagger)        | http://localhost:8000/docs |                                        |
| Adminer (GUI для БД) | http://localhost:8080      | см. [Adminer](#adminer)                |
| MinIO (консоль S3)   | http://localhost:9001      | `minioadmin` / `minioadmin`            |
| PostgreSQL           | `localhost:5432`           | `postgres` / `postgres`, база `app_db` |

Остановить:

```bash
docker compose down
```

Начать с чистой базой (**удалит все данные** PostgreSQL и MinIO):

```bash
docker compose down -v
```

Если что-то не работает:

- `docker compose ps` — какие сервисы запущены; `docker compose logs backend` — логи нужного сервиса.
- `port is already allocated` — порт занят другой программой. Остановите её или поменяйте **левую** часть порта в `docker-compose.yml` (например, `'18000:8000'`), но не коммитьте это.

## Что из чего состоит

```text
down-dog/
├── backend/              FastAPI
│   ├── main.py           эндпоинты и применение миграций при старте
│   ├── generator.py      генератор тренировок
│   ├── *_test.py         тесты (pytest)
│   └── sql/              миграции и seed-данные
├── frontend/             React + TypeScript + Vite, в контейнере — nginx
│   └── src/components/   экраны: HomeScreen, Player, FinishedScreen
├── android/              Android-приложение: Kotlin + Jetpack Compose
├── s3/                   разовая задача: создаёт бакет и заливает картинки в MinIO
├── Images/               картинки поз
├── scripts/              смоук-тест стека, проверка сообщений коммитов
└── docker-compose.yml
```

Сервисы в `docker-compose.yml`:

- **frontend** — nginx отдаёт собранный фронтенд и проксирует `/api/*` в backend;
- **backend** — FastAPI; при старте применяет все `backend/sql/*.sql` по алфавиту;
- **db** — PostgreSQL;
- **minio** — S3-совместимое хранилище;
- **s3** — запускается один раз: создаёт бакет `down-dog` и заливает туда `Images/`;
- **adminer** — веб-интерфейс к базе.

## Разработка без Docker

Удобно, когда правите код и хотите видеть изменения сразу, без пересборки образов. База всё равно нужна, её берём из Docker.

### Backend

```powershell
# база в Docker; backend из compose останавливаем, чтобы освободить порт 8000
docker compose up -d db
docker compose stop backend

# один раз: виртуальное окружение в корне репозитория
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements-dev.txt

# подключение к базе (PowerShell; в каждом новом терминале заново)
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "app_db"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "postgres"

cd backend
python -m uvicorn main:app --reload
```

API — http://localhost:8000/docs. Запускать нужно именно из папки `backend/`: модули импортируют друг друга напрямую (`from generator import ...`).

### Frontend

Нужен [Node.js](https://nodejs.org/) LTS.

```bash
cd frontend
npm ci
npm run dev
```

Откройте http://localhost:5173. Запросы к `/api` Vite проксирует на `http://localhost:8000`, так что backend должен быть запущен (в Docker или локально).

### Android

Нужна [Android Studio](https://developer.android.com/studio): в ней есть JDK, Android SDK и эмулятор. При первом запуске пройдите мастер настройки (Standard), затем создайте эмулятор в Device Manager.

1. **File → Open** → папка `android/` (не корень репозитория). Дождитесь окончания Gradle Sync.
2. Запустите backend (в Docker или локально).
3. Выберите эмулятор и нажмите **Run ▶**.

Приложение ходит в API по адресу `http://10.0.2.2:8000/` — так эмулятор видит `localhost` компьютера. Для телефона или другого порта укажите адрес в `android/local.properties` (файл не коммитится) и пересоберите:

```properties
downdog.apiUrl=http://192.168.1.10:8000/
```

Телефон и компьютер должны быть в одной Wi-Fi сети. Код экранов — в `android/app/src/main/java/.../ui/`, логика таймера — в `WorkoutViewModel.kt`.

## Тесты и проверки

```bash
pytest                      # из корня репозитория
pre-commit run --all-files  # все линтеры и форматтеры, как в CI
```

Android (из папки `android/`, то же запускает CI):

```bash
./gradlew lintDebug testDebugUnitTest assembleDebug
```

Один раз после клонирования поставьте хуки, чтобы проверки запускались на каждом `git commit`:

```bash
pip install pre-commit
pre-commit install
```

Это ставит сразу два хука: линтеры перед коммитом и проверку сообщения коммита.

Смоук-тест поднятого стека (нужен bash — например, Git Bash):

```bash
docker compose up -d --wait backend frontend db minio adminer
bash scripts/smoke_test.sh
```

## Как вносить изменения

1. Возьмите задачу на [доске](https://github.com/users/thehighestmath/projects/5) и назначьте её на себя.
2. Создайте ветку от свежего `master`. Напрямую в `master` пушить нельзя.
3. Коммитьте в формате [Conventional Commits](#сообщения-коммитов).
4. Откройте PR: заголовок тоже в формате Conventional Commits, в описании `Closes #<номер задачи>`.
5. Дождитесь зелёного CI и ревью. PR вливается squash-мержем, заголовок PR становится сообщением коммита.
6. Если `master` ушёл вперёд — влейте его в свою ветку (`git merge origin/master`), без rebase и force-push.

### Сообщения коммитов

```text
type(scope): subject
```

- **type** — обязателен: `feat`, `fix`, `build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`.
- **scope** — необязательный контекст, например `api`, `frontend`.
- **subject** — обязателен, без точки в конце.
- Ломающее изменение — `!` после type/scope: `feat!: change`.
- `Merge ...` и `Revert ...` пропускаются автоматически.

```text
feat: add new feature
fix(api): validate workout duration
feat!: breaking change
```

## Установка (однократно для каждого разработчика)

В активированном виртуальном окружении:

```bash
pip install pre-commit
```

Затем в корне проекта зарегистрируйте хук:

```bash
pre-commit install --hook-type commit-msg
```

Хук будет выполняться при каждом `git commit`. Убедиться, что он установлен:

```bash
pre-commit validate-config
```

# Запуск проекта через Docker Compose

Запускайте команды из корневой папки репозитория. Перед запуском убедитесь, что Docker Desktop запущен.

Проверьте конфигурацию и соберите/запустите все сервисы:

```bash
docker compose config
docker compose up --build -d
docker compose ps
```

Проверка доступных адресов:

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Backend healthcheck: [http://localhost:8000/health](http://localhost:8000/health)
- Adminer: [http://localhost:8080](http://localhost:8080)
- MinIO console: [http://localhost:9001](http://localhost:9001)

## Как выполняются миграции

1. Сервис `db` запускается и проходит проверку готовности PostgreSQL.
2. Одноразовый сервис `migrate` запускает `backend/migrate.py` и применяет SQL-файлы из `backend/sql/` в алфавитном порядке.
3. Таблица `schema_migrations` хранит имя каждого применённого файла, его SHA-256 checksum и время применения. Уже применённые файлы повторно не запускаются.
4. Сервис `backend` стартует только после успешного завершения `migrate`. Если миграция завершается с ошибкой или checksum изменённого ранее файла не совпадает, backend не запускается.
5. Endpoint `GET /health` проверяет соединение с PostgreSQL запросом `SELECT 1`. Docker Compose использует его как healthcheck; frontend ждёт, пока backend станет healthy.

**Важно: применённые SQL-файлы нельзя редактировать или переименовывать.** Если нужно изменить схему или seed-данные, создайте следующий файл, например `backend/sql/03_add_pose_metadata.sql`. Изменение уже применённого файла приведёт к ошибке checksum — это защита от незаметного изменения истории миграций.

## Логи и остановка

Просмотреть логи миграций и backend:

```bash
docker compose logs -f migrate
docker compose logs -f backend
```

Остановить сервисы, сохранив данные в volumes:

```bash
docker compose down
```

Команда `docker compose down -v` дополнительно удаляет volumes PostgreSQL и MinIO вместе с сохранёнными данными; используйте её только если действительно хотите сбросить локальную базу и файлы.


# Документация по работе с Adminer (GUI базы данных)

**Adminer** — это веб-интерфейс для управления СУБД PostgreSQL прямо из браузера. Он автоматически запускается вместе со всеми сервисами через `docker compose`.

## 1. Вход в веб-интерфейс

Миграции — SQL-файлы в `backend/sql/`, применяются по алфавиту при **каждом** старте backend. Поэтому:

- новое изменение — новый файл со следующим номером (`03_add_something.sql`), уже существующие не правим;
- SQL должен выдерживать повторный запуск: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, `INSERT ... ON CONFLICT DO NOTHING`.

## Adminer

Откройте http://localhost:8080 и введите:

| Поле             | Значение     |
| ---------------- | ------------ |
| **Система**      | `PostgreSQL` |
| **Сервер**       | `db`         |
| **Пользователь** | `postgres`   |
| **Пароль**       | `postgres`   |
| **База данных**  | `app_db`     |

Здесь можно посмотреть таблицы (например, `poses`), поправить записи и выполнить SQL-запрос без DBeaver или pgAdmin.

> Логины и пароли выше — только для локальной разработки.

## Запуск production-окружения

Для запуска production-конфигурации используется отдельный файл `docker-compose.prod.yml`. Он предназначен для развёртывания приложения на сервере и отличается от локальной конфигурации `docker-compose.yml` настройками доступа к сервисам и использованием переменных окружения.

**Важно:** production и development Compose-файлы являются самостоятельными конфигурациями. Не указывайте оба файла одновременно через `-f`.

### 1. Подготовка окружения

На сервере должны быть установлены:

- Docker Engine;
- Docker Compose Plugin.

Проверьте доступность Docker:

```bash
docker --version
docker compose version
```

Перейдите в корневую директорию проекта:

```bash
cd down-dog
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта. Он содержит настройки подключения к PostgreSQL, MinIO и разрешённые источники запросов к API.

Для удобства можно скопировать `.env.example`:

```bash
cp .env.example .env
```

Затем откройте `.env` и укажите реальные значения:

```env
# PostgreSQL
POSTGRES_DB=down_dog
POSTGRES_USER=app_user
POSTGRES_PASSWORD=replace_with_secure_password

# MinIO
MINIO_ROOT_USER=minio_user
MINIO_ROOT_PASSWORD=replace_with_secure_password

# S3 bucket
BUCKET_NAME=down-dog

# Разрешённые источники CORS
CORS_ORIGINS=https://your-domain.com
```

Назначение переменных:

| Переменная | Назначение |
|---|---|
| `POSTGRES_DB` | Имя базы данных |
| `POSTGRES_USER` | Пользователь PostgreSQL |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL |
| `MINIO_ROOT_USER` | Имя администратора MinIO |
| `MINIO_ROOT_PASSWORD` | Пароль администратора MinIO |
| `BUCKET_NAME` | Имя S3-бакета |
| `CORS_ORIGINS` | Разрешённые источники запросов к API |

Для нескольких источников CORS используйте список через запятую:

```env
CORS_ORIGINS=https://your-domain.com,https://admin.your-domain.com
```

Указывайте полный origin: протокол, домен и при необходимости порт. Не добавляйте путь `/api`.

**Безопасность:**
- Не храните реальные пароли и другие секреты в `.env.example`.
- Файл `.env` не должен попадать в Git.
- Используйте уникальные сложные пароли для PostgreSQL и MinIO.
- Не используйте демонстрационные значения из `.env.example` в production.

### 3. Проверка конфигурации

Перед запуском проверьте production-конфигурацию:

```bash
docker compose --env-file .env -f docker-compose.prod.yml config --quiet
```

Если команда завершилась без ошибок, конфигурация Compose успешно прошла проверку.

### 4. Сборка и запуск приложения

Соберите образы и запустите сервисы в фоновом режиме:

```bash
docker compose --env-file .env -f docker-compose.prod.yml up --build -d
```

Проверьте состояние контейнеров:

```bash
docker compose --env-file .env -f docker-compose.prod.yml ps
```

При запуске сервисы проходят следующую последовательность:

1. PostgreSQL и MinIO запускаются и проходят healthcheck.
2. Сервис `migrate` ожидает готовности PostgreSQL и применяет SQL-миграции.
3. Сервис `s3` ожидает готовности MinIO, создаёт бакет и загружает изображения.
4. Backend запускается после успешного завершения миграций и готовности необходимых зависимостей.
5. Frontend запускается после того, как backend перейдёт в состояние `healthy`.

Сервисы `migrate` и `s3` выполняют одноразовые задачи. Поэтому статус `Exited (0)` для них после успешной работы является ожидаемым.

### 5. Проверка работоспособности

Посмотреть состояние всех сервисов:

```bash
docker compose --env-file .env -f docker-compose.prod.yml ps
```

Проверить backend healthcheck:

```bash
docker compose --env-file .env -f docker-compose.prod.yml exec backend curl -fsS --max-time 3 http://127.0.0.1:8000/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

Проверить логи:

```bash
docker compose --env-file .env -f docker-compose.prod.yml logs backend
docker compose --env-file .env -f docker-compose.prod.yml logs migrate
docker compose --env-file .env -f docker-compose.prod.yml logs s3
```

### 6. Доступ к приложению

В production-конфигурации напрямую опубликован порт frontend — `3000`.

Приложение доступно по адресу:

```text
http://<SERVER_IP>:3000
```

Backend, PostgreSQL и MinIO не публикуют свои порты на хост. Внутреннее взаимодействие между сервисами осуществляется через Docker network `app-network`.

Для полноценного публичного deployment рекомендуется разместить перед frontend reverse proxy (например, Nginx или Caddy), настроить доменное имя и HTTPS.

### 7. Остановка приложения

Остановить и удалить контейнеры, сохранив данные:

```bash
docker compose --env-file .env -f docker-compose.prod.yml down
```

Для повторного запуска:

```bash
docker compose --env-file .env -f docker-compose.prod.yml up -d
```

**Внимание:** не используйте `docker compose down -v` без необходимости. Эта команда удаляет volumes PostgreSQL и MinIO вместе с сохранёнными данными.

Перед обновлением production-приложения рекомендуется сделать резервную копию базы данных.

### 8. Обновление приложения

После получения новых изменений из репозитория:

```bash
git pull origin master
```

Пересоберите образы и обновите контейнеры:

```bash
docker compose --env-file .env -f docker-compose.prod.yml up --build -d
```

Проверьте состояние сервисов:

```bash
docker compose --env-file .env -f docker-compose.prod.yml ps
```

Данные PostgreSQL и MinIO сохраняются в Docker volumes при обычном обновлении контейнеров.

При добавлении новых SQL-миграций сервис `migrate` автоматически проверит и применит их перед запуском backend.
