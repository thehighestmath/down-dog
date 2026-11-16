import math
import random
from collections.abc import Callable
from dataclasses import dataclass

FOCUS_KEYWORDS: dict[str, list[str]] = {
    "back": ["спина", "поясница", "верхняя часть спины"],
    "neck": ["шея"],
    "legs": ["ноги", "ягодицы", "квадрицепсы", "икры", "задняя поверхность бедра"],
    "relaxation": ["расслабление"],
    "full_body": [],
}

WARMUP_CATEGORIES = {"warmup"}
MAIN_CATEGORIES = {"mid", "balancing"}
COOLDOWN_CATEGORIES = {"cooldown"}

# Пропорции длительности фаз тренировки: 20% разминка, 60% основная часть, 20% заминка
WARMUP_SHARE_NUM = 1
MAIN_SHARE_NUM = 3
PHASE_SHARE_DEN = 5


@dataclass(frozen=True)
class _FillResult:
    poses: list[str]
    spent_time: int
    last_name: str | None


@dataclass(frozen=True)
class DifficultyBlock:
    """Доля основной части тренировки для заданного фильтра сложности."""

    difficulty_filter: Callable[[int], bool]
    share_num: int
    share_den: int


# Распределение времени основной части по уровням (согласно разделу 7 MVP.md)
MAIN_PLANS: dict[str, list[DifficultyBlock]] = {
    "beginner": [
        DifficultyBlock(difficulty_filter=lambda d: d <= 2, share_num=1, share_den=1),
    ],
    "intermediate": [
        DifficultyBlock(difficulty_filter=lambda d: d <= 2, share_num=1, share_den=3),
        DifficultyBlock(difficulty_filter=lambda d: d == 3, share_num=2, share_den=3),
    ],
    "advanced": [
        DifficultyBlock(difficulty_filter=lambda d: d >= 4, share_num=1, share_den=5),
        DifficultyBlock(difficulty_filter=lambda d: d == 3, share_num=3, share_den=5),
        DifficultyBlock(difficulty_filter=lambda d: d >= 4, share_num=1, share_den=5),
    ],
}


def get_poses_by_focus(all_poses: list[dict], focus: str) -> list[dict]:
    """Фильтрует позы по выбранному фокусу тренировки."""
    if focus == "full_body" or focus not in FOCUS_KEYWORDS:
        return all_poses

    keywords = FOCUS_KEYWORDS[focus]
    filtered = []
    for pose in all_poses:
        areas = (pose.get("focus_areas") or "").lower()
        if any(kw in areas for kw in keywords):
            filtered.append(pose)
    return filtered


def _is_valid_pose(pose: dict) -> bool:
    """Проверяет, что у позы задана корректная длительность > 0."""
    sec = pose.get("full_cycle_sec")
    return sec is not None and int(sec) > 0


def _get_phase_poses(
    all_poses: list[dict],
    focus: str,
    categories: set[str],
) -> list[dict]:
    """Возвращает позы нужной категории с учётом фокуса и fallback."""
    all_in_category = [p for p in all_poses if p.get("category") in categories]
    if not all_in_category:
        return []

    focused = get_poses_by_focus(all_in_category, focus)
    return focused if focused else all_in_category


def _fill_time(
    target_time: int,
    poses_pool: list[dict],
    difficulty_filter: Callable[[int], bool] | None = None,
    last_name: str | None = None,
) -> _FillResult:
    """Заполняет выделенный бюджет времени позами из пула без повторов подряд."""
    matching = [
        p
        for p in poses_pool
        if _is_valid_pose(p)
        and (
            difficulty_filter is None
            or difficulty_filter(int(p.get("difficulty") or 0))
        )
    ]
    if not matching or target_time <= 0:
        return _FillResult(poses=[], spent_time=0, last_name=last_name)

    selected: list[str] = []
    spent = 0
    current_last = last_name

    while spent < target_time:
        remaining = target_time - spent
        fitting = [p for p in matching if int(p["full_cycle_sec"]) <= remaining]
        if not fitting:
            break

        # Стараемся не повторять позы, пока не исчерпан уникальный пул
        unused = [p for p in fitting if p["name_en"] not in selected]
        candidates = unused if unused else fitting

        # Исключаем повторение одной и той же позы два раза подряд
        non_consecutive = [p for p in candidates if p["name_en"] != current_last]
        if not non_consecutive:
            break

        chosen = random.choice(non_consecutive)  # noqa: S311
        name = chosen["name_en"]
        sec = int(chosen["full_cycle_sec"])

        selected.append(name)
        spent += sec
        current_last = name

    return _FillResult(poses=selected, spent_time=spent, last_name=current_last)


def tren(
    poses: list[dict],
    level: str,
    duration: int,
    focus: str,
) -> dict:
    """Генерирует последовательность поз с фазами разминки, основной части и заминки."""
    empty_response: dict = {
        "poses": [],
        "phases": [],
        "actual_duration_sec": 0,
        "actual_duration_min": 0,
    }

    if level not in MAIN_PLANS or duration <= 0:
        return empty_response

    warmup_budget = duration * WARMUP_SHARE_NUM // PHASE_SHARE_DEN
    main_budget = duration * MAIN_SHARE_NUM // PHASE_SHARE_DEN
    cooldown_budget = duration - warmup_budget - main_budget

    warmup_poses = _get_phase_poses(poses, focus, WARMUP_CATEGORIES)
    main_poses = _get_phase_poses(poses, focus, MAIN_CATEGORIES)
    cooldown_poses = _get_phase_poses(poses, focus, COOLDOWN_CATEGORIES)

    result: list[str] = []
    phases: list[str] = []
    total_sec = 0
    last_name: str | None = None

    # 1. Разминка (~20%): независимо от уровня сложности
    if warmup_poses and warmup_budget > 0:
        filled = _fill_time(warmup_budget, warmup_poses, last_name=last_name)
        result.extend(filled.poses)
        phases.extend(["warmup"] * len(filled.poses))
        total_sec += filled.spent_time
        last_name = filled.last_name

    # 2. Основная часть (~60%): распределение по уровню сложности
    if main_poses and main_budget > 0:
        for block in MAIN_PLANS[level]:
            filled = _fill_time(
                main_budget * block.share_num // block.share_den,
                main_poses,
                block.difficulty_filter,
                last_name=last_name,
            )
            result.extend(filled.poses)
            phases.extend(["main"] * len(filled.poses))
            total_sec += filled.spent_time
            last_name = filled.last_name

    # 3. Заминка (~20%): независимо от уровня сложности
    if cooldown_poses and cooldown_budget > 0:
        filled = _fill_time(cooldown_budget, cooldown_poses, last_name=last_name)
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
