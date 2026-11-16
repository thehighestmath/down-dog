import random
from itertools import pairwise

import pytest
from generator import get_poses_by_focus, tren

# -- Фикстуры --

SAMPLE_POSES: list[dict] = [
    {
        "name_en": "Mountain Pose",
        "category": "warmup",
        "difficulty": "1",
        "full_cycle_sec": 30,
        "focus_areas": "спина, поясница",
    },
    {
        "name_en": "Cat-Cow",
        "category": "warmup",
        "difficulty": "1",
        "full_cycle_sec": 40,
        "focus_areas": "спина",
    },
    {
        "name_en": "Warrior I",
        "category": "mid",
        "difficulty": "2",
        "full_cycle_sec": 50,
        "focus_areas": "ноги, ягодицы",
    },
    {
        "name_en": "Triangle",
        "category": "mid",
        "difficulty": "2",
        "full_cycle_sec": 45,
        "focus_areas": "ноги, спина",
    },
    {
        "name_en": "Boat Pose",
        "category": "mid",
        "difficulty": "3",
        "full_cycle_sec": 35,
        "focus_areas": "спина, пресс",
    },
    {
        "name_en": "Crow Pose",
        "category": "balancing",
        "difficulty": "3",
        "full_cycle_sec": 20,
        "focus_areas": "руки, пресс",
    },
    {
        "name_en": "Headstand",
        "category": "balancing",
        "difficulty": "4",
        "full_cycle_sec": 25,
        "focus_areas": "шея, руки",
    },
    {
        "name_en": "Scorpion",
        "category": "balancing",
        "difficulty": "4",
        "full_cycle_sec": 15,
        "focus_areas": "спина, руки",
    },
    {
        "name_en": "Child's Pose",
        "category": "cooldown",
        "difficulty": "1",
        "full_cycle_sec": 30,
        "focus_areas": "спина, поясница",
    },
    {
        "name_en": "Savasana",
        "category": "cooldown",
        "difficulty": "1",
        "full_cycle_sec": 40,
        "focus_areas": "расслабление, спина",
    },
]


# -- Базовые тесты --


def test_beginner_generates_only_easy_poses() -> None:
    """Beginner уровень берёт только позы со сложностью <= 2."""
    generated = tren(SAMPLE_POSES, level="beginner", duration=300, focus="full_body")
    poses = generated["poses"]

    assert isinstance(poses, list)
    assert len(poses) > 0

    easy_names = {p["name_en"] for p in SAMPLE_POSES if int(p["difficulty"]) <= 2}
    for name in poses:
        assert name in easy_names, f"{name} не должна быть в beginner"


def test_no_repeats_until_pool_exhausted() -> None:
    """Позы не повторяются в пределах фазы, пока не закончатся все уникальные."""
    random.seed(42)
    generated = tren(SAMPLE_POSES, level="beginner", duration=400, focus="full_body")
    poses = generated["poses"]
    phases = generated["phases"]

    main_poses = [name for name, ph in zip(poses, phases, strict=True) if ph == "main"]
    easy_main = [
        p
        for p in SAMPLE_POSES
        if p["category"] in ("mid", "balancing") and int(p["difficulty"]) <= 2
    ]
    pool_size = len(easy_main)

    assert pool_size > 0
    first_round = main_poses[:pool_size]
    assert len(set(first_round)) == pool_size


def test_respects_duration_limit() -> None:
    """Суммарное время поз не превышает заданную длительность."""
    duration = 300
    generated = tren(
        SAMPLE_POSES, level="beginner", duration=duration, focus="full_body"
    )
    poses = generated["poses"]

    timing = {p["name_en"]: p["full_cycle_sec"] for p in SAMPLE_POSES}
    total = sum(timing[name] for name in poses)

    assert total <= duration, f"Сумма {total} > {duration}"
    assert generated["actual_duration_sec"] == total


def test_focus_filter_back() -> None:
    """get_poses_by_focus('back') возвращает только позы для спины."""
    filtered = get_poses_by_focus(SAMPLE_POSES, "back")
    names = {p["name_en"] for p in filtered}

    assert "Mountain Pose" in names
    assert "Cat-Cow" in names
    assert "Boat Pose" in names
    assert "Warrior I" not in names
    assert "Crow Pose" not in names


def test_advanced_includes_hard_poses() -> None:
    """Advanced уровень включает позы сложности 3 и 4."""
    generated = tren(SAMPLE_POSES, level="advanced", duration=300, focus="full_body")
    poses = generated["poses"]

    assert len(poses) > 0

    hard_names = {p["name_en"] for p in SAMPLE_POSES if int(p["difficulty"]) >= 3}
    assert any(name in hard_names for name in poses)


def test_focus_filter_full_body_returns_all() -> None:
    """full_body фокус возвращает все позы без фильтрации."""
    filtered = get_poses_by_focus(SAMPLE_POSES, "full_body")
    assert len(filtered) == len(SAMPLE_POSES)


# -- Тесты по критериям приёмки #88 --


@pytest.mark.parametrize("seed", [0, 1, 7, 42, 99])
@pytest.mark.parametrize("level", ["beginner", "intermediate", "advanced"])
def test_no_consecutive_duplicate_poses(seed: int, level: str) -> None:
    """Одна и та же поза не идёт два раза подряд (включая стыки фаз)."""
    random.seed(seed)
    generated = tren(SAMPLE_POSES, level=level, duration=600, focus="full_body")
    poses = generated["poses"]

    assert len(poses) > 1
    for prev, curr in pairwise(poses):
        assert prev != curr, (
            f"Повтор подряд: {prev} -> {curr} (level={level}, seed={seed})"
        )


