"""Slack formatting utilities for TaskChute Cloud analysis."""

from typing import Any


class SlackFormatter:
    """Handles Slack-specific formatting for analysis results."""

    def format_slack_message(
        self,
        results: list[dict[str, Any]],
        analysis_type: str,
        base_time: str | None,
        get_analysis_config_func: Any,
        is_total_row_func: Any,
    ) -> str:
        """Format results as Slack message."""
        config = get_analysis_config_func(analysis_type)

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
            row = self._format_slack_row(result, config, base_time, results)

            # Add separator before total row
            row_fields = [str(result.get(field, "")) for field in config["fields"]]
            if is_total_row_func(i, row_fields, len(results)):
                table_lines.append("-" * len(headers))

            table_lines.append(row)

        table_lines.append("```")

        # Combine all sections
        all_lines = [header, "", description, *table_lines]
        return "\n".join(all_lines)

    def _get_slack_headers(
        self,
        config: dict[str, Any],
        results: list[dict[str, Any]],
        base_time: str | None,
    ) -> str:
        """Generate Slack table headers."""
        has_percentage = bool(results and "percentage" in results[0])
        headers = self._build_header_names(config, has_percentage, base_time)
        widths = self._calculate_column_widths(config, results, headers, base_time)
        return self._format_aligned_headers(headers, widths, config, has_percentage)

    def _build_header_names(
        self,
        config: dict[str, Any],
        has_percentage: bool,
        base_time: str | None,
    ) -> list[str]:
        """Build header names for display."""
        headers: list[str] = []
        valid_fields = self._get_valid_fields(config, has_percentage)

        for field in valid_fields:
            headers.append(self._get_slack_header_name(field))

        # Add base time percentage header if needed
        if base_time is not None and not has_percentage:
            headers.append("基準%")

        return headers

    def _format_aligned_headers(
        self,
        headers: list[str],
        widths: list[int],
        config: dict[str, Any],
        has_percentage: bool,
    ) -> str:
        """Format headers with proper alignment and widths."""
        valid_fields = self._get_valid_fields(config, has_percentage)
        aligned_headers: list[str] = []

        for i, header in enumerate(headers):
            width = widths[i]
            if i < len(valid_fields):
                field = valid_fields[i]
                alignment = "<" if field in ["project", "mode"] else ">"
            else:
                alignment = ">"  # Base percentage column
            aligned_headers.append(f"{header:{alignment}{width}}")

        return " | ".join(aligned_headers)

    def _calculate_column_widths(
        self,
        config: dict[str, Any],
        results: list[dict[str, Any]],
        headers: list[str],
        base_time: str | None,
    ) -> list[int]:
        """Calculate dynamic column widths based on content."""
        has_percentage = bool(results and "percentage" in results[0])
        valid_fields = self._get_valid_fields(config, has_percentage)
        widths = self._calculate_field_widths(valid_fields, headers, results)

        # Add base time percentage column width if needed
        if base_time is not None and not has_percentage:
            base_width = self._calculate_base_time_width(results)
            widths.append(base_width)

        return widths

    def _calculate_field_widths(
        self,
        fields: list[str],
        headers: list[str],
        results: list[dict[str, Any]],
    ) -> list[int]:
        """Calculate width for each field."""
        widths: list[int] = []

        for i, field in enumerate(fields):
            header_width = len(headers[i])
            max_content_width = header_width

            # Check all data values for this field
            for result in results:
                value_str = str(result.get(field, ""))
                max_content_width = max(max_content_width, len(value_str))

            # Set minimum width based on field type
            min_width = 8 if field in ["project", "mode"] else 6
            widths.append(max(min_width, max_content_width))

        return widths

    def _calculate_base_time_width(self, results: list[dict[str, Any]]) -> int:
        """Calculate width for base time percentage column."""
        base_header_width = len("基準%")
        max_base_width = base_header_width

        for result in results:
            percentage_str = str(result.get("percentage", ""))
            max_base_width = max(max_base_width, len(percentage_str))

        return max(6, max_base_width)

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
        all_results: list[dict[str, Any]],
    ) -> str:
        """Format a single result row for Slack."""
        has_percentage = "percentage" in result
        headers = self._build_header_names(config, has_percentage, base_time)
        widths = self._calculate_column_widths(config, all_results, headers, base_time)

        row_data = self._format_slack_row_fields(result, config, has_percentage, widths)
        self._add_base_time_percentage_if_needed(
            result, base_time, has_percentage, widths, row_data
        )

        return " | ".join(row_data)

    def _format_slack_row_fields(
        self,
        result: dict[str, Any],
        config: dict[str, Any],
        has_percentage: bool,
        widths: list[int],
    ) -> list[str]:
        """Format the main fields for a Slack row."""
        valid_fields = self._get_valid_fields(config, has_percentage)
        row_data: list[str] = []

        for i, field in enumerate(valid_fields):
            value = str(result.get(field, ""))
            width = widths[i]
            formatted_value = self._format_slack_field_value(field, value, width)
            row_data.append(formatted_value)

        return row_data

    def _format_slack_field_value(self, field: str, value: str, width: int) -> str:
        """Format a single field value with proper alignment."""
        if field in ["project", "mode"]:
            return f"{value:<{width}}"  # Left align
        else:
            return f"{value:>{width}}"  # Right align

    def _add_base_time_percentage_if_needed(
        self,
        result: dict[str, Any],
        base_time: str | None,
        has_percentage: bool,
        widths: list[int],
        row_data: list[str],
    ) -> None:
        """Add base time percentage column if needed."""
        if base_time is not None and not has_percentage:
            width = widths[len(row_data)]
            percentage_value = str(result.get("percentage", ""))
            row_data.append(f"{percentage_value:>{width}}")

    def _get_valid_fields(
        self, config: dict[str, Any], has_percentage: bool
    ) -> list[str]:
        """Get list of valid fields that should be included."""
        valid_fields: list[str] = []
        for field in config["fields"]:
            if not (field == "percentage" and not has_percentage):
                valid_fields.append(field)
        return valid_fields
