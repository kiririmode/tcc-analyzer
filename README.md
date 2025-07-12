# TCC Analyzer

[![CI](https://github.com/kiririmode/tcc-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/kiririmode/tcc-analyzer/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kiririmode/tcc-analyzer/branch/main/graph/badge.svg)](https://codecov.io/gh/kiririmode/tcc-analyzer)

A Python CLI tool for analyzing and visualizing your time management with TaskChute Cloud logs.

## Features

- 📊 Analyze by project, mode, or project×mode combinations
- 📈 Calculate time allocation percentages against a base time
- 📋 Automatic total row with percentage calculations
- 💬 Slack-formatted output for team sharing
- 🎨 Multiple output formats: Rich tables, JSON, CSV, and Slack
- ⚡ Fast CSV processing with encoding detection

## Installation

```bash
git clone https://github.com/kiririmode/tcc-analyzer.git
cd tcc-analyzer
uv sync
```

## Basic Usage

```bash
# Analyze by project
uv run -m src.tcc_analyzer.cli task logs/tasks.csv

# Analyze with percentage and totals
uv run -m src.tcc_analyzer.cli task logs/tasks.csv --base-time 08:00:00

# Slack format for sharing
uv run -m src.tcc_analyzer.cli task logs/tasks.csv --output-format slack
```

## Output Examples

### Table Format (Default)
```
            TaskChute Cloud - Project Time Analysis
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Project              ┃ Total Time ┃ Task Count ┃ Percentage ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 💻 Development       │ 03:45:49   │ 7          │ 38.5%      │
│ 📊 Research          │ 03:34:18   │ 4          │ 36.7%      │
│ 📋 Administration    │ 02:23:58   │ 11         │ 24.8%      │
├──────────────────────┼────────────┼────────────┼────────────┤
│ Total                │ 09:44:05   │ 22         │ 100.0%     │
└──────────────────────┴────────────┴────────────┴────────────┘
```

### Slack Format
```
*TaskChute Cloud - Project Time Analysis*

*Development*: 03:45:49 (7 tasks) - 38.5%
*Research*: 03:34:18 (4 tasks) - 36.7%
*Administration*: 02:23:58 (11 tasks) - 24.8%
──────────────────────────────
*Total*: 09:44:05 (22 tasks) - 100.0%
```

## CLI Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--group-by` | `project`, `mode`, `project-mode` | `project` | Group results by analysis type |
| `--sort-by` | `time`, `project`, `mode` | `time` | Sort results by field |
| `--reverse` | flag | `false` | Reverse sort order |
| `--output-format` | `table`, `json`, `csv`, `slack` | `table` | Output format |
| `--base-time` | `HH:MM:SS` | - | Base time for percentage calculation |

## Development

```bash
# Setup development environment
uv sync --all-extras --dev
./scripts/setup-hooks.sh

# Run tests
uv run pytest

# Code quality checks
uv run ruff format .
uv run ruff check . --fix
uv run pyright
```

## CSV Format

TaskChute Cloud CSV exports with these columns:
- `プロジェクト名` (Project Name)
- `モード名` (Mode Name)
- `実績時間` (Actual Time in HH:MM:SS format)

## License

MIT License - see [LICENSE](LICENSE) file for details.
