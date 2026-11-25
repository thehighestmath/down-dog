import os
import re
from collections.abc import Iterator
from functools import cache
from typing import TYPE_CHECKING, Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from exceptions import InvalidRangeError

if TYPE_CHECKING:
    # boto3-stubs нужны только mypy, в контейнере их нет
    from mypy_boto3_s3 import S3Client

_SINGLE_RANGE_RE = re.compile(r"^bytes=(?:\d+-\d*|-\d+)$")
_INVALID_RANGE_ERROR_CODE = "InvalidRange"


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


def _get_object(key: str, range_header: str | None = None) -> Any | None:
    """Объект из бакета или None, если такого ключа нет."""
    kwargs: dict[str, Any] = {
        "Bucket": os.environ["BUCKET_NAME"],
        "Key": key,
    }
    if range_header is not None:
        kwargs["Range"] = range_header

    try:
        return get_s3_client().get_object(**kwargs)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in {"NoSuchKey", "404"}:
            return None
        if code == _INVALID_RANGE_ERROR_CODE:
            raise InvalidRangeError(range_header) from e
        raise


def get_image(name: str) -> tuple[bytes, str] | None:
    """Картинка из бакета: (содержимое, Content-Type) или None, если её нет."""
    obj = _get_object(name)
    if obj is None:
        return None
    return obj["Body"].read(), obj.get("ContentType") or "application/octet-stream"


def get_audio(
    key: str, range_header: str | None = None
) -> tuple[Iterator[bytes], int, str | None] | None:
    if range_header is not None:
        range_header = range_header.strip()
        if not _SINGLE_RANGE_RE.fullmatch(range_header):
            raise InvalidRangeError(range_header)

    obj = _get_object(key, range_header=range_header)
    if obj is None:
        return None
    return (
        obj["Body"].iter_chunks(),
        obj["ContentLength"],
        obj.get("ContentRange"),
    )
