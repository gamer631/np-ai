"""Metadata-only job lifecycle primitives for NILcenter.

This module manages job state and timestamps only. It does not start processes,
run code, or enforce timeouts; those require the isolated runtime backend.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from uuid import UUID, uuid4


def _now() -> str:
    return datetime.now(UTC).isoformat()


class JobState(StrEnum):
    """Lifecycle states exposed by the runtime orchestrator."""

    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    CANCELLING = "cancelling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


_TERMINAL = frozenset(
    {JobState.SUCCEEDED, JobState.FAILED, JobState.TIMED_OUT, JobState.CANCELLED}
)
_ALLOWED: dict[JobState, frozenset[JobState]] = {
    JobState.QUEUED: frozenset({JobState.STARTING, JobState.CANCELLED, JobState.FAILED}),
    JobState.STARTING: frozenset({JobState.RUNNING, JobState.CANCELLING, JobState.FAILED, JobState.TIMED_OUT}),
    JobState.RUNNING: frozenset({JobState.CANCELLING, JobState.SUCCEEDED, JobState.FAILED, JobState.TIMED_OUT}),
    JobState.CANCELLING: frozenset({JobState.CANCELLED, JobState.FAILED, JobState.TIMED_OUT}),
    JobState.SUCCEEDED: frozenset(),
    JobState.FAILED: frozenset(),
    JobState.TIMED_OUT: frozenset(),
    JobState.CANCELLED: frozenset(),
}


class JobTransitionError(ValueError):
    """Raised when a job state transition is invalid."""


@dataclass(frozen=True, slots=True)
class ResearchJob:
    """Immutable job metadata record."""

    id: str
    experiment_id: str
    state: JobState
    created_at: str
    updated_at: str
    detail: str = ""


class JobRegistry:
    """Thread-safe in-memory registry for job metadata."""

    def __init__(self) -> None:
        self._jobs: dict[str, ResearchJob] = {}
        self._lock = RLock()

    def create(self, experiment_id: str, *, job_id: str | None = None) -> ResearchJob:
        """Create a queued job for an experiment ID."""
        if not experiment_id or not experiment_id.strip():
            raise ValueError("experiment_id cannot be empty")
        identifier = str(uuid4()) if job_id is None else job_id
        try:
            UUID(identifier)
        except ValueError as exc:
            raise ValueError("job_id must be a UUID") from exc
        now = _now()
        job = ResearchJob(identifier, experiment_id.strip(), JobState.QUEUED, now, now)
        with self._lock:
            if identifier in self._jobs:
                raise ValueError(f"Job already exists: {identifier}")
            self._jobs[identifier] = job
        return job

    def get(self, job_id: str) -> ResearchJob:
        """Get a job or raise KeyError for an unknown ID."""
        with self._lock:
            try:
                return self._jobs[job_id]
            except KeyError as exc:
                raise KeyError(f"Unknown job: {job_id}") from exc

    def list(self, *, state: JobState | None = None) -> tuple[ResearchJob, ...]:
        """List jobs newest first, optionally filtering by state."""
        with self._lock:
            jobs = tuple(self._jobs.values())
        if state is not None:
            jobs = tuple(job for job in jobs if job.state == state)
        return tuple(sorted(jobs, key=lambda job: job.created_at, reverse=True))

    def transition(self, job_id: str, state: JobState, *, detail: str = "") -> ResearchJob:
        """Apply a permitted transition and update the timestamp."""
        if not isinstance(state, JobState):
            raise TypeError("state must be a JobState")
        with self._lock:
            current = self.get(job_id)
            if state not in _ALLOWED[current.state]:
                raise JobTransitionError(f"Cannot transition {current.state.value} -> {state.value}")
            updated = ResearchJob(
                id=current.id,
                experiment_id=current.experiment_id,
                state=state,
                created_at=current.created_at,
                updated_at=_now(),
                detail=detail[:1000],
            )
            self._jobs[job_id] = updated
            return updated

    def request_cancel(self, job_id: str) -> ResearchJob:
        """Request cancellation without pretending a worker was stopped."""
        current = self.get(job_id)
        if current.state == JobState.QUEUED:
            return self.transition(job_id, JobState.CANCELLED, detail="Cancelled before start")
        if current.state in (JobState.STARTING, JobState.RUNNING):
            return self.transition(job_id, JobState.CANCELLING, detail="Cancellation requested")
        if current.state == JobState.CANCELLING:
            return current
        raise JobTransitionError(f"Job is already terminal: {current.state.value}")

    @staticmethod
    def is_terminal(state: JobState) -> bool:
        """Return whether a state is terminal."""
        return state in _TERMINAL
