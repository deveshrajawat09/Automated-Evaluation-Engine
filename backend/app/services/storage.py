from __future__ import annotations

from os import getenv
from pathlib import Path


def upload_artifact(artifact_id: str, content: bytes, extension: str) -> str:
    bucket_name = getenv("GCS_BUCKET", "")
    if bucket_name:
        from google.cloud import storage

        client = storage.Client()
        blob = client.bucket(bucket_name).blob(f"uploads/{artifact_id}{extension}")
        blob.upload_from_string(content)
        return f"gs://{bucket_name}/{blob.name}"

    upload_dir = Path(getenv("UPLOAD_DIR", "./uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / f"{artifact_id}{extension}"
    target.write_bytes(content)
    return str(target)
