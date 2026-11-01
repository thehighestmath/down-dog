# Системный дизайн: AI Yoga Training App

## 1. Обзор системы

**Назначение:** Веб-приложение для персонализированных йога-тренировок с AI-подбором поз, визуализацией и голосовыми инструкциями (аналог Down Dog).

**Целевая аудитория:**

- Начинающие и продолжающие практиковать йогу
- Пользователи с ограничениями по здоровью (травмы, хронические состояния)
- Люди с разным количеством времени на тренировку (5-60 минут)

**Подход к разработке:**

- **MVP** — ядро тренировки (1-2 недели), без регистрации, без истории
- **Phase 2+** — пользователь, история, аналитика
- **Phase 3+** — админка, мобильные приложения, ML

---

## 2. Функциональные требования

### 2.1 MVP — Ядро тренировки

Требования MVP со статусом реализации — в [MVP.md, раздел 2](MVP.md). Там же отмечено, что из этого уже сделано.

### 2.2 Phase 2 — Пользователь и история

| ID   | Требование                                  | Приоритет |
| ---- | ------------------------------------------- | --------- |
| F-20 | Регистрация (email + пароль, JWT)           | Medium    |
| F-21 | Профиль пользователя на сервере             | Medium    |
| F-22 | Лог тренировок (история)                    | Medium    |
| F-23 | Статистика (время практики за неделю/месяц) | Low       |
| F-24 | Выбор голоса TTS                            | Low       |

### 2.3 Phase 3 — Polish

| ID   | Требование                           | Приоритет |
| ---- | ------------------------------------ | --------- |
| F-30 | Offline-режим (PWA, Service Worker)  | Low       |
| F-31 | Обратная связь (like/dislike поз)    | Low       |
| F-32 | ~~Пропуск позы / пауза~~ — уже в MVP | —         |
| F-33 | Фоновая музыка (опционально)         | Low       |

### 2.4 Phase 4 — Scale (Post-MVP)

| ID   | Требование                                        | Приоритет |
| ---- | ------------------------------------------------- | --------- |
| F-40 | Админ-интерфейс для каталога поз                  | Low       |
| F-41 | ML-рекомендации на основе истории                 | Low       |
| F-42 | Мобильные приложения: Android (Kotlin + Compose)  | Low       |
| F-43 | Интеграции с трекерами (Apple Health, Google Fit) | Low       |

---

## 3. Нефункциональные требования

### 3.1 MVP

Нефункциональные требования MVP — в [MVP.md, раздел 3](MVP.md). Там же отмечено, что из этого уже сделано.

### 3.2 Целевое решение (Phase 2+)

| Категория              | Требование                                                         |
| ---------------------- | ------------------------------------------------------------------ |
| **Производительность** | API latency p95 < 200 мс, 60 FPS анимации                          |
| **Масштабируемость**   | 10,000 одновременных пользователей, горизонтальное масштабирование |
| **Надёжность**         | 99.9% SLA, graceful degradation при недоступности TTS              |
| **Безопасность**       | HTTPS, JWT, rate limiting, bcrypt/argon2, GDPR                     |
| **Юзабилити**          | PWA (offline-режим), ARIA, контрастность                           |
| **Локализация**        | Русский (MVP), английский, расширяемо                              |

---

## 4. Архитектура

### 4.1 MVP — Упрощённая

Схема того, как MVP устроен сейчас (frontend на nginx, backend, PostgreSQL, MinIO, Adminer), — в [MVP.md, раздел 4](MVP.md).

**Упрощения MVP:**

- Нет аутентификации
- Нет User Service / Analytics Service
- Нет Redis
- Нет CDN
- 1 таблица в БД (`poses`), миграции — сырые SQL-файлы

---

