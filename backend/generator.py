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
) -> list[str]:
    """Заполняет время позами, используя все уникальные позы перед повторами."""
    result: list[str] = []

    candidates = [
        p
        for p in poses
        if p.get("full_cycle_sec") is not None
        and difficulty_filter(int(p["difficulty"]))
    ]

    if not candidates:
        return result

    pool: list[dict] = []
    last_name: str | None = None

    while t_max > 0:
        if not pool:
            pool = list(candidates)
            random.shuffle(pool)
            if last_name and len(pool) > 1 and pool[0]["name_en"] == last_name:
                pool.append(pool.pop(0))

        pose = pool.pop(0)
        name = pose["name_en"]
        value = pose["full_cycle_sec"]

        if value <= t_max:
            result.append(name)
            t_max -= value
            last_name = name
        else:
            found = False
            for i, p in enumerate(pool):
                if p["full_cycle_sec"] <= t_max:
                    result.append(p["name_en"])
                    t_max -= p["full_cycle_sec"]
                    last_name = p["name_en"]
                    pool.pop(i)
                    found = True
                    break
            if not found:
                break

    return result


def tren(
    poses: list[dict],
    level: str,
    duration: int,
    focus: str | None = None,
) -> list[str]:
    filtered = get_poses_by_focus(poses, focus)
    if not filtered:
        return []

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
    for diff_filter, num, den in plans.get(level, []):
        result.extend(_fill_time(duration * num // den, filtered, diff_filter))

    return result
