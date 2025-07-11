"""Tests for CLI module."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from click.testing import CliRunner
from src.tcc_analyzer.cli import main


class TestCLI:
    """Test class for CLI functionality."""

    def test_cli_help(self) -> None:
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "TCC Analyzer" in result.output

    def test_task_command_help(self) -> None:
        """Test task command help."""
        runner = CliRunner()
        result = runner.invoke(main, ["task", "--help"])
        assert result.exit_code == 0
        assert "Analyze TaskChute Cloud task logs" in result.output
        assert "--base-time" in result.output

    def test_task_command_basic_execution(self) -> None:
        """Test basic task command execution."""
        # Create sample CSV data
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
            runner = CliRunner()
            result = runner.invoke(main, ["task", str(csv_path)])
            assert result.exit_code == 0
            assert "Analysis" in result.output
            assert "Work" in result.output
            assert "Study" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_multiple_files(self) -> None:
        """Test task command with multiple CSV files."""
        csv_content1 = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Focus,01:00:00\n"
        )
        csv_content2 = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Review,01:30:00\n"
            "Personal,Task,00:45:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f1:
            f1.write(csv_content1)
            f1.flush()
            csv_path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f2:
            f2.write(csv_content2)
            f2.flush()
            csv_path2 = Path(f2.name)

        try:
            runner = CliRunner()
            result = runner.invoke(main, ["task", str(csv_path1), str(csv_path2)])
            assert result.exit_code == 0
            assert "Analysis" in result.output
            assert "Work" in result.output
            assert "Study" in result.output
            assert "Personal" in result.output
        finally:
            csv_path1.unlink()
            csv_path2.unlink()

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
                main, ["task", str(csv_path), "--base-time", "08:00:00"]
            )
            assert result.exit_code == 0
            assert "08:00:00" in result.output
            assert "Percentage" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_json_output(self) -> None:
        """Test task command with JSON output."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--output-format", "json"]
            )
            assert result.exit_code == 0
            assert '"project": "Work"' in result.output
        finally:
            csv_path.unlink()

    def test_task_command_csv_output(self) -> None:
        """Test task command with CSV output."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--output-format", "csv"]
            )
            assert result.exit_code == 0
            assert "Project,Total Time,Task Count" in result.output
            assert "Work,02:00,1" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_mode_analysis(self) -> None:
        """Test task command with mode analysis."""
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
            runner = CliRunner()
            result = runner.invoke(main, ["task", str(csv_path), "--group-by", "mode"])
            assert result.exit_code == 0
            assert "Mode" in result.output and "Analysis" in result.output
            assert "Focus" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_project_mode_analysis(self) -> None:
        """Test task command with project-mode analysis."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Review,01:00:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--group-by", "project-mode"]
            )
            assert result.exit_code == 0
            assert "Project x Mode Time Analysis" in result.output
            assert "Work" in result.output
            assert "Focus" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_sorting_options(self) -> None:
        """Test task command with different sorting options."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "B_Project,Focus,02:00:00\n"
            "A_Project,Focus,01:00:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            # Test sort by project name
            result = runner.invoke(
                main, ["task", str(csv_path), "--sort-by", "project"]
            )
            assert result.exit_code == 0

            # Test reverse sorting
            result = runner.invoke(main, ["task", str(csv_path), "--reverse"])
            assert result.exit_code == 0
        finally:
            csv_path.unlink()

    def test_task_command_nonexistent_file(self) -> None:
        """Test task command with nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(main, ["task", "nonexistent.csv"])
        assert result.exit_code != 0

    def test_task_command_invalid_base_time_format(self) -> None:
        """Test task command with invalid base time format."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            # Test invalid format: single digit hour/minute
            result = runner.invoke(main, ["task", str(csv_path), "--base-time", "8:0"])
            assert result.exit_code != 0
            assert "Invalid base time format" in result.output
            assert "Use HH:MM format" in result.output

            # Test another invalid format
            result = runner.invoke(main, ["task", str(csv_path), "--base-time", "1:30"])
            assert result.exit_code != 0
            assert "Invalid base time format" in result.output
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.VisualizationFactory")
    def test_task_command_with_bar_chart(self, mock_factory: Any) -> None:
        """Test task command with bar chart generation."""
        # Mock the visualizer
        mock_visualizer = Mock()
        mock_factory.create_visualizer.return_value = mock_visualizer

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
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "test_chart"
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    [
                        "task",
                        str(csv_path),
                        "--chart",
                        "bar",
                        "--chart-output",
                        str(output_path),
                        "--chart-format",
                        "png",
                    ],
                )
                assert result.exit_code == 0
                mock_factory.create_visualizer.assert_called_once()
                mock_visualizer.create_chart.assert_called_once()
                mock_visualizer.save_chart.assert_called_once()
                mock_visualizer.close_chart.assert_called_once()
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.VisualizationFactory")
    def test_task_command_with_pie_chart(self, mock_factory: Any) -> None:
        """Test task command with pie chart generation."""
        mock_visualizer = Mock()
        mock_factory.create_visualizer.return_value = mock_visualizer

        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--chart", "pie", "--chart-format", "svg"]
            )
            assert result.exit_code == 0
            mock_factory.create_visualizer.assert_called_once()
            mock_visualizer.create_chart.assert_called_once()
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.VisualizationFactory")
    def test_task_command_with_line_chart(self, mock_factory: Any) -> None:
        """Test task command with line chart generation."""
        mock_visualizer = Mock()
        mock_factory.create_visualizer.return_value = mock_visualizer

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
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["task", str(csv_path), "--chart", "line", "--chart-format", "pdf"],
            )
            assert result.exit_code == 0
            mock_factory.create_visualizer.assert_called_once()
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.VisualizationFactory")
    def test_task_command_with_histogram_chart(self, mock_factory: Any) -> None:
        """Test task command with histogram chart generation."""
        mock_visualizer = Mock()
        mock_factory.create_visualizer.return_value = mock_visualizer

        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--chart", "histogram"]
            )
            assert result.exit_code == 0
            mock_factory.create_visualizer.assert_called_once()
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.VisualizationFactory")
    def test_task_command_with_heatmap_chart(self, mock_factory: Any) -> None:
        """Test task command with heatmap chart generation."""
        mock_visualizer = Mock()
        mock_factory.create_visualizer.return_value = mock_visualizer

        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(main, ["task", str(csv_path), "--chart", "heatmap"])
            assert result.exit_code == 0
            mock_factory.create_visualizer.assert_called_once()
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.VisualizationFactory")
    def test_task_command_with_show_chart(self, mock_factory: Any) -> None:
        """Test task command with show chart format."""
        mock_visualizer = Mock()
        mock_factory.create_visualizer.return_value = mock_visualizer

        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["task", str(csv_path), "--chart", "bar", "--chart-format", "show"],
            )
            assert result.exit_code == 0
            mock_visualizer.show_chart.assert_called_once()
        finally:
            csv_path.unlink()

    @patch("src.tcc_analyzer.cli.VisualizationFactory")
    def test_chart_generation_error_handling(self, mock_factory: Any) -> None:
        """Test chart generation error handling."""
        # Mock visualizer to raise an exception
        mock_factory.create_visualizer.side_effect = Exception("Chart creation failed")

        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(main, ["task", str(csv_path), "--chart", "bar"])
            assert result.exit_code != 0
            assert "Error generating chart" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_with_mode_group_and_chart(self) -> None:
        """Test task command with mode grouping and chart."""
        with patch("src.tcc_analyzer.cli.VisualizationFactory") as mock_factory:
            mock_visualizer = Mock()
            mock_factory.create_visualizer.return_value = mock_visualizer

            csv_content = (
                "プロジェクト名,モード名,実績時間\n"
                "Work,Focus,02:00:00\n"
                "Study,Review,01:00:00\n"
            )

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                f.write(csv_content)
                f.flush()
                csv_path = Path(f.name)

            try:
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    ["task", str(csv_path), "--group-by", "mode", "--chart", "bar"],
                )
                assert result.exit_code == 0
                mock_factory.create_visualizer.assert_called_once()
            finally:
                csv_path.unlink()

    def test_task_command_with_project_mode_group_and_chart(self) -> None:
        """Test task command with project-mode grouping and chart."""
        with patch("src.tcc_analyzer.cli.VisualizationFactory") as mock_factory:
            mock_visualizer = Mock()
            mock_factory.create_visualizer.return_value = mock_visualizer

            csv_content = (
                "プロジェクト名,モード名,実績時間\n"
                "Work,Focus,02:00:00\n"
                "Study,Review,01:00:00\n"
            )

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                f.write(csv_content)
                f.flush()
                csv_path = Path(f.name)

            try:
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    [
                        "task",
                        str(csv_path),
                        "--group-by",
                        "project-mode",
                        "--chart",
                        "pie",
                    ],
                )
                assert result.exit_code == 0
                mock_factory.create_visualizer.assert_called_once()
            finally:
                csv_path.unlink()

    def test_task_command_invalid_base_time_edge_cases(self) -> None:
        """Test task command with various invalid base time formats."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()

            # Test zero time (00:00)
            result = runner.invoke(
                main, ["task", str(csv_path), "--base-time", "00:00"]
            )
            assert result.exit_code != 0
            assert "Invalid base time format" in result.output

            # Test zero time with seconds (00:00:00)
            result = runner.invoke(
                main, ["task", str(csv_path), "--base-time", "00:00:00"]
            )
            assert result.exit_code != 0
            assert "Invalid base time format" in result.output

            # Test invalid format
            result = runner.invoke(
                main, ["task", str(csv_path), "--base-time", "invalid"]
            )
            assert result.exit_code != 0
            assert "Invalid base time format" in result.output

            # Test valid formats (should succeed)
            result = runner.invoke(
                main, ["task", str(csv_path), "--base-time", "08:30"]
            )
            assert result.exit_code == 0

            result = runner.invoke(
                main, ["task", str(csv_path), "--base-time", "08:30:45"]
            )
            assert result.exit_code == 0
        finally:
            csv_path.unlink()

    def test_import_fallback_mechanism(self) -> None:
        """Test the import fallback mechanism."""
        # This test verifies that the fallback import paths exist and are importable
        # We can't easily test the actual ImportError fallback in the CLI module itself
        # without complex mocking, but we can test that the fallback imports work

        # Test that the imported modules are available
        # Since they are already imported at module level, we can check they exist
        # Import moved to the test to avoid linting issue about top-level imports
        import sys  # noqa: PLC0415

        sys.path.insert(0, "src")
        try:
            from tcc_analyzer import cli  # noqa: PLC0415

            # Verify the CLI module has the necessary components
            assert hasattr(cli, "TaskAnalyzer")
            assert hasattr(cli, "ChartType")
            assert hasattr(cli, "OutputFormat")
            assert hasattr(cli, "VisualizationFactory")
            assert hasattr(cli, "DataProcessor")
        finally:
            sys.path.pop(0)

    def test_chart_output_path_generation(self) -> None:
        """Test automatic chart output path generation."""
        with patch("src.tcc_analyzer.cli.VisualizationFactory") as mock_factory:
            mock_visualizer = Mock()
            mock_factory.create_visualizer.return_value = mock_visualizer

            csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                f.write(csv_content)
                f.flush()
                csv_path = Path(f.name)

            try:
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    [
                        "task",
                        str(csv_path),
                        "--chart",
                        "bar",
                        # No --chart-output specified, should auto-generate
                    ],
                )
                assert result.exit_code == 0

                # Verify that save_chart was called (with auto-generated path)
                mock_visualizer.save_chart.assert_called_once()

                # Check that the output message includes the generated filename
                assert "Chart saved to:" in result.output
            finally:
                csv_path.unlink()

    def test_all_chart_formats(self) -> None:
        """Test all supported chart output formats."""
        with patch("src.tcc_analyzer.cli.VisualizationFactory") as mock_factory:
            mock_visualizer = Mock()
            mock_factory.create_visualizer.return_value = mock_visualizer

            csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                f.write(csv_content)
                f.flush()
                csv_path = Path(f.name)

            try:
                runner = CliRunner()
                formats = ["png", "svg", "pdf"]

                for fmt in formats:
                    mock_factory.reset_mock()
                    mock_visualizer.reset_mock()

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
                    mock_factory.create_visualizer.assert_called_once()
                    mock_visualizer.save_chart.assert_called_once()
            finally:
                csv_path.unlink()
