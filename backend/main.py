import logging
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from database import get_db_connection
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from generator import get_poses_by_focus, tren
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def init_db() -> None:
    sql_dir = os.path.join(BASE_DIR, "sql")

    if not os.path.exists(sql_dir):
        logger.warning("Папка миграций НЕ найдена по пути: %s", sql_dir)
        return

    sql_files = sorted([f for f in os.listdir(sql_dir) if f.endswith(".sql")])

    if not sql_files:
        logger.warning("В папке %s не найдено .sql файлов", sql_dir)
        return

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            for file_name in sql_files:
                file_path = os.path.join(sql_dir, file_name)
                logger.info("Применение миграции: %s", file_name)

                with open(file_path, encoding="utf-8") as f:
                    cursor.execute(f.read())

        conn.commit()
        conn.close()
        logger.info("Все миграции PostgreSQL успешно применены!")

    except Exception as e:
        logger.error("Ошибка при применении миграции: %s", e, exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для разработки; в проде укажи свой домен
    allow_credentials=False,  # "*" + credentials=True нельзя вместе
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------
# Временное хранилище тренировок
# -----------------------------------------

workouts: dict[str, dict] = {}


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
            return [dict(row) for row in rows]
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

    workout_poses = tren(
        poses=poses,
        level=request.level,
        duration=request.duration_min * 60,
        focus=request.focus,
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
        "level": request.level,
        "focus": request.focus,
        "poses": workout_poses,
    }

    workouts[workout_id] = workout

    return workout


# =========================================
# GET /api/workouts/{id}
# =========================================


@app.get("/api/workouts/{workout_id}")
def get_workout(workout_id: str) -> dict:
    workout = workouts.get(workout_id)

    if workout is None:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    return workout
