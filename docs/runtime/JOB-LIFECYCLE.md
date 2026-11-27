# NILcenter Job Lifecycle

The SDK job registry is a metadata-only lifecycle model. It is in-memory, not
persistent, and does not launch a worker or enforce a deadline.

## States

- queued
- starting
- running
- cancelling
- succeeded
- failed
- timed_out
- cancelled

Terminal states are succeeded, failed, timed_out, and cancelled. Terminal jobs
cannot be transitioned again. Cancellation of queued jobs marks them cancelled;
cancellation of a starting/running job moves to cancelling and **does not claim**
the worker has stopped. The future worker must confirm termination before it moves
the job to cancelled.

## Example

```python
from nilcenter.jobs import JobRegistry, JobState

registry = JobRegistry()
job = registry.create("experiment-123")
registry.transition(job.id, JobState.STARTING)
registry.transition(job.id, JobState.RUNNING)
# worker reports result only after isolated execution
registry.transition(job.id, JobState.SUCCEEDED)
```

## Not implemented in this milestone

- worker process/container launch
- persisted job queue
- cross-process coordination
- real timeout enforcement
- descendant process termination
- resource monitoring
- execution sandboxing

Do not use the registry as a production job queue. It is a state-machine foundation
for the orchestrator.
