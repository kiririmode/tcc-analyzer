"""Task analyzer for TaskChute Cloud logs."""

import json
from collections.abc import Callable
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

    def __init__(self, csv_files: Path | list[Path]) -> None:
        """Initialize the analyzer with CSV file(s)."""
        if isinstance(csv_files, Path):
            self.csv_files = [csv_files]
        else:
            self.csv_files = csv_files
        self.console = Console()
        self._data: pd.DataFrame | None = None
        self._tag_filter: str | None = None

    def _parse_csv_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse date columns in CSV data."""
        if "開始日時" in df.columns and "終了日時" in df.columns:
            df["開始日時"] = pd.to_datetime(df["開始日時"])  # type: ignore
            df["終了日時"] = pd.to_datetime(df["終了日時"])  # type: ignore
        return df

    def _read_csv_file(self, csv_file: str | Path) -> pd.DataFrame:
        """Read a single CSV file with fallback encoding."""
        try:
            # Read CSV with UTF-8 encoding, handling BOM
            df = pd.read_csv(csv_file, encoding="utf-8-sig")  # type: ignore
            return self._parse_csv_dates(df)
        except UnicodeDecodeError:
            # Fallback to Shift-JIS if UTF-8 fails
            df = pd.read_csv(csv_file, encoding="shift-jis")  # type: ignore
            return self._parse_csv_dates(df)

    def _load_data(self) -> pd.DataFrame:
        """Load and parse the CSV data."""
        if self._data is None:
            dataframes: list[pd.DataFrame] = []
            for csv_file in self.csv_files:
                df = self._read_csv_file(str(csv_file))
                dataframes.append(df)

            # Combine all dataframes
            if len(dataframes) == 1:
                self._data = dataframes[0]
            else:
                self._data = pd.concat(dataframes, ignore_index=True)

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
        """Format timedelta as HH:MM string."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

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

    def add_total_row_and_percentages(
        self, results: list[dict[str, Any]], analysis_type: str
    ) -> list[dict[str, Any]]:
        """Add total row and percentage columns to results."""
        if not results:
            return results

        # Calculate totals
        total_seconds = sum(result["total_seconds"] for result in results)
        total_task_count = sum(int(result["task_count"]) for result in results)
        total_duration = timedelta(seconds=total_seconds)

        # Add percentage to each result
        updated_results: list[dict[str, Any]] = []
        for result in results:
            updated_result = result.copy()
            # Calculate percentage of total
            if total_seconds > 0:
                percentage = (result["total_seconds"] / total_seconds) * 100
                updated_result["percentage"] = f"{percentage:.1f}%"
            else:
                updated_result["percentage"] = "0.0%"
            updated_results.append(updated_result)

        # Create total row
        total_row = self._create_total_row(
            total_duration, total_task_count, analysis_type
        )
        updated_results.append(total_row)

        return updated_results

    def _create_total_row(
        self, total_duration: timedelta, total_task_count: int, analysis_type: str
    ) -> dict[str, Any]:
        """Create total row for analysis results."""
        total_row: dict[str, Any] = {
            "total_time": self._format_duration(total_duration),
            "total_seconds": int(total_duration.total_seconds()),
            "task_count": str(total_task_count),
            "percentage": "100.0%",
        }

        # Add type-specific fields for total row
        if analysis_type == "project":
            total_row["project"] = "Total"
        elif analysis_type == "mode":
            total_row["mode"] = "Total"
        elif analysis_type == "project-mode":
            total_row["project"] = "Total"
            total_row["mode"] = "-"
            total_row["project_mode"] = "Total | -"

        return total_row

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

    def _parse_tag_names(self, tag_names_str: str | float) -> list[str]:
        """Parse tag names from CSV string (comma-separated)."""
        if pd.isna(tag_names_str) or tag_names_str == "":  # type: ignore[arg-type]
            return []

        if not isinstance(tag_names_str, str):
            return []

        # Split by comma and strip whitespace
        tags = [tag.strip() for tag in tag_names_str.split(",")]
        return [tag for tag in tags if tag]  # Remove empty strings

    def _filter_by_tag(self, data: pd.DataFrame, tag_filter: str) -> pd.DataFrame:
        """Filter data by tag name."""
        if not tag_filter:
            return data

        # Create a mask for rows that contain the specified tag
        mask = data["タグ名"].apply(lambda x: tag_filter in self._parse_tag_names(x))  # type: ignore[arg-type]

        return data[mask]

    def set_tag_filter(self, tag_filter: str) -> None:
        """Set tag filter for analysis."""
        self._tag_filter = tag_filter

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

    def _get_sort_key(
        self, sort_by: str, analysis_type: str
    ) -> Callable[[dict[str, Any]], Any]:
        """Get sort key function based on sort_by and analysis_type."""
        if sort_by == "time":
            return lambda x: int(x["total_seconds"])

        return self._get_default_sort_key(sort_by, analysis_type)

    def _get_default_sort_key(
        self, sort_by: str, analysis_type: str
    ) -> Callable[[dict[str, Any]], Any]:
        """Get default sort key based on sort_by and analysis_type."""
        # Define sort key configurations
        sort_configs: dict[tuple[str, str], Callable[[dict[str, Any]], Any]] = {
            ("project", "project"): lambda x: str(x["project"]),
            ("project", "project-mode"): lambda x: (str(x["project"]), str(x["mode"])),
            ("mode", "mode"): lambda x: str(x["mode"]),
            ("mode", "project-mode"): lambda x: (str(x["mode"]), str(x["project"])),
        }

        # Try to find specific configuration
        key = (sort_by, analysis_type)
        if key in sort_configs:
            return sort_configs[key]

        # Fall back to default based on analysis type
        default_configs: dict[str, Callable[[dict[str, Any]], Any]] = {
            "project": lambda x: str(x["project"]),
            "mode": lambda x: str(x["mode"]),
        }

        def default_func(x: dict[str, Any]) -> tuple[str, str]:
            return (str(x["project"]), str(x["mode"]))

        return default_configs.get(analysis_type, default_func)

    def _sort_results(
        self,
        results: list[dict[str, Any]],
        sort_by: str,
        reverse: bool,
        analysis_type: str,
    ) -> list[dict[str, Any]]:
        """Sort results based on sort_by parameter and analysis type."""
        sort_key = self._get_sort_key(sort_by, analysis_type)
        results.sort(key=sort_key, reverse=reverse)
        return results

    def _analyze_by_type(
        self, analysis_type: str, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze data by specified type with sorting options."""
        data = self._load_data()

        # Apply tag filter if set
        if self._tag_filter:
            data = self._filter_by_tag(data, self._tag_filter)

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
                    ("Percentage", "magenta"),
                ],
                "percentage_style": "magenta",
                "fields": ["mode", "total_time", "task_count", "percentage"],
                "csv_header": "Mode,Total Time,Task Count,Percentage",
            },
            "project": {
                "title": "TaskChute Cloud - Project Time Analysis",
                "columns": [
                    ("Project", "cyan"),
                    ("Total Time", "green"),
                    ("Task Count", "yellow"),
                    ("Percentage", "bright_red"),
                ],
                "percentage_style": "bright_red",
                "fields": ["project", "total_time", "task_count", "percentage"],
                "csv_header": "Project,Total Time,Task Count,Percentage",
            },
            "project-mode": {
                "title": "TaskChute Cloud - Project x Mode Time Analysis",
                "columns": [
                    ("Project", "cyan"),
                    ("Mode", "magenta"),
                    ("Total Time", "green"),
                    ("Task Count", "yellow"),
                    ("Percentage", "bright_blue"),
                ],
                "percentage_style": "bright_blue",
                "fields": ["project", "mode", "total_time", "task_count", "percentage"],
                "csv_header": "Project,Mode,Total Time,Task Count,Percentage",
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
            row_data: list[str] = []
            for field in config["fields"]:
                if field == "percentage" and field not in result:
                    # Skip percentage field if not present in result
                    continue
                row_data.append(str(result[field]))
            # Add base_time percentage only if provided and different from internal %
            if base_time is not None and "percentage" not in config["fields"]:
                row_data.append(str(result["percentage"]))
            rows.append(row_data)

        return config, rows

    def _create_table(
        self, results: list[dict[str, Any]], analysis_type: str, base_time: str | None
    ) -> Table:
        """Create table for analysis results."""
        config, rows = self._prepare_output_data(results, analysis_type, base_time)

        title = self._build_table_title(config["title"], base_time)
        table = Table(title=title)

        self._add_table_columns(table, config, results, base_time)
        self._add_table_rows(table, rows)

        return table

    def _build_table_title(self, base_title: str, base_time: str | None) -> str:
        """Build table title with optional base time."""
        if base_time is not None:
            return f"{base_title} (Base: {base_time})"
        return base_title

    def _add_table_columns(
        self,
        table: Table,
        config: dict[str, Any],
        results: list[dict[str, Any]],
        base_time: str | None,
    ) -> None:
        """Add columns to the table based on configuration and data."""
        has_percentage = bool(results and "percentage" in results[0])

        for column_name, style in config["columns"]:
            if self._should_skip_column(column_name, has_percentage):
                continue
            self._add_single_column(table, column_name, style)

        self._add_base_time_column(table, config, base_time, has_percentage)

    def _should_skip_column(self, column_name: str, has_percentage: bool) -> bool:
        """Check if column should be skipped."""
        return column_name == "Percentage" and not has_percentage

    def _add_single_column(self, table: Table, column_name: str, style: str) -> None:
        """Add a single column to the table."""
        no_wrap_columns = ["Mode", "Project"]
        right_align_columns = ["Total Time", "Task Count", "Percentage"]

        table.add_column(
            column_name,
            style=style,
            no_wrap=column_name in no_wrap_columns,
            justify="right" if column_name in right_align_columns else "left",
        )

    def _add_base_time_column(
        self,
        table: Table,
        config: dict[str, Any],
        base_time: str | None,
        has_percentage: bool,
    ) -> None:
        """Add base time percentage column if needed."""
        column_names = [col[0] for col in config["columns"]]
        should_add = (
            base_time is not None
            and "percentage" not in column_names
            and not has_percentage
        )

        if should_add:
            table.add_column(
                "Base %", style=config["percentage_style"], justify="right"
            )

    def _add_table_rows(self, table: Table, rows: list[list[str]]) -> None:
        """Add all rows to the table with appropriate styling."""
        for i, row_data in enumerate(rows):
            is_total_row = self._is_total_row(i, row_data, len(rows))

            if is_total_row:
                self._add_total_row(table, row_data, i)
            else:
                table.add_row(*row_data)

    def _is_total_row(self, index: int, row_data: list[str], total_rows: int) -> bool:
        """Check if the current row is a total row."""
        return index == total_rows - 1 and any(
            "Total" in str(data) for data in row_data
        )

    def _add_total_row(self, table: Table, row_data: list[str], index: int) -> None:
        """Add total row with special formatting."""
        if index > 0:
            table.add_section()
        styled_row = [f"[bold]{data}[/bold]" for data in row_data]
        table.add_row(*styled_row)

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
                if field == "percentage" and field not in result:
                    # Skip percentage field if not present in result
                    continue
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

        self._print_csv_header(config, results, base_time)
        self._print_csv_rows(rows)

    def _print_csv_header(
        self,
        config: dict[str, Any],
        results: list[dict[str, Any]],
        base_time: str | None,
    ) -> None:
        """Print CSV header with base time comment and column names."""
        if base_time is not None:
            print(f"# Base Time: {base_time}")

        header = self._build_csv_header(config, results, base_time)
        print(header)

    def _build_csv_header(
        self,
        config: dict[str, Any],
        results: list[dict[str, Any]],
        base_time: str | None,
    ) -> str:
        """Build CSV header string based on data and configuration."""
        has_percentage = bool(results and "percentage" in results[0])
        header_fields = self._get_csv_header_fields(config, has_percentage)
        header = ",".join(header_fields)

        if self._should_add_base_time_header(base_time, has_percentage):
            header += ",Base %"

        return header

    def _get_csv_header_fields(
        self, config: dict[str, Any], has_percentage: bool
    ) -> list[str]:
        """Get CSV header field names."""
        header_fields: list[str] = []

        for field in config["fields"]:
            if field == "percentage" and not has_percentage:
                continue
            header_fields.append(self._format_field_name(field))

        return header_fields

    def _format_field_name(self, field: str) -> str:
        """Format field name for CSV header."""
        if field == "task_count":
            return "Task Count"
        elif field == "total_time":
            return "Total Time"
        else:
            return field.replace("_", " ").title()

    def _should_add_base_time_header(
        self, base_time: str | None, has_percentage: bool
    ) -> bool:
        """Check if base time percentage header should be added."""
        return base_time is not None and not has_percentage

    def _print_csv_rows(self, rows: list[list[str]]) -> None:
        """Print CSV data rows."""
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
