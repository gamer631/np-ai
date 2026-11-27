"""Fail-closed policy contract for future isolated experiment execution.

This module validates requests only; it does not execute code or provide a sandbox.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    timeout_seconds: int = 30
    memory_mb: int = 256
    cpu_seconds: int = 15
    max_processes: int = 1

    def validate(self) -> None:
        if not 1 <= self.timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be between 1 and 300")
        if not 32 <= self.memory_mb <= 4096:
            raise ValueError("memory_mb must be between 32 and 4096")
        if not 1 <= self.cpu_seconds <= 300:
            raise ValueError("cpu_seconds must be between 1 and 300")
        if not 1 <= self.max_processes <= 16:
            raise ValueError("max_processes must be between 1 and 16")


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    tool_id: str
    source: str
    workspace: str
    network_access: bool = False
    requested_capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RuntimePolicy:
    """Default-deny request validator; this is not an operating-system security boundary."""

    limits: ResourceLimits = ResourceLimits()
    allowed_capabilities: frozenset[str] = frozenset()
    allow_network: bool = False
    max_source_bytes: int = 256_000

    def validate(self, request: ExecutionRequest) -> None:
        self.limits.validate()
        if not request.tool_id.strip():
            raise ValueError("tool_id is required")
        if not request.workspace.strip():
            raise ValueError("workspace is required")
        if len(request.source.encode("utf-8")) > self.max_source_bytes:
            raise ValueError("source exceeds policy size limit")
        if request.network_access and not self.allow_network:
            raise PermissionError("network access is denied by default")
        denied = set(request.requested_capabilities) - self.allowed_capabilities
        if denied:
            raise PermissionError(f"capabilities not approved: {', '.join(sorted(denied))}")
