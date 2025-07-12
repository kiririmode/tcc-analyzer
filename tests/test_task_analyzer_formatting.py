"""Tests for TaskAnalyzer output formatting functionality."""

import io
import json
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzerFormatting:
    """Test class for TaskAnalyzer output formatting functionality."""

    def test_display_table_with_base_time(self) -> None:
        """Test display table with base time percentage."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Work",
                "total_time": "04:00",
                "total_seconds": 14400,
                "task_count": "10",
            }
        ]

        # Add percentage based on base time
        results_with_percentage = analyzer._add_percentage_to_results(results, "08:00")

        # Check that percentage was added
        assert len(results_with_percentage) == 1
        assert results_with_percentage[0]["percentage"] == "50.0%"

        # Test display (should not raise any exceptions)
        analyzer.display_table(results_with_percentage, base_time="08:00")

    def test_display_json_with_base_time(self) -> None:
        """Test JSON output with base time."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Test Project",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        # Capture stdout to test JSON output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            analyzer.display_json(results, base_time="08:00")
            output = captured_output.getvalue()

            # Parse the JSON output
            json_data = json.loads(output)

            # Check that the result contains expected fields
            assert "results" in json_data
            results = json_data["results"]
            assert len(results) == 1
            result = results[0]
            assert result["project"] == "Test Project"
            assert result["total_time"] == "01:30"
            assert result["task_count"] == 5
            assert "percentage" in result

        finally:
            sys.stdout = old_stdout

    def test_display_csv_with_base_time(self) -> None:
        """Test CSV output with base time."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Test Project",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        # Capture stdout to test CSV output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            analyzer.display_csv(results, base_time="08:00")
            output = captured_output.getvalue()

            # Check CSV headers and content
            lines = output.strip().split("\n")
            assert len(lines) >= 3  # Base time comment + Header + at least one data row

            # Find the header line (skip the base time comment)
            header = None
            for line in lines:
                if "Project" in line:
                    header = line
                    break

            assert header is not None
            assert "Project" in header
            assert "Total Time" in header
            assert "Task Count" in header
            assert "Percentage" in header

        finally:
            sys.stdout = old_stdout

    def test_display_table_without_base_time(self) -> None:
        """Test display table without base time percentage."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Work",
                "total_time": "04:00",
                "total_seconds": 14400,
                "task_count": "10",
            }
        ]

        # Test display without base time (should not raise any exceptions)
        analyzer.display_table(results)

    def test_display_json_without_base_time(self) -> None:
        """Test JSON output without base time."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Test Project",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        # Capture stdout to test JSON output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            analyzer.display_json(results)
            output = captured_output.getvalue()

            # Parse the JSON output
            json_data: Any = json.loads(output)

            # Check that the result contains expected fields
            if isinstance(json_data, list):
                # Direct list format when no base time
                results: list[Any] = cast(list[Any], json_data)
            else:
                # Wrapped format when base time is provided
                results: list[Any] = cast(list[Any], json_data["results"])

            assert len(results) == 1
            result = results[0]
            assert result["project"] == "Test Project"
            assert result["total_time"] == "01:30"
            assert result["task_count"] == 5
            # Should not have percentage when no base time
            assert "percentage" not in result

        finally:
            sys.stdout = old_stdout

    def test_display_csv_without_base_time(self) -> None:
        """Test CSV output without base time."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Test Project",
                "total_time": "01:30",
                "task_count": "5",
                "total_seconds": 5400,
            }
        ]

        # Capture stdout to test CSV output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            analyzer.display_csv(results)
            output = captured_output.getvalue()

            # Check CSV headers and content
            lines = output.strip().split("\n")
            assert len(lines) >= 2  # Header + at least one data row

            # Check that header does not contain percentage column
            header = lines[0]
            assert "Project" in header
            assert "Total Time" in header
            assert "Task Count" in header
            assert "Percentage" not in header

        finally:
            sys.stdout = old_stdout

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

    def test_display_table_mode(self) -> None:
        """Test display table for mode analysis."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "mode": "Focus Mode",
                "total_time": "02:00",
                "total_seconds": 7200,
                "task_count": "3",
            }
        ]

        # Test display (should not raise any exceptions)
        analyzer.display_table(results, analysis_type="mode")

    def test_display_json_mode_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test JSON output for mode analysis."""
        results = [
            {
                "mode": "Focus Mode",
                "total_time": "02:00",
                "task_count": "3",
                "total_seconds": 7200,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results, analysis_type="mode")

        captured = capsys.readouterr()
        assert "Focus Mode" in captured.out
        assert "02:00" in captured.out
        assert "3" in captured.out

    def test_display_csv_mode_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test CSV output for mode analysis."""
        results = [
            {
                "mode": "Focus Mode",
                "total_time": "02:00",
                "task_count": "3",
                "total_seconds": 7200,
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results, analysis_type="mode")

        captured = capsys.readouterr()
        assert "Mode,Total Time,Task Count" in captured.out
        assert "Focus Mode,02:00,3" in captured.out

    def test_display_table_project_mode(self) -> None:
        """Test display table for project-mode analysis."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        results = [
            {
                "project": "Project A",
                "mode": "Focus",
                "total_time": "01:30",
                "total_seconds": 5400,
                "task_count": "2",
                "project_mode": "Project A | Focus",
            }
        ]

        # Test display (should not raise any exceptions)
        analyzer.display_table(results, analysis_type="project-mode")

    def test_display_json_project_mode_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test JSON output for project-mode analysis."""
        results = [
            {
                "project": "Project A",
                "mode": "Focus",
                "total_time": "01:30",
                "task_count": "2",
                "total_seconds": 5400,
                "project_mode": "Project A | Focus",
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results, analysis_type="project-mode")

        captured = capsys.readouterr()
        assert "Project A" in captured.out
        assert "Focus" in captured.out
        assert "01:30" in captured.out

    def test_display_csv_project_mode_output(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test CSV output for project-mode analysis."""
        results = [
            {
                "project": "Project A",
                "mode": "Focus",
                "total_time": "01:30",
                "task_count": "2",
                "total_seconds": 5400,
                "project_mode": "Project A | Focus",
            }
        ]

        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results, analysis_type="project-mode")

        captured = capsys.readouterr()
        assert "Project,Mode,Total Time,Task Count" in captured.out
        assert "Project A,Focus,01:30,2" in captured.out

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
            "percentage": "75.0%",
        }

        row = analyzer._format_slack_row(result, config, None)
        assert "Test Project" in row
        assert "01:30" in row
        assert "5" in row
        assert "75.0%" in row
        assert "|" in row
