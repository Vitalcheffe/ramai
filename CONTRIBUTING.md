# Contributing

## Setup

```bash
git clone https://github.com/Vitalcheffe/ramai.git
cd ramai
pip install -e . pytest
python -m pytest tests/
```

## Before you PR

- Run `python -m pytest tests/` — all 149 tests must pass
- If you add a feature, add tests for it
- Keep docstrings short (one line for modules, only on complex functions)
- Commit messages: mix of conventional and casual is fine

## What I'm looking for

- Bug reports with reproduction steps
- New Rami variants (config presets)
- Improvements to the vision pipeline
- Better AI strategies (the Champion's TD error is stuck at 0.5)

## What I'm not looking for

- Refactor-only PRs
- Changes to the test framework
- Formatting changes without functional changes
