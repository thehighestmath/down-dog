from typing import Any
from uuid import UUID

from database import get_db_connection
from psycopg2.extras import Json


def save_workout(
    workout_id: str,
    duration_min: int,
    level: str,
    focus: str,
    poses: list[str],
) -> None:
    """Сохраняет сгенерированную тренировку в PostgreSQL."""
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO workouts (
                    id,
                    duration_min,
                    level,
                    focus,
                    poses
                )
                VALUES (%s::uuid, %s, %s, %s, %s)
                """,
                (
                    workout_id,
                    duration_min,
                    level,
                    focus,
                    Json(poses),
                ),
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_workout_by_id(workout_id: UUID) -> dict[str, Any] | None:
    """Получает тренировку из PostgreSQL по UUID."""
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    duration_min,
                    level,
                    focus,
                    poses
                FROM workouts
                WHERE id = %s::uuid
                """,
                (str(workout_id),),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            workout = dict(row)
            workout["id"] = str(workout["id"])

            return workout

    finally:
        conn.close()
