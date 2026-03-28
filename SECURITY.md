# Security Policy

## Supported Versions

This project currently supports security fixes on the active `main` branch.

| Version | Supported |
| --- | --- |
| `main` | Yes |
| Older snapshots and tags | No |

## Reporting a Vulnerability

Please do not open a public GitHub issue for security-sensitive problems.

Examples:
- exposed MT5 credentials or account numbers
- hardcoded secrets committed by mistake
- vulnerable dependency or unsafe secret-handling flow
- a bug that could cause unauthorized trading behavior or unsafe account exposure

Preferred process:

1. Use GitHub private vulnerability reporting if it is enabled for this repository.
2. If private reporting is unavailable, contact the repository owner privately through GitHub before disclosing details publicly.
3. Include:
   - a short summary of the issue
   - affected files or workflow
   - reproduction steps if safe to share
   - likely impact
   - any immediate mitigation you recommend

## Secret Handling Expectations

- Never publish live MT5 `LOGIN`, `PASSWORD`, or private broker details in issues, pull requests, or screenshots.
- Treat local `*_grid_bot.py` files and `nas100_grid_bot.py` as secret-bearing local files.
- If credentials are exposed, rotate them immediately and remove them from any public history as soon as possible.
- Redact account IDs, passwords, and sensitive log excerpts before sharing diagnostics.

## Response Goals

The project will aim to:
- acknowledge valid reports promptly
- confirm whether the issue is reproducible
- communicate mitigation or fix status when possible
- credit reporters if they want public acknowledgment after a fix is available
