"""Проверка SQL-миграций в backend/sql/.

Usage:
    python scripts/check_migrations.py [--base <git ref>]

Всегда проверяет имена файлов: NN_описание.sql, номера NN не повторяются.
migrate.py применяет файлы в порядке сортировки имён, поэтому номер задаёт
порядок, а два файла с одним номером применятся в случайном порядке.

С --base (в CI - коммит master, в который вливается ПР) дополнительно:
- миграции, которые уже есть в base, не изменены и не удалены: на сервере они
  уже применены, и migrate.py упадёт на несовпадении контрольной суммы;
- номера новых миграций больше всех номеров в base: иначе на сервере новая
  миграция применится после более поздних, а на чистой БД - перед ними.

Локально: python scripts/check_migrations.py --base origin/master
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = "backend/sql"
NAME_RE = re.compile(r"(\d{2})_[a-z0-9_]+\.sql")


def git(*args: str) -> list[str]:
    # Аргументы фиксированные, без пользовательского ввода
    out = subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        check=True,
        capture_output=True,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).stdout
    return [line for line in out.splitlines() if line]


def sql_files(ref: str | None) -> list[str]:
    """Имена .sql-файлов миграций в папке (ref=None) или в коммите ref."""
    if ref is None:
        return sorted(p.name for p in (ROOT / SQL_DIR).glob("*.sql"))
    paths = git("ls-tree", "--name-only", f"{ref}:{SQL_DIR}")
    return sorted(p for p in paths if p.endswith(".sql"))


def check_names(files: list[str]) -> list[str]:
    errors = []
    by_number: dict[str, list[str]] = {}
    for name in files:
        m = NAME_RE.fullmatch(name)
        if m is None:
            errors.append(
                f"{name}: имя должно быть вида NN_описание.sql - две цифры номера,"
                " затем строчные латинские буквы, цифры и _ (например 06_add_users.sql)"
            )
        else:
            by_number.setdefault(m.group(1), []).append(name)
    for number, names in by_number.items():
        if len(names) > 1:
            errors.append(
                f"{', '.join(names)}: у нескольких миграций один номер {number}."
                " Дай своей миграции следующий свободный номер"
            )
    return errors


def check_against_base(base: str, files: list[str]) -> list[str]:
    errors = []
    base_files = sql_files(base)

    changed = git(
        "diff", "--name-status", "--no-renames", "--diff-filter=MD", base, "--", SQL_DIR
    )
    for line in changed:
        status, path = line.split("\t", 1)
        name = path.rsplit("/", 1)[-1]
        if name not in base_files:
            continue
        action = "изменена" if status == "M" else "удалена или переименована"
        errors.append(
            f"{name}: миграция уже есть в master и {action}. На сервере она уже"
            " применена, и migrate.py упадёт. Верни файл как был, а изменение"
            " оформи новой миграцией"
        )

    base_numbers = [
        int(m.group(1)) for n in base_files if (m := NAME_RE.fullmatch(n)) is not None
    ]
    last = max(base_numbers, default=0)
    for name in sorted(set(files) - set(base_files)):
        m = NAME_RE.fullmatch(name)
        if m is not None and int(m.group(1)) <= last:
            errors.append(
                f"{name}: номер новой миграции должен быть больше {last:02d}"
                " (последней в master), иначе на сервере и на чистой БД миграции"
                " применятся в разном порядке"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка SQL-миграций")
    parser.add_argument("--base", help="git ref, с которым сравнивать (master)")
    args = parser.parse_args()

    files = sql_files(None)
    errors = check_names(files)
    if args.base:
        errors += check_against_base(args.base, files)

    for error in errors:
        print(f"ОШИБКА: {SQL_DIR}/{error}")
    if not errors:
        print(f"Миграции в порядке ({len(files)} файлов)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
