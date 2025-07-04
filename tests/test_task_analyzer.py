"""Tests for TaskAnalyzer."""

import math
import tempfile
from datetime import timedelta
from pathlib import Path

import pytest
from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzer:
    """Test class for TaskAnalyzer."""

    def test_parse_time_duration_valid(self) -> None:
        """Test parsing valid time duration strings."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        assert analyzer._parse_time_duration("01:30:45") == timedelta(
            hours=1, minutes=30, seconds=45
        )
        assert analyzer._parse_time_duration("00:00:00") == timedelta(0)
        assert analyzer._parse_time_duration("12:59:59") == timedelta(
            hours=12, minutes=59, seconds=59
        )

    def test_parse_time_duration_invalid(self) -> None:
        """Test parsing invalid time duration strings."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        assert analyzer._parse_time_duration("") == timedelta(0)
        assert analyzer._parse_time_duration("invalid") == timedelta(0)
        assert analyzer._parse_time_duration("1:2") == timedelta(0)

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
            == "01:30:45"
        )
        assert analyzer._format_duration(timedelta(0)) == "00:00:00"

    def test_calculate_percentage(self) -> None:
        """Test percentage calculation against base time."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test basic percentage calculation
        duration = timedelta(hours=1)  # 1 hour
        base_time = "08:00:00"  # 8 hours
        percentage = analyzer._calculate_percentage(duration, base_time)
        assert percentage == 12.5  # 1/8 * 100 = 12.5%

        # Test 100% case
        duration = timedelta(hours=8)
        percentage = analyzer._calculate_percentage(duration, base_time)
        assert percentage == 100.0

        # Test zero base time (edge case)
        percentage = analyzer._calculate_percentage(duration, "00:00:00")
        assert percentage == 0.0

    def test_add_percentage_to_results(self) -> None:
        """Test adding percentage column to results."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Work",
                "total_time": "04:00:00",
                "total_seconds": 14400,  # 4 hours in seconds
                "task_count": "5",
            },
            {
                "project": "Study",
                "total_time": "02:00:00",
                "total_seconds": 7200,  # 2 hours in seconds
                "task_count": "3",
            },
        ]

        updated_results = analyzer._add_percentage_to_results(results, "08:00:00")

        assert len(updated_results) == 2
        assert updated_results[0]["percentage"] == "50.0%"  # 4/8 * 100
        assert updated_results[1]["percentage"] == "25.0%"  # 2/8 * 100

    def test_analyze_by_project(self) -> None:
        """Test project analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間,開始日時,終了日時\n"
            "Project A,Mode 1,00:15:00,2025-07-01 09:00:00,2025-07-01 09:15:00\n"
            "Project A,Mode 1,00:10:00,2025-07-01 09:15:00,2025-07-01 09:25:00\n"
            "Project B,Mode 2,00:30:00,2025-07-01 10:00:00,2025-07-01 10:30:00\n"
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

            # Check Project A (should have 00:25:00 total)
            project_a = next(r for r in results if r["project"] == "Project A")
            assert project_a["total_time"] == "00:25:00"
            assert project_a["task_count"] == "2"

            # Check Project B (should have 00:30:00 total)
            project_b = next(r for r in results if r["project"] == "Project B")
            assert project_b["total_time"] == "00:30:00"
            assert project_b["task_count"] == "1"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_sort_by_project(self) -> None:
        """Test project analysis with project name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Mode 1,00:15:00\n"
            "A Project,Mode 2,00:10:00\n"
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
            "Z Project,Mode 1,00:15:00\n"
            "A Project,Mode 2,00:10:00\n"
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

    def test_display_json_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test JSON output format."""
        results = [
            {
                "project": "Test Project",
                "total_time": "01:30:00",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results)

        captured = capsys.readouterr()
        assert "Test Project" in captured.out
        assert "01:30:00" in captured.out
        assert "5" in captured.out

    def test_display_csv_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CSV output format."""
        results = [
            {
                "project": "Test Project",
                "total_time": "01:30:00",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results)

        captured = capsys.readouterr()
        assert "Project,Total Time,Task Count" in captured.out
        assert "Test Project,01:30:00,5" in captured.out

    def test_analyze_by_mode(self) -> None:
        """Test mode analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Focus Mode,00:15:00\n"
            "Project A,Focus Mode,00:10:00\n"
            "Project B,Meeting Mode,00:30:00\n"
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

            # Check Focus Mode (should have 00:25:00 total)
            focus_mode = next(r for r in results if r["mode"] == "Focus Mode")
            assert focus_mode["total_time"] == "00:25:00"
            assert focus_mode["task_count"] == "2"

            # Check Meeting Mode (should have 00:30:00 total)
            meeting_mode = next(r for r in results if r["mode"] == "Meeting Mode")
            assert meeting_mode["total_time"] == "00:30:00"
            assert meeting_mode["task_count"] == "1"

        finally:
            csv_path.unlink()

    def test_analyze_by_mode_sort_by_mode(self) -> None:
        """Test mode analysis with mode name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Z Mode,00:15:00\n"
            "Project B,A Mode,00:10:00\n"
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
            "Project A,Z Mode,00:15:00\n"
            "Project B,A Mode,00:10:00\n"
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
                "total_time": "01:30:00",
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
                "total_time": "01:30:00",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results, analysis_type="mode")

        captured = capsys.readouterr()
        assert "Test Mode" in captured.out
        assert "01:30:00" in captured.out
        assert "5" in captured.out

    def test_display_csv_mode_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CSV output format for mode analysis."""
        results = [
            {
                "mode": "Test Mode",
                "total_time": "01:30:00",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results, analysis_type="mode")

        captured = capsys.readouterr()
        assert "Mode,Total Time,Task Count" in captured.out
        assert "Test Mode,01:30:00,5" in captured.out

    def test_analyze_by_project_mode(self) -> None:
        """Test project-mode analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Focus Mode,00:15:00\n"
            "Project A,Focus Mode,00:10:00\n"
            "Project A,Meeting Mode,00:20:00\n"
            "Project B,Focus Mode,00:30:00\n"
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

            # Check Project A + Focus Mode (should have 00:25:00 total)
            project_a_focus = next(
                r
                for r in results
                if r["project"] == "Project A" and r["mode"] == "Focus Mode"
            )
            assert project_a_focus["total_time"] == "00:25:00"
            assert project_a_focus["task_count"] == "2"

            # Check Project A + Meeting Mode (should have 00:20:00 total)
            project_a_meeting = next(
                r
                for r in results
                if r["project"] == "Project A" and r["mode"] == "Meeting Mode"
            )
            assert project_a_meeting["total_time"] == "00:20:00"
            assert project_a_meeting["task_count"] == "1"

            # Check Project B + Focus Mode (should have 00:30:00 total)
            project_b_focus = next(
                r
                for r in results
                if r["project"] == "Project B" and r["mode"] == "Focus Mode"
            )
            assert project_b_focus["total_time"] == "00:30:00"
            assert project_b_focus["task_count"] == "1"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_sort_by_project(self) -> None:
        """Test project-mode analysis with project sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,B Mode,00:15:00\n"
            "Z Project,A Mode,00:10:00\n"
            "A Project,C Mode,00:30:00\n"
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
            "Z Project,B Mode,00:15:00\n"
            "Z Project,A Mode,00:10:00\n"
            "A Project,C Mode,00:30:00\n"
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
            "Z Project,B Mode,00:15:00\n"
            "Z Project,A Mode,00:10:00\n"
            "A Project,C Mode,00:30:00\n"
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
                "total_time": "01:30:00",
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
                "total_time": "01:30:00",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results, analysis_type="project-mode")

        captured = capsys.readouterr()
        assert "Test Project" in captured.out
        assert "Test Mode" in captured.out
        assert "01:30:00" in captured.out
        assert "5" in captured.out

    def test_display_csv_project_mode_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test CSV output format for project-mode analysis."""
        results = [
            {
                "project": "Test Project",
                "mode": "Test Mode",
                "total_time": "01:30:00",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results, analysis_type="project-mode")

        captured = capsys.readouterr()
        assert "Project,Mode,Total Time,Task Count" in captured.out
        assert "Test Project,Test Mode,01:30:00,5" in captured.out
