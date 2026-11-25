"""Top-level NILcenter SDK client."""

from __future__ import annotations

from nilcenter.catalog import LabCatalog
from nilcenter.models import LabDescriptor, ToolDescriptor
from nilcenter.registry import ToolRegistry


class LabCollection:
    """Convenient entry point for laboratory discovery."""

    def __init__(self, catalog: LabCatalog, registry: ToolRegistry) -> None:
        self._catalog = catalog
        self._registry = registry

    def list(self) -> tuple[LabDescriptor, ...]:
        """List all available laboratory descriptors."""
        return self._catalog.list()

    def search(self, query: str) -> tuple[LabDescriptor, ...]:
        """Search laboratories by name, identifier or research focus."""
        return self._catalog.search(query)

    def get(self, lab_id: str) -> LabDescriptor:
        """Get a laboratory descriptor."""
        return self._catalog.get(lab_id)

    def tools(self, lab_id: str) -> tuple[ToolDescriptor, ...]:
        """List registered tool metadata for a laboratory."""
        self._catalog.get(lab_id)  # Validate the laboratory identifier.
        return self._registry.list(lab_id)


class NIL:
    """Offline-first NILcenter SDK client.

    The initial release exposes discovery and metadata only. It deliberately
    has no arbitrary command execution or plugin auto-loading API.
    """

    def __init__(self) -> None:
        self._catalog = LabCatalog()
        self.tools_registry = ToolRegistry()
        self.labs = LabCollection(self._catalog, self.tools_registry)

    def lab(self, lab_id: str) -> LabDescriptor:
        """Resolve a laboratory by identifier."""
        return self._catalog.get(lab_id)
