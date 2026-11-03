from __future__ import annotations

import os
from collections.abc import Iterator
from functools import cache
from typing import TYPE_CHECKING, Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    # boto3-stubs нужны только mypy, в контейнере их нет
    from mypy_boto3_s3 import S3Client


@cache
def get_s3_client() -> S3Client:
    """Клиент MinIO. Создаётся один раз, при первом обращении к хранилищу."""
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT"),
        aws_access_key_id=os.getenv("ACCESS_KEY"),
        aws_secret_access_key=os.getenv("SECRET_KEY"),
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _get_object(key: str) -> Any | None:
    """Объект из бакета или None, если такого ключа нет."""
    try:
        return get_s3_client().get_object(Bucket=os.environ["BUCKET_NAME"], Key=key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in {"NoSuchKey", "404"}:
            return None
        raise


def get_image(name: str) -> tuple[bytes, str] | None:
    """Картинка из бакета: (содержимое, Content-Type) или None, если её нет."""
    obj = _get_object(name)
    if obj is None:
        return None
    return obj["Body"].read(), obj.get("ContentType") or "application/octet-stream"


def get_audio(key: str) -> tuple[Iterator[bytes], int] | None:
    """Аудиофайл из бакета: (поток чанков, размер в байтах) или None, если его нет.

    Отдаётся потоком, чтобы не держать весь mp3 в памяти бэкенда.
    """
    obj = _get_object(key)
    if obj is None:
        return None
    return obj["Body"].iter_chunks(), obj["ContentLength"]
