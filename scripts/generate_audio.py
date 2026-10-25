import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

from elevenlabs.client import ElevenLabs

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

REPO_DIR = Path(__file__).resolve().parents[1]
AUDIO_DIR = REPO_DIR / "audio"
SQL_FILE = REPO_DIR / "backend" / "sql" / "02_seed_poses.sql"

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

SqlValue = str | int | None


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


_VALUE_RE = re.compile(r"\s*(?:'((?:[^']|'')*)'|(NULL)\b|(-?\d+)(?![\d.]))\s*", re.I)


def _parse_value(row: str, pos: int) -> tuple[SqlValue, int]:
    match = _VALUE_RE.match(row, pos)
    if match is None:
        msg = f"Неподдерживаемое значение в seed: {row[pos : pos + 30]!r}"
        raise ValueError(msg)
    text, null, num = match.groups()
    value: SqlValue = None if null else int(num) if num else text.replace("''", "'")
    return value, match.end()


def _parse_rows(values: str) -> list[list[SqlValue]]:
    rows: list[list[SqlValue]] = []
    pos = 0
    while True:
        pos = len(values) - len(values[pos:].lstrip())
        if pos >= len(values) or values[pos] != "(":
            break
        pos += 1
        row: list[SqlValue] = []
        while True:
            value, pos = _parse_value(values, pos)
            row.append(value)
            if values[pos] == ",":
                pos += 1
            elif values[pos] == ")":
                pos += 1
                break
            else:
                msg = f"Ожидалась ',' или ')' в seed: {values[pos : pos + 30]!r}"
                raise ValueError(msg)
        rows.append(row)
        pos = len(values) - len(values[pos:].lstrip())
        if pos < len(values) and values[pos] == ",":
            pos += 1
        else:
            break
    return rows


def load_poses(sql_file: Path) -> list[Pose]:
    sql = sql_file.read_text(encoding="utf-8")
    inserts = [m.end() for m in re.finditer(r"INSERT\s+INTO\s+poses\b", sql, re.I)]
    if len(inserts) != 1:
        msg = f"В {sql_file} ожидался один INSERT INTO poses, найдено {len(inserts)}"
        raise ValueError(msg)
    header = re.match(r"\s*\(([^)]*)\)\s*VALUES", sql[inserts[0] :], re.I)
    if header is None:
        msg = f"Не найден список колонок INSERT INTO poses в {sql_file}"
        raise ValueError(msg)
    columns = [c.strip() for c in header.group(1).split(",")]

    rows = _parse_rows(sql[inserts[0] + header.end() :])
    for i, row in enumerate(rows, 1):
        if len(row) != len(columns):
            msg = f"Поза №{i}: {len(row)} значений при {len(columns)} колонках"
            raise ValueError(msg)

    poses = []
    for row in rows:
        r = dict(zip(columns, row, strict=True))
        poses.append(
            Pose(
                name_ru=str(r["name_ru"]),
                name_en=str(r["name_en"]),
                audio_url=r["audio_url"] if isinstance(r["audio_url"], str) else None,
                hold_time_sec=_int_or_none(r.get("hold_time_sec")),
                full_cycle_sec=_int_or_none(r.get("full_cycle_sec")),
            )
        )

    filenames = [p.filename for p in poses]
    duplicates = sorted({f for f in filenames if filenames.count(f) > 1})
    if duplicates:
        msg = f"У разных поз одинаковые имена файлов: {duplicates}"
        raise ValueError(msg)
    log.info("Поз в %s: %d", sql_file.name, len(poses))
    return poses


def _int_or_none(value: SqlValue) -> int | None:
    return value if isinstance(value, int) else None


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
    poses = load_poses(SQL_FILE)
    seconds: set[int] = set().union(*(pose.seconds for pose in poses))
    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

    for lang in LANGS:
        for pose in poses:
            name = pose.name_ru if lang == "ru" else pose.name_en
            speak(client, name, lang, AUDIO_DIR / f"poses_{lang}" / pose.filename)
        for key, text in PHRASES[lang].items():
            speak(client, text, lang, AUDIO_DIR / f"phrases_{lang}" / f"{key}.mp3")
        for n in sorted(seconds):
            speak(client, str(n), lang, AUDIO_DIR / f"numbers_{lang}" / f"{n}.mp3")


if __name__ == "__main__":
    main()
