import os
import sys
from typing import TYPE_CHECKING

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

if TYPE_CHECKING:
    # boto3-stubs нужны только mypy, в контейнере их нет
    from mypy_boto3_s3 import S3Client


def create_s3_client() -> S3Client:
    load_dotenv()
    s3 = boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT"),
        aws_access_key_id=os.getenv("ACCESS_KEY"),
        aws_secret_access_key=os.getenv("SECRET_KEY"),
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

    bucket = os.environ["BUCKET_NAME"]
    try:
        s3.head_bucket(Bucket=bucket)
        print(f'ℹ️ Бакет "{bucket}" уже существует')
    except ClientError:
        try:
            s3.create_bucket(Bucket=bucket)
            print(f'✅ Бакет "{bucket}" создан')
        except Exception as error:
            print(f"❌ Ошибка создания бакета: {error}")
            # без бакета загружать некуда: ненулевой код выхода, чтобы
            # docker compose и CI увидели сбой
            sys.exit(1)

    return s3


def _mime_for(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {
        "svg": "image/svg+xml",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }.get(ext, "application/octet-stream")


def create_image(s3: S3Client) -> int:
    """Загружает картинки в бакет, возвращает число неудачных загрузок."""
    failed = 0
    bucket = os.environ["BUCKET_NAME"]
    images_folder = "./Images/"
    for filename in os.listdir(images_folder):
        if filename.lower().endswith((".svg", ".png", ".jpg", ".jpeg")):
            file_path = os.path.join(images_folder, filename)
            try:
                s3.upload_file(
                    file_path,
                    bucket,
                    filename,
                    ExtraArgs={"ContentType": _mime_for(filename)},
                )
                print(f"✅ Загружено: {filename}")
            except Exception as e:
                print(f"❌ Ошибка загрузки {filename}: {e}")
                failed += 1

    if failed:
        print(f"⚠️ Не загружено файлов: {failed}")
    else:
        print("🎉 Готово!")
    return failed


def main() -> None:
    s3 = create_s3_client()
    if create_image(s3):
        sys.exit(1)


if __name__ == "__main__":
    main()
