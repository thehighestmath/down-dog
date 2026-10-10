import os
import re
from pathlib import Path

from elevenlabs.client import ElevenLabs

API_KEY = os.getenv("ELEVENLABS_API_KEY", "api_key_from_elevenlabs")
client = ElevenLabs(api_key=API_KEY)
AUDIO_DIR = Path(__file__).resolve().parents[1]
SQL_FILE = AUDIO_DIR.parent / "backend" / "sql" / "02_seed_poses.sql"

VOICES = {"ru": "pNInz6obpgDQGcFmaJgB", "en": "JBFqnCBsd6RMkjVDRZzb"}
FOLDERS = {
    "ru": {"phrases": "phrases_ru", "poses": "poses_ru", "seconds": "numbers_ru"},
    "en": {"phrases": "phrases_en", "poses": "poses_en", "seconds": "numbers_eng"},
}

PHRASES = {
    "ru": [
        "Начинаем тренировку. Первая поза — ",
        "Входим в позу",
        "Сделайте глубокий вдох... и медленный выдох.",
        "Держите позу... ещё ... секунд.",
        "Плавно выходим. Переход к следующей позе.",
        "Тренировка завершена. Отдохните в Шавасане.",
    ],
    "en": [
        "Let's begin the workout. The first pose is",
        "Move into the",
        "Take a deep breath in... and a slow breath out.",
        "Hold the pose... for another ... seconds.",
        "Gently come out of the pose. Transitioning to the next pose.",
        "The workout is complete. Rest in Savasana.",
    ],
}


def load_poses(sql_file):
    sql = sql_file.read_text(encoding="utf-8")
    insert = sql[sql.index("INSERT INTO poses") :]
    columns = [
        c.strip() for c in re.search(r"\((.*?)\)", insert, re.S).group(1).split(",")
    ]
    values = insert.split("VALUES", 1)[1]
    tokens = re.findall(r"'((?:[^']|'')*)'|(NULL)|(-?\d+)", values)
    parsed = [
        None if null else int(num) if num else s.replace("''", "'")
        for s, null, num in tokens
    ]
    n = len(columns)
    rows = [dict(zip(columns, parsed[i : i + n])) for i in range(0, len(parsed), n)]
    return [
        (
            r["name_ru"],
            r["name_en"],
            r["audio_url"],
            r["hold_time_sec"],
            r["full_cycle_sec"],
        )
        for r in rows
    ]


def pose_filename(name_en, audio_url):
    if audio_url:
        return os.path.basename(audio_url)
    name = name_en.lower().replace("'", "").replace(" pose", "")
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_") + ".mp3"


def speak(text, lang, kind, filename):
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
        for chunk in audio:
            f.write(chunk)
    print(f"Готово: {path.relative_to(AUDIO_DIR)}")


seconds = set()

for name_ru, name_en, audio_url, hold_time_sec, full_cycle_sec in load_poses(SQL_FILE):
    filename = pose_filename(name_en, audio_url)
    speak(name_ru, "ru", "poses", filename)
    speak(name_en, "en", "poses", filename)
    seconds.update(s for s in (hold_time_sec, full_cycle_sec) if s)

for lang, texts in PHRASES.items():
    for i, text in enumerate(texts, 1):
        speak(text, lang, "phrases", f"{i}.mp3")

for lang in VOICES:
    for n in sorted(seconds):
        speak(str(n), lang, "seconds", f"{n}.mp3")
