"""Tests for TaskAnalyzer."""

import io
import json
import math
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzer:
    """Test class for TaskAnalyzer."""

    def test_parse_time_duration_valid(self) -> None:
        """Test parsing valid time duration strings."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test HH:MM:SS format
        assert analyzer._parse_time_duration("01:30:45") == timedelta(
            hours=1, minutes=30, seconds=45
        )
        assert analyzer._parse_time_duration("00:00") == timedelta(0)
        assert analyzer._parse_time_duration("12:59:59") == timedelta(
            hours=12, minutes=59, seconds=59
        )

        # Test HH:MM format (seconds omitted)
        assert analyzer._parse_time_duration("01:30") == timedelta(
            hours=1, minutes=30, seconds=0
        )
        assert analyzer._parse_time_duration("08:00") == timedelta(
            hours=8, minutes=0, seconds=0
        )
        assert analyzer._parse_time_duration("00:45") == timedelta(
            hours=0, minutes=45, seconds=0
        )

    def test_parse_time_duration_invalid(self) -> None:
        """Test parsing invalid time duration strings."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        assert analyzer._parse_time_duration("") == timedelta(0)
        assert analyzer._parse_time_duration("invalid") == timedelta(0)
        assert analyzer._parse_time_duration("1:2") == timedelta(0)  # Not HH:MM format
        assert analyzer._parse_time_duration("25:70") == timedelta(0)  # Invalid minutes
        assert analyzer._parse_time_duration("abc:def") == timedelta(0)  # Non-numeric
        assert analyzer._parse_time_duration("12:60") == timedelta(
            0
        )  # Minutes out of range
        assert analyzer._parse_time_duration("12:59:60") == timedelta(
            0
        )  # Seconds out of range

    def test_parse_time_duration_nan(self) -> None:
        """Test parsing NaN values."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test with float NaN which is more common in real data
        assert analyzer._parse_time_duration(math.nan) == timedelta(0)

    def test_format_duration(self) -> None:
        """Test formatting timedelta objects."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        assert (
            analyzer._format_duration(timedelta(hours=1, minutes=30, seconds=45))
            == "01:30"
        )
        assert analyzer._format_duration(timedelta(0)) == "00:00"

    def test_calculate_percentage(self) -> None:
        """Test percentage calculation against base time."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test basic percentage calculation
        duration = timedelta(hours=1)  # 1 hour
        base_time = "08:00"  # 8 hours
        percentage = analyzer._calculate_percentage(duration, base_time)
        assert percentage == 12.5  # 1/8 * 100 = 12.5%

        # Test 100% case
        duration = timedelta(hours=8)
        percentage = analyzer._calculate_percentage(duration, base_time)
        assert percentage == 100.0

        # Test zero base time (edge case)
        percentage = analyzer._calculate_percentage(duration, "00:00")
        assert percentage == 0.0

    def test_add_total_row_and_percentages(self) -> None:
        """Test adding total row and percentage columns to results."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test with project analysis results
        results = [
            {
                "project": "Project A",
                "total_time": "01:30",
                "total_seconds": 5400,
                "task_count": "2",
            },
            {
                "project": "Project B",
                "total_time": "00:30",
                "total_seconds": 1800,
                "task_count": "1",
            },
        ]

        updated_results = analyzer.add_total_row_and_percentages(results, "project")

        # Should have 3 rows now (2 original + 1 total)
        assert len(updated_results) == 3

        # Check that percentages were added to original rows
        assert updated_results[0]["percentage"] == "75.0%"  # 5400/7200 * 100
        assert updated_results[1]["percentage"] == "25.0%"  # 1800/7200 * 100

        # Check total row
        total_row = updated_results[2]
        assert total_row["project"] == "Total"
        assert (
            total_row["total_time"] == "02:00"
        )  # 5400 + 1800 = 7200 seconds = 2 hours
        assert total_row["total_seconds"] == 7200
        assert total_row["task_count"] == "3"  # 2 + 1
        assert total_row["percentage"] == "100.0%"

    def test_add_total_row_and_percentages_mode(self) -> None:
        """Test adding total row and percentages for mode analysis."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "mode": "Focus",
                "total_time": "02:00",
                "total_seconds": 7200,
                "task_count": "3",
            },
        ]

        updated_results = analyzer.add_total_row_and_percentages(results, "mode")

        assert len(updated_results) == 2
        assert updated_results[0]["percentage"] == "100.0%"

        # Check total row
        total_row = updated_results[1]
        assert total_row["mode"] == "Total"
        assert total_row["total_time"] == "02:00"
        assert total_row["percentage"] == "100.0%"

    def test_add_total_row_and_percentages_project_mode(self) -> None:
        """Test adding total row and percentages for project-mode analysis."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Project A",
                "mode": "Focus",
                "total_time": "01:00",
                "total_seconds": 3600,
                "task_count": "2",
                "project_mode": "Project A | Focus",
            },
            {
                "project": "Project A",
                "mode": "Meeting",
                "total_time": "00:30",
                "total_seconds": 1800,
                "task_count": "1",
                "project_mode": "Project A | Meeting",
            },
        ]

        updated_results = analyzer.add_total_row_and_percentages(
            results, "project-mode"
        )

        assert len(updated_results) == 3
        assert updated_results[0]["percentage"] == "66.7%"  # 3600/5400 * 100 ≈ 66.7%
        assert updated_results[1]["percentage"] == "33.3%"  # 1800/5400 * 100 ≈ 33.3%

        # Check total row
        total_row = updated_results[2]
        assert total_row["project"] == "Total"
        assert total_row["mode"] == "-"
        assert total_row["project_mode"] == "Total | -"
        assert (
            total_row["total_time"] == "01:30"
        )  # 3600 + 1800 = 5400 seconds = 1.5 hours
        assert total_row["percentage"] == "100.0%"

    def test_add_total_row_and_percentages_empty_results(self) -> None:
        """Test adding total row with empty results."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results: list[dict[str, Any]] = []
        updated_results = analyzer.add_total_row_and_percentages(results, "project")

        # Should return empty list unchanged
        assert len(updated_results) == 0

    def test_create_total_row(self) -> None:
        """Test creating total row for different analysis types."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test project analysis total row
        total_row = analyzer._create_total_row(
            timedelta(hours=2, minutes=30), 5, "project"
        )

        assert total_row["project"] == "Total"
        assert total_row["total_time"] == "02:30"
        assert total_row["total_seconds"] == 9000
        assert total_row["task_count"] == "5"
        assert total_row["percentage"] == "100.0%"

        # Test mode analysis total row
        total_row = analyzer._create_total_row(timedelta(hours=1), 3, "mode")

        assert total_row["mode"] == "Total"
        assert total_row["total_time"] == "01:00"

        # Test project-mode analysis total row
        total_row = analyzer._create_total_row(timedelta(minutes=45), 2, "project-mode")

        assert total_row["project"] == "Total"
        assert total_row["mode"] == "-"
        assert total_row["project_mode"] == "Total | -"

    def test_add_percentage_to_results(self) -> None:
        """Test adding percentage column to results."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Work",
                "total_time": "04:00",
                "total_seconds": 14400,  # 4 hours in seconds
                "task_count": "5",
            },
            {
                "project": "Study",
                "total_time": "02:00",
                "total_seconds": 7200,  # 2 hours in seconds
                "task_count": "3",
            },
        ]

        updated_results = analyzer._add_percentage_to_results(results, "08:00")

        assert len(updated_results) == 2
        assert updated_results[0]["percentage"] == "50.0%"  # 4/8 * 100
        assert updated_results[1]["percentage"] == "25.0%"  # 2/8 * 100

    def test_display_table_with_base_time(self) -> None:
        """Test table display includes base time in title."""
        # Create sample CSV data
        csv_content = (
            "プロジェクト名,モード名,実績時間\nWork,Focus,02:00\nStudy,Focus,01:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            # Add percentage to results for base time test
            results_with_percentage = analyzer._add_percentage_to_results(
                results, "08:00"
            )

            # Test that table creation includes base time in title
            table = analyzer._create_table(results_with_percentage, "project", "08:00")
            assert table.title is not None
            assert "Base: 08:00" in table.title

            # Test without base time
            table_no_base = analyzer._create_table(results, "project", None)
            assert table_no_base.title is not None
            assert "Base:" not in table_no_base.title

        finally:
            csv_path.unlink()

    def test_display_json_with_base_time(self) -> None:
        """Test JSON output includes base time metadata."""

        # Create sample CSV data
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            analyzer.display_json(results, "project", "08:00")

            # Restore stdout
            sys.stdout = sys.__stdout__

            # Parse JSON output
            output = json.loads(captured_output.getvalue())

            # Check that base_time and analysis_type are included
            assert "base_time" in output
            assert output["base_time"] == "08:00"
            assert "analysis_type" in output
            assert "results" in output

        finally:
            csv_path.unlink()

    def test_display_csv_with_base_time(self) -> None:
        """Test CSV output includes base time comment."""

        # Create sample CSV data
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            analyzer.display_csv(results, "project", "08:00")

            # Restore stdout
            sys.stdout = sys.__stdout__

            output_lines = captured_output.getvalue().strip().split("\n")

            # Check that first line contains base time comment
            assert output_lines[0] == "# Base Time: 08:00"
            assert "Percentage" in output_lines[1]  # Header line

        finally:
            csv_path.unlink()

    def test_encoding_fallback_to_shift_jis(self) -> None:
        """Test encoding fallback to Shift-JIS when UTF-8 fails."""
        # Create a CSV file with Shift-JIS encoding
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,01:00\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="shift-jis"
        ) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            # This should trigger the Shift-JIS fallback when UTF-8 fails
            data = analyzer._load_data()
            assert len(data) == 1
            assert data.iloc[0]["プロジェクト名"] == "Work"
        finally:
            csv_path.unlink()

    def test_date_parsing_with_datetime_columns(self) -> None:
        """Test date parsing when datetime columns exist."""
        csv_content = (
            "プロジェクト名,モード名,実績時間,開始日時,終了日時\n"
            "Work,Focus,01:00,2023-01-01 09:00,2023-01-01 10:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            data = analyzer._load_data()
            # Check that datetime columns are parsed
            assert "開始日時" in data.columns
            assert "終了日時" in data.columns
        finally:
            csv_path.unlink()

    def test_parse_time_duration_float_input(self) -> None:
        """Test parsing time duration with float input."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test with float input (should return 0)
        assert analyzer._parse_time_duration(123.45) == timedelta(0)

        # Test with non-string types
        assert analyzer._parse_time_duration(None) == timedelta(0)  # type: ignore

    def test_analyze_by_mode_empty_results(self) -> None:
        """Test mode analysis with empty or invalid data."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            ",Focus,01:00\n"  # Empty project name
            "Work,,01:00\n"  # Empty mode name
            "Work,Focus,\n"  # Empty time
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode()
            # Should only include the valid Focus mode entry
            assert len(results) == 1
            assert results[0]["mode"] == "Focus"
        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_invalid_data(self) -> None:
        """Test project-mode analysis with invalid data."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            ",Focus,01:00\n"  # Empty project name
            "Work,,01:00\n"  # Empty mode name
            "Work,Focus,invalid\n"  # Invalid time format
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode()
            # Should have one valid result (Work + Focus with invalid time becomes 0)
            assert len(results) == 1
            assert results[0]["project"] == "Work"
            assert results[0]["mode"] == "Focus"
        finally:
            csv_path.unlink()

    def test_display_table_without_base_time(self) -> None:
        """Test table display without base time."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,01:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            # Capture stdout to test display_table
            captured_output = io.StringIO()
            sys.stdout = captured_output

            analyzer.display_table(results, "project", None)

            # Restore stdout
            sys.stdout = sys.__stdout__

            output = captured_output.getvalue()
            assert "Project" in output and "Analysis" in output
            assert "Base:" not in output

        finally:
            csv_path.unlink()

    def test_display_json_without_base_time(self) -> None:
        """Test JSON display without base time."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,01:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            analyzer.display_json(results, "project", None)

            # Restore stdout
            sys.stdout = sys.__stdout__

            # Parse JSON output
            output = json.loads(captured_output.getvalue())

            # Should be a list, not an object with metadata
            assert isinstance(output, list)
            assert len(output) == 1  # type: ignore[misc]
            output_item = output[0]  # type: ignore[misc]
            assert output_item["project"] == "Work"

        finally:
            csv_path.unlink()

    def test_display_csv_without_base_time(self) -> None:
        """Test CSV display without base time."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,01:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            analyzer.display_csv(results, "project", None)

            # Restore stdout
            sys.stdout = sys.__stdout__

            output_lines = captured_output.getvalue().strip().split("\n")

            # Should not have base time comment
            assert not output_lines[0].startswith("# Base Time:")
            assert output_lines[0] == "Project,Total Time,Task Count"

        finally:
            csv_path.unlink()

    def test_base_time_without_seconds(self) -> None:
        """Test base time functionality with HH:MM format (no seconds)."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\nWork,Focus,02:00\nStudy,Focus,01:30\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            # Test with HH:MM format base time (no seconds)
            results_with_percentage = analyzer._add_percentage_to_results(
                results,
                "08:00",  # 8 hours without seconds
            )

            # Verify percentage calculations work correctly
            work_result = next(
                r for r in results_with_percentage if r["project"] == "Work"
            )
            study_result = next(
                r for r in results_with_percentage if r["project"] == "Study"
            )

            # Work: 2 hours / 8 hours = 25%
            assert work_result["percentage"] == "25.0%"
            # Study: 1.5 hours / 8 hours = 18.75%
            assert study_result["percentage"] == "18.8%"

        finally:
            csv_path.unlink()

    def test_analyze_by_project(self) -> None:
        """Test project analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間,開始日時,終了日時\n"
            "Project A,Mode 1,00:15,2025-07-01 09:00,2025-07-01 09:15\n"
            "Project A,Mode 1,00:10,2025-07-01 09:15,2025-07-01 09:25\n"
            "Project B,Mode 2,00:30,2025-07-01 10:00,2025-07-01 10:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            assert len(results) == 2

            # Check Project A (should have 00:25 total)
            project_a = next(r for r in results if r["project"] == "Project A")
            assert project_a["total_time"] == "00:25"
            assert project_a["task_count"] == "2"

            # Check Project B (should have 00:30 total)
            project_b = next(r for r in results if r["project"] == "Project B")
            assert project_b["total_time"] == "00:30"
            assert project_b["task_count"] == "1"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_sort_by_project(self) -> None:
        """Test project analysis with project name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Mode 1,00:15\n"
            "A Project,Mode 2,00:10\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project(sort_by="project")

            assert len(results) == 2
            assert results[0]["project"] == "A Project"
            assert results[1]["project"] == "Z Project"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_sort_by_name(self) -> None:
        """Test project analysis with legacy name sorting (backward compatibility)."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Mode 1,00:15\n"
            "A Project,Mode 2,00:10\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project(sort_by="name")

            assert len(results) == 2
            assert results[0]["project"] == "A Project"
            assert results[1]["project"] == "Z Project"

        finally:
            csv_path.unlink()

    def test_multiple_files_initialization(self) -> None:
        """Test initializing TaskAnalyzer with multiple CSV files."""
        csv_data1 = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Mode 1,01:30\n"
            "Project B,Mode 2,02:00\n"
        )
        csv_data2 = (
            "プロジェクト名,モード名,実績時間\n"
            "Project C,Mode 3,00:45\n"
            "Project A,Mode 1,01:00\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f1:
            f1.write(csv_data1)
            csv_path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f2:
            f2.write(csv_data2)
            csv_path2 = Path(f2.name)

        try:
            # Test with list of files
            analyzer = TaskAnalyzer([csv_path1, csv_path2])
            results = analyzer.analyze_by_project(sort_by="project")

            # Should have 3 projects (A, B, C)
            assert len(results) == 3

            # Project A should have combined time from both files
            project_a = next((r for r in results if r["project"] == "Project A"), None)
            assert project_a is not None
            assert project_a["total_seconds"] == 9000  # 1:30:00 + 1:00:00 = 2:30:00

        finally:
            csv_path1.unlink()
            csv_path2.unlink()

    def test_single_file_as_path(self) -> None:
        """Test initializing TaskAnalyzer with a single Path object."""
        csv_data = "プロジェクト名,モード名,実績時間\nProject A,Mode 1,01:30\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project(sort_by="project")

            assert len(results) == 1
            assert results[0]["project"] == "Project A"

        finally:
            csv_path.unlink()

    def test_display_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test JSON output format."""
        results = [
            {
                "project": "Test Project",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results)

        captured = capsys.readouterr()
        assert "Test Project" in captured.out
        assert "01:30" in captured.out
        assert "5" in captured.out

    def test_display_csv_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CSV output format."""
        results = [
            {
                "project": "Test Project",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results)

        captured = capsys.readouterr()
        assert "Project,Total Time,Task Count" in captured.out
        assert "Test Project,01:30,5" in captured.out

    def test_analyze_by_mode(self) -> None:
        """Test mode analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Focus Mode,00:15\n"
            "Project A,Focus Mode,00:10\n"
            "Project B,Meeting Mode,00:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode()

            assert len(results) == 2

            # Check Focus Mode (should have 00:25 total)
            focus_mode = next(r for r in results if r["mode"] == "Focus Mode")
            assert focus_mode["total_time"] == "00:25"
            assert focus_mode["task_count"] == "2"

            # Check Meeting Mode (should have 00:30 total)
            meeting_mode = next(r for r in results if r["mode"] == "Meeting Mode")
            assert meeting_mode["total_time"] == "00:30"
            assert meeting_mode["task_count"] == "1"

        finally:
            csv_path.unlink()

    def test_analyze_by_mode_sort_by_mode(self) -> None:
        """Test mode analysis with mode name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Z Mode,00:15\n"
            "Project B,A Mode,00:10\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode(sort_by="mode")

            assert len(results) == 2
            assert results[0]["mode"] == "A Mode"
            assert results[1]["mode"] == "Z Mode"

        finally:
            csv_path.unlink()

    def test_analyze_by_mode_sort_by_name(self) -> None:
        """Test mode analysis with name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Z Mode,00:15\n"
            "Project B,A Mode,00:10\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode(sort_by="name")

            assert len(results) == 2
            assert results[0]["mode"] == "A Mode"
            assert results[1]["mode"] == "Z Mode"

        finally:
            csv_path.unlink()

    def test_display_table_mode(self) -> None:
        """Test table display for mode analysis."""
        results = [
            {
                "mode": "Test Mode",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        # This should not raise an exception
        analyzer.display_table(results, analysis_type="mode")

    def test_display_json_mode_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test JSON output format for mode analysis."""
        results = [
            {
                "mode": "Test Mode",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results, analysis_type="mode")

        captured = capsys.readouterr()
        assert "Test Mode" in captured.out
        assert "01:30" in captured.out
        assert "5" in captured.out

    def test_display_csv_mode_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CSV output format for mode analysis."""
        results = [
            {
                "mode": "Test Mode",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results, analysis_type="mode")

        captured = capsys.readouterr()
        assert "Mode,Total Time,Task Count" in captured.out
        assert "Test Mode,01:30,5" in captured.out

    def test_analyze_by_project_mode(self) -> None:
        """Test project-mode analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Focus Mode,00:15\n"
            "Project A,Focus Mode,00:10\n"
            "Project A,Meeting Mode,00:20\n"
            "Project B,Focus Mode,00:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode()

            assert len(results) == 3

            # Check Project A + Focus Mode (should have 00:25 total)
            project_a_focus = next(
                r
                for r in results
                if r["project"] == "Project A" and r["mode"] == "Focus Mode"
            )
            assert project_a_focus["total_time"] == "00:25"
            assert project_a_focus["task_count"] == "2"

            # Check Project A + Meeting Mode (should have 00:20 total)
            project_a_meeting = next(
                r
                for r in results
                if r["project"] == "Project A" and r["mode"] == "Meeting Mode"
            )
            assert project_a_meeting["total_time"] == "00:20"
            assert project_a_meeting["task_count"] == "1"

            # Check Project B + Focus Mode (should have 00:30 total)
            project_b_focus = next(
                r
                for r in results
                if r["project"] == "Project B" and r["mode"] == "Focus Mode"
            )
            assert project_b_focus["total_time"] == "00:30"
            assert project_b_focus["task_count"] == "1"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_sort_by_project(self) -> None:
        """Test project-mode analysis with project sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,B Mode,00:15\n"
            "Z Project,A Mode,00:10\n"
            "A Project,C Mode,00:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode(sort_by="project")

            assert len(results) == 3
            # First should be A Project (alphabetically first)
            assert results[0]["project"] == "A Project"
            assert results[0]["mode"] == "C Mode"
            # Next should be Z Project with A Mode (alphabetically)
            assert results[1]["project"] == "Z Project"
            assert results[1]["mode"] == "A Mode"
            # Last should be Z Project with B Mode
            assert results[2]["project"] == "Z Project"
            assert results[2]["mode"] == "B Mode"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_sort_by_mode(self) -> None:
        """Test project-mode analysis with mode sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,B Mode,00:15\n"
            "Z Project,A Mode,00:10\n"
            "A Project,C Mode,00:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode(sort_by="mode")

            assert len(results) == 3
            # First should be A Mode (alphabetically first)
            assert results[0]["mode"] == "A Mode"
            assert results[0]["project"] == "Z Project"
            # Next should be B Mode
            assert results[1]["mode"] == "B Mode"
            assert results[1]["project"] == "Z Project"
            # Last should be C Mode
            assert results[2]["mode"] == "C Mode"
            assert results[2]["project"] == "A Project"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_sort_by_name(self) -> None:
        """Test project-mode analysis with name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,B Mode,00:15\n"
            "Z Project,A Mode,00:10\n"
            "A Project,C Mode,00:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode(sort_by="name")

            assert len(results) == 3
            # First should be A Project + C Mode (alphabetically first)
            assert results[0]["project"] == "A Project"
            assert results[0]["mode"] == "C Mode"
            # Second should be Z Project + A Mode
            assert results[1]["project"] == "Z Project"
            assert results[1]["mode"] == "A Mode"
            # Third should be Z Project + B Mode
            assert results[2]["project"] == "Z Project"
            assert results[2]["mode"] == "B Mode"

        finally:
            csv_path.unlink()

    def test_display_table_project_mode(self) -> None:
        """Test table display for project-mode analysis."""
        results = [
            {
                "project": "Test Project",
                "mode": "Test Mode",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        # This should not raise an exception
        analyzer.display_table(results, analysis_type="project-mode")

    def test_display_json_project_mode_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test JSON output format for project-mode analysis."""
        results = [
            {
                "project": "Test Project",
                "mode": "Test Mode",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results, analysis_type="project-mode")

        captured = capsys.readouterr()
        assert "Test Project" in captured.out
        assert "Test Mode" in captured.out
        assert "01:30" in captured.out
        assert "5" in captured.out

    def test_display_csv_project_mode_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test CSV output format for project-mode analysis."""
        results = [
            {
                "project": "Test Project",
                "mode": "Test Mode",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results, analysis_type="project-mode")

        captured = capsys.readouterr()
        assert "Project,Mode,Total Time,Task Count" in captured.out
        assert "Test Project,Test Mode,01:30,5" in captured.out

    def test_parse_tag_names(self) -> None:
        """Test parsing tag names from CSV string."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test empty or invalid input
        assert analyzer._parse_tag_names("") == []
        assert analyzer._parse_tag_names(float("nan")) == []
        assert analyzer._parse_tag_names(123) == []

        # Test single tag
        assert analyzer._parse_tag_names("work") == ["work"]

        # Test multiple tags
        assert analyzer._parse_tag_names("work,personal") == ["work", "personal"]

        # Test with spaces
        assert analyzer._parse_tag_names("work, personal , urgent") == [
            "work",
            "personal",
            "urgent",
        ]

        # Test with empty strings after split
        assert analyzer._parse_tag_names("work,,personal") == ["work", "personal"]

    def test_filter_by_tag(self) -> None:
        """Test filtering data by tag name."""
        # Create sample data with tag column
        data = pd.DataFrame(
            {
                "タスク名": ["Task 1", "Task 2", "Task 3", "Task 4"],
                "タグ名": ["work", "work,personal", "personal", ""],
                "実績時間": ["00:15", "00:30", "00:45", "01:00"],
            }
        )

        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test filtering by "work" tag
        filtered = analyzer._filter_by_tag(data, "work")
        assert len(filtered) == 2
        assert list(filtered["タスク名"]) == ["Task 1", "Task 2"]

        # Test filtering by "personal" tag
        filtered = analyzer._filter_by_tag(data, "personal")
        assert len(filtered) == 2
        assert list(filtered["タスク名"]) == ["Task 2", "Task 3"]

        # Test filtering by non-existent tag
        filtered = analyzer._filter_by_tag(data, "nonexistent")
        assert len(filtered) == 0

        # Test empty filter
        filtered = analyzer._filter_by_tag(data, "")
        assert len(filtered) == 4  # Should return all data

    def test_set_tag_filter(self) -> None:
        """Test setting tag filter."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Initially no filter
        assert analyzer._tag_filter is None

        # Set filter
        analyzer.set_tag_filter("work")
        assert analyzer._tag_filter == "work"

    def test_tag_filter_integration(self) -> None:
        """Test tag filtering integration with analysis methods."""
        # Create sample CSV data with tags
        csv_data = (
            "プロジェクト名,モード名,実績時間,タグ名\n"
            "Project A,Focus Mode,00:15,work\n"
            'Project A,Focus Mode,00:10,"work,urgent"\n'
            "Project B,Meeting Mode,00:30,personal\n"
            "Project C,Focus Mode,00:20,work\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)

            # Test without filter - should get all projects
            results = analyzer.analyze_by_project()
            assert len(results) == 3

            # Test with "work" filter - should only get Project A and C
            analyzer.set_tag_filter("work")
            results = analyzer.analyze_by_project()
            assert len(results) == 2

            project_names = [r["project"] for r in results]
            assert "Project A" in project_names
            assert "Project C" in project_names
            assert "Project B" not in project_names

            # Check time aggregation for Project A (should be 00:25)
            project_a = next(r for r in results if r["project"] == "Project A")
            assert project_a["total_time"] == "00:25"
            assert project_a["task_count"] == "2"

            # Test with "personal" filter - should only get Project B
            analyzer.set_tag_filter("personal")
            results = analyzer.analyze_by_project()
            assert len(results) == 1
            assert results[0]["project"] == "Project B"
            assert results[0]["total_time"] == "00:30"

        finally:
            csv_path.unlink()

    def test_display_slack_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test Slack output format."""
        results = [
            {
                "project": "Test Project",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
                "percentage": "75.0%",
            },
            {
                "project": "Another Project",
                "total_time": "00:30",
                "task_count": "2",
                "total_seconds": 1800,
                "percentage": "25.0%",
            },
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_slack(results)

        captured = capsys.readouterr()
        assert "📊 TaskChute Cloud 分析結果" in captured.out
        assert "*プロジェクト別時間分析*" in captured.out
        assert "Test Project" in captured.out
        assert "01:30" in captured.out
        assert "75.0%" in captured.out
        assert "```" in captured.out

    def test_display_slack_with_base_time(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test Slack output format with base time."""
        results = [
            {
                "project": "Work",
                "total_time": "04:00",
                "task_count": "5",
                "total_seconds": 14400,
            },
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_slack(results, "project", "08:00")

        captured = capsys.readouterr()
        assert "📊 TaskChute Cloud 分析結果 (基準時間: 08:00)" in captured.out
        assert "*プロジェクト別時間分析*" in captured.out
        assert "50.0%" in captured.out  # 4/8 * 100

    def test_display_slack_mode_analysis(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test Slack output format for mode analysis."""
        results = [
            {
                "mode": "Focus Mode",
                "total_time": "02:00",
                "task_count": "3",
                "total_seconds": 7200,
                "percentage": "80.0%",
            },
            {
                "mode": "Meeting Mode",
                "total_time": "00:30",
                "task_count": "1",
                "total_seconds": 1800,
                "percentage": "20.0%",
            },
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_slack(results, analysis_type="mode")

        captured = capsys.readouterr()
        assert "📊 TaskChute Cloud 分析結果" in captured.out
        assert "*モード別時間分析*" in captured.out
        assert "Focus Mode" in captured.out
        assert "Meeting Mode" in captured.out
        assert "02:00" in captured.out
        assert "80.0%" in captured.out

    def test_display_slack_project_mode_analysis(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test Slack output format for project-mode analysis."""
        results = [
            {
                "project": "Project A",
                "mode": "Focus",
                "total_time": "01:30",
                "task_count": "2",
                "total_seconds": 5400,
                "percentage": "60.0%",
                "project_mode": "Project A | Focus",
            },
            {
                "project": "Project A",
                "mode": "Meeting",
                "total_time": "01:00",
                "task_count": "1",
                "total_seconds": 3600,
                "percentage": "40.0%",
                "project_mode": "Project A | Meeting",
            },
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_slack(results, analysis_type="project-mode")

        captured = capsys.readouterr()
        assert "📊 TaskChute Cloud 分析結果" in captured.out
        assert "*プロジェクトxモード別時間分析*" in captured.out
        assert "Project A" in captured.out
        assert "Focus" in captured.out
        assert "Meeting" in captured.out
        assert "01:30" in captured.out
        assert "60.0%" in captured.out

    def test_display_slack_long_names_truncation(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test Slack output truncates long project/mode names."""
        results = [
            {
                "project": "Very Long Project Name That Should Be Truncated",
                "total_time": "01:30",
                "task_count": "2",
                "total_seconds": 5400,
                "percentage": "100.0%",
            },
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_slack(results)

        captured = capsys.readouterr()
        assert "Very Long..." in captured.out

    def test_display_slack_without_percentage(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test Slack output without percentage column."""
        results = [
            {
                "project": "Test Project",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            },
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_slack(results)

        captured = capsys.readouterr()
        output_lines = captured.out.split("\n")

        # Find the header line (should be inside code block)
        header_line = None
        for line in output_lines:
            if "プロジェクト" in line and "|" in line:
                header_line = line
                break

        assert header_line is not None
        # Should not contain percentage header when no percentage data
        assert "割合" not in header_line

    def test_slack_header_formatting(self) -> None:
        """Test Slack header formatting."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        config = analyzer._get_analysis_config("project")
        results = [
            {
                "project": "Test",
                "total_time": "01:00",
                "task_count": "1",
                "total_seconds": 3600,
            }
        ]

        headers = analyzer._get_slack_headers(config, results, None)
        assert "プロジェクト" in headers
        assert "時間" in headers
        assert "タスク数" in headers
        assert "|" in headers

    def test_slack_row_formatting(self) -> None:
        """Test Slack row formatting."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        config = analyzer._get_analysis_config("project")
        result = {
            "project": "Test Project",
            "total_time": "01:30",
            "task_count": "5",
            "total_seconds": 5400,
            "percentage": "75.0%"
        }

        row = analyzer._format_slack_row(result, config, None)
        assert "Test Project" in row
        assert "01:30" in row
        assert "5" in row
        assert "75.0%" in row
        assert "|" in row