### 4.2 Целевое решение (Phase 2+) — Монолит

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Web App   │  │  Mobile Web │  │  PWA (offline cache)    │  │
│  │  (React)    │  │   (React)   │  │  (Service Worker)       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS / REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MONOLITH (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Internal Modules (один процесс, общие модели)           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐   │   │
│  │  │  Auth    │ │ Workout  │ │  Content │ │  TTS       │   │   │
│  │  │  Module  │ │ Generator│ │  Module  │ │  Module    │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘   │   │
│  │  ┌──────────┐ ┌──────────┐                               │   │
│  │  │  Users   │ │ Analytics│                               │   │
│  │  │  Module  │ │ Module   │                               │   │
│  │  └──────────┘ └──────────┘                               │   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  Shared: DB connections, Redis client, S3 client   │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   PostgreSQL     │ │     Redis        │ │   Object Storage │
│   (5+ tables)    │ │   (cache/queue)  │ │   (S3 compat)    │
└──────────────────┘ └──────────────────┘ └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  TTS API    │  │  Email      │  │  CDN                    │  │
│  │  (ElevenLabs│  │  (SendGrid) │  │  (CloudFront/Cloudflare)│  │
│  │   /YC TTS)  │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Преимущества монолита:**

- Один репозиторий, один деплой
- Общие Pydantic модели между модулями
- Нет network overhead между сервисами
- Легче рефактить (не нужно менять API контракты)

**Структура проекта:**

```
app/
├── auth/          # JWT, регистрация, логин
├── users/         # Профиль, настройки
├── workouts/      # Генератор, история
├── poses/         # Каталог поз
├── tts/           # TTS интеграция, кэш
├── analytics/     # Статистика, рекомендации
├── shared/        # DB, Redis, S3 клиенты
└── main.py        # Роутинг, middleware
```

**Модули целевого решения:**

| Модуль                | Назначение                               |
| --------------------- | ---------------------------------------- |
| **Auth**              | JWT, регистрация, логин, refresh токенов |
| **Users**             | Профиль, настройки, предпочтения         |
| **Workout Generator** | Rule-based / ML подбор поз, тайминг      |
| **Content**           | CRUD поз, медиа, категории               |
| **TTS**               | Интеграция с TTS API, кэширование аудио  |
| **Analytics**         | Статистика, рекомендации, отчёты         |
| **Shared**            | DB подключения, Redis клиент, S3 клиент  |

**Инфраструктура:**

| Компонент      | Назначение                                        |
| -------------- | ------------------------------------------------- |
| **PostgreSQL** | Пользователи, позы, тренировки, история, feedback |
| **Redis**      | Кэш TTS, сессии, rate limiting                    |
| **S3**         | Изображения поз, аудио-файлы, видео               |
| **CDN**        | Раздача статики (изображения, аудио)              |

---

## 5. Модель данных

### 5.1 MVP — 1 таблица

Фактическая схема таблицы `poses` и состав seed-данных — в [MVP.md, раздел 5](MVP.md).

### 5.2 Целевое решение — 5+ таблиц

```sql
-- Пользователи
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    level           VARCHAR(20) DEFAULT 'beginner',
    goals           JSONB,
    limitations     TEXT[],
    preferences     JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Позы
CREATE TABLE poses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_ru         VARCHAR(100) NOT NULL,
    name_sanskrit   VARCHAR(100),
    category        VARCHAR(50) NOT NULL,
    difficulty      INTEGER NOT NULL,
    focus_areas     TEXT[],
    contraindications TEXT[],
    description     TEXT,
    image_url       TEXT NOT NULL,
    video_url       TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Тренировки
CREATE TABLE workouts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    name            VARCHAR(100),
    duration_min    INTEGER NOT NULL,
    difficulty      VARCHAR(20),
    focus_area      VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Позы в тренировке
CREATE TABLE workout_poses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id      UUID REFERENCES workouts(id),
    pose_id         UUID REFERENCES poses(id),
    order_index     INTEGER NOT NULL,
    phase           VARCHAR(20),              -- warmup, main, cooldown
    hold_duration   INTEGER NOT NULL,         -- секунды
    transition_time INTEGER NOT NULL          -- секунды
);

-- Обратная связь
CREATE TABLE pose_feedback (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    pose_id         UUID REFERENCES poses(id),
    liked           BOOLEAN NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 6. Data Flow: Генерация тренировки (MVP)

Формат запроса и ответа — в [MVP.md, раздел 6](MVP.md), логика генератора — в [разделе 7](MVP.md).

---

## 7. API Endpoints

### 7.1 MVP

| Метод | Endpoint                 | Описание                  |
| ----- | ------------------------ | ------------------------- |
| GET   | `/api/poses`             | Каталог поз (с фильтрами) |
| POST  | `/api/workouts/generate` | Генерация тренировки      |
| GET   | `/api/workouts/:id`      | Получение тренировки      |

### 7.2 Phase 2+

| Метод | Endpoint             | Описание           |
| ----- | -------------------- | ------------------ |
| POST  | `/api/auth/register` | Регистрация        |
| POST  | `/api/auth/login`    | Логин (JWT)        |
| POST  | `/api/auth/refresh`  | Refresh токена     |
| GET   | `/api/user/profile`  | Профиль            |
| PUT   | `/api/user/profile`  | Обновление профиля |
| GET   | `/api/user/workouts` | История тренировок |
| POST  | `/api/feedback/pose` | Like/dislike позы  |

---

## 8. TTS-озвучка

Шаблоны фраз и план интеграции — в [MVP.md, раздел 8](MVP.md).

**Phase 2+:** кэш в S3 + Redis (TTL 30 дней), ключ `hash(pose_id + template_id + language)`, при недоступности TTS — текст на экране.

---

### Шаблоны инструкций

```python
TTS_TEMPLATES = {
    "intro": "Начинаем тренировку. Первая поза — {pose_name}.",
    "pose_enter": "Входим в позу {pose_name}.",
    "breathing": "Сделайте глубокий вдох... и медленный выдох.",
    "hold": "Держите позу... ещё {seconds} секунд.",
    "transition": "Плавно выходим. Переход к следующей позе.",
    "outro": "Тренировка завершена. Отдохните в Шавасане.",
}
```

### Кэширование

- **Ключ:** `hash(pose_id + template_id + language)`
- **Хранилище:** S3 + Redis (TTL: 30 дней)
- **Fallback:** Текст на экране при недоступности TTS

---

## 9. Roadmap

### Phase 1: MVP Core — Ядро тренировки

Майлстоун [v0.0.1a](https://github.com/thehighestmath/down-dog/milestone/1).

- [x] Seed каталога поз (54 асаны) через SQL
- [x] Бэкенд: `/api/poses`, `/api/workouts/generate`, `/api/workouts/{id}`
- [x] Фронтенд: страница настроек + тренировка
- [ ] TTS интеграция (кэширование)
- [ ] Логирование событий для метрик
- [ ] Мобильная адаптация

### Phase 2: Пользователь и история (2-3 недели)

- [ ] Аутентификация (JWT)
- [ ] Профиль на сервере
- [ ] Лог тренировок
- [ ] Статистика

### Phase 3: Polish (2 недели)

- [ ] PWA (offline-режим)
- [ ] Like/dislike поз
- [ ] Выбор голоса TTS

### Phase 4: Scale (4+ недель)

- [ ] Админка для каталога
- [ ] ML-рекомендации
- [x] Android-приложение (Kotlin + Jetpack Compose, MVP в `android/`)
- [ ] iOS-приложение
- [ ] Интеграции с трекерами

---

## 10. Technology Stack

| Компонент      | MVP                              | Целевое решение (монолит)                  |
| -------------- | -------------------------------- | ------------------------------------------ |
| **Frontend**   | React 19, TS, Vite, nginx        | + PWA, Service Worker                      |
| **Backend**    | Python 3.14, FastAPI (1 сервис)  | FastAPI (монолит, 6 модулей)               |
| **Database**   | PostgreSQL 16 (1 таблица)        | PostgreSQL 16 (5+ таблиц) + Redis 7        |
| **Storage**    | S3 (MinIO локально, AWS в проде) | S3 + CDN (CloudFront/Cloudflare)           |
| **TTS**        | ElevenLabs / Yandex SpeechKit    | + кэширование (Redis, TTL 30 дней)         |
| **Infra**      | Docker Compose (6 сервисов)      | Docker Compose / K8s (опционально) + Nginx |
| **CI/CD**      | GitHub Actions                   | GitHub Actions + auto-deploy               |
| **Monitoring** | —                                | Prometheus + Grafana (опционально)         |

**Модули монолита (Phase 2+):**

- `auth/` — JWT, регистрация, логин
- `users/` — Профиль, настройки
- `workouts/` — Генератор тренировок, история
- `poses/` — Каталог поз
- `tts/` — TTS интеграция, кэш
- `analytics/` — Статистика, рекомендации
- `shared/` — DB, Redis, S3 клиенты

---

## 11. Эволюция архитектуры: MVP → Монолит

| Этап          | Что добавляется                                 | Сложность | Риск ломки |
| ------------- | ----------------------------------------------- | --------- | ---------- |
| **MVP**       | 1 таблица (`poses`), 3 endpoint'а               | —         | —          |
| **Phase 2.1** | Таблица `users` + JWT auth                      | Низкая    | Нет        |
| **Phase 2.2** | Таблицы `workouts`, `workout_poses` + история   | Низкая    | Нет        |
| **Phase 2.3** | Профиль на сервере (localStorage → API)         | Средняя   | Нет        |
| **Phase 2.4** | Redis (кэш TTS)                                 | Низкая    | Нет        |
| **Phase 3**   | Модули `analytics`, `tts` (выделение логически) | Средняя   | Нет        |
| **Phase 4**   | CDN, мониторинг, авто-деплой                    | Низкая    | Нет        |

**Ключевой принцип:** Ядро (генератор тренировок) не переписывается, а **расширяется**.

```python
# MVP
def generate_workout(duration, level, focus):
    poses = db.query("SELECT * FROM poses WHERE ...")
    return {"poses": split_by_phase(poses)}


# Phase 2+ (добавляется сохранение истории)
def generate_workout(duration, level, focus, user_id=None):
    poses = db.query("SELECT * FROM poses WHERE ...")  # ← тот же запрос
    workout = {"poses": split_by_phase(poses)}  # ← та же логика

    if user_id:
        save_to_history(user_id, workout)  # ← просто доп. шаг

    return workout
```

**90% кода MVP переносится в целевое решение без изменений.**

---

## 12. Риски и mitigation

| Риск                       | Вероятность | Влияние | Mitigation                                             |
| -------------------------- | ----------- | ------- | ------------------------------------------------------ |
| TTS API недоступен         | Medium      | High    | Кэширование 100%, fallback на текст                    |
| Нет изображений поз        | Medium      | High    | yoga-api (open source, MIT)                            |
| Генератор выдаёт ерунду    | High        | Medium  | Ручная проверка, итеративная настройка правил          |
| Таймер глючит на мобильных | Medium      | Medium  | `requestAnimationFrame`, тесты на реальных устройствах |
| Дорогой TTS                | Medium      | Medium  | Yandex SpeechKit дешевле ElevenLabs, кэш               |

---

## 13. Метрики успеха MVP

См. [MVP.md, раздел 12](MVP.md).
