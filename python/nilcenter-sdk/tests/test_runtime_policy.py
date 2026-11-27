from __future__ import annotations

import pytest

from nilcenter.runtime_policy import ExecutionRequest, ResourceLimits, RuntimePolicy


def request(**overrides: object) -> ExecutionRequest:
    values: dict[str, object] = {
        "tool_id": "lab:sample",
        "source": "print('research')",
        "workspace": "/workspace/experiment-1",
    }
    values.update(overrides)
    return ExecutionRequest(**values)  # type: ignore[arg-type]


def test_default_policy_accepts_minimal_request():
    RuntimePolicy().validate(request())


def test_network_is_denied_by_default():
    with pytest.raises(PermissionError, match="denied by default"):
        RuntimePolicy().validate(request(network_access=True))


def test_network_can_only_be_enabled_by_explicit_policy():
    RuntimePolicy(allow_network=True).validate(request(network_access=True))


def test_unapproved_capability_is_rejected():
    with pytest.raises(PermissionError, match="not approved"):
        RuntimePolicy().validate(request(requested_capabilities=("filesystem.write",)))


def test_approved_capability_passes():
    RuntimePolicy(allowed_capabilities=frozenset({"dataset.read"})).validate(
        request(requested_capabilities=("dataset.read",))
    )


def test_empty_tool_or_workspace_is_rejected():
    with pytest.raises(ValueError, match="tool_id"):
        RuntimePolicy().validate(request(tool_id=" "))
    with pytest.raises(ValueError, match="workspace"):
        RuntimePolicy().validate(request(workspace=" "))


def test_source_size_limit_is_enforced():
    with pytest.raises(ValueError, match="size limit"):
        RuntimePolicy(max_source_bytes=4).validate(request(source="12345"))


@pytest.mark.parametrize(
    "limits",
    [
        ResourceLimits(timeout_seconds=0),
        ResourceLimits(memory_mb=16),
        ResourceLimits(cpu_seconds=0),
        ResourceLimits(max_processes=0),
    ],
)
def test_invalid_resource_limits_rejected(limits: ResourceLimits):
    with pytest.raises(ValueError):
        RuntimePolicy(limits=limits).validate(request())
