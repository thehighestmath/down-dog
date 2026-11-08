import logging
from typing import Any
from uuid import UUID

import psycopg2
from database import get_db_connection
from psycopg2.extras import Json

logger = logging.getLogger("app.repo.workouts")


def _db_error_fields(exc: BaseException) -> dict[str, Any]:
    """Достаёт из psycopg2-исключения поля для структурного лога."""
    if not isinstance(exc, psycopg2.Error):
        return {}
    diag = getattr(exc, "diag", None)
    return {
        "sqlstate": exc.pgcode,  # '22P02', '23505', ...
        "constraint": getattr(diag, "constraint_name", None),
        "message": getattr(diag, "message_primary", str(exc)),
    }


def save_workout(
    workout_id: str,
    duration_min: int,
    level: str,
    focus: str,
    poses: list[str],
) -> None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO workouts (id, duration_min, level, focus, poses)
                VALUES (%s::uuid, %s, %s, %s, %s)
                """,
                (workout_id, duration_min, level, focus, Json(poses)),
            )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.exception(
            "workout insert failed id=%s level=%s focus=%s duration_min=%s "
            "poses_count=%d sqlstate=%s constraint=%s",
            workout_id,
            level,
            focus,
            duration_min,
            len(poses),
            getattr(exc, "pgcode", None),
            getattr(getattr(exc, "diag", None), "constraint_name", None),
        )
        raise
    finally:
        conn.close()


def get_workout_by_id(workout_id: UUID) -> dict[str, Any] | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, duration_min, level, focus, poses
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
    except Exception as exc:
        logger.exception(
            "workout select failed id=%s sqlstate=%s",
            workout_id,
            getattr(exc, "pgcode", None),
        )
        raise
    finally:
        conn.close()
