# GitHub Repo Kit Design

**Date:** 2026-03-28

## Objective

Add a practical full GitHub-ready repository kit to `Exness_Bot` without changing the project into a packaged library or overcomplicating the current script-first workflow.

## Recommended Approach

Use a practical full repo kit:

- keep the repository as an application repo, not a PyPI package
- add standard GitHub/community files that public repositories are expected to have
- codify setup and lightweight validation with `requirements.txt` plus a minimal CI workflow
- refresh README and long-form docs only where they drift from current behavior
- preserve the existing template-first credential workflow for MT5 bot files

## Alternatives Considered

### Minimal public repo kit

Add only legal and basic documentation files.

Pros:
- least work
- minimal maintenance

Cons:
- weaker contributor guidance
- no automated validation
- less complete public repository presentation

### Heavyweight maintainer kit

Add packaging, release automation, lint frameworks, and stricter contribution automation.

Pros:
- stronger engineering controls
- better long-term automation if the project becomes a library

Cons:
- higher maintenance burden
- unnecessary complexity for a script-first MT5 bot repo
- would imply a distribution model this project does not currently use

## Scope

### Repository essentials

- `LICENSE` with MIT terms and `Copyright (c) 2026 Sithu Win San`
- `requirements.txt`
- `.editorconfig`
- `.gitattributes`
- fix `.gitignore` so `.github/` is versioned correctly

### GitHub community files

- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `CODEOWNERS`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/pull_request_template.md`

### CI

Add a lightweight Windows GitHub Actions workflow that:

- installs Python
- installs dependencies from `requirements.txt`
- compiles tracked Python files
- runs `tests/test_daily_loss_scope.py`

This intentionally avoids pretending MT5 integration can run inside CI.

### Documentation refresh

- keep `README.md` as the front door
- keep detailed usage and operations detail in `docs/`
- update docs only where current runtime/setup behavior would otherwise be stale or contradictory
- add a changelog entry for repo-maintenance and contributor workflow improvements

## Design Principles

- favor practical contributor ergonomics over enterprise-style process
- document the credential/template workflow prominently to reduce accidental secret commits
- keep CI honest and lightweight
- avoid adding packaging/release infrastructure the project does not need
- preserve existing project-specific instructions in `CLAUDE.md` and the workspace skill files

## Validation Plan

- verify local links and referenced files still exist
- run `python -m py_compile` against tracked Python sources and templates
- run `python -m unittest discover -s tests -p "test_*.py"`
- review `git status --short` to confirm the intended tracked file set
