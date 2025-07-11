"""Tests for CLI analysis type functionality."""

import tempfile
from pathlib import Path

from click.testing import CliRunner
from src.tcc_analyzer.cli import main


class TestCLIAnalysisTypes:
    """Test class for CLI analysis type functionality."""

    def test_task_command_mode_analysis(self) -> None:
        """Test task command with mode analysis."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Focus,01:00:00\n"
            "Work,Review,01:30:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(main, ["task", str(csv_path), "--group-by", "mode"])
            assert result.exit_code == 0
            assert "Analysis" in result.output
            assert "Focus" in result.output
            assert "Review" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_project_mode_analysis(self) -> None:
        """Test task command with project-mode analysis."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Focus,01:00:00\n"
            "Work,Review,01:30:00\n"
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
            assert "Analysis" in result.output
            assert "Work" in result.output
            assert "Study" in result.output
            assert "Focus" in result.output
            assert "Review" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_with_mode_group_and_chart(self) -> None:
        """Test task command with mode grouping and chart generation."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Focus,01:00:00\n"
            "Work,Review,01:30:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
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
                    "mode",
                    "--chart",
                    "bar",
                    "--chart-format",
                    "png",
                ],
            )
            assert result.exit_code == 0
            assert "Chart saved" in result.output
            assert "mode_analysis_chart.png" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_with_project_mode_group_and_chart(self) -> None:
        """Test task command with project-mode grouping and chart generation."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Focus,01:00:00\n"
            "Work,Review,01:30:00\n"
            "Personal,Task,00:45:00\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
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
                    "--chart-format",
                    "svg",
                ],
            )
            assert result.exit_code == 0
            assert "Chart saved" in result.output
            assert "project_mode_analysis_chart.svg" in result.output
        finally:
            csv_path.unlink()