# Security

Report vulnerabilities privately via
[GitHub Security Advisories](https://github.com/lumitive/lumi-style/security/advisories/new)
— please do not open a public issue for a security finding.

Scope notes: this repository ships development/CI scripts (Python standard
library; optional local Playwright for rendering checks) and static design
assets. It contains no service, no network listener, and no credential
handling; CI runs a secret scan (`check_repo.py`'s secrets guard) on every
push. The `scripts/ops/emergency_merge.sh` runbook documents its own threat
model in its header comments.
