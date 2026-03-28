# Contributing

Thanks for helping improve `Exness_Bot`.

This repository is a script-first MT5 automation project, so good contributions are usually small, explicit, and careful about safety, documentation, and secret handling.

## Before you start

- Read [README.md](README.md) for the project overview and quick start.
- Use [docs/mt5-setup.md](docs/mt5-setup.md) for terminal and broker setup.
- Use [docs/operations-and-troubleshooting.md](docs/operations-and-troubleshooting.md) for runtime behavior and common failure modes.
- Never commit live MT5 credentials, account numbers, or sensitive logs.

## Local setup

1. Create and activate a virtual environment if you want an isolated Python environment.
2. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Create a local bot file from a tracked template:

```powershell
Copy-Item usdjpy_grid_bot.py.template usdjpy_grid_bot.py
```

4. Fill in the local file with your own MT5 credentials.

## Credential and template workflow

Tracked source of truth:
- `*_grid_bot.py.template`
- `nas100_grid_bot.py.template`
- shared files such as `forex_grid_engine.py`

Local-only files:
- `*_grid_bot.py`
- `nas100_grid_bot.py`

Rules:
- Edit the `.template.py` file first when changing wrapper logic or config.
- Sync the same change into your local credential-bearing bot file after that.
- Do not commit local bot files with credentials.
- Do not paste real account numbers, passwords, or private broker details into issues or pull requests.

## Validation

Run the same lightweight checks used by CI before opening a pull request:

```powershell
@'
import py_compile

files = [
    "daily_loss_scope.py",
    "forex_grid_engine.py",
    "eurusd_grid_bot.py.template",
    "gbpusd_grid_bot.py.template",
    "usdjpy_grid_bot.py.template",
    "audusd_grid_bot.py.template",
    "nzdusd_grid_bot.py.template",
    "usdcad_grid_bot.py.template",
    "nas100_grid_bot.py.template",
    "tests/test_daily_loss_scope.py",
]

for path in files:
    py_compile.compile(path, doraise=True)

print(f"Compiled {len(files)} files successfully")
'@ | python -

python -m unittest discover -s tests -p "test_*.py" -v
```

## Documentation expectations

Update docs when your change affects:
- behavior
- safety controls
- setup steps
- validation steps
- contributor workflow

At minimum, check whether `README.md`, `CHANGELOG.md`, and any touched `docs/` pages need an update.

## Pull request guidelines

- Keep the change focused.
- Explain the problem and the chosen fix clearly.
- Mention any setup or documentation changes.
- Include validation notes.
- If you changed trading behavior, call that out explicitly.

## What not to contribute

- Hardcoded live credentials
- Commits that treat local credential-bearing bot files as tracked source of truth
- Changes that loosen safety protections without documentation
- Large unrelated refactors mixed into one PR
