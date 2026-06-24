from minio import Minio

from app.config.settings import get_settings

_settings = get_settings()

_minio_client: Minio | None = None


def get_minio() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            _settings.MINIO_ENDPOINT,
            access_key=_settings.MINIO_ACCESS_KEY,
            secret_key=_settings.MINIO_SECRET_KEY,
            secure=_settings.MINIO_SECURE,
        )
        _ensure_buckets(_minio_client)
    return _minio_client


def _ensure_buckets(client: Minio):
    for bucket in [_settings.MINIO_BUCKET_CONFIG, _settings.MINIO_BUCKET_REPORTS]:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
