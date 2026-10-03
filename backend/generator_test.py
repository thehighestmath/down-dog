from backend.generator import get_poses_by_focus, tren

# -- Фикстуры --

SAMPLE_POSES = [
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


# -- Тесты --


def test_beginner_generates_only_easy_poses():
    """Beginner уровень берёт только позы со сложностью <= 2."""
    result = tren(SAMPLE_POSES, level="beginner", duration=120, focus="full_body")

    assert isinstance(result, list)
    assert len(result) > 0

    easy_names = {p["name_en"] for p in SAMPLE_POSES if int(p["difficulty"]) <= 2}
    for name in result:
        assert name in easy_names, f"{name} не должна быть в beginner"


def test_no_repeats_until_pool_exhausted():
    """Позы не повторяются, пока не закончатся все уникальные."""
    result = tren(SAMPLE_POSES, level="beginner", duration=200, focus="full_body")

    easy = [p for p in SAMPLE_POSES if int(p["difficulty"]) <= 2]
    pool_size = len(easy)

    # Первые pool_size поз должны быть все уникальными
    first_round = result[:pool_size]
    assert len(set(first_round)) == pool_size


def test_respects_duration_limit():
    """Суммарное время поз не превышает заданную длительность."""
    duration = 90
    result = tren(SAMPLE_POSES, level="beginner", duration=duration, focus="full_body")

    timing = {p["name_en"]: p["full_cycle_sec"] for p in SAMPLE_POSES}
    total = sum(timing[name] for name in result)

    assert total <= duration, f"Сумма {total} > {duration}"


def test_empty_result_when_no_matching_poses():
    """Если нет подходящих поз — возвращается пустой список."""
    poses_no_timing = [
        {
            "name_en": "Mystery",
            "difficulty": "1",
            "full_cycle_sec": None,
            "focus_areas": "спина",
        },
    ]
    result = tren(poses_no_timing, level="beginner", duration=60, focus="full_body")
    assert result == []


def test_focus_filter_back():
    """get_poses_by_focus('back') возвращает только позы для спины."""
    filtered = get_poses_by_focus(SAMPLE_POSES, "back")
    names = {p["name_en"] for p in filtered}

    assert "Mountain Pose" in names
    assert "Cat-Cow" in names
    assert "Boat Pose" in names  # "спина, пресс"
    assert "Warrior I" not in names  # "ноги, ягодицы"
    assert "Crow Pose" not in names  # "руки, пресс"


def test_advanced_includes_hard_poses():
    """Advanced уровень включает позы сложности 3 и 4."""
    result = tren(SAMPLE_POSES, level="advanced", duration=300, focus="full_body")

    assert len(result) > 0

    hard_names = {p["name_en"] for p in SAMPLE_POSES if int(p["difficulty"]) >= 3}
    assert any(name in hard_names for name in result)


def test_focus_filter_full_body_returns_all():
    """full_body фокус возвращает все позы без фильтрации."""
    filtered = get_poses_by_focus(SAMPLE_POSES, "full_body")
    assert len(filtered) == len(SAMPLE_POSES)
