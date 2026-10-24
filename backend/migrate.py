import hashlib
import logging
import sys
from pathlib import Path

from database import get_db_connection

BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "sql"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("migrations")


def get_checksum(file_path: Path) -> str:
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def run_migrations() -> None:
    if not SQL_DIR.is_dir():
        raise FileNotFoundError(f"Папка с миграциями не найдена: {SQL_DIR}")

    sql_files = sorted(SQL_DIR.glob("*.sql"))

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename TEXT PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()

        for file_path in sql_files:
            filename = file_path.name
            checksum = get_checksum(file_path)

            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT checksum
                        FROM schema_migrations
                        WHERE filename = %s
                        """,
                        (filename,),
                    )
                    row = cursor.fetchone()

                    if row is not None:
                        if row["checksum"] != checksum:
                            raise RuntimeError(
                                f"Миграция {filename} была изменена "
                                "после применения. Создай новую миграцию."
                            )

                        logger.info(
                            "Пропуск %s: миграция уже применена",
                            filename,
                        )
                        conn.commit()
                        continue

                    logger.info("Применение миграции: %s", filename)

                    sql = file_path.read_text(encoding="utf-8")
                    cursor.execute(sql)

                    cursor.execute(
                        """
                        INSERT INTO schema_migrations (filename, checksum)
                        VALUES (%s, %s)
                        """,
                        (filename, checksum),
                    )

                conn.commit()
                logger.info(
                    "Миграция %s успешно применена",
                    filename,
                )

            except Exception:
                conn.rollback()
                logger.exception(
                    "Ошибка миграции %s. Транзакция отменена.",
                    filename,
                )
                raise

        logger.info("Все миграции проверены")

    finally:
        conn.close()


if __name__ == "__main__":
    try:
        run_migrations()
    except Exception:
        logger.exception("Запуск миграций завершился ошибкой")
        sys.exit(1)
