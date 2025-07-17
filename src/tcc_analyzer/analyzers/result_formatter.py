"""Result formatting utilities for TaskChute Cloud analysis."""

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from .constants import MAX_SLACK_FIELD_LENGTH, TRUNCATED_LENGTH
from .result_processor import ResultProcessor


class ResultFormatter:
    """Handles formatting and display of analysis results in various formats."""

    def __init__(self) -> None:
        """Initialize the result formatter."""
        self.console = Console()

    def _prepare_results_with_percentage(
        self, results: list[dict[str, Any]], base_time: str | None
    ) -> list[dict[str, Any]]:
        """Add percentage column if base_time is provided."""
        if base_time is not None:
            return ResultProcessor.add_percentage_to_results(results, base_time)
        return results

    def display_table(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as a rich table."""
        results = self._prepare_results_with_percentage(results, base_time)
        table = self._create_table(results, analysis_type, base_time)
        self.console.print(table)

    def display_json(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as JSON."""
        results = self._prepare_results_with_percentage(results, base_time)
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

    def display_csv(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results as CSV."""
        results = self._prepare_results_with_percentage(results, base_time)
        self._print_csv(results, analysis_type, base_time)

    def display_slack(
        self,
        results: list[dict[str, Any]],
        analysis_type: str = "project",
        base_time: str | None = None,
    ) -> None:
        """Display results in Slack-formatted message."""
        results = self._prepare_results_with_percentage(results, base_time)
        slack_message = self._format_slack_message(results, analysis_type, base_time)
        print(slack_message)

    def _get_analysis_config(self, analysis_type: str) -> dict[str, Any]:
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

    def _format_slack_message(
        self,
        results: list[dict[str, Any]],
        analysis_type: str,
        base_time: str | None,
    ) -> str:
        """Format results as Slack message."""
        config = self._get_analysis_config(analysis_type)

        # Build enhanced header
        header_parts = ["⏰ TaskChute Cloud 分析レポート"]
        if base_time is not None:
            header_parts.append(f"(基準時間: {base_time})")
        header = " ".join(header_parts)

        # Build analysis type description
        type_descriptions = {
            "project": "📂 プロジェクト別",
            "mode": "🎯 モード別",
            "project-mode": "📂🎯 プロジェクト×モード別",  # noqa: RUF001
        }
        description = f"*{type_descriptions.get(analysis_type, analysis_type)}時間分析*"

        # Build table with visual improvements
        table_lines = ["", "```"]
        headers = self._get_slack_headers(config, results, base_time)
        table_lines.append(headers)
        table_lines.append("-" * len(headers))

        # Add data rows including total row with enhanced formatting
        for i, result in enumerate(results):
            row = self._format_slack_row(result, config, base_time)

            # Add separator before total row
            row_fields = [str(result.get(field, "")) for field in config["fields"]]
            if self._is_total_row(i, row_fields, len(results)):
                table_lines.append("-" * len(headers))

            table_lines.append(row)

        table_lines.append("```")

        # Combine all sections
        all_lines = [header, "", description, *table_lines]
        return "\n".join(all_lines)

    def _should_include_percentage_field(
        self, field: str, has_percentage: bool
    ) -> bool:
        """Check if percentage field should be included."""
        return not (field == "percentage" and not has_percentage)

    def _get_slack_headers(
        self,
        config: dict[str, Any],
        results: list[dict[str, Any]],
        base_time: str | None,
    ) -> str:
        """Generate Slack table headers."""
        headers: list[str] = []
        has_percentage = bool(results and "percentage" in results[0])

        for field in config["fields"]:
            if self._should_include_percentage_field(field, has_percentage):
                headers.append(self._get_slack_header_name(field))

        # Add base time percentage header if needed
        if base_time is not None and not has_percentage:
            headers.append("基準%")

        # Apply alignment based on field type
        aligned_headers: list[str] = []
        for i, header in enumerate(headers):
            field_names = list(config["fields"])
            if i < len(field_names):
                field = field_names[i]
                if field in ["project", "mode"]:
                    aligned_headers.append(f"{header:<12}")  # Left align
                else:
                    aligned_headers.append(f"{header:>12}")  # Right align
            else:
                # Base percentage column
                aligned_headers.append(f"{header:>12}")
        return " | ".join(aligned_headers)

    def _get_slack_header_name(self, field: str) -> str:
        """Get Slack-formatted header name for field."""
        header_mapping = {
            "project": "プロジェクト",
            "mode": "モード",
            "total_time": "時間",
            "task_count": "タスク数",
            "percentage": "割合",
        }
        return header_mapping.get(field, field)

    def _format_slack_row(
        self,
        result: dict[str, Any],
        config: dict[str, Any],
        base_time: str | None,
    ) -> str:
        """Format a single result row for Slack."""
        row_data: list[str] = []
        has_percentage = "percentage" in result

        for field in config["fields"]:
            if self._should_include_percentage_field(field, has_percentage):
                value = str(result.get(field, ""))
                # Truncate long project/mode names for Slack readability
                if field in ["project", "mode"] and len(value) > MAX_SLACK_FIELD_LENGTH:
                    value = value[:TRUNCATED_LENGTH] + "..."
                # Apply alignment based on field type
                if field in ["project", "mode"]:
                    row_data.append(f"{value:<12}")  # Left align
                else:
                    row_data.append(f"{value:>12}")  # Right align

        # Add base time percentage if needed
        if base_time is not None and not has_percentage:
            row_data.append(f"{result.get('percentage', ''):>12}")

        return " | ".join(row_data)

    # Public methods for backward compatibility
    def get_analysis_config(self, analysis_type: str) -> dict[str, Any]:
        """Get configuration for analysis type."""
        return self._get_analysis_config(analysis_type)

    def create_table(
        self, results: list[dict[str, Any]], analysis_type: str, base_time: str | None
    ) -> Table:
        """Create table for analysis results."""
        return self._create_table(results, analysis_type, base_time)

    def is_total_row(self, index: int, row_data: list[str], total_rows: int) -> bool:
        """Check if the current row is a total row."""
        return self._is_total_row(index, row_data, total_rows)

    def get_slack_headers(
        self,
        config: dict[str, Any],
        results: list[dict[str, Any]],
        base_time: str | None,
    ) -> str:
        """Generate Slack table headers."""
        return self._get_slack_headers(config, results, base_time)

    def format_slack_row(
        self,
        result: dict[str, Any],
        config: dict[str, Any],
        base_time: str | None,
    ) -> str:
        """Format a single result row for Slack."""
        return self._format_slack_row(result, config, base_time)
