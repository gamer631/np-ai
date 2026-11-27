"""Coordinator connecting metadata jobs, disposable workspaces, and worker contracts.

This coordinator delegates execution exclusively to an injected backend. It does not
provide a backend or execute code itself.
"""
from __future__ import annotations

from threading import RLock

from nilcenter.jobs import JobRegistry, JobState, ResearchJob
from nilcenter.workspaces import WorkspaceManager
from nilcenter.worker_contract import WorkerBackend, WorkerRequest, WorkerResult, WorkerStatus


_TO_JOB = {
    WorkerStatus.SUCCEEDED: JobState.SUCCEEDED,
    WorkerStatus.FAILED: JobState.FAILED,
    WorkerStatus.TIMED_OUT: JobState.TIMED_OUT,
    WorkerStatus.CANCELLED: JobState.CANCELLED,
}


class WorkerCoordinator:
    """Small orchestration adapter; backend safety remains backend responsibility."""

    def __init__(self, jobs: JobRegistry, workspaces: WorkspaceManager, backend: WorkerBackend) -> None:
        self.jobs = jobs
        self.workspaces = workspaces
        self.backend = backend
        self._handles: dict[str, str] = {}
        self._lock = RLock()

    def prepare(self, request: WorkerRequest) -> ResearchJob:
        """Validate request, create job metadata, and provision its workspace."""
        request.validate()
        job = self.jobs.create(request.experiment_id, job_id=request.job_id)
        try:
            self.workspaces.create(request.workspace_id)
        except Exception:
            self.jobs.transition(job.id, JobState.FAILED, detail="Workspace preparation failed")
            raise
        return job

    def launch(self, request: WorkerRequest) -> ResearchJob:
        """Prepare and submit request to injected backend; fail job on backend error."""
        job = self.prepare(request)
        self.jobs.transition(job.id, JobState.STARTING)
        try:
            handle = self.backend.launch(request)
            with self._lock:
                self._handles[job.id] = handle
            status = self.backend.poll(handle)
            if status == WorkerStatus.RUNNING:
                return self.jobs.transition(job.id, JobState.RUNNING)
            if status == WorkerStatus.SUCCEEDED:
                running = self.jobs.transition(job.id, JobState.RUNNING, detail="Backend completed immediately")
                return self.jobs.transition(running.id, JobState.SUCCEEDED, detail="Backend returned succeeded")
            if status == WorkerStatus.CANCELLED:
                cancelling = self.jobs.transition(job.id, JobState.CANCELLING, detail="Backend cancelled immediately")
                return self.jobs.transition(cancelling.id, JobState.CANCELLED, detail="Backend returned cancelled")
            if status in _TO_JOB:
                return self.jobs.transition(job.id, _TO_JOB[status], detail=f"Backend returned {status.value}")
            return self.jobs.get(job.id)
        except Exception as exc:
            return self.jobs.transition(job.id, JobState.FAILED, detail=f"Backend launch failed: {type(exc).__name__}")

    def poll(self, job_id: str) -> ResearchJob:
        """Refresh metadata from backend; terminal jobs are left unchanged."""
        current = self.jobs.get(job_id)
        if self.jobs.is_terminal(current.state):
            return current
        status = self.backend.poll(self._get_handle(job_id))
        if status == WorkerStatus.RUNNING and current.state == JobState.STARTING:
            return self.jobs.transition(job_id, JobState.RUNNING)
        target = _TO_JOB.get(status)
        if target is not None:
            if current.state == JobState.STARTING and status == WorkerStatus.SUCCEEDED:
                running = self.jobs.transition(job_id, JobState.RUNNING, detail="Backend completed")
                return self.jobs.transition(running.id, JobState.SUCCEEDED, detail="Backend completed: succeeded")
            if current.state == JobState.STARTING and status == WorkerStatus.CANCELLED:
                cancelling = self.jobs.transition(job_id, JobState.CANCELLING, detail="Backend cancelled")
                return self.jobs.transition(cancelling.id, JobState.CANCELLED, detail="Backend completed: cancelled")
            if current.state == JobState.CANCELLING and status != WorkerStatus.CANCELLED:
                return self.jobs.transition(job_id, JobState.FAILED, detail=f"Unexpected terminal backend status: {status.value}")
            return self.jobs.transition(job_id, target, detail=f"Backend completed: {status.value}")
        return current

    def cancel(self, job_id: str) -> ResearchJob:
        """Request backend cancellation and reflect only its observed status."""
        current = self.jobs.get(job_id)
        if current.state == JobState.QUEUED:
            return self.jobs.request_cancel(job_id)
        if current.state not in (JobState.STARTING, JobState.RUNNING, JobState.CANCELLING):
            raise ValueError(f"Cannot cancel terminal job: {current.state.value}")
        if current.state != JobState.CANCELLING:
            current = self.jobs.request_cancel(job_id)
        status = self.backend.cancel(self._get_handle(job_id))
        if status == WorkerStatus.CANCELLED:
            return self.jobs.transition(job_id, JobState.CANCELLED, detail="Backend confirmed cancellation")
        if status in (WorkerStatus.FAILED, WorkerStatus.TIMED_OUT):
            return self.jobs.transition(job_id, _TO_JOB[status], detail=f"Backend returned {status.value}")
        return current

    def collect(self, job_id: str) -> WorkerResult:
        """Collect output only from a terminal backend result and validate bounds."""
        current = self.jobs.get(job_id)
        if not self.jobs.is_terminal(current.state):
            raise ValueError("Job must be terminal before collection")
        result = self.backend.collect(self._get_handle(job_id))
        result.validate()
        return result

    def _get_handle(self, job_id: str) -> str:
        with self._lock:
            try:
                return self._handles[job_id]
            except KeyError as exc:
                raise KeyError(f"No backend handle for job: {job_id}") from exc
