import math
import random
from collections.abc import Callable
from dataclasses import dataclass

WARMUP_CATEGORIES = {"warmup"}
MAIN_CATEGORIES = {"mid", "balancing"}
COOLDOWN_CATEGORIES = {"cooldown"}


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


@dataclass
class FillTimeResult:
    poses: list[str]
    spent_time: int
    last_name: str | None


def _fill_time(
    t_max: int,
    poses: list[dict],
    difficulty_filter: Callable[[int], bool],
    last_name: str | None = None,
) -> FillTimeResult:
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
        return FillTimeResult(poses=result, spent_time=spent_time, last_name=last_name)

    if len(candidates) == 1 and candidates[0]["name_en"] == last_name:
        return FillTimeResult(poses=result, spent_time=spent_time, last_name=last_name)

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

    return FillTimeResult(poses=result, spent_time=spent_time, last_name=last_name)


def _select_phase_poses(
    all_poses: list[dict],
    focus: str | None,
    categories: set[str],
) -> list[dict]:
    """Возвращает позы нужной категории с учётом фокуса и fallback."""
    all_in_category = [p for p in all_poses if p.get("category") in categories]
    if not all_in_category:
        return []

    focused = get_poses_by_focus(all_in_category, focus)
    return focused if focused else all_in_category


def tren(
    poses: list[dict],
    level: str,
    duration: int,
    focus: str | None = None,
) -> dict:
    empty_response = {
        "poses": [],
        "phases": [],
        "actual_duration_sec": 0,
        "actual_duration_min": 0,
    }
    if not poses or duration <= 0:
        return empty_response

    main_plans: dict[str, list[tuple[Callable[[int], bool], int, int]]] = {
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

    if level not in main_plans:
        return empty_response

    warmup_budget = duration // 5
    main_budget = (duration * 3) // 5
    cooldown_budget = duration - warmup_budget - main_budget

    warmup_poses = _select_phase_poses(poses, focus, WARMUP_CATEGORIES)
    main_poses = _select_phase_poses(poses, focus, MAIN_CATEGORIES)
    cooldown_poses = _select_phase_poses(poses, focus, COOLDOWN_CATEGORIES)

    result: list[str] = []
    phases: list[str] = []
    total_sec = 0
    last_name: str | None = None

    # 1. Разминка (~20%): фаза важнее уровня сложности
    if warmup_poses and warmup_budget > 0:
        filled = _fill_time(
            warmup_budget,
            warmup_poses,
            lambda _d: True,
            last_name=last_name,
        )
        result.extend(filled.poses)
        phases.extend(["warmup"] * len(filled.poses))
        total_sec += filled.spent_time
        last_name = filled.last_name

    # 2. Основная часть (~60%): распределение по уровню сложности
    if main_poses and main_budget > 0:
        for diff_filter, num, den in main_plans[level]:
            filled = _fill_time(
                main_budget * num // den,
                main_poses,
                diff_filter,
                last_name=last_name,
            )
            result.extend(filled.poses)
            phases.extend(["main"] * len(filled.poses))
            total_sec += filled.spent_time
            last_name = filled.last_name

    # 3. Заминка (~20%): фаза важнее уровня сложности
    if cooldown_poses and cooldown_budget > 0:
        filled = _fill_time(
            cooldown_budget,
            cooldown_poses,
            lambda _d: True,
            last_name=last_name,
        )
        result.extend(filled.poses)
        phases.extend(["cooldown"] * len(filled.poses))
        total_sec += filled.spent_time
        last_name = filled.last_name

    return {
        "poses": result,
        "phases": phases,
        "actual_duration_sec": total_sec,
        "actual_duration_min": math.ceil(total_sec / 60) if total_sec > 0 else 0,
    }
