"""Tests for CLI basic functionality."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from click.testing import CliRunner
from src.tcc_analyzer.cli import main


class TestCLIBasic:
    """Test class for CLI basic functionality."""

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

    def test_task_command_nonexistent_file(self) -> None:
        """Test task command with nonexistent file."""
        runner = CliRunner()
        result = runner.invoke(main, ["task", "nonexistent.csv"])
        assert result.exit_code != 0

    def test_import_fallback_mechanism(self) -> None:
        """Test that matplotlib import fallback works correctly."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            # Mock matplotlib import to fail
            with patch("builtins.__import__") as mock_import:

                def side_effect(name, *args, **kwargs):
                    if name == "matplotlib":
                        raise ImportError("matplotlib not available")
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = side_effect

                runner = CliRunner()
                # Should still work without charts
                result = runner.invoke(main, ["task", str(csv_path)])
                assert result.exit_code == 0

        finally:
            csv_path.unlink()

    def test_chart_generation_error_handling(self, mock_factory: Any) -> None:
        """Test error handling during chart generation."""
        csv_content = "プロジェクト名,モード名,実績時間\nWork,Focus,02:00:00\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            csv_path = Path(f.name)

        try:
            # Mock chart creation to raise an exception
            mock_chart = Mock()
            mock_chart.create_chart.side_effect = Exception("Chart creation failed")
            mock_factory.return_value = mock_chart

            with patch("src.tcc_analyzer.cli.ChartFactory", mock_factory):
                runner = CliRunner()
                result = runner.invoke(main, ["task", str(csv_path), "--chart", "bar"])
                # Should handle the error gracefully
                assert result.exit_code == 0
                assert "Error creating chart" in result.output

        finally:
            csv_path.unlink()