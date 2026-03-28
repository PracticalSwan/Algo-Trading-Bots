# GitHub Repo Kit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a full but practical GitHub/public-repository kit for `Exness_Bot`, codify setup and lightweight validation, and refresh repository documentation so it matches the current project state.

**Architecture:** Keep `Exness_Bot` as a script-first MT5 automation repository. Add repository-community files, GitHub templates, and a Windows-focused CI workflow around the existing codebase without introducing packaging or fake integration testing. Update the front-door README and supporting docs so legal, contribution, setup, and safety guidance are all accurate and easy to find.

**Tech Stack:** Python 3, MetaTrader5, pandas, numpy, unittest, GitHub Actions, Markdown, PowerShell-oriented setup commands

---

### Task 1: Add repository hygiene and GitHub metadata files

**Files:**
- Create: `LICENSE`
- Create: `requirements.txt`
- Create: `.editorconfig`
- Create: `.gitattributes`
- Create: `CODEOWNERS`
- Modify: `.gitignore`

**Step 1: Write the files**

Add the MIT license, dependency manifest, editor defaults, text normalization rules, code ownership, and fix `.gitignore` so `.github/` is no longer ignored.

**Step 2: Review tracked/ignored behavior**

Run: `git check-ignore -v .github/workflows/ci.yml`
Expected: no ignore match after the `.gitignore` fix.

**Step 3: Commit-ready review**

Confirm the files support the current repo model:
- no packaging metadata
- no secrets in tracked files
- `.github/skills/` remains versioned

### Task 2: Add community and GitHub workflow templates

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `SECURITY.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/pull_request_template.md`
- Create: `.github/workflows/ci.yml`

**Step 1: Write the docs and templates**

Add contributor guidance, behavior standards, security reporting guidance, issue/PR templates, and a lightweight Windows CI workflow.

**Step 2: Keep the workflow honest**

The CI workflow must:
- install Python
- install `requirements.txt`
- compile tracked `.py` and `.template.py` files
- run `python -m unittest tests.test_daily_loss_scope`

**Step 3: Sanity check the workflow file**

Review the workflow for:
- correct Windows runner choice
- no MT5 live-login assumptions
- commands that match the repository layout exactly

### Task 3: Refresh README and supporting docs

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `CLAUDE.md`
- Modify: `docs/mt5-setup.md`
- Modify: `docs/operations-and-troubleshooting.md`
- Modify: `docs/strategy-and-profiles.md`

**Step 1: Refresh front-door documentation**

Update `README.md` to include:
- clearer repo summary
- MIT licensing note
- `requirements.txt` setup flow
- contributor/development entry points
- current docs map and safety posture

**Step 2: Refresh supporting docs where drift exists**

Update supporting docs so they reflect:
- `requirements.txt` as the standard install path
- current daily-loss and trim-to-core behavior
- current contributor/verification workflow
- the presence of lightweight CI rather than “no CI/CD”

**Step 3: Add changelog coverage**

Record the repository/community/CI additions in `CHANGELOG.md` without implying trading-logic changes.

### Task 4: Verify the repository state and document the session

**Files:**
- Modify: `lessons.md` if a concise implementation lesson is warranted

**Step 1: Run validation**

Run:
- `python -m py_compile daily_loss_scope.py forex_grid_engine.py eurusd_grid_bot.py.template gbpusd_grid_bot.py.template usdjpy_grid_bot.py.template audusd_grid_bot.py.template nzdusd_grid_bot.py.template usdcad_grid_bot.py.template nas100_grid_bot.py.template`
- `python -m unittest tests.test_daily_loss_scope`

Expected:
- `py_compile` exits successfully
- tests pass

**Step 2: Check docs and repo surface**

Run:
- `git status --short`
- `git check-ignore -v .github/workflows/ci.yml`

Expected:
- only intended repo-kit/doc files appear as changes
- `.github/workflows/ci.yml` is not ignored

**Step 3: Update project memory**

Record the repo-kit additions, `.gitignore` fix, new contributor workflow, and verification results in Serena memory for future sessions.
