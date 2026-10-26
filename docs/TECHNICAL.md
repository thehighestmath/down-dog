# Техническая документация

Подробные инструкции по отдельным частям проекта: MinIO, FastAPI, виртуальное окружение. Раньше они лежали в README.

> Основной способ запуска — `docker compose up -d --build`, см. [README](../README.md#быстрый-старт-docker). Он сам поднимает MinIO, создаёт бакет и запускает FastAPI. Инструкции ниже нужны, если вы запускаете что-то по отдельности или разбираетесь, как оно устроено.

- [MinIO](#minio)
- [FastAPI](#fastapi)

---

## MinIO

В проекте для хранения изображений используется **MinIO** — S3-совместимое объектное хранилище, запускаемое в Docker-контейнере.

### 1. Установка Docker

Если Docker ещё не установлен:

1. Скачайте [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Установите Docker, следуя инструкциям установщика.
3. Запустите Docker Desktop.
4. Убедитесь, что используется **WSL 2** (рекомендуется). Обычно это настройка по умолчанию.

### 2. Отдельный запуск MinIO

> При запуске через `docker compose` этот шаг не нужен: MinIO поднимается сервисом `minio`, а бакет `down-dog` создаёт сервис `s3`.

Чтобы запустить только MinIO, без остального проекта, откройте терминал (**PowerShell**, **cmd** или **WSL**) и выполните:

```bash
docker run -d --name minio -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" -v minio_data:/data minio/minio server /data --console-address ":9001"
```

#### Параметры команды

| Параметр                       | Назначение                         |
| ------------------------------ | ---------------------------------- |
| `-d`                           | Запуск контейнера в фоновом режиме |
| `--name minio`                 | Имя контейнера                     |
| `-p 9000:9000`                 | Порт для S3 API                    |
| `-p 9001:9001`                 | Порт для веб-консоли               |
| `-e "MINIO_ROOT_USER=..."`     | Логин для доступа                  |
| `-e "MINIO_ROOT_PASSWORD=..."` | Пароль для доступа                 |
| `-v minio_data:/data`          | Docker Volume для хранения данных  |

#### Проверка запуска

```bash
docker ps
```

В списке должен присутствовать контейнер `minio` со статусом `Up`.

#### Веб-консоль MinIO

Откройте в браузере [http://localhost:9001](http://localhost:9001).

Для входа используются логин и пароль из `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` (локально — `minioadmin` / `minioadmin`).

После входа:

1. Создайте бакет (bucket) `down-dog`.
2. При необходимости сделайте бакет публичным: **Access Policy → Public**.

### 3. Последующие запуски

> После перезагрузки компьютера или остановки Docker контейнер может быть остановлен. **Создавать контейнер заново не нужно.**

#### 3.1. Проверка состояния контейнера

Для Windows:

```powershell
docker ps -a | findstr minio
```

Для Linux/macOS:

```bash
docker ps -a | grep minio
```

Если статус `Up`, контейнер уже работает. Если `Exited` или `Created` — его нужно запустить.

#### 3.2. Запуск существующего контейнера

```bash
docker start minio
```

#### 3.3. Проверка

```bash
docker ps
```

У контейнера `minio` должен быть статус `Up`. Все ранее сохранённые данные остаются на месте: бакеты и файлы хранятся в Docker Volume `minio_data`.

### 4. Переменные окружения

Скрипт `s3/s3.py` (загрузка картинок) читает настройки подключения из переменных окружения или из файла `.env` в корне проекта. Пример — в [`.env.example`](../.env.example):

```dotenv
MINIO_ENDPOINT=http://localhost:9000
ACCESS_KEY=minioadmin
SECRET_KEY=minioadmin
BUCKET_NAME=down-dog
```

#### Безопасность

> **Важно:** файл `.env` не должен попадать в Git, особенно если в нём находятся реальные учётные данные. Он уже добавлен в `.gitignore`.

В репозитории хранится только `.env.example` — те же названия переменных, но без реальных секретов.

### Схема работы

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
        Bucket: down-dog
              │
              ▼
          Изображения
```

---

## FastAPI

**FastAPI** используется для backend API приложения Down Dog. Для запуска используется **Uvicorn**.

### 1. Создание виртуального окружения

> Этот шаг выполняется один раз — при первой настройке проекта.

Откройте терминал (**PowerShell**, **cmd** или **WSL**) и перейдите в корневую папку проекта:

```bash
cd путь_к_проекту
```

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

#### Активация виртуального окружения

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

После активации в терминале должно появиться:

```text
(.venv)
```

### 2. Установка зависимостей

В активированном виртуальном окружении:

```bash
pip install -r backend/requirements-dev.txt
```

Это поставит FastAPI, Uvicorn и всё остальное, что нужно backend и тестам.

#### Проверка установки

```bash
pip show fastapi
pip show uvicorn
```

### 3. Запуск FastAPI

Backend нужна база PostgreSQL и переменные для подключения к ней — как их задать, см. [README, «Разработка без Docker»](../README.md#backend). Затем:

```bash
cd backend
python -m uvicorn main:app --reload
```

#### Параметры команды

| Параметр   | Назначение                                             |
| ---------- | ------------------------------------------------------ |
| `main`     | Файл `backend/main.py`                                 |
| `app`      | Объект FastAPI с именем `app` в этом файле             |
| `--reload` | Автоматический перезапуск сервера после изменения кода |

После запуска API доступно по адресу `http://127.0.0.1:8000`.

### 4. Swagger / OpenAPI

FastAPI автоматически создаёт интерактивную документацию API:

- `http://127.0.0.1:8000/docs` — Swagger UI;
- `http://127.0.0.1:8000/redoc` — альтернативная документация.

#### Проверка endpoint через Swagger

1. Откройте `/docs`.
2. Найдите нужный endpoint.
3. Нажмите **Try it out**.
4. Укажите необходимые параметры.
5. Нажмите **Execute**.
6. Проверьте результат в **Response**.

Endpoint'ы MVP:

```text
GET  /api/poses
POST /api/workouts/generate
GET  /api/workouts/{id}
```

Подробнее о запросах и ответах — в [MVP.md, раздел 6](../MVP.md).

### 5. Зависимости

Зависимости хранятся рядом с кодом, который их использует:

- `backend/requirements.txt` — API (ставится в Docker-образ backend);
- `backend/requirements-dev.txt` — то же плюс инструменты для разработки и CI (pytest);
- `s3/requirements.txt` — загрузчик картинок в MinIO.

Добавив библиотеку, впишите её в нужный файл с версией (узнать версию: `pip show <пакет>`).
Не используйте `pip freeze >` — он выгрузит всё окружение, включая лишние пакеты.

### 6. Последующие запуски

> После перезагрузки компьютера **создавать виртуальное окружение заново и устанавливать зависимости повторно не нужно**.

1. Перейдите в папку проекта: `cd путь_к_проекту`.
2. Активируйте окружение: `.venv\Scripts\Activate.ps1` (PowerShell) или `.venv\Scripts\activate.bat` (CMD).
3. Задайте переменные для базы и запустите: `cd backend`, затем `python -m uvicorn main:app --reload`.

### 7. Если Uvicorn не запускается

Ошибка:

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

При необходимости переустановите зависимости:

```bash
pip install -r backend/requirements-dev.txt
```

Запуск через `python -m uvicorn ...` работает, даже если папка `Scripts` окружения не попала в `PATH`.

### 8. Если появилась ошибка импорта

Если `python -m uvicorn main:app --reload` выдаёт ошибку импорта (`No module named 'main'`, `No module named 'generator'`), проверьте:

1. Вы находитесь в папке `backend/`, а не в корне проекта: модули импортируют друг друга напрямую (`from generator import ...`).
2. Виртуальное окружение активировано.

Строка `main:app` означает:

```text
main.py → файл (в текущей папке)
app     → объект FastAPI внутри него
```

### 9. Остановка FastAPI

В терминале нажмите `Ctrl + C`.

### 10. Связь FastAPI и MinIO

FastAPI и MinIO выполняют разные задачи:

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

При запуске FastAPI повторно создавать контейнер MinIO или бакет не нужно.

### Схема запуска

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
cd backend
python -m uvicorn main:app --reload
   │
   ▼
http://127.0.0.1:8000
   │
   ├── API
   │
   └── Swagger → /docs
```
