# NP.ai OS — Nepal Innovation Labs

**Status:** Architecture proposal / pre-implementation  
**Company:** Nepal Innovation Labs (NIL.ai)  
**Project:** NP.ai OS  
**Scope:** Desktop and mobile computing

NP.ai OS is a long-term research and engineering program to create a coherent, AI-native computing experience across desktop and mobile devices. It is one initiative within NIL.ai's broader technology research and innovation mission—not the definition of the whole company.

## Product thesis

Build a secure, user-controlled computing platform where intelligence is a first-class system capability, while preserving conventional applications, local control, accessibility, offline operation and user choice.

AI must be an optional, permissioned system capability. The operating system must remain useful when AI providers are unavailable, the device is offline, or the user disables AI.

## Recommended foundation

| Target | Foundation | NIL.ai-owned work |
|---|---|---|
| Desktop | Linux distribution / image built from an established upstream; Wayland; systemd; immutable or atomic base where practical | NP Shell, system services, settings, assistant UX, integrations, update policy, curated app experience |
| Mobile | Android Open Source Project (AOSP) on explicitly supported reference devices | NP Launcher, assistant UX, system apps, device integrations, policy/configuration and supported device builds |
| Shared | Versioned APIs, identity and policy contracts, model/runtime abstraction, sync protocol, developer SDK | NP Intelligence services, permission model, cross-device continuity and developer platform |

Do **not** start with a new kernel. Reuse upstream kernels and platform security mechanisms. Revisit kernel work only when a demonstrated requirement cannot be met safely or sustainably upstream.

## Architecture at a glance

```text
                 NEPAL INNOVATION LABS (NIL.ai)
          Research • Engineering • Open Innovation
                              |
                         NP.ai OS
            +-----------------+-----------------+
            |                                   |
      NP Desktop OS                         NP Mobile OS
      Linux foundation                       AOSP foundation
            |                                   |
      NP Shell / UX                         NP Launcher / UX
      Desktop services                      Android services
      Package & update                      APK / system apps
            +-----------------+-----------------+
                              |
                    Shared NP Platform
       Identity • Policy • Intelligence • Sync • SDK
                              |
        Local runtimes / user-selected remote providers
```

## Non-negotiable principles

1. **User control:** explicit consent for microphone, camera, files, location, screen content, network access and external actions.
2. **Least privilege:** AI tools receive narrowly scoped, short-lived capabilities; no unrestricted shell or root access.
3. **Local-first:** settings, files and core OS functions work without cloud connectivity. Local inference is used when practical and supported.
4. **Provider independence:** model providers are adapters, not the operating system's foundation.
5. **Open standards:** prefer upstream components, documented APIs and interoperable formats.
6. **Security updates:** signed artifacts, verified update metadata, rollback protection where supported, vulnerability response and reproducible build goals.
7. **Accessibility and localization:** keyboard, assistive technology, scalable UI, Nepali and English language support.
8. **Research integrity:** distinguish prototypes, benchmarks, supported devices and production-ready claims.

## First milestone

The first deliverable is **NP Desktop Shell Prototype** on one supported Linux base and one reference PC. It is not a complete OS distribution. Prove the shell, system-service boundary, permission UX, update approach and AI action safety before expanding.

Mobile begins as a separate feasibility track: AOSP build environment, reference-device selection, boot/unlock constraints, hardware support and signed image pipeline. Do not promise broad Android phone compatibility until each device is validated.

## Documentation

- [System architecture](ARCHITECTURE.md)
- [Platform matrix and technology choices](PLATFORM-MATRIX.md)
- [Security architecture and threat model](SECURITY.md)
- [Research and engineering roadmap](ROADMAP.md)
- [ADR 0001 — Platform foundation](decisions/0001-platform-foundation.md)

## Current implementation status

This directory records architecture and decisions only. It does not claim that an NP.ai OS image, kernel, shell, mobile ROM, installer, update service or device build currently exists. Every implementation milestone must have code, tests, build artifacts and supported-device evidence before it is marked complete.
