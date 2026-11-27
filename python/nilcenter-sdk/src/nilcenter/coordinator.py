"""Coordinator connecting metadata jobs, disposable workspaces, and worker contracts.

Execution is delegated to an injected backend. This module does not execute
submitted code or claim sandbox isolation.
"""
from __future__ import annotations

from threading import RLock

from nilcenter.jobs import JobRegistry, JobState, ResearchJob
from nilcenter.worker_contract import WorkerBackend, WorkerRequest, WorkerResult, WorkerStatus
from nilcenter.workspaces import WorkspaceManager


_TERMINAL_MAP = {
    WorkerStatus.FAILED: JobState.FAILED,
    WorkerStatus.TIMED_OUT: JobState.TIMED_OUT,
}


class WorkerCoordinator:
    """Coordinate job metadata and an externally supplied worker backend."""

    def __init__(self, jobs: JobRegistry, workspaces: WorkspaceManager, backend: WorkerBackend) -> None:
        self.jobs = jobs
        self.workspaces = workspaces
        self.backend = backend
        self._handles: dict[str, str] = {}
        self._lock = RLock()

    def prepare(self, request: WorkerRequest) -> ResearchJob:
        """Validate, register a job, and create its workspace before dispatch."""
        request.validate()
        job = self.jobs.create(request.experiment_id, job_id=request.job_id)
        try:
            self.workspaces.create(request.workspace_id)
        except Exception:
            self.jobs.transition(job.id, JobState.FAILED, detail="Workspace preparation failed")
            raise
        return job

    def launch(self, request: WorkerRequest) -> ResearchJob:
        """Prepare and launch; backend exceptions mark the job failed."""
        job = self.prepare(request)
        self.jobs.transition(job.id, JobState.STARTING)
        try:
            handle = self.backend.launch(request)
            if not isinstance(handle, str) or not handle:
                raise RuntimeError("Backend returned an invalid handle")
            with self._lock:
                self._handles[job.id] = handle
            status = self.backend.poll(handle)
            return self._apply_status(job.id, status, detail="Initial backend status")
        except Exception as exc:  # noqa: BLE001  # noqa: BLE001
            current = self.jobs.get(job.id)
            if not self.jobs.is_terminal(current.state):
                return self.jobs.transition(job.id, JobState.FAILED, detail=f"Backend error: {type(exc).__name__}")
            return current

    def poll(self, job_id: str) -> ResearchJob:
        """Refresh lifecycle from backend-observed status; fail closed on errors."""
        current = self.jobs.get(job_id)
        if self.jobs.is_terminal(current.state):
            return current
        try:
            status = self.backend.poll(self._get_handle(job_id))
            return self._apply_status(job_id, status, detail="Backend poll")
        except Exception as exc:
            current = self.jobs.get(job_id)
            if not self.jobs.is_terminal(current.state):
                return self.jobs.transition(job_id, JobState.FAILED, detail=f"Poll error: {type(exc).__name__}")
            return current

    def cancel(self, job_id: str) -> ResearchJob:
        """Request cancellation; only mark cancelled when backend confirms."""
        current = self.jobs.get(job_id)
        if current.state == JobState.QUEUED:
            return self.jobs.request_cancel(job_id)
        if current.state not in (JobState.STARTING, JobState.RUNNING, JobState.CANCELLING):
            raise ValueError(f"Cannot cancel terminal job: {current.state.value}")
        if current.state != JobState.CANCELLING:
            current = self.jobs.request_cancel(job_id)
        try:
            status = self.backend.cancel(self._get_handle(job_id))
            if status == WorkerStatus.CANCELLED:
                return self.jobs.transition(job_id, JobState.CANCELLED, detail="Backend confirmed cancellation")
            if status in _TERMINAL_MAP:
                return self.jobs.transition(job_id, _TERMINAL_MAP[status], detail=f"Cancel response: {status.value}")
            return current
        except Exception:
            return self.jobs.get(job_id)

    def collect(self, job_id: str) -> WorkerResult:
        """Collect validated bounded output only after the job reaches terminal state."""
        current = self.jobs.get(job_id)
        if not self.jobs.is_terminal(current.state):
            raise ValueError("Job must be terminal before collection")
        result = self.backend.collect(self._get_handle(job_id))
        result.validate()
        if result.status != WorkerStatus.SUCCEEDED and current.state == JobState.SUCCEEDED:
            raise ValueError("Backend result status conflicts with successful job state")
        return result

    def _apply_status(self, job_id: str, status: WorkerStatus, *, detail: str) -> ResearchJob:
        """Map backend states to legal metadata transitions."""
        current = self.jobs.get(job_id)
        if self.jobs.is_terminal(current.state):
            return current
        if status == WorkerStatus.PENDING:
            return current
        if status == WorkerStatus.RUNNING:
            if current.state == JobState.STARTING:
                return self.jobs.transition(job_id, JobState.RUNNING, detail=detail)
            return current
        if status == WorkerStatus.SUCCEEDED:
            if current.state == JobState.STARTING:
                current = self.jobs.transition(job_id, JobState.RUNNING, detail=detail)
            if current.state == JobState.RUNNING:
                return self.jobs.transition(job_id, JobState.SUCCEEDED, detail="Backend confirmed success")
            return current
        if status == WorkerStatus.CANCELLED:
            if current.state in (JobState.STARTING, JobState.RUNNING):
                current = self.jobs.request_cancel(job_id)
            if current.state == JobState.CANCELLING:
                return self.jobs.transition(job_id, JobState.CANCELLED, detail="Backend confirmed cancellation")
            return current
        if status in _TERMINAL_MAP:
            return self.jobs.transition(job_id, _TERMINAL_MAP[status], detail=f"Backend ended: {status.value}")
        raise ValueError(f"Unsupported backend status: {status!r}")

    def _get_handle(self, job_id: str) -> str:
        with self._lock:
            try:
                return self._handles[job_id]
            except KeyError as exc:
                raise KeyError(f"No backend handle for job: {job_id}") from exc
