"""Tests for TaskAnalyzer backward compatibility methods."""

from datetime import timedelta
from pathlib import Path
from typing import Any

from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzerCompatibility:
    """Test class for TaskAnalyzer backward compatibility methods."""

    def test_add_total_row_and_percentages(self) -> None:
        """Test adding total row and percentage columns to results."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test with project analysis results
        results = [
            {
                "project": "Work",
                "total_time": "04:00",
                "total_seconds": 14400,
                "task_count": "10",
            },
            {
                "project": "Personal",
                "total_time": "02:00",
                "total_seconds": 7200,
                "task_count": "5",
            },
        ]

        updated_results = analyzer.add_total_row_and_percentages(results, "project")

        # Should have original results plus total row
        assert len(updated_results) == 3

        # Check percentages were added
        work_result = next(r for r in updated_results if r["project"] == "Work")
        assert work_result["percentage"] == "66.7%"  # 4/6 * 100

        personal_result = next(
            r for r in updated_results if r["project"] == "Personal"
        )
        assert personal_result["percentage"] == "33.3%"  # 2/6 * 100

        # Check total row
        total_result = next(r for r in updated_results if r["project"] == "Total")
        assert total_result["total_time"] == "06:00"
        assert total_result["task_count"] == "15"
        assert total_result["percentage"] == "100.0%"

    def test_add_total_row_and_percentages_mode(self) -> None:
        """Test adding total row and percentage columns for mode analysis."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "mode": "Focus",
                "total_time": "03:00",
                "total_seconds": 10800,
                "task_count": "6",
            },
            {
                "mode": "Meeting",
                "total_time": "01:00",
                "total_seconds": 3600,
                "task_count": "2",
            },
        ]

        updated_results = analyzer.add_total_row_and_percentages(results, "mode")

        # Should have original results plus total row
        assert len(updated_results) == 3

        # Check total row for mode analysis
        total_result = next(r for r in updated_results if r["mode"] == "Total")
        assert total_result["total_time"] == "04:00"
        assert total_result["task_count"] == "8"
        assert total_result["percentage"] == "100.0%"

    def test_add_total_row_and_percentages_project_mode(self) -> None:
        """Test adding total row and percentage columns for project-mode analysis."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Work",
                "mode": "Focus",
                "total_time": "02:00",
                "total_seconds": 7200,
                "task_count": "4",
                "project_mode": "Work | Focus",
            },
            {
                "project": "Work",
                "mode": "Meeting",
                "total_time": "01:00",
                "total_seconds": 3600,
                "task_count": "2",
                "project_mode": "Work | Meeting",
            },
        ]

        updated_results = analyzer.add_total_row_and_percentages(
            results, "project-mode"
        )

        # Should have original results plus total row
        assert len(updated_results) == 3

        # Check total row for project-mode analysis
        total_result = next(r for r in updated_results if r["project"] == "Total")
        assert total_result["mode"] == "-"
        assert total_result["project_mode"] == "Total | -"
        assert total_result["total_time"] == "03:00"
        assert total_result["task_count"] == "6"
        assert total_result["percentage"] == "100.0%"

    def test_add_total_row_and_percentages_empty_results(self) -> None:
        """Test adding total row and percentages with empty results."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results: list[dict[str, Any]] = []
        updated_results = analyzer.add_total_row_and_percentages(results, "project")

        # Empty input should return empty output
        assert updated_results == []

    def test_create_total_row(self) -> None:
        """Test creating total row for analysis results."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test project analysis total row
        total_duration = timedelta(hours=6)
        total_task_count = 15
        total_row = analyzer._create_total_row(
            total_duration, total_task_count, "project"
        )

        assert total_row["project"] == "Total"
        assert total_row["total_time"] == "06:00"
        assert total_row["task_count"] == "15"
        assert total_row["total_seconds"] == 21600
        assert total_row["percentage"] == "100.0%"

        # Test mode analysis total row
        total_row = analyzer._create_total_row(total_duration, total_task_count, "mode")

        assert total_row["mode"] == "Total"
        assert total_row["total_time"] == "06:00"

        # Test project-mode analysis total row
        total_row = analyzer._create_total_row(
            total_duration, total_task_count, "project-mode"
        )

        assert total_row["project"] == "Total"
        assert total_row["mode"] == "-"
        assert total_row["project_mode"] == "Total | -"

    def test_add_percentage_to_results(self) -> None:
        """Test adding percentage column to results based on base time."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Work",
                "total_time": "04:00",
                "total_seconds": 14400,
                "task_count": "10",
            },
            {
                "project": "Personal",
                "total_time": "02:00",
                "total_seconds": 7200,
                "task_count": "5",
            },
        ]

        updated_results = analyzer._add_percentage_to_results(results, "08:00")

        assert len(updated_results) == 2

        work_result = next(r for r in updated_results if r["project"] == "Work")
        assert work_result["percentage"] == "50.0%"  # 4/8 * 100

        personal_result = next(
            r for r in updated_results if r["project"] == "Personal"
        )
        assert personal_result["percentage"] == "25.0%"  # 2/8 * 100