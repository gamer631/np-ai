"""Typed, platform-neutral models used by the NILcenter SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class RiskLevel(StrEnum):
    """Declared operational risk for a research tool."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class LabDescriptor:
    """Discoverable research laboratory metadata."""

    id: str
    name: str
    summary: str
    focus_areas: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolDescriptor:
    """Metadata for a tool; it does not imply that the tool is installed or runnable."""

    id: str
    name: str
    laboratory: str
    version: str
    summary: str
    risk_level: RiskLevel = RiskLevel.LOW
    capabilities: tuple[str, ...] = ()
    installed: bool = False


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Structured result envelope for future approved tool adapters."""

    success: bool
    summary: str
    data: Mapping[str, Any] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()

    @classmethod
    def ok(
        cls,
        data: Mapping[str, Any] | None = None,
        summary: str = "Completed",
        evidence: tuple[str, ...] = (),
    ) -> ToolResult:
        """Create a successful result without executing any operation."""
        return cls(True, summary, data or {}, evidence)

    @classmethod
    def failure(cls, summary: str) -> ToolResult:
        """Create a failure result."""
        return cls(False, summary)
