from nilcenter import NIL, RiskLevel, ToolDescriptor


def test_catalog_has_twelve_initial_laboratories() -> None:
    nil = NIL()
    assert len(nil.labs.list()) == 12


def test_search_finds_cybersecurity_lab() -> None:
    nil = NIL()
    results = nil.labs.search("forensics")
    assert [lab.id for lab in results] == ["cybersecurity"]


def test_lab_lookup_is_case_insensitive() -> None:
    nil = NIL()
    assert nil.lab("AI-ML").id == "ai-ml"


def test_unknown_lab_raises_clear_error() -> None:
    nil = NIL()
    try:
        nil.lab("not-a-lab")
    except KeyError as exc:
        assert "Unknown NILcenter laboratory" in str(exc)
    else:
        raise AssertionError("Expected KeyError")


def test_registry_registers_and_filters_tools() -> None:
    nil = NIL()
    tool = ToolDescriptor(
        id="org.nilcenter.example.dataset-inspector",
        name="Dataset Inspector",
        laboratory="data-science",
        version="0.1.0",
        summary="Inspect a selected dataset.",
        risk_level=RiskLevel.LOW,
    )
    nil.tools_registry.register(tool)
    assert nil.labs.tools("data-science") == (tool,)
    assert nil.tools_registry.get(tool.id) == tool


def test_registry_rejects_duplicate_ids() -> None:
    nil = NIL()
    tool = ToolDescriptor(
        id="org.nilcenter.example.sample",
        name="Sample",
        laboratory="software-engineering",
        version="0.1.0",
        summary="A test descriptor.",
    )
    nil.tools_registry.register(tool)
    try:
        nil.tools_registry.register(tool)
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
