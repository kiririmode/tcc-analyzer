ユーザに対しては日本語で回答すること
ソースコードやコメント等は英語で記載すること

# This Product

A Python CLI tool for analyzing and visualizing your time management with TaskChute Cloud logs.
It provides individuals with insights on task completion, time allocation, and categories.
Key features: daily/weekly/monthly breakdowns, category-based analysis, and visualization of concentration trends.

## Architecture

- **CLI Interface**: Command-line interface with multiple subcommands for different log types
- **Multiple Log Types**: Support for various log formats, each handled by dedicated subcommands
- **Subcommand Structure**: Each log type has its own analysis pipeline and visualization options

# Development Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

## Core Development Rules

1. Package Management
   - ONLY use uv, NEVER pip
   - Installation: `uv add package`
   - Running tools: `uv run tool`
   - Upgrading: `uv add --dev package --upgrade-package package`
   - FORBIDDEN: `uv pip install`, `@latest` syntax

2. Code Quality
   - Type hints required for all code
   - Public APIs must have docstrings
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 88 chars maximum
   - **Cyclomatic Complexity**: Maximum CCN of 10 per function
     - Check with: `uv run lizard src/vtt2minutes --CCN 10`
     - Functions exceeding CCN 10 must be refactored into smaller functions
     - CI automatically monitors complexity and fails builds with CCN > 10
   - **Code Similarity**: Monitor and reduce code duplication
     - Check with: `similarity-py src --threshold 0.85 --min-lines 8 --print`
     - Target: Keep function similarity below 85% for maintainability
     - Functions with ≥85% similarity and ≥8 lines must be refactored
     - Extract common patterns into shared utility functions
     - Use `similarity-py src --threshold 0.85 --min-lines 8` for analysis
     - Review and refactor identified duplicates immediately
   - **File Length Limits**: Keep Python files manageable
     - **Maximum Lines**: No Python file should exceed 600 lines (including tests)
     - Check with: `python scripts/check_file_length.py`
     - Files exceeding 600 lines should be refactored into smaller modules
     - Consider extracting classes, functions, or logical components
     - Maintain clear separation of concerns
     - Large test files should be split by test categories or functionality

3. Testing Requirements
   - Framework: `uv run --frozen pytest`
   - Async testing: use anyio, not asyncio
   - Coverage: test edge cases and errors
   - New features require tests
   - Bug fixes require regression tests
   - **Coverage Standards**:
     - **Overall Coverage**: Project must maintain at least 85% overall test coverage
     - **Class Coverage**: Each class must maintain at least 85% individual coverage
     - **File Coverage**: Each source file must maintain at least 85% test coverage
     - Check with: `uv run --frozen pytest --cov=src --cov-report=term-missing`
     - Files or classes below 85% coverage will block commits
     - Exclude only justifiable cases (e.g., __main__.py, error handling paths)
     - **Coverage Monitoring**: Use `uv run --frozen pytest --cov=src --cov-report=html` for detailed class-by-class coverage analysis

- For commits fixing bugs or adding features based on user reports add:
```bash
  git commit --trailer "Reported-by:<name>"
  ```
  Where `<name>` is the name of the user.

- For commits related to a Github issue, add
  ```bash
  git commit --trailer "Github-Issue:#<number>"
  ```
- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Pull Requests

- Create a detailed message of what changed. Focus on the high level description of
  the problem it tries to solve, and how it is solved. Don't go into the specifics of the
  code unless it adds clarity.

- Always add `jerome3o-anthropic` and `jspahrsummers` as reviewer.

- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Pre-commit Hooks

- Pre-commit hooks are automatically installed and run quality checks before each commit
- The hooks check: formatting (ruff), linting (ruff), type checking (pyright), tests (pytest), and cyclomatic complexity (lizard)
- If any check fails, the commit is blocked until issues are resolved
- To install hooks after cloning: `./scripts/setup-hooks.sh`
- To run manually: `uv run --frozen pre-commit run --all-files`
- To bypass temporarily (not recommended): `git commit --no-verify`
- **Quality Gates**: Pre-commit hooks enforce:
  - Code formatting and linting (ruff)
  - Type checking (pyright)
  - Test coverage ≥85% per class and overall
  - Cyclomatic complexity ≤10 per function
  - File length ≤600 lines per Python file

## Python Tools

## Code Formatting

1. Ruff
   - Format: `uv run --frozen ruff format .`
   - Check: `uv run --frozen ruff check .`
   - Fix: `uv run --frozen ruff check . --fix`
   - Critical issues:
     - Line length (88 chars)
     - Import sorting (I001)
     - Unused imports
   - Line wrapping:
     - Strings: use parentheses
     - Function calls: multi-line with proper indent
     - Imports: split into multiple lines

2. Type Checking
   - Tool: `uv run --frozen pyright`
   - Strict mode enabled with comprehensive error reporting
   - Requirements:
     - Complete type annotations for all functions
     - Explicit None checks for Optional types
     - Type narrowing for union types
     - pandas-stubs installed for pandas type support
   - Configuration in pyproject.toml under [tool.pyright]

3. Pre-commit Setup
   - Install: `uv add --dev pre-commit`
   - Config: `.pre-commit-config.yaml`
   - Runs automatically on git commit
   - Tools included:
     - Ruff (linting and formatting)
     - Pyright (type checking)
     - Pytest (test execution)
     - Standard hooks (trailing whitespace, end-of-file, yaml check, etc.)
   - Manual run: `uv run --frozen pre-commit run --all-files`

## Error Resolution

1. CI Failures
   - Fix order:
     1. Formatting
     2. Type errors
     3. Linting
   - Type errors:
     - Get full line context
     - Check Optional types
     - Add type narrowing
     - Verify function signatures

2. Common Issues
   - Line length:
     - Break strings with parentheses
     - Multi-line function calls
     - Split imports
   - Types:
     - Add None checks
     - Narrow string types
     - Match existing patterns
   - Pytest:
     - If the tests aren't finding the anyio pytest mark, try adding PYTEST_DISABLE_PLUGIN_AUTOLOAD=""
       to the start of the pytest run command eg:
       `PYTEST_DISABLE_PLUGIN_AUTOLOAD="" uv run --frozen pytest`

3. Best Practices
   - Check git status before commits
   - Run formatters before type checks
   - Keep changes minimal
   - Follow existing patterns
   - Document public APIs
   - Test thoroughly

## Continuous Integration

- GitHub Actions workflow: `.github/workflows/ci.yml`
- Runs on: push to main, pull requests
- Python versions tested: 3.10, 3.11, 3.12
- Jobs:
  1. **Test Job**: Runs ruff linting, ruff formatting, pyright type checking, pytest with coverage
- Code coverage reporting with Codecov integration
- All checks must pass for PR merge
