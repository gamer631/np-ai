"""Validation for portable NILcenter tool manifests."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from nilcenter.models import RiskLevel

_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)+$")
_VERSION_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")
_ALLOWED_FIELDS = {
    "id",
    "name",
    "summary",
    "laboratory",
    "version",
    "risk_level",
    "capabilities",
}


@dataclass(frozen=True, slots=True)
class ToolManifest:
    """Validated metadata describing one NILcenter tool module."""

    id: str
    name: str
    summary: str
    laboratory: str
    version: str
    risk_level: RiskLevel
    capabilities: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> ToolManifest:
        """Validate a decoded JSON object and create a typed manifest."""
        unknown = set(value) - _ALLOWED_FIELDS
        if unknown:
            raise ValueError(f"Unknown manifest fields: {', '.join(sorted(unknown))}")

        required = _ALLOWED_FIELDS
        missing = required - set(value)
        if missing:
            raise ValueError(f"Missing manifest fields: {', '.join(sorted(missing))}")

        string_fields = ("id", "name", "summary", "laboratory", "version", "risk_level")
        for field_name in string_fields:
            field_value = value[field_name]
            if not isinstance(field_value, str) or not field_value.strip():
                raise ValueError(f"Manifest field '{field_name}' must be a non-empty string")

        module_id = str(value["id"])
        if not _ID_PATTERN.fullmatch(module_id):
            raise ValueError("Manifest field 'id' must be a stable reverse-DNS-style identifier")

        version = str(value["version"])
        if not _VERSION_PATTERN.fullmatch(version):
            raise ValueError("Manifest field 'version' must use semantic versioning")

        laboratory = str(value["laboratory"])
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", laboratory):
            raise ValueError("Manifest field 'laboratory' must be a lowercase catalog identifier")

        raw_capabilities = value["capabilities"]
        if not isinstance(raw_capabilities, list) or any(
            not isinstance(item, str) or not item.strip() for item in raw_capabilities
        ):
            raise ValueError("Manifest field 'capabilities' must be a list of non-empty strings")

        try:
            risk_level = RiskLevel(str(value["risk_level"]))
        except ValueError as exc:
            raise ValueError("Manifest field 'risk_level' is not supported") from exc

        return cls(
            id=module_id,
            name=str(value["name"]).strip(),
            summary=str(value["summary"]).strip(),
            laboratory=laboratory,
            version=version,
            risk_level=risk_level,
            capabilities=tuple(raw_capabilities),
        )
