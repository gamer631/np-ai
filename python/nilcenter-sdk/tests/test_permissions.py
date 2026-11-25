from __future__ import annotations

import pytest

from nilcenter.permissions import CapabilityBroker


def test_grant_requires_explicit_approval():
    broker = CapabilityBroker()
    with pytest.raises(PermissionError):
        broker.grant(
            subject="tool:demo",
            capability="dataset.read",
            resource="dataset:public-1",
            approved=False,
        )


def test_grant_is_exactly_scoped_and_revocable():
    broker = CapabilityBroker()
    grant = broker.grant(
        subject="tool:demo",
        capability="dataset.read",
        resource="dataset:public-1",
        approved=True,
    )
    assert broker.authorize(
        grant.token,
        subject="tool:demo",
        capability="dataset.read",
        resource="dataset:public-1",
    )
    assert not broker.authorize(
        grant.token,
        subject="tool:other",
        capability="dataset.read",
        resource="dataset:public-1",
    )
    assert broker.revoke(grant.token)
    assert not broker.authorize(
        grant.token,
        subject="tool:demo",
        capability="dataset.read",
        resource="dataset:public-1",
    )


def test_invalid_capability_and_ttl_are_rejected():
    broker = CapabilityBroker(max_ttl_seconds=10)
    with pytest.raises(ValueError):
        broker.grant(
            subject="tool:demo",
            capability="*",
            resource="all",
            approved=True,
        )
    with pytest.raises(ValueError):
        broker.grant(
            subject="tool:demo",
            capability="dataset.read",
            resource="all",
            approved=True,
            ttl_seconds=11,
        )
