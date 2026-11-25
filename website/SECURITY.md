# Website security notes

- Do not put secrets in NEXT_PUBLIC_ variables or client components.
- Keep dependencies pinned and review automated dependency/security alerts.
- Use HTTPS at the deployment edge.
- Configure a restrictive Content Security Policy and other security headers at deployment after inventorying required asset origins.
- Avoid third-party analytics until a privacy review and consent decision are complete.
- Keep contact handling server-side with validation, rate limiting and spam controls; no unconnected form is presented.
- Treat all external links and future user-submitted content as untrusted.
- Report vulnerabilities privately to the repository owner; do not publish exploitable details before remediation.
- Before production, verify domain ownership, legal entity status, privacy notice, terms and data-retention practices.
