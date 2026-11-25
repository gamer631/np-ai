# NILcenter.ai Research Platform Roadmap

## Phase 0 — Foundation (current branch)

- [x] Define research-center product scope and laboratory catalog.
- [x] Define module manifest and security boundaries.
- [x] Create initial Python SDK catalog and registry skeleton.
- [ ] Add CI for supported Python versions and static checks.
- [ ] Review licenses and upstream tool inventory.

## Phase 1 — Python developer experience

- Python SDK with stable public APIs.
- CLI for listing labs, tools and module metadata.
- Jupyter integration and starter notebooks.
- Typed workflow definitions and local experiment records.
- Package/environment manager with lockfiles.
- Documentation, examples and compatibility tests.

## Phase 2 — Safe execution substrate

- Threat model and sandbox backend selection.
- Disposable local workspaces.
- Capability broker and per-run consent.
- Resource quotas, network policy, cancellation and cleanup.
- Audit/evidence bundle format.
- Security tests and independent review.

## Phase 3 — First three laboratory verticals

Prioritize cybersecurity/defensive testing, AI & machine learning, and software engineering. Integrate a small number of high-quality upstream tools per lab. Do not chase module counts before usability and maintenance are proven.

## Phase 4 — Research workbench UX

- Lab explorer and searchable tool catalog.
- Python Studio, terminal and notebooks.
- Workspace manager and experiment history.
- Evidence viewer and report builder.
- Keyboard-first navigation, screen-reader support and Nepali/English localization.

## Phase 5 — Desktop OS prototype

Build on the existing Linux/AOSP architecture decision. Deliver a reproducible desktop VM image with the research shell and SDK integrated. A bootable prototype is not a production OS.

## Phase 6 — Scale the laboratory network

Add labs based on research demand and maintainer capacity. Mature labs may target 100+ validated modules, with signed releases, clear ownership and lifecycle management. Explore mobile companion support after desktop workflows and security controls are proven.

## Exit criteria

A phase is complete only when code, automated tests, documentation, build evidence and known limitations are available. Roadmap checkboxes must not be marked complete based on plans alone.
