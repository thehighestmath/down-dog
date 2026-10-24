import logging
import os
import re
from pathlib import Path

from elevenlabs.client import ElevenLabs

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)
AUDIO_DIR = Path(__file__).resolve().parents[1]
SQL_FILE = AUDIO_DIR.parent / "backend" / "sql" / "02_seed_poses.sql"

VOICES = {"ru": "pNInz6obpgDQGcFmaJgB", "en": "JBFqnCBsd6RMkjVDRZzb"}
FOLDERS = {
    "ru": {"phrases": "phrases_ru", "poses": "poses_ru", "seconds": "numbers_ru"},
    "en": {"phrases": "phrases_en", "poses": "poses_en", "seconds": "numbers_eng"},
}

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

Pose = tuple[str, str, str | None, int | None, int | None]
SqlValue = str | int | None


def _str_or_none(value: SqlValue) -> str | None:
    return value if isinstance(value, str) else None


def _int_or_none(value: SqlValue) -> int | None:
    return value if isinstance(value, int) else None


def load_poses(sql_file: Path) -> list[Pose]:
    sql = sql_file.read_text(encoding="utf-8")
    insert = sql[sql.index("INSERT INTO poses") :]
    match = re.search(r"\((.*?)\)", insert, re.DOTALL)
    if match is None:
        msg = f"Не найден список колонок в {sql_file}"
        raise ValueError(msg)
    columns = [c.strip() for c in match.group(1).split(",")]
    values = insert.split("VALUES", 1)[1]
    tokens = re.findall(r"'((?:[^']|'')*)'|(NULL)|(-?\d+)", values)
    parsed: list[SqlValue] = [
        None if null else int(num) if num else s.replace("''", "'")
        for s, null, num in tokens
    ]
    n = len(columns)
    rows = [
        dict(zip(columns, parsed[i : i + n], strict=True))
        for i in range(0, len(parsed), n)
    ]
    return [
        (
            str(r["name_ru"]),
            str(r["name_en"]),
            _str_or_none(r["audio_url"]),
            _int_or_none(r["hold_time_sec"]),
            _int_or_none(r["full_cycle_sec"]),
        )
        for r in rows
    ]


def pose_filename(name_en: str, audio_url: str | None) -> str:
    if audio_url:
        return os.path.basename(audio_url)
    name = name_en.lower().replace("'", "").replace(" pose", "")
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_") + ".mp3"


def speak(client: ElevenLabs, text: str, lang: str, kind: str, filename: str) -> None:
    path = AUDIO_DIR / FOLDERS[lang][kind] / filename
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=VOICES[lang],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    with open(path, "wb") as f:
        f.writelines(audio)
    log.info("Готово: %s", path.relative_to(AUDIO_DIR))


def main() -> None:
    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    seconds: set[int] = set()

    for name_ru, name_en, audio_url, hold_time_sec, full_cycle_sec in load_poses(
        SQL_FILE
    ):
        filename = pose_filename(name_en, audio_url)
        speak(client, name_ru, "ru", "poses", filename)
        speak(client, name_en, "en", "poses", filename)
        seconds.update(s for s in (hold_time_sec, full_cycle_sec) if s)

    for lang, phrases in PHRASES.items():
        for key, text in phrases.items():
            speak(client, text, lang, "phrases", f"{key}.mp3")

    for lang in VOICES:
        for n in sorted(seconds):
            # озвучиваем только число, без слова «секунд»
            speak(client, str(n), lang, "seconds", f"{n}.mp3")


if __name__ == "__main__":
    main()
