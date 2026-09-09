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
