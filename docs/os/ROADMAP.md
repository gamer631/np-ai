# NP.ai OS Research and Engineering Roadmap

**Status:** Proposed. Dates are intentionally not promised until team capacity and hardware are known.

## Stage 0 — Architecture and feasibility

Deliverables:
- Agree on product principles and desktop/mobile boundaries.
- Select candidate Linux base and evaluate AOSP build environment.
- Audit repository ownership, licensing and third-party obligations.
- Define reference PC and shortlist mobile devices based on bootloader, kernel, vendor and recovery support.
- Write threat model, API contracts and build/release design.

Exit criteria: architecture decision records accepted; candidate desktop image boots in a test VM or reference PC; mobile feasibility report identifies a realistic target or records blockers.

## Stage 1 — NP Desktop Shell prototype

Build:
- bootable developer image based on selected upstream;
- NP Shell application with launcher, workspace, settings and accessible navigation;
- NP System service skeleton and D-Bus integration;
- permission broker prototype;
- NP Intelligence adapter behind an explicit user-triggered interface;
- offline baseline: shell and ordinary desktop functions work with network disconnected.

Exit criteria: clean build from documented steps, install/boot on declared hardware, automated tests, permission UX demonstrated, no privileged arbitrary command execution.

## Stage 2 — Mobile feasibility prototype

Build:
- reproducible AOSP build for one selected reference device;
- NP Launcher and one or two system-app prototypes;
- Android permission and foreground-service integration;
- device-specific hardware validation;
- signed test OTA and recovery procedure.

Exit criteria: exact device/build matrix, core hardware functions validated, signed update/recovery test passed. If device support is not feasible, keep mobile as a launcher/app experience rather than claiming an OS port.

## Stage 3 — Shared NP Platform

Build:
- versioned identity and capability contracts;
- provider/model abstraction with user-controlled routing;
- local inference evaluation on supported hardware;
- encrypted opt-in sync and device pairing;
- developer SDK and extension API;
- Nepali/English localization and accessibility.

Exit criteria: same user-facing capability works safely on desktop and mobile through documented APIs; offline and provider-failure behavior tested.

## Stage 4 — Developer preview

Build:
- signed images and release manifests;
- update/recovery infrastructure;
- security response process and vulnerability reporting;
- automated compatibility and regression suites;
- documentation, known issues and supported hardware list.

Exit criteria: external testers can install, update, recover and report issues without undocumented manual steps.

## Stage 5 — Public beta and ecosystem

Only after security and reliability gates:
- broaden hardware support;
- publish stable SDK and app distribution guidance;
- establish release cadence and long-term maintenance;
- consider enterprise, education and research deployments;
- publish benchmarks with reproducible methodology.

## First 30-day execution plan

1. Inventory current repository and preserve existing NP.ai web/backend work.
2. Add OS architecture docs and an architecture tracking issue.
3. Create a desktop Linux VM proof of concept; test boot, session, graphics and update/rollback.
4. Run AOSP build feasibility in a separate environment; do not promise a mobile build before selecting a device.
5. Implement no production privileged service until threat model and capability API are reviewed.

## Definition of done

A feature is done only when code, tests, documentation, build artifact or reproducible build evidence, security implications and known limitations are recorded. A mock UI, architecture document or successful compile alone is not a complete OS.
