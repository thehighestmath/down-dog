import json
import logging
import os
import re
import uuid
from typing import Annotated

import storage
from analytics import MAX_BODY_BYTES, AnalyticsEvent
from cors import setup_cors
from database import get_db_connection
from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from generator import get_poses_by_focus, tren
from pydantic import BaseModel
from workouts_repository import (
    get_workout_by_id,
    save_workout,
)

logger = logging.getLogger("app")

app = FastAPI()
setup_cors(app)


@app.get("/health")
def health_check() -> dict[str, str]:
    conn = None

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    finally:
        if conn is not None:
            conn.close()


# -----------------------------------------
# S3 (MinIO): озвучка
# -----------------------------------------


AUDIO_LANGS = {"ru", "en"}
AUDIO_KINDS = {"poses", "phrases", "numbers"}
AUDIO_NAME_RE = re.compile(r"[a-z0-9_]+")


def audio_name(name_en: str, audio_url: str | None) -> str:
    if audio_url:
        return os.path.basename(audio_url).removesuffix(".mp3")
    name = name_en.lower().replace("'", "").replace(" pose", "")
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")


# -----------------------------------------
# Вспомогательная функция: загрузка поз из БД
# -----------------------------------------


def load_poses_from_db() -> list[dict]:
    """Загружает все позы из таблицы poses в PostgreSQL."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name_ru, name_sanskrit, name_en, category, "
                "difficulty, focus_areas, contraindications, description, "
                "image_url, audio_url, hold_time_sec, full_cycle_sec "
                "FROM poses ORDER BY id"
            )
            rows = cursor.fetchall()
            poses = [dict(row) for row in rows]
            for pose in poses:
                pose["audio_name"] = audio_name(pose["name_en"], pose["audio_url"])
            return poses
    finally:
        conn.close()


# -----------------------------------------
# Модель запроса
# -----------------------------------------


class WorkoutRequest(BaseModel):
    duration_min: int
    level: str
    focus: str


# =========================================
# GET /api/poses
# =========================================


@app.get("/api/poses")
def get_poses(
    category: str | None = None, difficulty: int | None = None, focus: str | None = None
) -> list[dict]:
    poses = load_poses_from_db()

    # Фильтр по категории
    if category is not None:
        poses = [p for p in poses if p["category"] == category]

    # Фильтр по сложности
    if difficulty is not None:
        poses = [p for p in poses if int(p["difficulty"]) == difficulty]

    # Фильтр по фокусу
    if focus is not None:
        poses = get_poses_by_focus(poses, focus)

    return poses


# =========================================
# POST /api/workouts/generate
# =========================================


@app.post("/api/workouts/generate")
def generate_workout(request: WorkoutRequest) -> dict:
    # -------------------------------------
    # Проверяем длительность
    # -------------------------------------

    allowed_duration = [5, 10, 15, 20, 30]

    if request.duration_min not in allowed_duration:
        raise HTTPException(
            status_code=400, detail="duration_min должен быть 5, 10, 15, 20 или 30"
        )

    # -------------------------------------
    # Проверяем уровень
    # -------------------------------------

    allowed_levels = {"beginner", "intermediate", "advanced"}

    if request.level not in allowed_levels:
        raise HTTPException(
            status_code=400,
            detail="level должен быть beginner, intermediate или advanced",
        )

    # -------------------------------------
    # Проверяем фокус
    # -------------------------------------

    allowed_focus = {"back", "neck", "legs", "full_body", "relaxation"}

    if request.focus not in allowed_focus:
        raise HTTPException(status_code=400, detail="Неизвестный focus")

    # -------------------------------------
    # Загружаем позы из БД и генерируем тренировку
    # -------------------------------------

    poses = load_poses_from_db()

    generated = tren(
        poses=poses,
        level=request.level,
        duration=request.duration_min * 60,
        focus=request.focus,
    )
    workout_poses = generated["poses"]
    actual_duration_sec = generated["actual_duration_sec"]

    # -------------------------------------
    # Проверяем, удалось ли сгенерировать позы
    # -------------------------------------

    if not workout_poses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Не удалось подобрать позы для выбранных параметров. "
                "В будущих обновлениях мы сделаем подбор более гибким."
                "Попробуйте снизить уровень сложности или выбрать другой фокус."
            ),
        )

    # -------------------------------------
    # Создаём ID
    # -------------------------------------

    workout_id = str(uuid.uuid4())

    # -------------------------------------
    # Сохраняем тренировку
    # -------------------------------------

    workout = {
        "id": workout_id,
        "duration_min": request.duration_min,
        "actual_duration_sec": actual_duration_sec,
        "actual_duration_min": generated["actual_duration_min"],
        "level": request.level,
        "focus": request.focus,
        "poses": workout_poses,
    }

    save_workout(
        workout_id=workout_id,
        duration_min=request.duration_min,
        level=request.level,
        focus=request.focus,
        poses=workout_poses,
    )

    return workout


# =========================================
# GET /api/workouts/{id}
# =========================================


@app.get("/api/workouts/{workout_id}")
def get_workout(workout_id: str) -> dict:
    try:
        parsed_id = uuid.UUID(workout_id)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Тренировка не найдена",
        ) from None

    workout = get_workout_by_id(parsed_id)

    if workout is None:
        raise HTTPException(
            status_code=404,
            detail="Тренировка не найдена",
        )

    if not workout.get("poses"):
        raise HTTPException(
            status_code=400,
            detail="Тренировка не содержит упражнений. Пожалуйста, сгенерируйте новую.",
        )

    return workout


async def limit_body_size(request: Request) -> None:
    if len(await request.body()) > MAX_BODY_BYTES:
        raise HTTPException(
            status_code=413, detail=f"Событие больше {MAX_BODY_BYTES} байт"
        )


@app.post("/api/analytics/track", dependencies=[Depends(limit_body_size)])
def track_event(
    event: Annotated[AnalyticsEvent, Body(discriminator="event_type")],
) -> dict[str, str]:
    payload = event.payload.model_dump(mode="json", exclude_none=True)

    logging.info(
        "Event %s session=%s fields=%s",
        event.event_type,
        event.session_id,
        sorted(payload),
    )

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO analytics_events (event_type, user_id, session_id, payload)
                VALUES (%s, %s::uuid, %s::uuid, %s::jsonb)
                """,
                (
                    event.event_type,
                    str(event.user_id),
                    str(event.session_id),
                    json.dumps(payload),
                ),
            )
        conn.commit()
    finally:
        conn.close()

    return {"status": "ok"}


# =========================================
# GET /api/images/{name}
# =========================================


@app.get("/api/images/{name}")
def get_image(name: str) -> Response:
    """Картинка позы из MinIO. Ссылки на неё лежат в poses.image_url."""
    image = storage.get_image(name)

    if image is None:
        raise HTTPException(status_code=404, detail="Картинка не найдена")

    content, content_type = image
    # Картинки не меняются, пусть браузер и приложение кэшируют их на сутки
    return Response(
        content=content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


# =========================================
# GET /api/audio/{lang}/{kind}/{name}
# =========================================


@app.get("/api/audio/{lang}/{kind}/{name}")
def get_audio(lang: str, kind: str, name: str) -> StreamingResponse:
    if (
        lang not in AUDIO_LANGS
        or kind not in AUDIO_KINDS
        or not AUDIO_NAME_RE.fullmatch(name)
    ):
        raise HTTPException(status_code=404, detail="Аудио не найдено")

    audio = storage.get_audio(f"audio/{kind}_{lang}/{name}.mp3")

    if audio is None:
        raise HTTPException(status_code=404, detail="Аудио не найдено")

    chunks, size = audio
    return StreamingResponse(
        chunks,
        media_type="audio/mpeg",
        headers={"Content-Length": str(size)},
    )
