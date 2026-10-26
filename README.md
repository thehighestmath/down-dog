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

## Тесты и проверки

```bash
pytest                      # из корня репозитория
pre-commit run --all-files  # все линтеры и форматтеры, как в CI
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

### Миграции базы

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
