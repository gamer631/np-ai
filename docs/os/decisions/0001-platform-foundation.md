# ADR 0001: Use Linux and AOSP foundations for NP.ai OS

- **Status:** Proposed
- **Date:** 2026-11-25
- **Decision owners:** NIL.ai / NP.ai maintainers
- **Scope:** Desktop and mobile operating-system foundations

## Context

NP.ai OS targets both desktop and mobile. Building a new kernel, hardware abstraction layer, driver ecosystem, application platform, secure boot chain and update infrastructure would create an unsustainable initial scope. Desktop Linux and Android also have fundamentally different application, hardware and security models.

The company requires room for original research and engineering while preserving a realistic path to bootable prototypes and supported devices.

## Decision

1. Build NP Desktop OS on a maintained upstream Linux distribution/image.
2. Build NP Mobile OS on AOSP for a narrowly selected reference-device set.
3. Develop NIL-owned shell/launcher, system services, AI integration, permission UX, developer experience and product identity.
4. Share versioned service contracts and selected platform-neutral components; keep privileged platform integrations native.
5. Do not develop a new kernel in the initial program.

## Alternatives considered

### New kernel for both platforms
Rejected for the initial phase. It would require extensive driver, hardware, security, application and maintenance investment before users receive value. Reconsider only for a research objective that cannot be met on existing kernels.

### Linux on desktop and Linux phone for mobile
Not selected as the primary mobile path. Linux phones are valuable research targets but have narrower device/driver/application support. Could be a separate experimental track.

### Android apps only, no mobile OS
Viable fallback if AOSP device feasibility fails. A launcher and companion app can validate mobile UX without claiming to ship an OS.

### One shared cross-platform UI and service implementation
Rejected as a hard requirement. Shared design tokens and contracts are useful, but Linux and Android should use native security boundaries and system APIs.

## Consequences

Positive:
- Faster route to demonstrable prototypes.
- Reuses upstream security work, drivers and application ecosystems.
- Keeps NIL engineering focused on distinctive product capabilities.
- Supports a coherent desktop/mobile product vision without pretending the kernels are identical.

Costs and risks:
- Must maintain two platform build/release tracks.
- AOSP device enablement and vendor components are difficult and device-specific.
- Linux distribution/image maintenance and update infrastructure require ongoing ownership.
- Upstream licenses and trademarks must be respected.
- Cross-device feature parity will be gradual, not automatic.

## Revisit when

- A demonstrated product requirement cannot be implemented on Linux/AOSP.
- Device support, maintenance burden or upstream direction changes materially.
- NIL has sufficient kernel/security/hardware engineering capacity and a funded research case.
