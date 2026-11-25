"""Application-level capability grants for future NILcenter adapters.

This is an in-process policy primitive, not an operating-system security
boundary. It must be backed by a separately implemented OS permission broker
and sandbox before any untrusted workload is executed.
"""
from __future__ import annotations

import re
import secrets
import time
from dataclasses import dataclass, field

_CAPABILITY = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class CapabilityGrant:
    """Opaque, short-lived grant bound to one subject and resource."""

    token: str = field(repr=False)
    subject: str
    capability: str
    resource: str
    expires_at: float


class CapabilityBroker:
    """Deny-by-default in-memory capability policy.

    A caller must explicitly pass approved=True after obtaining user consent.
    Grants are exact-match, short-lived and revocable.
    """

    def __init__(self, *, max_ttl_seconds: int = 900) -> None:
        if max_ttl_seconds < 1:
            raise ValueError("max_ttl_seconds must be positive")
        self._max_ttl = max_ttl_seconds
        self._grants: dict[str, CapabilityGrant] = {}

    def grant(
        self,
        *,
        subject: str,
        capability: str,
        resource: str,
        approved: bool,
        ttl_seconds: int = 300,
    ) -> CapabilityGrant:
        """Issue a scoped grant only after explicit approval."""
        if not approved:
            raise PermissionError("Explicit user approval is required")
        if not subject.strip() or not resource.strip():
            raise ValueError("Subject and resource are required")
        if not _CAPABILITY.fullmatch(capability):
            raise ValueError("Invalid capability identifier")
        if ttl_seconds < 1 or ttl_seconds > self._max_ttl:
            raise ValueError(f"Grant TTL must be between 1 and {self._max_ttl} seconds")
        grant = CapabilityGrant(
            token=secrets.token_urlsafe(32),
            subject=subject,
            capability=capability,
            resource=resource,
            expires_at=time.monotonic() + ttl_seconds,
        )
        self._grants[grant.token] = grant
        return grant

    def authorize(
        self, token: str, *, subject: str, capability: str, resource: str
    ) -> bool:
        """Check exact grant scope and expiry; unknown tokens are denied."""
        grant = self._grants.get(token)
        if grant is None:
            return False
        if time.monotonic() >= grant.expires_at:
            self._grants.pop(token, None)
            return False
        return (
            grant.subject == subject
            and grant.capability == capability
            and grant.resource == resource
        )

    def revoke(self, token: str) -> bool:
        """Revoke a grant; return whether it existed."""
        return self._grants.pop(token, None) is not None
