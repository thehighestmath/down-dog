import math
import random
from collections.abc import Callable


def get_poses_by_focus(
    poses: list[dict],
    focus: str | None,
) -> list[dict]:
    if focus is None or focus == "full_body":
        return poses

    focus_map = {
        "back": ["спина", "поясница", "верхняя часть спины"],
        "neck": ["шея"],
        "legs": ["ноги", "ягодицы", "квадрицепсы", "икры", "задняя поверхность бедра"],
        "relaxation": ["расслабление"],
    }

    search_words = focus_map.get(focus)

    if search_words is None:
        return poses

    selected = []

    for pose in poses:
        muscle_groups = str(pose["focus_areas"]).lower()

        for word in search_words:
            if word.lower() in muscle_groups:
                selected.append(pose)
                break

    return selected


def _fill_time(
    t_max: int,
    poses: list[dict],
    difficulty_filter: Callable[[int], bool],
    last_name: str | None = None,
) -> tuple[list[str], int, str | None]:
    """Заполняет время позами без повторов подряд."""
    result: list[str] = []
    spent_time = 0

    candidates = [
        p
        for p in poses
        if p.get("full_cycle_sec") is not None
        and difficulty_filter(int(p["difficulty"]))
    ]

    if not candidates:
        return result, spent_time, last_name

    if len(candidates) == 1 and candidates[0]["name_en"] == last_name:
        return result, spent_time, last_name

    pool: list[dict] = []

    while t_max > 0:
        if not pool:
            pool = [p for p in candidates if p["name_en"] != last_name]
            if not pool:
                break
            random.shuffle(pool)

        chosen_idx = None
        for i, p in enumerate(pool):
            if p["name_en"] != last_name and p["full_cycle_sec"] <= t_max:
                chosen_idx = i
                break

        if chosen_idx is not None:
            pose = pool.pop(chosen_idx)
            name = pose["name_en"]
            value = pose["full_cycle_sec"]

            result.append(name)
            t_max -= value
            spent_time += value
            last_name = name
        else:
            has_other_fitting = any(
                p["name_en"] != last_name and p["full_cycle_sec"] <= t_max
                for p in candidates
            )
            if has_other_fitting:
                pool = []
                continue
            break

    return result, spent_time, last_name


def tren(
    poses: list[dict],
    level: str,
    duration: int,
    focus: str | None = None,
) -> dict:
    filtered = get_poses_by_focus(poses, focus)
    if not filtered:
        return {"poses": [], "actual_duration_sec": 0, "actual_duration_min": 0}

    plans = {
        "beginner": [
            (lambda d: d <= 2, 1, 1),
        ],
        "intermediate": [
            (lambda d: d <= 2, 1, 3),
            (lambda d: d == 3, 2, 3),
        ],
        "advanced": [
            (lambda d: d >= 4, 1, 5),
            (lambda d: d == 3, 3, 5),
            (lambda d: d >= 4, 1, 5),
        ],
    }

    result: list[str] = []
    total_sec = 0
    last_name: str | None = None

    for diff_filter, num, den in plans.get(level, []):
        block_poses, block_sec, last_name = _fill_time(
            duration * num // den,
            filtered,
            diff_filter,
            last_name=last_name,
        )
        result.extend(block_poses)
        total_sec += block_sec

    return {
        "poses": result,
        "actual_duration_sec": total_sec,
        "actual_duration_min": math.ceil(total_sec / 60) if total_sec > 0 else 0,
    }
