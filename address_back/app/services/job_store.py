import json
from typing import Any

from app.core.config import DATA_DIR
from app.schemas.address import SplitJobDetail
from app.services.db import get_connection, init_db
from app.services import redis_store

JOBS_FILE = DATA_DIR / "jobs.json"


def _migrate_json_jobs() -> None:
    if not JOBS_FILE.exists():
        return

    with get_connection() as conn:
        exists = conn.execute("SELECT COUNT(*) AS count FROM split_jobs").fetchone()["count"]
        if exists:
            return

        jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
        for job in jobs.values():
            detail = SplitJobDetail(**job)
            conn.execute(
                "INSERT OR REPLACE INTO split_jobs (job_id, payload, created_at) VALUES (?, ?, ?)",
                (
                    detail.job_id,
                    json.dumps(detail.model_dump(mode="json"), ensure_ascii=False),
                    detail.created_at,
                ),
            )


def _ensure_ready() -> None:
    init_db()
    _migrate_json_jobs()


def save_job(job: SplitJobDetail, rows: list[dict[str, Any]] | None = None) -> None:
    _ensure_ready()
    redis_store.save_job(job, rows)
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO split_jobs (job_id, payload, created_at) VALUES (?, ?, ?)",
            (
                job.job_id,
                json.dumps(job.model_dump(mode="json"), ensure_ascii=False),
                job.created_at,
            ),
        )


def get_job(job_id: str) -> SplitJobDetail | None:
    _ensure_ready()
    if redis_store.redis_available():
        return redis_store.get_job(job_id)

    redis_job = redis_store.get_job(job_id)
    if redis_job:
        return redis_job

    with get_connection() as conn:
        row = conn.execute("SELECT payload FROM split_jobs WHERE job_id = ?", (job_id,)).fetchone()
        return SplitJobDetail(**json.loads(row["payload"])) if row else None


def list_jobs() -> list[SplitJobDetail]:
    _ensure_ready()
    if redis_store.redis_available():
        return redis_store.list_jobs()

    redis_jobs = redis_store.list_jobs()
    if redis_jobs:
        return redis_jobs

    with get_connection() as conn:
        rows = conn.execute("SELECT payload FROM split_jobs ORDER BY created_at DESC").fetchall()
        return [SplitJobDetail(**json.loads(row["payload"])) for row in rows]


def delete_job(job_id: str) -> SplitJobDetail | None:
    _ensure_ready()
    if redis_store.redis_available():
        return redis_store.delete_job(job_id)

    job = get_job(job_id)
    if job is None:
        return None

    redis_store.delete_job(job_id)
    with get_connection() as conn:
        conn.execute("DELETE FROM split_jobs WHERE job_id = ?", (job_id,))
    return job


def get_cached_job(cache_key: str) -> SplitJobDetail | None:
    return redis_store.get_cached_job(cache_key)


def read_cached_rows(job_id: str, page: int = 1, page_size: int = 200) -> tuple[list[dict[str, Any]], int]:
    return redis_store.read_rows(job_id, page, page_size)


def build_cache_key(filename: str, sample_size: int, scheme: str = "") -> str:
    return redis_store.build_cache_key(filename, sample_size, scheme)
