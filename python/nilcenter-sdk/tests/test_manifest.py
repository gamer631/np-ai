import pytest

from nilcenter import RiskLevel
from nilcenter.manifest import ToolManifest


def valid_manifest() -> dict[str, object]:
    return {
        "id": "org.nilcenter.data.dataset-inspector",
        "name": "Dataset Inspector",
        "summary": "Inspect a selected research dataset.",
        "laboratory": "data-science",
        "version": "1.2.0",
        "risk_level": "low",
        "capabilities": ["workspace.read"],
    }


def test_manifest_parses_valid_metadata() -> None:
    manifest = ToolManifest.from_mapping(valid_manifest())
    assert manifest.id == "org.nilcenter.data.dataset-inspector"
    assert manifest.risk_level is RiskLevel.LOW
    assert manifest.capabilities == ("workspace.read",)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "bad-id"),
        ("version", "1.2"),
        ("laboratory", "Data Science"),
        ("risk_level", "untrusted"),
        ("capabilities", "workspace.read"),
    ],
)
def test_manifest_rejects_invalid_fields(field: str, value: object) -> None:
    payload = valid_manifest()
    payload[field] = value
    with pytest.raises(ValueError):
        ToolManifest.from_mapping(payload)


def test_manifest_rejects_unknown_fields() -> None:
    payload = valid_manifest()
    payload["execute_shell"] = True
    with pytest.raises(ValueError, match="Unknown manifest fields"):
        ToolManifest.from_mapping(payload)
