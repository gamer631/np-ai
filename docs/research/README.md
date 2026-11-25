# NILcenter.ai Research Platform

**Status:** Foundation specification and first Python SDK skeleton  
**Program:** Nepal Innovation Labs  
**Product:** NILcenter.ai Research OS  
**Shared intelligence:** NP.ai

NILcenter.ai is a dedicated technology research, engineering, experimentation and innovation environment. It is not a general-purpose entertainment OS. Its primary interface is a coherent collection of specialist laboratories and integrated tools, with Python as the main user-facing automation and extension language.

## Product promise

Give researchers, ethical security practitioners, engineers, developers and students one dependable environment to discover tools, create isolated workspaces, run reproducible experiments, inspect evidence and build new capabilities.

Kali Linux is an inspiration for the integrated specialist-tool workflow, not a template to copy. NILcenter.ai extends the concept across technology disciplines.

## Initial architecture

```
NILcenter.ai Research OS
├── Research Shell / Workspace UI
├── Laboratory Catalog
│   ├── Cybersecurity & Defensive Testing
│   ├── Reverse Engineering
│   ├── AI & Machine Learning
│   ├── Software Engineering
│   ├── Network & Protocol Research
│   ├── Hardware & Electronics
│   ├── Robotics & Automation
│   ├── Cloud & Infrastructure
│   ├── Data Science
│   ├── Scientific Computing
│   ├── Quantum Computing
│   └── Prototyping & Innovation
├── NIL Tool Runtime
│   ├── signed/versioned tool manifests
│   ├── dependency and environment resolver
│   ├── isolated execution backends
│   ├── permission/capability broker
│   └── evidence and experiment records
├── NIL Python SDK
│   ├── discover laboratories and tools
│   ├── compose approved workflows
│   ├── manage research workspaces
│   └── query results and evidence
└── NP.ai Intelligence Adapters (optional, permissioned)
```

## Python-first, not Python-only

Python is the primary user-facing language for scripting, automation, notebooks, experiment orchestration and tool integration. System-critical components may use Rust, C/C++ or established upstream services for performance and security. Every supported component should expose a documented, typed Python API where practical.

## First implementation boundary

The first SDK milestone provides an offline laboratory catalog and a typed tool registry. It deliberately does **not** execute arbitrary shell commands, load untrusted plugins, perform network scans, or grant elevated privileges. Execution backends will be added only after the permission broker, sandbox profiles, audit trail and authorization checks are implemented and tested.

## Quality requirements

- Python 3.11+; type annotations and documented public APIs.
- Deterministic offline catalog behavior.
- Explicit tool identifiers, versions, risk levels and capability declarations.
- No implicit root access or unrestricted shell execution.
- Reproducible workspaces with pinned dependencies.
- Structured, privacy-conscious experiment metadata.
- Unit tests and security tests for every execution boundary.
- Accessibility, localization and offline usability in the desktop experience.

## Documents

- [Laboratory catalog](LAB-CATALOG.md)
- [Tool and module contract](TOOL-MODULE-SPEC.md)
- [Security and execution model](SECURITY-EXECUTION.md)
- [Implementation roadmap](ROADMAP.md)
- [Python SDK](../../python/nilcenter-sdk/README.md)

## Status honesty

This milestone is a specification plus an initial SDK skeleton. It is not a bootable OS, desktop shell, production sandbox, or a collection of fully integrated research tools.
