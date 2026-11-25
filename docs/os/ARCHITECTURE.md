# NP.ai OS System Architecture

**Status:** Proposed architecture; implementation not started.

## 1. System boundaries

NP.ai OS consists of two platform products with a shared product contract:

- **NP Desktop OS:** Linux-based desktop experience.
- **NP Mobile OS:** AOSP-based mobile experience.
- **NP Shared Platform:** cross-platform services and APIs that can run locally or in NIL.ai-operated infrastructure.

The desktop and mobile products share product principles and service contracts, not a single kernel or identical implementation. Platform-specific security models remain authoritative.

## 2. Logical layers

### A. Hardware and upstream platform

**Desktop:** upstream Linux kernel, firmware, device drivers, systemd, Wayland compositor and established graphics/audio stacks. Start from a maintained distribution/image project rather than maintaining a distribution infrastructure from zero.

**Mobile:** AOSP framework, Android kernel common/vendor components, HALs, verified boot chain, SELinux policy and device-specific vendor integration. AOSP alone does not guarantee a working build for arbitrary devices; each target requires hardware support and vendor components.

### B. Platform experience

- **NP Shell (desktop):** workspace, launcher, windows, notifications, settings, accessibility and system search.
- **NP Launcher (mobile):** home experience, app discovery, widgets, notifications and assistant entry point.
- Preserve normal desktop/mobile navigation and app launching. AI must not be the only way to operate the device.

### C. NP System Services

Services are separated by responsibility and privilege:

| Service | Responsibility | Trust boundary |
|---|---|---|
| np-session | Session lifecycle and user preferences | User session |
| np-permissions | Consent UI and capability grants | Privileged broker |
| np-intelligence | Model/runtime routing and inference requests | Unprivileged service; no ambient device access |
| np-actions | Typed, allow-listed system actions | Brokered capability execution |
| np-indexer | User-approved local search/indexing | Per-user sandbox |
| np-sync | Optional encrypted cross-device synchronization | Network boundary |
| np-updater | Verify and apply signed platform updates | Privileged updater |
| np-telemetry | Opt-in diagnostics with minimization | Separate opt-in boundary |

Names are provisional. Avoid creating separate microservices before a real deployment or isolation requirement exists.

### D. NP Intelligence

NP Intelligence is an operating-system capability, not the operating system itself.

Components:
1. **Request broker:** validates caller identity, user intent, permissions and policy.
2. **Model router:** chooses an available local runtime or user-configured provider according to explicit policy.
3. **Context broker:** supplies only the selected, consented context; never silently indexes all user data.
4. **Tool registry:** exposes typed tools with schemas, versioning and explicit permission scopes.
5. **Action planner:** proposes an action plan and obtains confirmation for consequential operations.
6. **Audit record:** records security-relevant action metadata without storing unnecessary prompts or private content.

Provider credentials belong in OS credential storage or a secure backend secret store, never in the UI bundle, repository or logs. Provider selection, data egress and retention must be visible to the user.

### E. Shared platform contracts

Define versioned, platform-neutral contracts before implementing cross-platform features:

- Identity: stable local account identity; optional cloud account linkage.
- Permission: subject, resource, action, scope, expiry, decision and revocation.
- Tool: typed input/output schema, capability requirements and risk class.
- Model: provider, model identifier, capabilities, limits, locality and data-handling metadata.
- Sync: encrypted object envelope, conflict policy, device identity and revocation.
- Update: signed manifest, target platform, version, hash, minimum compatible version and rollback policy.

Use OpenAPI for network APIs and protobuf or another schema-first IPC format only where process boundaries justify it. Keep contracts versioned and generated clients tested.

## 3. AI action safety model

Every system action must pass through a permission broker. The model itself is never an authority.

Risk classes:
- **Read-only low risk:** query time, open a settings page, search an explicitly selected folder.
- **Reversible change:** create a draft, change a non-security preference, move a user-selected file to trash.
- **Sensitive action:** send a message, upload a file, install software, modify network/security settings or access sensitive data.
- **Prohibited by default:** privilege escalation, disabling security controls, silent surveillance, credential extraction, destructive bulk operations and arbitrary unrestricted command execution.

For sensitive actions, show the exact target, data to be sent, consequences and recipient, then require a clear user confirmation. Re-check authorization at execution time. Permission grants must be revocable and expire.

Prompt injection from webpages, documents, notifications or retrieved content is untrusted input. It cannot grant permissions or override policy.

## 4. Desktop reference architecture

- Base: maintained Linux distribution with a reproducible image/build pipeline.
- Session: Wayland-first; use an established compositor/desktop stack.
- Shell: start as a user-session application/desktop shell extension; avoid forking the compositor initially.
- System integration: D-Bus and standard desktop portals where available.
- Packaging: upstream package formats initially; consider Flatpak for desktop application isolation.
- Updates: signed, atomic image updates where supported by the chosen base; recovery and rollback tested before release.
- Service implementation: choose Rust for small security-sensitive daemons where team capability supports it; use established desktop APIs rather than inventing replacements.

## 5. Mobile reference architecture

- Base: AOSP build for a small, explicitly selected reference-device set.
- UI: native Android/Kotlin system apps and launcher; use platform APIs and permission prompts.
- Security: verified boot, SELinux enforcing, Android permission model, scoped storage and hardware-backed keystore when available.
- Updates: signed OTA packages and a documented device-specific update/recovery path.
- AI integration: foreground service and explicit runtime permissions; background microphone capture is not a default feature.
- Compatibility: publish a support matrix by exact device/model/build. AOSP source availability does not imply unlockability, driver availability or safe OTA support.

## 6. Cross-device continuity

Cross-device sync is optional and end-to-end encrypted where feasible. Device pairing must be explicit. Users can inspect and revoke linked devices. Do not sync raw microphone, camera, screen or file content by default. Define conflict handling and deletion propagation before implementing sync.

## 7. Reliability and observability

- Structured logs with secrets and personal content redacted.
- No prompt or file-content logging by default.
- Crash reporting opt-in; diagnostic bundles reviewed for sensitive data.
- Health checks for services and clear degraded/offline modes.
- Resource limits, timeouts, cancellation and bounded queues for model requests.
- Graceful behavior when a provider, network, model runtime or sync service is unavailable.

## 8. Quality gates

No milestone is complete without:
- reproducible build instructions and pinned toolchains;
- automated unit/integration tests;
- security review of privileged boundaries;
- accessibility and localization checks;
- signed artifact verification;
- tested rollback/recovery path for update changes;
- exact supported hardware/software matrix;
- documented known limitations.

## 9. Explicit non-goals for the first release

- A new kernel or custom hypervisor.
- Replacing all Android or Linux applications.
- Universal support for every PC and Android phone.
- Always-listening cloud voice assistant.
- Autonomous unrestricted shell control.
- Custom app store, cloud sync or payment system before core platform validation.
