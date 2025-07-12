#!/usr/bin/env python3
"""Check Python files for excessive line count."""

import argparse
import sys
from pathlib import Path


def check_file_length(file_path: Path, max_lines: int = 600) -> tuple[bool, int]:
    """Check if file exceeds maximum line count.

    Args:
        file_path: Path to the file to check
        max_lines: Maximum allowed lines (default: 600)

    Returns:
        Tuple of (is_violation, actual_line_count)

    """
    try:
        with open(file_path, encoding="utf-8") as f:
            line_count = sum(1 for _ in f)
        return line_count > max_lines, line_count
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False, 0


def main() -> int:
    """Check file lengths and report violations."""
    args = _parse_arguments()
    files_to_check = _get_files_to_check(args)

    if not files_to_check:
        return 1

    violations = _check_files(files_to_check, args.max_lines)
    return _report_results(violations, args.max_lines)


def _parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Check Python files for excessive line count"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (if not specified, check all .py files in src/)",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=600,
        help="Maximum allowed lines per file (default: 600)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Patterns to exclude (can be used multiple times)",
    )
    return parser.parse_args()


def _get_files_to_check(args):
    """Get list of files to check."""
    if args.files:
        return [Path(f) for f in args.files if f.endswith(".py")]

    files_to_check = []
    for directory in ["src", "tests"]:
        dir_path = Path(directory)
        if dir_path.exists():
            files_to_check.extend(list(dir_path.rglob("*.py")))

    if not files_to_check:
        print("No Python files found in src/ or tests/ directories", file=sys.stderr)
        return []

    return _apply_exclusions(files_to_check, args.exclude)


def _apply_exclusions(files_to_check, excluded_patterns):
    """Apply exclusion patterns to file list."""
    if not excluded_patterns:
        return files_to_check

    filtered_files = []
    for file_path in files_to_check:
        file_str = str(file_path)
        if not any(pattern in file_str for pattern in excluded_patterns):
            filtered_files.append(file_path)
    return filtered_files


def _check_files(files_to_check, max_lines):
    """Check files for violations."""
    violations = []
    for file_path in files_to_check:
        if not file_path.exists():
            continue

        is_violation, line_count = check_file_length(file_path, max_lines)
        if is_violation:
            violations.append((file_path, line_count))
    return violations


def _report_results(violations, max_lines):
    """Report check results."""
    if violations:
        print(f"❌ Files exceeding {max_lines} lines:")
        for file_path, line_count in violations:
            print(f"  {file_path}: {line_count} lines")
        print("\n💡 Consider refactoring large files into smaller modules")
        return 1
    else:
        print(f"✅ All Python files are within {max_lines} line limit")
        return 0


if __name__ == "__main__":
    sys.exit(main())
