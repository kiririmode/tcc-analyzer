"""Task analyzer for TaskChute Cloud logs."""

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console
from rich.table import Table

# Constants for time validation
MIN_TIME_PARTS = 2
MAX_TIME_PARTS = 3
REQUIRED_DIGIT_LENGTH = 2
MAX_MINUTES_SECONDS = 60


class TaskAnalyzer:
    """Analyzer for TaskChute Cloud task logs."""

    def __init__(self, csv_file: Path) -> None:
        """Initialize the analyzer with a CSV file."""
        self.csv_file = csv_file
        self.console = Console()
        self._data: pd.DataFrame | None = None

    def _load_data(self) -> pd.DataFrame:
        """Load and parse the CSV data."""
        if self._data is None:
            try:
                # Read CSV with UTF-8 encoding, handling BOM
                self._data = pd.read_csv(self.csv_file, encoding="utf-8-sig")  # type: ignore
                # Parse dates if columns exist
                if (
                    "開始日時" in self._data.columns
                    and "終了日時" in self._data.columns
                ):
                    self._data["開始日時"] = pd.to_datetime(self._data["開始日時"])  # type: ignore
                    self._data["終了日時"] = pd.to_datetime(self._data["終了日時"])  # type: ignore
            except UnicodeDecodeError:
                # Fallback to Shift-JIS if UTF-8 fails
                self._data = pd.read_csv(self.csv_file, encoding="shift-jis")  # type: ignore
                # Parse dates if columns exist
                if (
                    "開始日時" in self._data.columns
                    and "終了日時" in self._data.columns
                ):
                    self._data["開始日時"] = pd.to_datetime(self._data["開始日時"])  # type: ignore
                    self._data["終了日時"] = pd.to_datetime(self._data["終了日時"])  # type: ignore
        return self._data

    def _parse_time_duration(self, time_str: str | float) -> timedelta:
        """Parse time duration string (HH:MM or HH:MM:SS) to timedelta."""
        if pd.isna(time_str) or time_str == "":  # type: ignore
            return timedelta(0)

        if not isinstance(time_str, str):
            return timedelta(0)

        return self._parse_time_string(time_str)

    def _parse_time_string(self, time_str: str) -> timedelta:
        """Parse time string and return timedelta."""
        try:
            parts = time_str.split(":")

            if not self._is_valid_time_format(parts):
                return timedelta(0)

            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2]) if len(parts) >= MAX_TIME_PARTS else 0

            if not self._is_valid_time_range(minutes, seconds):
                return timedelta(0)

            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except (ValueError, IndexError):
            return timedelta(0)

    def _is_valid_time_format(self, parts: list[str]) -> bool:
        """Check if time parts have valid format."""
        if len(parts) < MIN_TIME_PARTS or len(parts) > MAX_TIME_PARTS:
            return False
        if (
            len(parts[0]) != REQUIRED_DIGIT_LENGTH
            or len(parts[1]) != REQUIRED_DIGIT_LENGTH
        ):
            return False
        if len(parts) == MAX_TIME_PARTS and len(parts[2]) != REQUIRED_DIGIT_LENGTH:
            return False
        return True

    def _is_valid_time_range(self, minutes: int, seconds: int) -> bool:
        """Check if time values are within valid range."""
        return minutes < MAX_MINUTES_SECONDS and seconds < MAX_MINUTES_SECONDS

    def _format_duration(self, duration: timedelta) -> str:
        """Format timedelta as HH:MM:SS string."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _calculate_percentage(self, duration: timedelta, base_time_str: str) -> float:
        """Calculate percentage of duration against base time."""
        base_duration = self._parse_time_duration(base_time_str)
        if base_duration.total_seconds() == 0:
            return 0.0
        return (duration.total_seconds() / base_duration.total_seconds()) * 100

    def _add_percentage_to_results(
        self, results: list[dict[str, Any]], base_time_str: str
    ) -> list[dict[str, Any]]:
        """Add percentage column to results based on base time."""
        updated_results: list[dict[str, Any]] = []
        for result in results:
            updated_result = result.copy()
            duration = timedelta(seconds=result["total_seconds"])
            percentage = self._calculate_percentage(duration, base_time_str)
            updated_result["percentage"] = f"{percentage:.1f}%"
            updated_results.append(updated_result)
        return updated_results

    def _aggregate_by_fields(
        self, data: pd.DataFrame, fields: list[str], result_key_mapping: dict[str, str]
    ) -> dict[str, dict[str, Any]]:
        """Aggregate data by specified fields and return aggregated results."""
        times: dict[str, timedelta] = {}
        task_counts: dict[str, int] = {}
        field_values: dict[str, dict[str, str]] = {}

        for _, row in data.iterrows():  # type: ignore
            field_data = self._extract_field_data(row, fields)
            if field_data is None:
                continue

            composite_key = self._create_composite_key(field_data, fields)
            duration = self._parse_time_duration(row["実績時間"])

            self._update_aggregation_data(
                composite_key, duration, field_data, times, task_counts, field_values
            )

        return self._convert_to_results(
            times, task_counts, field_values, result_key_mapping, fields
        )

    def _extract_field_data(
        self,
        row: pd.Series,
        fields: list[str],  # type: ignore[misc]
    ) -> dict[str, str] | None:
        """Extract and validate field data from a row."""
        field_data: dict[str, str] = {}

        for field in fields:
            value = row[field]
            if pd.isna(value) or value == "":  # type: ignore[misc]
                return None
            if not isinstance(value, str):
                return None
            field_data[field] = value

        return field_data

    def _create_composite_key(
        self, field_data: dict[str, str], fields: list[str]
    ) -> str:
        """Create composite key from field data."""
        if len(fields) == 1:
            return field_data[fields[0]]
        return " | ".join(field_data[field] for field in fields)

    def _update_aggregation_data(
        self,
        composite_key: str,
        duration: timedelta,
        field_data: dict[str, str],
        times: dict[str, timedelta],
        task_counts: dict[str, int],
        field_values: dict[str, dict[str, str]],
    ) -> None:
        """Update aggregation dictionaries with new data."""
        if composite_key not in times:
            times[composite_key] = timedelta(0)
            task_counts[composite_key] = 0
            field_values[composite_key] = field_data

        times[composite_key] += duration
        task_counts[composite_key] += 1

    def _convert_to_results(
        self,
        times: dict[str, timedelta],
        task_counts: dict[str, int],
        field_values: dict[str, dict[str, str]],
        result_key_mapping: dict[str, str],
        fields: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Convert aggregated data to results format."""
        results: dict[str, dict[str, Any]] = {}

        for composite_key, total_time in times.items():
            result = self._create_result_entry(
                total_time,
                task_counts[composite_key],
                field_values[composite_key],
                result_key_mapping,
                fields,
                composite_key,
            )
            results[composite_key] = result

        return results

    def _create_result_entry(
        self,
        total_time: timedelta,
        task_count: int,
        field_data: dict[str, str],
        result_key_mapping: dict[str, str],
        fields: list[str],
        composite_key: str,
    ) -> dict[str, Any]:
        """Create a single result entry."""
        result: dict[str, Any] = {
            "total_time": self._format_duration(total_time),
            "total_seconds": int(total_time.total_seconds()),
            "task_count": str(task_count),
        }

        # Add field-specific keys
        for field, result_key in result_key_mapping.items():
            if field in field_data:
                result[result_key] = field_data[field]

        # Add composite key for project-mode combination
        if len(fields) > 1:
            result["project_mode"] = composite_key

        return result

    def _sort_results(
        self,
        results: list[dict[str, Any]],
        sort_by: str,
        reverse: bool,
        analysis_type: str,
    ) -> list[dict[str, Any]]:
        """Sort results based on sort_by parameter and analysis type."""
        if sort_by == "time":
            results.sort(key=lambda x: int(x["total_seconds"]), reverse=reverse)
        elif sort_by == "project" and analysis_type in ["project", "project-mode"]:
            if analysis_type == "project":
                results.sort(key=lambda x: str(x["project"]), reverse=reverse)
            else:  # project-mode
                results.sort(
                    key=lambda x: (str(x["project"]), str(x["mode"])), reverse=reverse
                )
        elif sort_by == "mode" and analysis_type in ["mode", "project-mode"]:
            if analysis_type == "mode":
                results.sort(key=lambda x: str(x["mode"]), reverse=reverse)
            else:  # project-mode
                results.sort(
                    key=lambda x: (str(x["mode"]), str(x["project"])), reverse=reverse
                )
        # Default sorting based on analysis type
        elif analysis_type == "project":
            results.sort(key=lambda x: str(x["project"]), reverse=reverse)
        elif analysis_type == "mode":
            results.sort(key=lambda x: str(x["mode"]), reverse=reverse)
        else:  # project-mode
            results.sort(
                key=lambda x: (str(x["project"]), str(x["mode"])), reverse=reverse
            )

        return results

    def _analyze_by_type(
        self, analysis_type: str, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze data by specified type with sorting options."""
        data = self._load_data()

        # Define field mappings for each analysis type
        field_mappings = {
            "project": (["プロジェクト名"], {"プロジェクト名": "project"}),
            "mode": (["モード名"], {"モード名": "mode"}),
            "project-mode": (
                ["プロジェクト名", "モード名"],
                {"プロジェクト名": "project", "モード名": "mode"},
            ),
        }

        fields, mapping = field_mappings[analysis_type]
        aggregated = self._aggregate_by_fields(data, fields, mapping)
        results = list(aggregated.values())
        return self._sort_results(results, sort_by, reverse, analysis_type)

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

    @classmethod
    def _get_analysis_config(cls, analysis_type: str) -> dict[str, Any]:
        """Get configuration for analysis type."""
        return {
            "mode": {
                "title": "TaskChute Cloud - Mode Time Analysis",
                "columns": [
                    ("Mode", "cyan"),
                    ("Total Time", "green"),
                    ("Task Count", "yellow"),
                ],
                "percentage_style": "magenta",
                "fields": ["mode", "total_time", "task_count"],
                "csv_header": "Mode,Total Time,Task Count",
            },
            "project": {
                "title": "TaskChute Cloud - Project Time Analysis",
                "columns": [
                    ("Project", "cyan"),
                    ("Total Time", "green"),
                    ("Task Count", "yellow"),
                ],
                "percentage_style": "bright_red",
                "fields": ["project", "total_time", "task_count"],
                "csv_header": "Project,Total Time,Task Count",
            },
            "project-mode": {
                "title": "TaskChute Cloud - Project x Mode Time Analysis",
                "columns": [
                    ("Project", "cyan"),
                    ("Mode", "magenta"),
                    ("Total Time", "green"),
                    ("Task Count", "yellow"),
                ],
                "percentage_style": "bright_blue",
                "fields": ["project", "mode", "total_time", "task_count"],
                "csv_header": "Project,Mode,Total Time,Task Count",
            },
        }[analysis_type]

    def _prepare_output_data(
        self, results: list[dict[str, Any]], analysis_type: str, base_time: str | None
    ) -> tuple[dict[str, Any], list[list[str]]]:
        """Prepare data for both table and CSV output."""
        config = self._get_analysis_config(analysis_type)

        # Prepare row data
        rows: list[list[str]] = []
        for result in results:
            row_data = [str(result[field]) for field in config["fields"]]
            if base_time is not None:
                row_data.append(str(result["percentage"]))
            rows.append(row_data)

        return config, rows

    def _create_table(
        self, results: list[dict[str, Any]], analysis_type: str, base_time: str | None
    ) -> Table:
        """Create table for analysis results."""
        config, rows = self._prepare_output_data(results, analysis_type, base_time)

        title = config["title"]
        if base_time is not None:
            title += f" (Base: {base_time})"

        table = Table(title=title)

        # Add columns
        for column_name, style in config["columns"]:
            table.add_column(
                column_name,
                style=style,
                no_wrap=True if column_name in ["Mode", "Project"] else False,
                justify="right"
                if column_name in ["Total Time", "Task Count"]
                else "left",
            )

        if base_time is not None:
            table.add_column(
                "Percentage", style=config["percentage_style"], justify="right"
            )

        # Add rows
        for row_data in rows:
            table.add_row(*row_data)

        return table

    def display_table(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as a rich table."""
        # Add percentage column if base_time is provided
        if base_time is not None:
            results = self._add_percentage_to_results(results, base_time)

        table = self._create_table(results, analysis_type, base_time)

        self.console.print(table)

    def display_json(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as JSON."""
        # Add percentage column if base_time is provided
        if base_time is not None:
            results = self._add_percentage_to_results(results, base_time)

        config = self._get_analysis_config(analysis_type)
        json_results: list[dict[str, Any]] = []

        for result in results:
            json_result: dict[str, Any] = {}
            for field in config["fields"]:
                if field == "task_count":
                    json_result[field] = int(result[field])
                else:
                    json_result[field] = result[field]

            if base_time is not None:
                json_result["percentage"] = result["percentage"]

            json_results.append(json_result)

        # Create final output with metadata if base_time is provided
        if base_time is not None:
            output = {
                "base_time": base_time,
                "analysis_type": analysis_type,
                "results": json_results,
            }
        else:
            output = json_results

        print(json.dumps(output, ensure_ascii=False, indent=2))

    def _print_csv(
        self, results: list[dict[str, Any]], analysis_type: str, base_time: str | None
    ) -> None:
        """Print CSV output for analysis results."""
        config, rows = self._prepare_output_data(results, analysis_type, base_time)

        # Add base time information as comment if provided
        if base_time is not None:
            print(f"# Base Time: {base_time}")

        header = config["csv_header"]
        if base_time is not None:
            header += ",Percentage"
        print(header)

        for row_values in rows:
            print(",".join(row_values))

    def display_csv(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as CSV."""
        # Add percentage column if base_time is provided
        if base_time is not None:
            results = self._add_percentage_to_results(results, base_time)

        self._print_csv(results, analysis_type, base_time)
