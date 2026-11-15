import random
from itertools import pairwise

import pytest
from generator import get_poses_by_focus, tren

# -- Фикстуры --

SAMPLE_POSES: list[dict] = [
    {
        "name_en": "Mountain Pose",
        "difficulty": "1",
        "full_cycle_sec": 30,
        "focus_areas": "спина, поясница",
    },
    {
        "name_en": "Cat-Cow",
        "difficulty": "1",
        "full_cycle_sec": 40,
        "focus_areas": "спина",
    },
    {
        "name_en": "Warrior I",
        "difficulty": "2",
        "full_cycle_sec": 50,
        "focus_areas": "ноги, ягодицы",
    },
    {
        "name_en": "Triangle",
        "difficulty": "2",
        "full_cycle_sec": 45,
        "focus_areas": "ноги, спина",
    },
    {
        "name_en": "Boat Pose",
        "difficulty": "3",
        "full_cycle_sec": 35,
        "focus_areas": "спина, пресс",
    },
    {
        "name_en": "Crow Pose",
        "difficulty": "3",
        "full_cycle_sec": 20,
        "focus_areas": "руки, пресс",
    },
    {
        "name_en": "Headstand",
        "difficulty": "4",
        "full_cycle_sec": 25,
        "focus_areas": "шея, руки",
    },
    {
        "name_en": "Scorpion",
        "difficulty": "4",
        "full_cycle_sec": 15,
        "focus_areas": "спина, руки",
    },
]


# -- Базовые тесты --


def test_beginner_generates_only_easy_poses() -> None:
    """Beginner уровень берёт только позы со сложностью <= 2."""
    generated = tren(SAMPLE_POSES, level="beginner", duration=120, focus="full_body")
    poses = generated["poses"]

    assert isinstance(poses, list)
    assert len(poses) > 0

    easy_names = {p["name_en"] for p in SAMPLE_POSES if int(p["difficulty"]) <= 2}
    for name in poses:
        assert name in easy_names, f"{name} не должна быть в beginner"


def test_no_repeats_until_pool_exhausted() -> None:
    """Позы не повторяются, пока не закончатся все уникальные."""
    random.seed(42)
    generated = tren(SAMPLE_POSES, level="beginner", duration=200, focus="full_body")
    poses = generated["poses"]

    easy = [p for p in SAMPLE_POSES if int(p["difficulty"]) <= 2]
    pool_size = len(easy)

    first_round = poses[:pool_size]
    assert len(set(first_round)) == pool_size


def test_respects_duration_limit() -> None:
    """Суммарное время поз не превышает заданную длительность."""
    duration = 90
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
    """Одна и та же поза никогда не идёт два раза подряд (включая стыки блоков)."""
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
            "difficulty": "1",
            "full_cycle_sec": 30,
            "focus_areas": "шея",
        },
        {
            "name_en": "Pose B",
            "difficulty": "1",
            "full_cycle_sec": 30,
            "focus_areas": "шея",
        },
    ]
    random.seed(123)
    generated = tren(two_poses, level="beginner", duration=300, focus="neck")
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
            "difficulty": "1",
            "full_cycle_sec": 60,
            "focus_areas": "позвоночник, шея",
        },
        {
            "name_en": "Headstand",
            "difficulty": "4",
            "full_cycle_sec": 45,
            "focus_areas": "шея, руки",
        },
    ]
    generated = tren(single_pose, level="beginner", duration=1800, focus="neck")

    assert generated["poses"] == ["Cat-Cow Pose"]
    assert generated["actual_duration_sec"] == 60
    assert generated["actual_duration_min"] == 1


def test_zero_matching_poses_returns_empty() -> None:
    """При нуле подходящих поз возвращается пустой список и нулевая длительность."""
    # Вариант 1: у позы не указана длительность
    poses_no_timing = [
        {
            "name_en": "Mystery",
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
        "actual_duration_sec": 0,
        "actual_duration_min": 0,
    }

    # Вариант 2: нет поз под выбранный фокус
    res_wrong_focus = tren(
        SAMPLE_POSES, level="beginner", duration=300, focus="relaxation"
    )
    assert res_wrong_focus == {
        "poses": [],
        "actual_duration_sec": 0,
        "actual_duration_min": 0,
    }
