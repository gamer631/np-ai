"""Coordinator tests using a stub backend (no processes or code execution)."""
from __future__ import annotations

from uuid import uuid4

import pytest

from nilcenter.coordinator import WorkerCoordinator
from nilcenter.jobs import JobRegistry, JobState
from nilcenter.workspaces import WorkspaceManager
from nilcenter.worker_contract import WorkerRequest, WorkerResult, WorkerStatus


class StubBackend:
    def __init__(self, status: WorkerStatus = WorkerStatus.RUNNING) -> None:
        self.status = status
        self.cancel_status = WorkerStatus.RUNNING
        self.calls: list[str] = []

    def launch(self, request: WorkerRequest) -> str:
        self.calls.append("launch")
        return "stub-handle"

    def poll(self, handle: str) -> WorkerStatus:
        self.calls.append("poll")
        return self.status

    def cancel(self, handle: str) -> WorkerStatus:
        self.calls.append("cancel")
        return self.cancel_status

    def collect(self, handle: str) -> WorkerResult:
        self.calls.append("collect")
        return WorkerResult(WorkerStatus.SUCCEEDED, exit_code=0, stdout="ok")


def req() -> WorkerRequest:
    return WorkerRequest(str(uuid4()), "exp-demo", str(uuid4()))


def coordinator(tmp_path: object, backend: StubBackend) -> WorkerCoordinator:
    return WorkerCoordinator(JobRegistry(), WorkspaceManager(tmp_path), backend)  # type: ignore[arg-type]


def test_launch_and_poll_running(tmp_path: object) -> None:
    backend = StubBackend()
    c = coordinator(tmp_path, backend)
    job = c.launch(req())
    assert job.state == JobState.RUNNING
    backend.status = WorkerStatus.SUCCEEDED
    assert c.poll(job.id).state == JobState.SUCCEEDED
    assert c.collect(job.id).stdout == "ok"


def test_launch_failure_sets_failed(tmp_path: object) -> None:
    class Broken(StubBackend):
        def launch(self, request: WorkerRequest) -> str:
            raise RuntimeError("backend unavailable")
    job = coordinator(tmp_path, Broken()).launch(req())
    assert job.state == JobState.FAILED
    assert "RuntimeError" in job.detail


def test_cancel_does_not_claim_stop_without_backend_confirmation(tmp_path: object) -> None:
    backend = StubBackend()
    c = coordinator(tmp_path, backend)
    job = c.launch(req())
    result = c.cancel(job.id)
    assert result.state == JobState.CANCELLING
    backend.cancel_status = WorkerStatus.CANCELLED
    assert c.cancel(job.id).state == JobState.CANCELLED


def test_collect_requires_terminal_job(tmp_path: object) -> None:
    c = coordinator(tmp_path, StubBackend())
    job = c.launch(req())
    with pytest.raises(ValueError):
        c.collect(job.id)
