# Документация по Docker и MinIO

В этом проекте для хранения изображений используется **MinIO** — S3-совместимое объектное хранилище, запускаемое в Docker-контейнере.

## 1. Установка Docker

Если Docker ещё не установлен:

1. Скачайте [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Установите Docker, следуя инструкциям установщика.
3. Запустите Docker Desktop.
4. Убедитесь, что используется **WSL 2** (рекомендуется). Обычно это настройка по умолчанию.

## 2. Первый запуск MinIO

> **Важно:** этот шаг выполняется только один раз — при первой настройке проекта.

Откройте терминал (**PowerShell**, **cmd** или **WSL**) и выполните:

```bash
docker run -d --name minio -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" -v minio_data:/data minio/minio server /data --console-address ":9001"
```

### Параметры команды

| Параметр | Назначение |
|---|---|
| `-d` | Запуск контейнера в фоновом режиме |
| `--name minio` | Имя контейнера |
| `-p 9000:9000` | Порт для S3 API |
| `-p 9001:9001` | Порт для веб-консоли |
| `-e "MINIO_ROOT_USER=..."` | Логин для доступа |
| `-e "MINIO_ROOT_PASSWORD=..."` | Пароль для доступа |
| `-v minio_data:/data` | Docker Volume для хранения данных |

### Проверка запуска

После запуска проверьте, что контейнер работает:

```bash
docker ps
```

В списке должен присутствовать контейнер `minio` со статусом `Up`.

### Веб-консоль MinIO

Откройте в браузере:

[http://localhost:9001](http://localhost:9001)

Для входа используются:

- **Логин:** `смотри .env.exaple
- **Пароль:** `смотри .env.exaple

После входа:

1. Создайте бакет (bucket), например `yogaimages`.
2. При необходимости сделайте бакет публичным: **Access Policy → Public**.

## 3. Последующие запуски

> После перезагрузки компьютера или остановки Docker контейнер может быть остановлен. **Создавать контейнер заново не нужно.**

### 3.1. Проверка состояния контейнера

Для Windows выполните:

```powershell
docker ps -a | findstr minio
```

Для Linux/macOS:

```bash
docker ps -a | grep minio
```

Если статус `Up`, контейнер уже работает.

Если статус `Exited` или `Created`, контейнер остановлен — его нужно запустить.

### 3.2. Запуск существующего контейнера

```bash
docker start minio
```

### 3.3. Проверка запуска

```bash
docker ps
```

У контейнера `minio` должен быть статус `Up`.

### 3.4. Открытие веб-консоли

Откройте:

[http://localhost:9001](http://localhost:9001)

Все ранее сохранённые данные должны остаться на месте: бакеты и файлы сохраняются в Docker Volume `minio_data`.

### 3.5. Настройки подключения из Python

В Python-скрипте используйте те же параметры подключения, которые указаны в `.env`:

```text
MINIO_ENDPOINT=http://localhost:9000
ACCESS_KEY=minioadmin
SECRET_KEY=minioadmin
BUCKET_NAME=yogaimages
```

## 4. Переменные окружения

Для подключения к MinIO из Python используйте файл `.env` в корне проекта:

```dotenv
MINIO_ENDPOINT=http://localhost:9000
ACCESS_KEY=minioadmin
SECRET_KEY=minioadmin
BUCKET_NAME=yogaimages
```

### Безопасность

> **Важно:** файл `.env` не должен попадать в Git, особенно если в нём находятся реальные учётные данные.

Добавьте `.env` в `.gitignore`:

```gitignore
.env
```

В репозитории рекомендуется хранить файл-пример `.env.example` с теми же названиями переменных, но без реальных секретов:

```dotenv
MINIO_ENDPOINT=http://localhost:9000
ACCESS_KEY=your_access_key
SECRET_KEY=your_secret_key
BUCKET_NAME=yogaimages
```

---

## Краткая схема работы

```text
Docker Desktop
      │
      ▼
  MinIO container
      │
      ├── S3 API → localhost:9000
      │
      └── Web Console → localhost:9001
              │
              ▼
        Bucket: yogaimages
              │
              ▼
          Изображения
```
# Документация по запуску FastAPI

В этом проекте **FastAPI** используется для создания backend API приложения Down Dog.
Для запуска FastAPI используется **Uvicorn**.

## 1. Создание виртуального окружения

> **Важно:** этот шаг выполняется только один раз — при первой настройке проекта.

Откройте терминал (**PowerShell**, **cmd** или **WSL**) и перейдите в корневую папку проекта:

```bash
cd путь_к_проекту
```

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

### Активация виртуального окружения

Для Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Для Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

После активации в терминале должно появиться:

```text
(.venv)
```

## 2. Установка FastAPI и Uvicorn

В активированном виртуальном окружении выполните:

```bash
pip install fastapi uvicorn
```

### Проверка установки

```bash
pip show fastapi
pip show uvicorn
```

## 3. Структура проекта

Пример минимальной структуры:

```text
down-dog/
│
├── app/
│   ├── __init__.py
│   └── main.py
│
├── .venv/
├── requirements.txt
├── .gitignore
├── .env
├── .env.example
└── README.md
```

Основной файл FastAPI:

```text
app/main.py
```

## 4. Запуск FastAPI

Из визуального окружения выполните:

```bash
uvicorn backend.main:backend --reload
```

### Параметры команды

| Параметр | Назначение |
|---|---|
| `app.main` | Файл `app/main.py` |
| `app` | Объект FastAPI с именем `app` |
| `--reload` | Автоматический перезапуск сервера после изменения кода |

После успешного запуска API будет доступно:

```text
http://127.0.0.1:8000
```

## 5. Проверка FastAPI

Откройте в браузере:

```text
http://127.0.0.1:8000
```

Если в `main.py` используется тестовый endpoint:

```python
@app.get("/")
def root():
    return {"message": "Down Dog API"}
```

ожидаемый ответ:

```json
{"message":"Down Dog API"}
```

## 6. Swagger / OpenAPI

FastAPI автоматически создаёт интерактивную документацию API.

Откройте:

```text
http://127.0.0.1:8000/docs
```

Также доступна альтернативная документация:

```text
http://127.0.0.1:8000/redoc
```

### Проверка endpoint через Swagger

1. Откройте `/docs`.
2. Найдите нужный endpoint.
3. Нажмите **Try it out**.
4. Укажите необходимые параметры.
5. Нажмите **Execute**.
6. Проверьте результат в **Response**.

Для текущей задачи Down Dog API должны использоваться:

```text
GET  /api/poses
POST /api/workouts/generate
GET  /api/workouts/{id}
```

## 7. Сохранение зависимостей

После установки библиотек создайте или обновите `requirements.txt`:

```bash
pip freeze > requirements.txt
```

В `requirements.txt` должны присутствовать установленные зависимости, включая:

```text
fastapi
uvicorn
```

В репозитории рекомендуется хранить `.env.example` с примерами переменных без реальных секретов.

## 8. Последующие запуски

> После перезагрузки компьютера или остановки работы **создавать виртуальное окружение заново и устанавливать FastAPI повторно не нужно**.

### 8.1. Перейдите в папку проекта

```bash
cd путь_к_проекту
```

### 8.2. Активируйте виртуальное окружение

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

### 8.3. Запустите FastAPI

```bash
uvicorn backend.main:backend --reload
```

## 9. Если Uvicorn не запускается

Если появилась ошибка:

```text
'uvicorn' is not recognized
```

Проверьте, что виртуальное окружение активировано:

```powershell
.venv\Scripts\Activate.ps1
```

Проверьте установку:

```bash
pip show uvicorn
```

При необходимости установите:

```bash
pip install uvicorn
```

Также можно использовать:

```bash
python -m uvicorn backend.main:backend --reload
```

## 10. Если появилась ошибка импорта

Если команда:

```bash
uvicorn backend.main:backend --reload
```

выдаёт ошибку импорта, проверьте:

1. Вы находитесь в корневой папке проекта.
2. Существует файл `app/main.py`.
3. В `main.py` есть объект FastAPI с именем `app`.
4. Виртуальное окружение активировано.

Команда:

```text
app.main:app
```

означает:

```text
app/       → папка
main.py    → файл
app        → объект FastAPI
```

## 11. Остановка FastAPI

Для остановки сервера в терминале нажмите:

```text
Ctrl + C
```

## 12. Порядок работы в проекте Down Dog

После запуска FastAPI:

1. Проверить `/`.
2. Проверить `/docs`.
3. Проверить существующие endpoint.
4. Обновить `requirements.txt`.
5. Реализовать `GET /api/poses`.
6. Добавить фильтры `category`, `difficulty` и `focus`.
7. Реализовать rule-based генератор тренировок.
8. Добавить `POST /api/workouts/generate`.
9. Добавить `GET /api/workouts/{id}`.
10. Написать тесты.

## 13. Связь FastAPI и MinIO

FastAPI и MinIO выполняют разные задачи.

```text
FastAPI
   │
   └── Backend API
          │
          └── Данные и логика приложения

MinIO
   │
   └── S3-хранилище
          │
          └── Изображения поз
```

MinIO уже создан и настроен отдельно.
При запуске FastAPI повторно создавать Docker-контейнер
или bucket не требуется.

---

## Краткая схема запуска

```text
Терминал
   │
   ▼
Папка проекта
   │
   ▼
Активация .venv
   │
   ▼
uvicorn app.main:app --reload
   │
   ▼
http://127.0.0.1:8000
   │
   ├── API
   │
   └── Swagger → /docs
```

# Conventional commit messages (pre-commit хук)

Проект использует формат **Conventional Commits** для сообщений коммитов. Формат проверяется на каждом `git commit` хуком `commit-msg` через [pre-commit](https://pre-commit.com).

## Формат сообщения

```text
type(scope): subject
```

- **type** — обязателен. Допустимые: `feat`, `fix`, `build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`.
- **scope** — необязательный контекст изменения, например `auth`, `api`.
- **subject** — обязателен, не должен заканчиваться точкой.
- Для ломающих изменений добавьте `!` после type/scope, например `feat!: change`.
- Сообщения `Merge ...` и `Revert ...` пропускаются автоматически.

Примеры:

```text
feat: add new feature
fix(auth): fix login flow
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
