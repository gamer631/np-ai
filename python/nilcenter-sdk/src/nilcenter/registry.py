"""Metadata-only tool registry for the initial SDK milestone."""

from __future__ import annotations

from nilcenter.models import ToolDescriptor


class ToolRegistry:
    """In-memory registry of reviewed tool descriptors.

    This class intentionally does not install, import or execute plugins.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDescriptor] = {}

    def register(self, tool: ToolDescriptor) -> None:
        """Register a descriptor, rejecting duplicate stable identifiers."""
        if tool.id in self._tools:
            raise ValueError(f"Tool is already registered: {tool.id}")
        self._tools[tool.id] = tool

    def list(self, laboratory: str | None = None) -> tuple[ToolDescriptor, ...]:
        """List registered descriptors, optionally filtered by laboratory."""
        values = self._tools.values()
        if laboratory is not None:
            values = (tool for tool in values if tool.laboratory == laboratory)
        return tuple(sorted(values, key=lambda item: (item.laboratory, item.name.casefold())))

    def get(self, tool_id: str) -> ToolDescriptor:
        """Return a descriptor by stable identifier."""
        try:
            return self._tools[tool_id]
        except KeyError as exc:
            raise KeyError(f"Unknown NILcenter tool: {tool_id}") from exc
