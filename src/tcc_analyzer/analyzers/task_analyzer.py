"""Task analyzer for TaskChute Cloud logs (refactored version)."""

from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from .data_analyzer import DataAnalyzer
from .data_loader import DataLoader
from .result_formatter import ResultFormatter
from .result_processor import ResultProcessor
from .result_sorter import ResultSorter
from .time_parser import TimeParser


class TaskAnalyzer:
    """Analyzer for TaskChute Cloud task logs."""

    def __init__(self, csv_files: Path | list[Path]) -> None:
        """Initialize the analyzer with CSV file(s)."""
        self._data_loader = DataLoader(csv_files)
        self._data_analyzer = DataAnalyzer()
        self._result_formatter = ResultFormatter()

    def set_tag_filter(self, tag_filter: str) -> None:
        """Set tag filter for analysis."""
        self._data_analyzer.set_tag_filter(tag_filter)

    def analyze_by_project(
        self, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze tasks by project and return aggregated results."""
        return self._analyze_by_type("project", sort_by, reverse)

    def analyze_by_mode(
        self, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze tasks by mode and return aggregated results."""
        return self._analyze_by_type("mode", sort_by, reverse)

    def analyze_by_project_mode(
        self, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze tasks by project-mode combination and return results."""
        return self._analyze_by_type("project-mode", sort_by, reverse)

    def add_total_row_and_percentages(
        self, results: list[dict[str, Any]], analysis_type: str
    ) -> list[dict[str, Any]]:
        """Add total row and percentage columns to results."""
        return ResultProcessor.add_total_row_and_percentages(results, analysis_type)

    def _delegate_display(
        self,
        method_name: str,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Delegate display to result formatter."""
        method = getattr(self._result_formatter, method_name)
        method(results, analysis_type, base_time)

    def display_table(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as a rich table."""
        self._delegate_display("display_table", results, analysis_type, base_time)

    def display_json(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as JSON."""
        self._delegate_display("display_json", results, analysis_type, base_time)

    def display_csv(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as CSV."""
        self._delegate_display("display_csv", results, analysis_type, base_time)

    def display_slack(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results in Slack-formatted message."""
        self._delegate_display("display_slack", results, analysis_type, base_time)

    def _analyze_by_type(
        self, analysis_type: str, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze data by specified type with sorting options."""
        data = self._data_loader.load_data()
        results = self._data_analyzer.analyze_by_type(data, analysis_type)
        return ResultSorter.sort_results(results, sort_by, reverse, analysis_type)

    # Backward compatibility methods for tests
    def _add_percentage_to_results(
        self, results: list[dict[str, Any]], base_time_str: str
    ) -> list[dict[str, Any]]:
        """Add percentage column to results based on base time."""
        return ResultProcessor.add_percentage_to_results(results, base_time_str)

    def _create_total_row(
        self, total_duration: timedelta, total_task_count: int, analysis_type: str
    ) -> dict[str, Any]:
        """Create total row for analysis results."""
        return ResultProcessor.create_total_row(
            total_duration, total_task_count, analysis_type
        )

    @property
    def _tag_filter(self) -> str | None:
        """Get tag filter for backward compatibility."""
        return self._data_analyzer.tag_filter

    def _load_data(self) -> pd.DataFrame:
        """Load data for backward compatibility."""
        return self._data_loader.load_data()

    def _parse_time_duration(self, time_str: str | float) -> timedelta:
        """Parse time duration for backward compatibility."""
        return TimeParser.parse_time_duration(time_str)

    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for backward compatibility."""
        return TimeParser.format_duration(duration)

    def _calculate_percentage(self, duration: timedelta, base_time_str: str) -> float:
        """Calculate percentage for backward compatibility."""
        return TimeParser.calculate_percentage(duration, base_time_str)

    def _parse_tag_names(self, tag_names_str: str | float) -> list[str]:
        """Parse tag names for backward compatibility."""
        return self._data_analyzer.parse_tag_names(tag_names_str)

    def _filter_by_tag(self, data: pd.DataFrame, tag_filter: str) -> pd.DataFrame:
        """Filter by tag for backward compatibility."""
        return self._data_analyzer.filter_by_tag(data, tag_filter)

    def _get_analysis_config(self, analysis_type: str) -> dict[str, Any]:
        """Get configuration for analysis type."""
        return self._result_formatter.get_analysis_config(analysis_type)

    def _create_table(
        self, results: list[dict[str, Any]], analysis_type: str, base_time: str | None
    ):
        """Create table for analysis results."""
        return self._result_formatter.create_table(results, analysis_type, base_time)

    def _is_total_row(self, index: int, row_data: list[str], total_rows: int) -> bool:
        """Check if the current row is a total row."""
        return self._result_formatter.is_total_row(index, row_data, total_rows)
