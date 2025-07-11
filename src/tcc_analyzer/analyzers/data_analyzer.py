"""Data analysis utilities for TaskChute Cloud logs."""

from datetime import timedelta
from typing import Any

import pandas as pd

from .time_parser import TimeParser


class DataAnalyzer:
    """Handles data analysis, filtering, and aggregation."""

    def __init__(self) -> None:
        """Initialize the data analyzer."""
        self._tag_filter: str | None = None

    def set_tag_filter(self, tag_filter: str) -> None:
        """Set tag filter for analysis."""
        self._tag_filter = tag_filter

    def analyze_by_type(
        self, data: pd.DataFrame, analysis_type: str
    ) -> list[dict[str, Any]]:
        """Analyze data by specified type."""
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
        return list(aggregated.values())

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
            duration = TimeParser.parse_time_duration(row["実績時間"])

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
            "total_time": TimeParser.format_duration(total_time),
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

    # Public methods for backward compatibility
    def parse_tag_names(self, tag_names_str: str | float) -> list[str]:
        """Parse tag names from string for backward compatibility."""
        return self._parse_tag_names(tag_names_str)

    def filter_by_tag(self, data: pd.DataFrame, tag_filter: str) -> pd.DataFrame:
        """Filter data by tag for backward compatibility."""
        return self._filter_by_tag(data, tag_filter)

    @property
    def tag_filter(self) -> str | None:
        """Get current tag filter for backward compatibility."""
        return self._tag_filter
