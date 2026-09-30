import logging
import os
import uuid
from contextlib import asynccontextmanager

import pandas as pd
from database import get_db_connection
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from generator import get_poses_by_focus, tren
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app")

def init_db():
    migration_path = os.path.join(BASE_DIR, "sql", "create_poses.sql")

    if os.path.exists(migration_path):
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                with open(migration_path, "r", encoding="utf-8") as f:
                    cursor.execute(f.read())
                conn.commit()
            conn.close()
            logger.info("Миграции PostgreSQL успешно применены")

        except Exception as e:
            logger.error("Ошибка при применении миграции: %s", e, exc_info=True)
    else:
        logger.warning("Файл миграции НЕ найден по пути: %s", migration_path)

@asynccontextmanager
async def lifespan(app: FastAPI):
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


# Получаем папку, в которой находится текущий скрипт (backend)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Соединяем путь к папке с именем файла
csv_path = os.path.join(BASE_DIR, "Pose_with_focus.csv")

# Передаем полный путь в pandas
df = pd.read_csv(csv_path)

# -----------------------------------------
# Временное хранилище тренировок
# -----------------------------------------

workouts = {}


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
):
    result = df.copy()

    # Фильтр по категории
    if category is not None:
        result = result[result["Категория"] == category]

    # Фильтр по сложности
    if difficulty is not None:
        result = result[result["Сложность (1-4)"] == difficulty]

    # Фильтр по фокусу
    if focus is not None:
        result = get_poses_by_focus(result, focus)

    return result.to_dict(orient="records")


# =========================================
# POST /api/workouts/generate
# =========================================


@app.post("/api/workouts/generate")
def generate_workout(request: WorkoutRequest):
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
    # Генерируем тренировку
    # -------------------------------------

    workout_poses = tren(
        df=df,
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
def get_workout(workout_id: str):
    workout = workouts.get(workout_id)

    if workout is None:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    return workout
