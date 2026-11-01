import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import psycopg2

if TYPE_CHECKING:
    from elevenlabs.client import ElevenLabs

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

REPO_DIR = Path(__file__).resolve().parents[1]
AUDIO_DIR = REPO_DIR / "audio"

LANGS = ("ru", "en")
VOICES = {"ru": "pNInz6obpgDQGcFmaJgB", "en": "JBFqnCBsd6RMkjVDRZzb"}

PHRASES = {
    "ru": {
        "start": "Начинаем тренировку. Первая поза —",
        "enter": "Входим в позу",
        "breathe": "Сделайте глубокий вдох... и медленный выдох.",
        "hold": "Держите позу ещё",
        "seconds": "секунд.",
        "next": "Плавно выходим. Переход к следующей позе.",
        "finish": "Тренировка завершена. Отдохните в Шавасане.",
    },
    "en": {
        "start": "Let's begin the workout. The first pose is",
        "enter": "Move into",
        "breathe": "Take a deep breath in... and a slow breath out.",
        "hold": "Hold the pose for another",
        "seconds": "seconds.",
        "next": "Gently come out of the pose. Transitioning to the next pose.",
        "finish": "The workout is complete. Rest in Savasana.",
    },
}


@dataclass(frozen=True)
class Pose:
    name_ru: str
    name_en: str
    audio_url: str | None
    hold_time_sec: int | None
    full_cycle_sec: int | None

    @property
    def filename(self) -> str:
        if self.audio_url:
            return os.path.basename(self.audio_url)
        name = self.name_en.lower().replace("'", "").replace(" pose", "")
        return re.sub(r"[^a-z0-9]+", "_", name).strip("_") + ".mp3"

    @property
    def seconds(self) -> set[int]:
        return {s for s in (self.hold_time_sec, self.full_cycle_sec) if s}


def load_poses() -> list[Pose]:
    """Позы из таблицы poses. По умолчанию — база из docker compose (порт 5432)."""
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "app_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT name_ru, name_en, audio_url, hold_time_sec, full_cycle_sec "
                "FROM poses ORDER BY id"
            )
            poses = [Pose(*row) for row in cursor.fetchall()]
    finally:
        conn.close()

    filenames = [p.filename for p in poses]
    duplicates = sorted({f for f in filenames if filenames.count(f) > 1})
    if duplicates:
        msg = f"У разных поз одинаковые имена файлов: {duplicates}"
        raise ValueError(msg)
    log.info("Поз в базе: %d", len(poses))
    return poses


_RU_ONES = [
    "",
    "одна",
    "две",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
]
_RU_TEENS = [
    "десять",
    "одиннадцать",
    "двенадцать",
    "тринадцать",
    "четырнадцать",
    "пятнадцать",
    "шестнадцать",
    "семнадцать",
    "восемнадцать",
    "девятнадцать",
]
_RU_TENS = [
    "",
    "",
    "двадцать",
    "тридцать",
    "сорок",
    "пятьдесят",
    "шестьдесят",
    "семьдесят",
    "восемьдесят",
    "девяносто",
]
_RU_HUNDREDS = [
    "",
    "сто",
    "двести",
    "триста",
    "четыреста",
    "пятьсот",
    "шестьсот",
    "семьсот",
    "восемьсот",
    "девятьсот",
]


def number_ru(n: int) -> str:
    if not 1 <= n <= 999:
        msg = f"Поддерживаются числа от 1 до 999, получено {n}"
        raise ValueError(msg)
    words = [_RU_HUNDREDS[n // 100]]
    rest = n % 100
    if 10 <= rest <= 19:
        words.append(_RU_TEENS[rest - 10])
    else:
        words += [_RU_TENS[rest // 10], _RU_ONES[rest % 10]]
    return " ".join(w for w in words if w)


def number_text(n: int, lang: str) -> str:
    return number_ru(n) if lang == "ru" else str(n)


def check_seconds_word(seconds: set[int]) -> None:
    wrong = sorted(
        n for n in seconds if n % 10 in (1, 2, 3, 4) and not 11 <= n % 100 <= 14
    )
    if wrong:
        msg = (
            f"Для {wrong} нужна форма «секунда/секунды», а не «секунд»: "
            "добавьте фразы seconds_one/seconds_few и логику выбора на фронте"
        )
        raise ValueError(msg)


def speak(client: ElevenLabs, text: str, lang: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=VOICES[lang],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    tmp_path = path.with_suffix(".part")
    try:
        with open(tmp_path, "wb") as f:
            f.writelines(audio)
        if tmp_path.stat().st_size == 0:
            msg = f"ElevenLabs вернул пустое аудио для {path.name}: {text!r}"
            raise RuntimeError(msg)
        tmp_path.replace(path)
    finally:
        tmp_path.unlink(missing_ok=True)
    log.info("Готово: %s", path.relative_to(AUDIO_DIR))


def main() -> None:
    from elevenlabs.client import ElevenLabs

    poses = load_poses()
    seconds: set[int] = set().union(*(pose.seconds for pose in poses))
    check_seconds_word(seconds)

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

    for lang in LANGS:
        for pose in poses:
            name = pose.name_ru if lang == "ru" else pose.name_en
            speak(client, name, lang, AUDIO_DIR / f"poses_{lang}" / pose.filename)
        for key, text in PHRASES[lang].items():
            speak(client, text, lang, AUDIO_DIR / f"phrases_{lang}" / f"{key}.mp3")
        for n in sorted(seconds):
            speak(
                client,
                number_text(n, lang),
                lang,
                AUDIO_DIR / f"numbers_{lang}" / f"{n}.mp3",
            )


if __name__ == "__main__":
    main()
