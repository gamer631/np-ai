from uuid import uuid4

import pytest

from nilcenter.jobs import JobRegistry, JobState, JobTransitionError


def test_job_created_queued_and_transitioned():
    registry = JobRegistry()
    job = registry.create("experiment-abc")
    assert job.state is JobState.QUEUED
    assert registry.transition(job.id, JobState.STARTING).state is JobState.STARTING
    assert registry.transition(job.id, JobState.RUNNING).state is JobState.RUNNING
    assert registry.transition(job.id, JobState.SUCCEEDED).state is JobState.SUCCEEDED


def test_queued_cancel_is_terminal():
    registry = JobRegistry()
    job = registry.create("exp")
    cancelled = registry.request_cancel(job.id)
    assert cancelled.state is JobState.CANCELLED
    with pytest.raises(JobTransitionError):
        registry.transition(job.id, JobState.RUNNING)


def test_running_cancel_requests_cancellation_not_completion():
    registry = JobRegistry()
    job = registry.create("exp")
    registry.transition(job.id, JobState.STARTING)
    registry.transition(job.id, JobState.RUNNING)
    assert registry.request_cancel(job.id).state is JobState.CANCELLING
    assert registry.request_cancel(job.id).state is JobState.CANCELLING
    assert registry.transition(job.id, JobState.CANCELLED).state is JobState.CANCELLED


def test_invalid_transition_rejected():
    registry = JobRegistry()
    job = registry.create("exp")
    with pytest.raises(JobTransitionError):
        registry.transition(job.id, JobState.SUCCEEDED)


def test_invalid_ids_and_duplicate_ids_rejected():
    registry = JobRegistry()
    with pytest.raises(ValueError):
        registry.create("")
    job_id = str(uuid4())
    registry.create("exp", job_id=job_id)
    with pytest.raises(ValueError):
        registry.create("exp", job_id=job_id)


def test_list_filters_state():
    registry = JobRegistry()
    registry.create("exp1")
    second = registry.create("exp2")
    registry.transition(second.id, JobState.STARTING)
    assert len(registry.list(state=JobState.QUEUED)) == 1
    assert len(registry.list(state=JobState.STARTING)) == 1
