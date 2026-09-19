from http.client import HTTPException

from fastapi import FastAPI, Request
from pydantic import BaseModel
import pandas as pd
import uuid
import os
import sys
from app.generator import tren, get_poses_by_focus

app = FastAPI()

# Получаем папку, в которой находится текущий скрипт (app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Соединяем путь к папке с именем файла
csv_path = os.path.join(BASE_DIR, 'Pose_with_focus.csv')

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
        category: str | None = None,
        difficulty: int | None = None,
        focus: str | None = None
):
    result = df.copy()

    # Фильтр по категории
    if category is not None:
        result = result[
            result["Категория"] == category
            ]

    # Фильтр по сложности
    if difficulty is not None:
        result = result[
            result["Сложность (1-4)"] == difficulty
            ]

    # Фильтр по фокусу
    if focus is not None:
        result = get_poses_by_focus(
            result,
            focus
        )

    return result.to_dict(
        orient="records"
    )


# =========================================
# POST /api/workouts/generate
# =========================================

@app.post("/api/workouts/generate")
def generate_workout(request: WorkoutRequest):
    # -------------------------------------
    # Проверяем длительность
    # -------------------------------------

    allowed_duration = [
        5,
        10,
        15,
        20,
        30
    ]

    if request.duration_min not in allowed_duration:
        raise HTTPException(
            status_code=400,
            detail="duration_min должен быть 5, 10, 15, 20 или 30"
        )

    # -------------------------------------
    # Проверяем уровень
    # -------------------------------------

    allowed_levels = [
        "beginner",
        "intermediate",
        "advanced"
    ]

    if request.level not in allowed_levels:
        raise HTTPException(
            status_code=400,
            detail="level должен быть beginner, intermediate или advanced"
        )

    # -------------------------------------
    # Проверяем фокус
    # -------------------------------------

    allowed_focus = [
        "back",
        "neck",
        "legs",
        "full_body",
        "relaxation"
    ]

    if request.focus not in allowed_focus:
        raise HTTPException(
            status_code=400,
            detail="Неизвестный focus"
        )

    # -------------------------------------
    # Генерируем тренировку
    # -------------------------------------

    workout_poses = tren(
        df=df,
        level=request.level,
        duration=request.duration_min * 60,
        focus=request.focus
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
        "poses": workout_poses
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
        raise HTTPException(
            status_code=404,
            detail="Тренировка не найдена"
        )

    return workout