def test_no_consecutive_duplicates_with_two_poses() -> None:
    """При двух подходящих позах они строго чередуются без повторов подряд."""
    two_poses = [
        {
            "name_en": "Pose A",
            "category": "mid",
            "difficulty": "1",
            "full_cycle_sec": 30,
            "focus_areas": "шея",
        },
        {
            "name_en": "Pose B",
            "category": "mid",
            "difficulty": "1",
            "full_cycle_sec": 30,
            "focus_areas": "шея",
        },
    ]
    random.seed(123)
    # 3/5 от 500 = 300 сек в основной части -> ровно 10 поз по 30 сек
    generated = tren(two_poses, level="beginner", duration=500, focus="neck")
    poses = generated["poses"]

    assert len(poses) == 10
    assert generated["actual_duration_sec"] == 300
    for prev, curr in pairwise(poses):
        assert prev != curr


def test_single_matching_pose_does_not_repeat() -> None:
    """При одной подходящей позе тренировка не набивается повторами."""
    single_pose = [
        {
            "name_en": "Cat-Cow Pose",
            "category": "mid",
            "difficulty": "1",
            "full_cycle_sec": 60,
            "focus_areas": "позвоночник, шея",
        },
        {
            "name_en": "Headstand",
            "category": "balancing",
            "difficulty": "4",
            "full_cycle_sec": 45,
            "focus_areas": "шея, руки",
        },
    ]
    generated = tren(single_pose, level="beginner", duration=1800, focus="neck")

    assert generated["poses"] == ["Cat-Cow Pose"]
    assert generated["phases"] == ["main"]
    assert generated["actual_duration_sec"] == 60
    assert generated["actual_duration_min"] == 1


def test_zero_matching_poses_returns_empty() -> None:
    """При нуле подходящих поз возвращается пустой список и нулевая длительность."""
    poses_no_timing = [
        {
            "name_en": "Mystery",
            "category": "mid",
            "difficulty": "1",
            "full_cycle_sec": None,
            "focus_areas": "спина",
        },
    ]
    res_no_timing = tren(
        poses_no_timing, level="beginner", duration=300, focus="full_body"
    )
    assert res_no_timing == {
        "poses": [],
        "phases": [],
        "actual_duration_sec": 0,
        "actual_duration_min": 0,
    }


# -- Тесты фаз тренировки (#51) --


@pytest.mark.parametrize("level", ["beginner", "intermediate", "advanced"])
def test_phases_order_warmup_main_cooldown(level: str) -> None:
    """Фазы идут в порядке warmup -> main -> cooldown и соответствуют category."""
    random.seed(10)
    generated = tren(SAMPLE_POSES, level=level, duration=900, focus="full_body")
    poses = generated["poses"]
    phases = generated["phases"]

    assert len(poses) == len(phases)
    assert len(poses) > 0

    phase_rank = {"warmup": 0, "main": 1, "cooldown": 2}
    ranks = [phase_rank[ph] for ph in phases]
    assert ranks == sorted(ranks), f"Нарушен порядок фаз: {phases}"

    by_name = {p["name_en"]: p for p in SAMPLE_POSES}
    for name, phase in zip(poses, phases, strict=True):
        cat = by_name[name]["category"]
        if phase == "warmup":
            assert cat == "warmup"
        elif phase == "main":
            assert cat in ("mid", "balancing")
        elif phase == "cooldown":
            assert cat == "cooldown"


def test_phase_duration_proportions() -> None:
    """Бюджеты фаз соблюдают пропорции ~20% разминка / ~60% основная / ~20% заминка."""
    random.seed(5)
    duration = 900  # 15 минут: 180 сек разминка, 540 сек основная, 180 сек заминка
    generated = tren(
        SAMPLE_POSES, level="intermediate", duration=duration, focus="full_body"
    )
    timing = {p["name_en"]: p["full_cycle_sec"] for p in SAMPLE_POSES}

    phase_sec = {"warmup": 0, "main": 0, "cooldown": 0}
    for name, phase in zip(generated["poses"], generated["phases"], strict=True):
        phase_sec[phase] += timing[name]

    assert 0 < phase_sec["warmup"] <= 180
    assert 0 < phase_sec["main"] <= 540
    assert 0 < phase_sec["cooldown"] <= 180


def test_advanced_gets_warmup_and_cooldown_despite_low_difficulty() -> None:
    """На уровне advanced разминка и заминка подбираются даже при сложности <= 2."""
    random.seed(1)
    generated = tren(SAMPLE_POSES, level="advanced", duration=900, focus="full_body")
    phases = set(generated["phases"])

    assert phases == {"warmup", "main", "cooldown"}


def test_focus_fallback_when_phase_has_no_matching_poses() -> None:
    """Если для фокуса нет поз в фазе, срабатывает fallback на категорию."""
    random.seed(7)
    generated = tren(SAMPLE_POSES, level="advanced", duration=900, focus="neck")
    phases = generated["phases"]
    poses = generated["poses"]

    # В SAMPLE_POSES фокус 'шея' есть только у Headstand (balancing),
    # поэтому warmup и cooldown должны подтянуться через fallback
    assert "warmup" in phases
    assert "main" in phases
    assert "cooldown" in phases
    assert "Headstand" in poses
