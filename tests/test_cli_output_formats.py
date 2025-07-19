"""Tests for CLI output format functionality."""

import tempfile
from pathlib import Path

from click.testing import CliRunner
from src.tcc_analyzer.cli import main


class TestCLIOutputFormats:
    """Test class for CLI output format functionality."""

    def test_task_command_json_output(self) -> None:
        """Test task command with JSON output."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--output-format", "json"]
            )
            assert result.exit_code == 0
            # JSON output should contain project information
            assert "Work" in result.output
            assert "{" in result.output  # JSON structure
        finally:
            csv_path.unlink()

    def test_task_command_csv_output(self) -> None:
        """Test task command with CSV output."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Focus,01:00:00\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--output-format", "csv"]
            )
            assert result.exit_code == 0
            # CSV output should contain headers and data
            assert "Project" in result.output
            assert "Work" in result.output
            assert "Study" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_slack_output(self) -> None:
        """Test task command with Slack output format."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            runner = CliRunner()
            result = runner.invoke(
                main, ["task", str(csv_path), "--output-format", "slack"]
            )
            assert result.exit_code == 0
            assert "⏰ TaskChute Cloud 分析レポート" in result.output
            assert "*📂 プロジェクト別時間分析*" in result.output
            assert "Work" in result.output
            assert "```" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_slack_output_with_base_time(self) -> None:
        """Test task command with Slack output format and base time."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
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
                    "--output-format",
                    "slack",
                    "--base-time",
                    "08:00",
                ],
            )
            assert result.exit_code == 0
            assert "⏰ TaskChute Cloud 分析レポート (基準時間: 08:00)" in result.output
            assert "*📂 プロジェクト別時間分析*" in result.output
            assert "25.0%" in result.output  # 2/8 * 100
        finally:
            csv_path.unlink()

    def test_task_command_slack_output_mode_analysis(self) -> None:
        """Test task command with Slack output for mode analysis."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Focus,01:00:00\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
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
                    "--output-format",
                    "slack",
                    "--group-by",
                    "mode",
                ],
            )
            assert result.exit_code == 0
            assert "⏰ TaskChute Cloud 分析レポート" in result.output
            assert "*🎯 モード別時間分析*" in result.output
            assert "Focus" in result.output
        finally:
            csv_path.unlink()

    def test_task_command_slack_output_project_mode_analysis(self) -> None:
        """Test task command with Slack output for project-mode analysis."""
        csv_content = (
            "プロジェクト名,モード名,実績時間\n"
            "Work,Focus,02:00:00\n"
            "Study,Review,01:00:00\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
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
                    "--output-format",
                    "slack",
                    "--group-by",
                    "project-mode",
                ],
            )
            assert result.exit_code == 0
            assert "⏰ TaskChute Cloud 分析レポート" in result.output
            assert "*📂🎯 プロジェクト×モード別時間分析*" in result.output  # noqa: RUF001
            assert "Work" in result.output
            assert "Focus" in result.output
        finally:
            csv_path.unlink()
