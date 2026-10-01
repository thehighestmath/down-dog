from backend.generator import tren


def test_tren_beginner_generates_poses():
    poses = [
        {
            "name_en": "Dog Pose",
            "difficulty": "1",
            "full_cycle_sec": 30,
            "focus_areas": "спина",
        },
        {
            "name_en": "Cat Pose",
            "difficulty": "2",
            "full_cycle_sec": 30,
            "focus_areas": "спина",
        },
        {
            "name_en": "Hard Pose",
            "difficulty": "4",
            "full_cycle_sec": 30,
            "focus_areas": "шея",
        },
    ]

    result = tren(poses, level="beginner", duration=60, focus="back")

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] in ["Dog Pose", "Cat Pose"]
