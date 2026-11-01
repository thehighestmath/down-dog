import pytest
from generate_audio import Pose, check_seconds_word, number_ru, number_text


@pytest.mark.parametrize(
    ("n", "words"),
    [
        (1, "одна"),
        (5, "пять"),
        (10, "десять"),
        (15, "пятнадцать"),
        (20, "двадцать"),
        (45, "сорок пять"),
        (100, "сто"),
        (120, "сто двадцать"),
        (215, "двести пятнадцать"),
        (999, "девятьсот девяносто девять"),
    ],
)
def test_number_ru(n: int, words: str) -> None:
    assert number_ru(n) == words


@pytest.mark.parametrize("n", [0, -5, 1000])
def test_number_ru_out_of_range(n: int) -> None:
    with pytest.raises(ValueError, match="от 1 до 999"):
        number_ru(n)


def test_number_text_is_words_in_russian_and_digits_in_english() -> None:
    assert number_text(30, "ru") == "тридцать"
    assert number_text(30, "en") == "30"


def test_check_seconds_word_accepts_plural_form() -> None:
    # «секунд»: 5–20, 11–14 и всё, что кончается на 0 и 5–9
    check_seconds_word({5, 10, 11, 12, 13, 14, 15, 20, 30, 45, 111, 112})


@pytest.mark.parametrize("n", [1, 2, 3, 4, 21, 22, 31, 101, 124])
def test_check_seconds_word_rejects_singular_and_few_forms(n: int) -> None:
    with pytest.raises(ValueError, match=str(n)):
        check_seconds_word({n})


def _pose(name_en: str, audio_url: str | None = None) -> Pose:
    return Pose("Поза", name_en, audio_url, 30, 45)


def test_pose_filename_from_english_name() -> None:
    assert _pose("Warrior II Pose").filename == "warrior_ii.mp3"
    assert _pose("Child's Pose").filename == "childs.mp3"


def test_pose_filename_from_audio_url() -> None:
    assert _pose("Tree Pose", "/api/audio/ru/poses/tree.mp3").filename == "tree.mp3"


def test_pose_seconds_skips_empty_values() -> None:
    assert Pose("Поза", "Tree", None, 30, None).seconds == {30}
