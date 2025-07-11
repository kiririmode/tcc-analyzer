"""Result processing utilities for TaskChute Cloud analysis."""

from datetime import timedelta
from typing import Any

from .time_parser import TimeParser


class ResultProcessor:
    """Handles processing of analysis results including totals and percentages."""

    @staticmethod
    def add_percentage_to_results(
        results: list[dict[str, Any]], base_time_str: str
    ) -> list[dict[str, Any]]:
        """Add percentage column to results based on base time."""
        updated_results: list[dict[str, Any]] = []
        for result in results:
            updated_result = result.copy()
            duration = timedelta(seconds=result["total_seconds"])
            percentage = TimeParser.calculate_percentage(duration, base_time_str)
            updated_result["percentage"] = f"{percentage:.1f}%"
            updated_results.append(updated_result)
        return updated_results

    @staticmethod
    def add_total_row_and_percentages(
        results: list[dict[str, Any]], analysis_type: str
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
        total_row = ResultProcessor._create_total_row(
            total_duration, total_task_count, analysis_type
        )
        updated_results.append(total_row)

        return updated_results

    @staticmethod
    def _create_total_row(
        total_duration: timedelta, total_task_count: int, analysis_type: str
    ) -> dict[str, Any]:
        """Create total row for analysis results."""
        total_row: dict[str, Any] = {
            "total_time": TimeParser.format_duration(total_duration),
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

    # Public method for backward compatibility
    @staticmethod
    def create_total_row(
        total_duration: timedelta, total_task_count: int, analysis_type: str
    ) -> dict[str, Any]:
        """Create total row for analysis results (public method for tests)."""
        return ResultProcessor._create_total_row(
            total_duration, total_task_count, analysis_type
        )
