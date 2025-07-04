"""Tests for CLI module."""

import tempfile
from pathlib import Path

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
            assert "Work,02:00:00,1" in result.output
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
            assert "Use HH:MM or HH:MM:SS format" in result.output

            # Test another invalid format
            result = runner.invoke(main, ["task", str(csv_path), "--base-time", "1:30"])
            assert result.exit_code != 0
            assert "Invalid base time format" in result.output
        finally:
            csv_path.unlink()
