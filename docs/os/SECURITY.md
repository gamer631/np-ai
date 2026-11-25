# NP.ai OS Security Architecture and Threat Model

**Status:** Initial threat model; requires implementation-specific review.

## Security objectives

Protect device integrity, user data, credentials, availability and user autonomy across desktop and mobile. Treat AI-generated content and external content as untrusted. The OS must not depend on model correctness for authorization.

## Assets

- Boot chain, kernel, system images and update signing keys.
- User files, messages, photos, microphone/camera/screen content and location.
- Provider API credentials, device keys and account tokens.
- Permission grants, action history and local indexes.
- Network identity, device pairing keys and sync data.

## Threat actors and failure sources

- Malicious applications, compromised dependencies and supply-chain attacks.
- Malicious or compromised model providers and tool endpoints.
- Prompt injection embedded in webpages, documents, email, notifications or retrieved content.
- Theft or physical access to an unlocked or locked device.
- Network interception, malicious Wi-Fi and compromised update mirrors.
- Accidental model actions, confused-deputy behavior and over-broad permissions.

## Required controls

### Boot, build and updates
- Build from maintained upstream sources with pinned dependencies and recorded provenance.
- Sign release artifacts and update metadata; keep signing keys offline or in a managed signing service.
- Verify updates before installation; support rollback/recovery and prevent downgrade attacks where platform support allows.
- Separate developer/test signing keys from release keys.
- Publish hashes, signatures, build instructions and security advisories.

### Privilege separation
- Run NP Intelligence without root/system privileges.
- Keep privileged operations in a small broker with a narrow typed API.
- Never expose a generic `exec(command)` or arbitrary shell tool to the model.
- Validate all inputs at the broker boundary; enforce allow-lists, path constraints, ownership and race-safe file operations.
- Use OS-native sandboxing, app permissions, SELinux/LSM policies and portals.

### AI-specific controls
- No ambient access to microphone, camera, screen, files, contacts, location or clipboard.
- Ask for permission at the moment the relevant capability is needed; display active capture/access state.
- Make network egress/provider selection visible; disclose what context leaves the device.
- Treat retrieved content and tool output as data, never as policy or instructions.
- Require explicit confirmation for sending, publishing, purchasing, installing, deleting, changing security settings or other consequential actions.
- Re-authorize at execution time; grants are scoped, time-limited and revocable.
- Provide a kill switch to disable AI services without disabling the OS.
- Rate-limit, time out and cancel provider/tool requests; redact secrets from logs.

### Data protection
- Use platform credential stores and hardware-backed key storage where available.
- Encrypt sync data; pair devices explicitly and support device revocation.
- Minimize retention; do not collect prompts or private content for telemetry by default.
- Keep local indexes per-user and deletable; document what is indexed.
- Define secure deletion expectations realistically, considering flash storage and backups.

### Mobile-specific
- Keep verified boot and SELinux enforcing.
- Preserve Android application sandbox and permission model.
- Do not enable background microphone/camera access by default.
- Provide signed OTA and tested recovery for each supported device.

### Desktop-specific
- Use standard user sessions, portals and sandboxing.
- Avoid privileged shell extensions and custom kernel modules in the first milestone.
- Keep the base image immutable/atomic where practical and verify update rollback.

## Abuse cases to test

1. A webpage instructs the assistant to upload local documents: no upload without user-selected files and explicit confirmation.
2. A document asks the model to reveal environment variables or API keys: secrets remain inaccessible to model context.
3. A model suggests `sudo` or destructive shell commands: no arbitrary shell capability exists.
4. A malicious app impersonates the NP assistant: identity and permission prompts are provided by trusted OS surfaces.
5. Provider compromise or outage: disable provider route, revoke credentials and retain local OS usability.
6. Update metadata or artifact is tampered with: signature verification rejects it.
7. Device is lost: revoke paired device and cloud sessions; local encryption protects data at rest where hardware supports it.

## Security release gates

No public OS image until boot/update chain, privileged broker, app isolation, data handling, recovery and supported-device behavior receive documented review. A threat model is not proof of security; each control requires implementation and tests.
