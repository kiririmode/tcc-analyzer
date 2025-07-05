# TCC Analyzer

[![CI](https://github.com/kiririmode/tcc-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/kiririmode/tcc-analyzer/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kiririmode/tcc-analyzer/branch/main/graph/badge.svg)](https://codecov.io/gh/kiririmode/tcc-analyzer)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Python CLI tool for analyzing and visualizing your time management with TaskChute Cloud logs. It provides individuals with insights on task completion, time allocation, and categories.

## ✨ Features

- **📊 Multiple Analysis Types**: Analyze by project, mode, or project×mode combinations
- **📈 Percentage Tracking**: Calculate time allocation percentages against a base time
- **🎨 Multiple Output Formats**: Rich tables, JSON, and CSV output
- **🔄 Flexible Sorting**: Sort by time, project name, or mode name
- **⚡ Fast Processing**: Efficient CSV parsing with encoding detection
- **🎯 Focus Insights**: Track concentration trends and productivity patterns

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/kiririmode/tcc-analyzer.git
cd tcc-analyzer

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Basic Usage

```bash
# Analyze by project (default)
uv run -m src.tcc_analyzer.cli task logs/tasks.csv

# Analyze by mode with percentage calculation
uv run -m src.tcc_analyzer.cli task logs/tasks.csv \
  --group-by mode \
  --base-time 08:00:00

# Export to JSON format
uv run -m src.tcc_analyzer.cli task logs/tasks.csv \
  --output-format json \
  --sort-by time \
  --reverse
```

## 📖 Usage Examples

### Project Analysis with Percentage
```bash
uv run -m src.tcc_analyzer.cli task logs/tasks.csv \
  --base-time 08:00:00 \
  --sort-by time \
  --reverse
```

Output:
```
            TaskChute Cloud - Project Time Analysis
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Project              ┃ Total Time ┃ Task Count ┃ Percentage ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ 💻 Development       │ 03:45:49   │ 7          │ 47.0%      │
│ 📊 Research          │ 03:34:18   │ 4          │ 44.6%      │
│ 📋 Administration    │ 02:23:58   │ 11         │ 30.0%      │
│ 🏠 Personal          │ 01:27:13   │ 18         │ 18.2%      │
└──────────────────────┴────────────┴────────────┴────────────┘
```

### Mode Analysis
```bash
uv run -m src.tcc_analyzer.cli task logs/tasks.csv \
  --group-by mode \
  --output-format json
```

### Project×Mode Combination
```bash
uv run -m src.tcc_analyzer.cli task logs/tasks.csv \
  --group-by project-mode \
  --output-format csv \
  --base-time 08:00:00
```

## 🛠️ CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--group-by` | `project\|mode\|project-mode` | `project` | Group results by analysis type |
| `--sort-by` | `time\|project\|mode` | `time` | Sort results by specified field |
| `--reverse` | flag | `false` | Reverse the sort order |
| `--output-format` | `table\|json\|csv` | `table` | Output format |
| `--base-time` | `HH:MM:SS` | - | Base time for percentage calculation |

## 📋 Requirements

- Python 3.10+
- TaskChute Cloud CSV export files
- Dependencies managed with [uv](https://github.com/astral-sh/uv)

## 🏗️ Development

### Setup

```bash
# Clone and setup development environment
git clone https://github.com/kiririmode/tcc-analyzer.git
cd tcc-analyzer

# Install development dependencies
uv sync --all-extras --dev

# Install pre-commit hooks
./scripts/setup-hooks.sh
```

### Code Quality

This project maintains high code quality standards:

```bash
# Formatting and linting
uv run ruff format .
uv run ruff check . --fix

# Type checking
uv run pyright

# Testing with coverage
uv run pytest --cov=src --cov-report=term-missing

# Code complexity check
uv run lizard src --CCN 10
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_task_analyzer.py -v
```

## 📂 Project Structure

```
tcc-analyzer/
├── src/
│   └── tcc_analyzer/
│       ├── __init__.py
│       ├── cli.py              # Command line interface
│       └── analyzers/
│           ├── __init__.py
│           └── task_analyzer.py # Core analysis logic
├── tests/
│   └── test_task_analyzer.py   # Comprehensive test suite
├── logs/                       # Sample CSV files
├── scripts/                    # Development scripts
├── .github/workflows/          # CI/CD configuration
├── pyproject.toml              # Project configuration
└── README.md
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following our code quality standards
4. **Add tests** for new functionality
5. **Ensure all checks pass**: `uv run pytest && uv run ruff check . && uv run pyright`
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Development Guidelines

- **Code Quality**: All code must pass ruff formatting, linting, and pyright type checking
- **Testing**: Maintain >85% test coverage for all source files
- **Complexity**: Keep cyclomatic complexity ≤10 per function
- **Documentation**: Add docstrings for all public APIs
- **Commits**: Use conventional commit messages

## 📊 CSV Format

TCC Analyzer expects TaskChute Cloud CSV exports with these columns:
- `プロジェクト名` (Project Name)
- `モード名` (Mode Name)
- `実績時間` (Actual Time in HH:MM:SS format)
- Additional columns are supported but not required

## 🐛 Troubleshooting

### Common Issues

**Encoding Errors**
```bash
# TCC Analyzer automatically handles UTF-8 and Shift-JIS encodings
# If you encounter encoding issues, ensure your CSV is in one of these formats
```

**Time Format Issues**
```bash
# Ensure time values are in HH:MM:SS format
# Invalid formats will be treated as 00:00:00
```

**Memory Usage**
```bash
# For very large CSV files (>100MB), consider splitting the file
# or processing in smaller date ranges
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [TaskChute Cloud](https://taskchute.cloud/) for time management methodology
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Click](https://click.palletsprojects.com/) for CLI framework
- [Pandas](https://pandas.pydata.org/) for data processing
- [uv](https://github.com/astral-sh/uv) for fast Python package management

## 📈 Roadmap

- [ ] Interactive dashboard with charts
- [ ] Time trend analysis over multiple days
- [ ] Export to additional formats (Excel, PDF)
- [ ] Integration with other time tracking tools
- [ ] Advanced filtering and search capabilities
- [ ] Productivity metrics and recommendations

---

<div align="center">
  <sub>Built with ❤️ for better time management</sub>
</div>
