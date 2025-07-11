#!/usr/bin/env python3
"""Check Python files for excessive line count."""

import argparse
import sys
from pathlib import Path
from typing import List


def check_file_length(file_path: Path, max_lines: int = 600) -> tuple[bool, int]:
    """Check if file exceeds maximum line count.

    Args:
        file_path: Path to the file to check
        max_lines: Maximum allowed lines (default: 600)

    Returns:
        Tuple of (is_violation, actual_line_count)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        return line_count > max_lines, line_count
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False, 0


def main() -> int:
    """Main function to check file lengths."""
    parser = argparse.ArgumentParser(
        description="Check Python files for excessive line count"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (if not specified, check all .py files in src/)"
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=600,
        help="Maximum allowed lines per file (default: 600)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Patterns to exclude (can be used multiple times)"
    )

    args = parser.parse_args()

    # Determine files to check
    if args.files:
        files_to_check = [Path(f) for f in args.files if f.endswith('.py')]
    else:
        # Check all Python files in src/ and tests/
        files_to_check = []
        for directory in ["src", "tests"]:
            dir_path = Path(directory)
            if dir_path.exists():
                files_to_check.extend(list(dir_path.rglob("*.py")))

        if not files_to_check:
            print("No Python files found in src/ or tests/ directories", file=sys.stderr)
            return 1

    # Apply exclusions
    excluded_patterns = args.exclude
    if excluded_patterns:
        filtered_files = []
        for file_path in files_to_check:
            file_str = str(file_path)
            if not any(pattern in file_str for pattern in excluded_patterns):
                filtered_files.append(file_path)
        files_to_check = filtered_files

    violations: List[tuple[Path, int]] = []

    for file_path in files_to_check:
        if not file_path.exists():
            continue

        is_violation, line_count = check_file_length(file_path, args.max_lines)
        if is_violation:
            violations.append((file_path, line_count))

    # Report results
    if violations:
        print(f"❌ Files exceeding {args.max_lines} lines:")
        for file_path, line_count in violations:
            print(f"  {file_path}: {line_count} lines")
        print(f"\n💡 Consider refactoring large files into smaller modules")
        return 1
    else:
        print(f"✅ All Python files are within {args.max_lines} line limit")
        return 0


if __name__ == "__main__":
    sys.exit(main())
