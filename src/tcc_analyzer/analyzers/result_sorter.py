"""Result sorting utilities for TaskChute Cloud analysis."""

from collections.abc import Callable
from typing import Any


class ResultSorter:
    """Handles sorting of analysis results."""

    @staticmethod
    def sort_results(
        results: list[dict[str, Any]],
        sort_by: str,
        reverse: bool,
        analysis_type: str,
    ) -> list[dict[str, Any]]:
        """Sort results based on sort_by parameter and analysis type."""
        sort_key = ResultSorter._get_sort_key(sort_by, analysis_type)
        results.sort(key=sort_key, reverse=reverse)
        return results

    @staticmethod
    def _get_sort_key(
        sort_by: str, analysis_type: str
    ) -> Callable[[dict[str, Any]], Any]:
        """Get sort key function based on sort_by and analysis_type."""
        if sort_by == "time":
            return lambda x: int(x["total_seconds"])

        if sort_by == "project" and analysis_type in ["project", "project-mode"]:
            return ResultSorter._get_project_sort_key(analysis_type)

        if sort_by == "mode" and analysis_type in ["mode", "project-mode"]:
            return ResultSorter._get_mode_sort_key(analysis_type)

        # Default sorting
        return ResultSorter._get_default_sort_key(analysis_type)

    @staticmethod
    def _get_project_sort_key(
        analysis_type: str,
    ) -> Callable[[dict[str, Any]], Any]:
        """Get sort key for project-based sorting."""
        if analysis_type == "project":
            return lambda x: str(x["project"])
        # project-mode
        return lambda x: (str(x["project"]), str(x["mode"]))

    @staticmethod
    def _get_mode_sort_key(analysis_type: str) -> Callable[[dict[str, Any]], Any]:
        """Get sort key for mode-based sorting."""
        if analysis_type == "mode":
            return lambda x: str(x["mode"])
        # project-mode
        return lambda x: (str(x["mode"]), str(x["project"]))

    @staticmethod
    def _get_default_sort_key(
        analysis_type: str,
    ) -> Callable[[dict[str, Any]], Any]:
        """Get default sort key based on analysis type."""
        if analysis_type == "project":
            return lambda x: str(x["project"])
        if analysis_type == "mode":
            return lambda x: str(x["mode"])
        # project-mode
        return lambda x: (str(x["project"]), str(x["mode"]))
