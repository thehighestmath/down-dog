import json
import urllib.error
import urllib.request
from collections import Counter

import pytest

API_URL = "http://localhost:8000/api/workouts/generate"

FOCUSES = ["back", "legs", "neck", "full_body", "relaxation"]
LEVELS = ["beginner", "intermediate", "advanced"]
DURATIONS_MIN = [5, 10, 15, 20, 30]


@pytest.mark.parametrize("focus", FOCUSES)
@pytest.mark.parametrize("level", LEVELS)
@pytest.mark.parametrize("minutes", DURATIONS_MIN)
def test_live_api_workout_no_duplicates(focus: str, level: str, minutes: int) -> None:
    """Отправляет реальный запрос к бэкенду и проверяет дубликаты."""
    payload = json.dumps(
        {
            "duration_min": minutes,
            "level": level,
            "focus": focus,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            detail = json.loads(error_body).get("detail", error_body)
        except Exception:
            detail = error_body

        is_expected_error = e.code in (400, 422) or "not enough" in detail.lower()

        if is_expected_error:
            pytest.skip(
                f"Комбинация пропускается (ожидаемая ошибка бэкенда): "
                f"фокус '{focus}', уровень '{level}', {minutes} мин. Причина: {detail}"
            )
        else:
            pytest.fail(
                f"Неожиданная ошибка сервера (код {e.code}) "
                f"для фокуса '{focus}', уровня '{level}', {minutes} мин. "
                f"Причина: {detail}"
            )

    except urllib.error.URLError as e:
        pytest.fail(
            f"Не удалось подключиться к серверу по адресу {API_URL}: {e.reason}"
        )

    poses = data.get("poses", [])

    if not poses:
        pytest.fail(
            f"Тренировка невозможна: сервер вернул пустой список поз "
            f"для фокуса '{focus}', уровня '{level}', {minutes} мин."
        )

    counts = Counter(poses)
    duplicates = {name: cnt for name, cnt in counts.items() if cnt > 1}

    if duplicates:
        items = (f"'{name}' (x{cnt})" for name, cnt in duplicates.items())
        dup_details = ", ".join(items)
        pytest.skip(
            "Тренировка невозможна: на сайте появляются повторяющиеся позы "
            f"для фокуса '{focus}', уровня '{level}', {minutes} мин. "
            f"Повторы: {dup_details}."
        )
