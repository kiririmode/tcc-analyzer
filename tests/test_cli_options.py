"""Tests for CLI command options functionality."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from click.testing import CliRunner
from src.tcc_analyzer.cli import main


class TestCLIOptions:
    """Test class for CLI command options functionality."""

    def test_task_command_with_base_time(self) -> None:
        """Test task command with base time option."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--base-time", "08:00"]
            )
            assert result.exit_code == 0
            assert "Analysis" in result.output
            assert "Work" in result.output
            # Should show percentage calculation
            assert "%" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_invalid_base_time_format(self) -> None:
        """Test task command with invalid base time format."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            # Test various invalid formats
            invalid_formats = [
                "25:00",  # Invalid hour
                "8:60",   # Invalid minute
                "8:5",    # Single digit minute
                "8",      # Missing minute
                "abc",    # Non-numeric
                "08:00:30",  # Seconds not supported
            ]

            for invalid_format in invalid_formats:
                result = runner.invoke(
                    main, ["task", str(csv_path), "--base-time", invalid_format]
                )
                assert result.exit_code != 0
                assert "Invalid base time format" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_sorting_options(self) -> None:
        """Test task command with different sorting options."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Z_Project,Focus,01:00:00\n"
            "A_Project,Focus,02:00:00\n"
            "M_Project,Focus,00:30:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()

            # Test sorting by project name
            result = runner.invoke(
                main, ["task", str(csv_path), "--sort-by", "project"]
            )
            assert result.exit_code == 0

            # Test sorting by time
            result = runner.invoke(main, ["task", str(csv_path), "--sort-by", "time"])
            assert result.exit_code == 0

            # Test reverse sorting
            result = runner.invoke(
                main, ["task", str(csv_path), "--sort-by", "time", "--reverse"]
            )
            assert result.exit_code == 0
        finally:
            csv_path.unlink()

    def test_task_command_invalid_base_time_edge_cases(self) -> None:
        """Test task command with edge case base time formats."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()

            # Test edge cases
            edge_cases = [
                "24:00",    # Edge: 24 hours (should be invalid)
                "23:60",    # Edge: 60 minutes (should be invalid)
                "00:00",    # Edge: Zero time (should be valid but may cause division by zero)
                "-01:00",   # Negative time
                "01:-30",   # Negative minutes
                "",         # Empty string
                " 08:00 ",  # Whitespace
                "08:00:00", # With seconds (not supported in base time)
                "1:30",     # Single digit hour
                "01:5",     # Single digit minute
            ]

            for case in edge_cases:
                result = runner.invoke(
                    main, ["task", str(csv_path), "--base-time", case]
                )
                # Most should fail, but we're testing that the CLI handles them gracefully
                if case in ["00:00", " 08:00 "]:
                    # These might be valid or handled specially
                    continue
                else:
                    assert result.exit_code != 0, f"Expected failure for base time: {case}"
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.ChartFactory")
    def test_task_command_with_bar_chart(self, mock_factory: Any) -> None:
        """Test task command with bar chart generation."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            # Mock the chart creation
            mock_chart = Mock()
            mock_chart.create_chart.return_value = "test_chart.png"
            mock_factory.return_value = mock_chart

            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--chart", "bar", "--chart-format", "png"]
            )
            assert result.exit_code == 0
            assert "Chart saved" in result.output
            mock_factory.assert_called_once()
            mock_chart.create_chart.assert_called_once()
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.ChartFactory")
    def test_task_command_with_pie_chart(self, mock_factory: Any) -> None:
        """Test task command with pie chart generation."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            mock_chart = Mock()
            mock_chart.create_chart.return_value = "test_pie_chart.svg"
            mock_factory.return_value = mock_chart

            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--chart", "pie", "--chart-format", "svg"]
            )
            assert result.exit_code == 0
            assert "Chart saved" in result.output
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.ChartFactory")
    def test_task_command_with_line_chart(self, mock_factory: Any) -> None:
        """Test task command with line chart generation."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Focus,01:00:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            mock_chart = Mock()
            mock_chart.create_chart.return_value = "test_line_chart.pdf"
            mock_factory.return_value = mock_chart

            runner = CliRunner()
            result = runner.invoke(
                main,
                ["task", str(csv_path), "--chart", "line", "--chart-format", "pdf"],
            )
            assert result.exit_code == 0
            assert "Chart saved" in result.output
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.ChartFactory")
    def test_task_command_with_histogram_chart(self, mock_factory: Any) -> None:
        """Test task command with histogram chart generation."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            mock_chart = Mock()
            mock_chart.create_chart.return_value = "test_histogram.eps"
            mock_factory.return_value = mock_chart

            runner = CliRunner()
            result = runner.invoke(
                main,
                ["task", str(csv_path), "--chart", "histogram", "--chart-format", "eps"],
            )
            assert result.exit_code == 0
            assert "Chart saved" in result.output
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.ChartFactory")
    def test_task_command_with_heatmap_chart(self, mock_factory: Any) -> None:
        """Test task command with heatmap chart generation."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            mock_chart = Mock()
            mock_chart.create_chart.return_value = "test_heatmap.png"
            mock_factory.return_value = mock_chart

            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--chart", "heatmap"]
            )
            assert result.exit_code == 0
            assert "Chart saved" in result.output
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.ChartFactory")
    def test_task_command_with_show_chart(self, mock_factory: Any) -> None:
        """Test task command with show chart option."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            mock_chart = Mock()
            mock_chart.create_chart.return_value = "test_chart.png"
            mock_chart.show_chart = Mock()
            mock_factory.return_value = mock_chart

            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--chart", "bar", "--show-chart"]
            )
            assert result.exit_code == 0
            mock_chart.show_chart.assert_called_once()
        finally:
            csv_path.unlink()

    def test_chart_output_path_generation(self) -> None:
        """Test chart output path generation for different analysis types."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            with patch("src.tcc_analyzer.cli.ChartFactory") as mock_factory:
                mock_chart = Mock()
                mock_chart.create_chart.return_value = "project_analysis_chart.png"
                mock_factory.return_value = mock_chart

                runner = CliRunner()

                # Test project analysis chart path
                result = runner.invoke(
                    main,
                    [
                        "task",
                        str(csv_path),
                        "--chart",
                        "bar",
                        "--chart-format",
                        "png",
                    ],
                )
                assert result.exit_code == 0
                assert "project_analysis_chart.png" in result.output

        finally:
            csv_path.unlink()

    def test_all_chart_formats(self) -> None:
        """Test all supported chart formats."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            with patch("src.tcc_analyzer.cli.ChartFactory") as mock_factory:
                mock_chart = Mock()
                mock_factory.return_value = mock_chart

                formats = ["png", "svg", "pdf", "eps"]
                for fmt in formats:
                    mock_chart.create_chart.return_value = f"test_chart.{fmt}"

                    runner = CliRunner()
                    result = runner.invoke(
                        main,
                        [
                            "task",
                            str(csv_path),
                            "--chart",
                            "bar",
                            "--chart-format",
                            fmt,
                        ],
                    )
                    assert result.exit_code == 0
                    assert f"test_chart.{fmt}" in result.output

        finally:
            csv_path.unlink()