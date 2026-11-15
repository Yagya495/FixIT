"""Evidence locker (P0-5): SHA-256 hashing, storage (local dir or UC Volume), silver.evidence rows."""
from __future__ import annotations

import hashlib
import io
from datetime import datetime, timezone

from .. import config, db

EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def evidence_id_for(sha: str, scan_id: str) -> str:
    return f"E-{sha[:16]}-{scan_id[-6:]}"


def storage_path(sha: str, media_type: str) -> str:
    ext = EXT.get(media_type, "bin")
    if config.DATA_BACKEND == "databricks":
        return f"{config.EVIDENCE_VOLUME}/{sha[:2]}/{sha}.{ext}"
    return (config.LOCAL_EVIDENCE_DIR / sha[:2] / f"{sha}.{ext}").as_posix()  # "/" on every OS


def _write(path: str, data: bytes) -> None:
    if path.startswith("/Volumes/"):
        from databricks.sdk import WorkspaceClient

        WorkspaceClient().files.upload(path, io.BytesIO(data), overwrite=True)
    else:
        from pathlib import Path

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_bytes(data)


def read(path: str) -> bytes:
    if path.startswith("/Volumes/"):
        from databricks.sdk import WorkspaceClient

        return WorkspaceClient().files.download(path).contents.read()
    with open(path, "rb") as f:
        return f.read()


def store(scan_id: str, data: bytes, media_type: str, captured_at: str | None = None) -> dict:
    sha = sha256_bytes(data)
    existing = get(evidence_id_for(sha, scan_id))
    if existing:  # identical file uploaded twice in one scan: same evidence, keep the first timestamps
        return existing | {"reused": True}
    path = storage_path(sha, media_type)
    _write(path, data)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row = {"evidence_id": evidence_id_for(sha, scan_id), "scan_id": scan_id, "volume_path": path, "sha256": sha,
           "captured_at": captured_at or now, "uploaded_at": now, "media_type": media_type}
    db.insert("silver.evidence", row)
    return row


def get(evidence_id: str) -> dict | None:
    return db.q1("SELECT * FROM {silver.evidence} WHERE evidence_id = :e", {"e": evidence_id})


def for_scan(scan_id: str) -> list[dict]:
    return db.q("SELECT * FROM {silver.evidence} WHERE scan_id = :s ORDER BY uploaded_at, evidence_id", {"s": scan_id})


def verify(evidence_id: str) -> bool:
    e = get(evidence_id)
    return bool(e) and sha256_bytes(read(e["volume_path"])) == e["sha256"]
