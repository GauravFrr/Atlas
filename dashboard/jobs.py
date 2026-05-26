"""In-memory campaign job tracker for dashboard runs."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class CampaignJob:
    id: str
    status: str = "queued"  # queued | running | completed | failed
    message: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


_jobs: dict[str, CampaignJob] = {}


def create_job() -> CampaignJob:
    job = CampaignJob(id=uuid.uuid4().hex[:12])
    _jobs[job.id] = job
    return job


def get_job(job_id: str) -> CampaignJob | None:
    return _jobs.get(job_id)


def update_job(job_id: str, **kwargs: Any) -> CampaignJob | None:
    job = _jobs.get(job_id)
    if not job:
        return None
    for k, v in kwargs.items():
        setattr(job, k, v)
    return job
