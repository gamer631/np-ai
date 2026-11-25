# NILcenter.ai Security and Tool Execution Model

## Trust boundaries

1. **UI boundary:** the shell displays tool metadata and asks for user intent; it is not a privilege authority.
2. **Python SDK boundary:** scripts request typed operations; they do not receive implicit root access.
3. **Tool broker:** validates identity, policy, capability scope, target, expiry and risk class.
4. **Execution boundary:** tools run in disposable, resource-limited workspaces using OS isolation.
5. **Evidence boundary:** logs and artifacts are stored with provenance and privacy controls.
6. **External network boundary:** network access is disabled by default and enabled only for an approved workflow and target scope.

## Risk classes

| Class | Examples | Default policy |
|---|---|---|
| Low | Parse a local sample, format code, analyze an explicitly selected dataset | Allowed within workspace |
| Moderate | Access a lab network, install a package, run a local service | Explicit scope and confirmation |
| High | Active security testing, firmware flashing, cloud changes | Isolated environment, authorization record and per-run approval |
| Critical | Destructive operations, credential extraction, persistence or disabling safeguards | Denied by default; not exposed as general-purpose modules |

## Mandatory controls

- No arbitrary unrestricted shell tool in the initial SDK.
- No ambient root, administrator or host filesystem access.
- Per-tool allow-listed capabilities and per-run authorization.
- Disposable containers/VMs or stronger platform isolation selected according to threat model.
- Network egress deny-by-default, with destination and protocol restrictions.
- CPU, memory, process, disk and time quotas.
- Signed manifests and verified artifacts.
- Secrets supplied through scoped secret handles, never environment dumps or logs.
- Cancellation, timeout and cleanup on failure.
- Audit records for who/what/when/scope/result, minimizing sensitive payload capture.
- Prompt-injection-resistant separation between model suggestions and permission decisions.

## AI integration

NP.ai may recommend tools, explain output and draft workflows. AI output is untrusted input. It cannot grant capabilities, expand target scope or approve its own actions. The user and policy broker remain authoritative.

## Cybersecurity research

The platform supports authorized security education, defensive assessment, forensics, malware analysis in isolation and controlled lab ranges. Tool design must prevent accidental execution against third-party targets. High-risk workflows require an explicit target allow-list and authorization evidence.

## Release gate

No host-execution backend is production-ready until threat modelling, sandbox escape review, capability enforcement, adversarial tests, cleanup tests and independent security review are complete.
