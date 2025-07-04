"""Task analyzer for TaskChute Cloud logs."""

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console
from rich.table import Table


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
        """Parse time duration string (HH:MM:SS) to timedelta."""
        if pd.isna(time_str) or time_str == "":  # type: ignore
            return timedelta(0)

        if not isinstance(time_str, str):
            return timedelta(0)

        try:
            parts = time_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except (ValueError, IndexError):
            return timedelta(0)

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

    def analyze_by_project(
        self, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze tasks by project and return aggregated results."""
        data = self._load_data()

        # Group by project name and calculate total time
        project_times: dict[str, timedelta] = {}
        project_task_counts: dict[str, int] = {}

        for _, row in data.iterrows():  # type: ignore
            project_name = row["プロジェクト名"]
            actual_time = row["実績時間"]

            # Skip rows without project name
            if pd.isna(project_name) or project_name == "":  # type: ignore
                continue

            # Ensure project_name is string
            if not isinstance(project_name, str):
                continue

            duration = self._parse_time_duration(actual_time)

            if project_name not in project_times:
                project_times[project_name] = timedelta(0)
                project_task_counts[project_name] = 0

            project_times[project_name] += duration
            project_task_counts[project_name] += 1

        # Convert to list of dictionaries
        results = []
        for project_name, total_time in project_times.items():
            results.append(  # type: ignore
                {
                    "project": project_name,
                    "total_time": self._format_duration(total_time),
                    "total_seconds": int(total_time.total_seconds()),
                    "task_count": str(project_task_counts[project_name]),
                }
            )

        # Sort results
        if sort_by == "time":

            def time_key(x: dict[str, Any]) -> int:
                return int(x["total_seconds"])

            results.sort(key=time_key, reverse=reverse)  # type: ignore
        elif sort_by == "project":

            def project_key(x: dict[str, Any]) -> str:
                return str(x["project"])

            results.sort(key=project_key, reverse=reverse)  # type: ignore
        else:  # default to project for this analysis type

            def default_key(x: dict[str, Any]) -> str:
                return str(x["project"])

            results.sort(key=default_key, reverse=reverse)  # type: ignore

        return results  # type: ignore

    def analyze_by_mode(
        self, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze tasks by mode and return aggregated results."""
        data = self._load_data()

        # Group by mode name and calculate total time
        mode_times: dict[str, timedelta] = {}
        mode_task_counts: dict[str, int] = {}

        for _, row in data.iterrows():  # type: ignore
            mode_name = row["モード名"]
            actual_time = row["実績時間"]

            # Skip rows without mode name
            if pd.isna(mode_name) or mode_name == "":  # type: ignore
                continue

            # Ensure mode_name is string
            if not isinstance(mode_name, str):
                continue

            duration = self._parse_time_duration(actual_time)

            if mode_name not in mode_times:
                mode_times[mode_name] = timedelta(0)
                mode_task_counts[mode_name] = 0

            mode_times[mode_name] += duration
            mode_task_counts[mode_name] += 1

        # Convert to list of dictionaries
        results = []
        for mode_name, total_time in mode_times.items():
            results.append(  # type: ignore
                {
                    "mode": mode_name,
                    "total_time": self._format_duration(total_time),
                    "total_seconds": int(total_time.total_seconds()),
                    "task_count": str(mode_task_counts[mode_name]),
                }
            )

        # Sort results
        if sort_by == "time":

            def time_key(x: dict[str, Any]) -> int:
                return int(x["total_seconds"])

            results.sort(key=time_key, reverse=reverse)  # type: ignore
        elif sort_by == "mode":

            def mode_key(x: dict[str, Any]) -> str:
                return str(x["mode"])

            results.sort(key=mode_key, reverse=reverse)  # type: ignore
        else:  # default to mode for this analysis type

            def default_key(x: dict[str, Any]) -> str:
                return str(x["mode"])

            results.sort(key=default_key, reverse=reverse)  # type: ignore

        return results  # type: ignore

    def analyze_by_project_mode(
        self, sort_by: str = "time", reverse: bool = False
    ) -> list[dict[str, Any]]:
        """Analyze tasks by project-mode combination and return results."""
        data = self._load_data()

        # Group by project and mode name combination and calculate total time
        project_mode_times: dict[str, timedelta] = {}
        project_mode_task_counts: dict[str, int] = {}
        project_mode_pairs: dict[str, tuple[str, str]] = {}

        for _, row in data.iterrows():  # type: ignore
            project_name = row["プロジェクト名"]
            mode_name = row["モード名"]
            actual_time = row["実績時間"]

            # Skip rows without project or mode name
            if (  # type: ignore
                pd.isna(project_name)  # type: ignore
                or project_name == ""
                or pd.isna(mode_name)  # type: ignore
                or mode_name == ""
            ):
                continue

            # Ensure both are strings
            if not isinstance(project_name, str) or not isinstance(mode_name, str):
                continue

            # Create a composite key for project-mode combination
            composite_key = f"{project_name} | {mode_name}"
            duration = self._parse_time_duration(actual_time)

            if composite_key not in project_mode_times:
                project_mode_times[composite_key] = timedelta(0)
                project_mode_task_counts[composite_key] = 0
                project_mode_pairs[composite_key] = (project_name, mode_name)

            project_mode_times[composite_key] += duration
            project_mode_task_counts[composite_key] += 1

        # Convert to list of dictionaries
        results = []
        for composite_key, total_time in project_mode_times.items():
            project_name, mode_name = project_mode_pairs[composite_key]
            results.append(  # type: ignore
                {
                    "project": project_name,
                    "mode": mode_name,
                    "project_mode": composite_key,
                    "total_time": self._format_duration(total_time),
                    "total_seconds": int(total_time.total_seconds()),
                    "task_count": str(project_mode_task_counts[composite_key]),
                }
            )

        # Sort results
        if sort_by == "time":

            def time_key(x: dict[str, Any]) -> int:
                return int(x["total_seconds"])

            results.sort(key=time_key, reverse=reverse)  # type: ignore
        elif sort_by == "project":

            def project_key(x: dict[str, Any]) -> tuple[str, str]:
                return (str(x["project"]), str(x["mode"]))

            results.sort(key=project_key, reverse=reverse)  # type: ignore
        elif sort_by == "mode":

            def mode_key(x: dict[str, Any]) -> tuple[str, str]:
                return (str(x["mode"]), str(x["project"]))

            results.sort(key=mode_key, reverse=reverse)  # type: ignore
        else:  # default to project-mode combination

            def default_key(x: dict[str, Any]) -> tuple[str, str]:
                return (str(x["project"]), str(x["mode"]))

            results.sort(key=default_key, reverse=reverse)  # type: ignore

        return results  # type: ignore

    def _create_mode_table(
        self, results: list[dict[str, Any]], base_time: str | None
    ) -> Table:
        """Create table for mode analysis."""
        table = Table(title="TaskChute Cloud - Mode Time Analysis")
        table.add_column("Mode", style="cyan", no_wrap=True)
        table.add_column("Total Time", style="green")
        table.add_column("Task Count", style="yellow")
        if base_time is not None:
            table.add_column("Percentage", style="magenta")

        for result in results:
            row_data = [
                str(result["mode"]),
                str(result["total_time"]),
                str(result["task_count"]),
            ]
            if base_time is not None:
                row_data.append(str(result["percentage"]))
            table.add_row(*row_data)
        return table

    def _create_project_mode_table(
        self, results: list[dict[str, Any]], base_time: str | None
    ) -> Table:
        """Create table for project-mode analysis."""
        table = Table(title="TaskChute Cloud - Project x Mode Time Analysis")
        table.add_column("Project", style="cyan", no_wrap=True)
        table.add_column("Mode", style="magenta", no_wrap=True)
        table.add_column("Total Time", style="green")
        table.add_column("Task Count", style="yellow")
        if base_time is not None:
            table.add_column("Percentage", style="bright_blue")

        for result in results:
            row_data = [
                str(result["project"]),
                str(result["mode"]),
                str(result["total_time"]),
                str(result["task_count"]),
            ]
            if base_time is not None:
                row_data.append(str(result["percentage"]))
            table.add_row(*row_data)
        return table

    def _create_project_table(
        self, results: list[dict[str, Any]], base_time: str | None
    ) -> Table:
        """Create table for project analysis."""
        table = Table(title="TaskChute Cloud - Project Time Analysis")
        table.add_column("Project", style="cyan", no_wrap=True)
        table.add_column("Total Time", style="green")
        table.add_column("Task Count", style="yellow")
        if base_time is not None:
            table.add_column("Percentage", style="bright_red")

        for result in results:
            row_data = [
                str(result["project"]),
                str(result["total_time"]),
                str(result["task_count"]),
            ]
            if base_time is not None:
                row_data.append(str(result["percentage"]))
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

        if analysis_type == "mode":
            table = self._create_mode_table(results, base_time)
        elif analysis_type == "project-mode":
            table = self._create_project_mode_table(results, base_time)
        else:
            table = self._create_project_table(results, base_time)

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
        # Remove internal fields for JSON output
        json_results: list[dict[str, Any]] = []
        for result in results:
            if analysis_type == "mode":
                mode_result = {
                    "mode": result["mode"],
                    "total_time": result["total_time"],
                    "task_count": int(result["task_count"]),
                }
                if base_time is not None:
                    mode_result["percentage"] = result["percentage"]
                json_results.append(mode_result)  # type: ignore
            elif analysis_type == "project-mode":
                project_mode_result = {
                    "project": result["project"],
                    "mode": result["mode"],
                    "total_time": result["total_time"],
                    "task_count": int(result["task_count"]),
                }
                if base_time is not None:
                    project_mode_result["percentage"] = result["percentage"]
                json_results.append(project_mode_result)  # type: ignore
            else:
                project_result = {
                    "project": result["project"],
                    "total_time": result["total_time"],
                    "task_count": int(result["task_count"]),
                }
                if base_time is not None:
                    project_result["percentage"] = result["percentage"]
                json_results.append(project_result)  # type: ignore

        print(json.dumps(json_results, ensure_ascii=False, indent=2))

    def _print_mode_csv(
        self, results: list[dict[str, Any]], base_time: str | None
    ) -> None:
        """Print CSV for mode analysis."""
        header = "Mode,Total Time,Task Count"
        if base_time is not None:
            header += ",Percentage"
        print(header)
        for result in results:
            row = f"{result['mode']},{result['total_time']},{result['task_count']}"
            if base_time is not None:
                row += f",{result['percentage']}"
            print(row)

    def _print_project_mode_csv(
        self, results: list[dict[str, Any]], base_time: str | None
    ) -> None:
        """Print CSV for project-mode analysis."""
        header = "Project,Mode,Total Time,Task Count"
        if base_time is not None:
            header += ",Percentage"
        print(header)
        for result in results:
            row = (
                f"{result['project']},{result['mode']},"
                f"{result['total_time']},{result['task_count']}"
            )
            if base_time is not None:
                row += f",{result['percentage']}"
            print(row)

    def _print_project_csv(
        self, results: list[dict[str, Any]], base_time: str | None
    ) -> None:
        """Print CSV for project analysis."""
        header = "Project,Total Time,Task Count"
        if base_time is not None:
            header += ",Percentage"
        print(header)
        for result in results:
            row = f"{result['project']},{result['total_time']},{result['task_count']}"
            if base_time is not None:
                row += f",{result['percentage']}"
            print(row)

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

        if analysis_type == "mode":
            self._print_mode_csv(results, base_time)
        elif analysis_type == "project-mode":
            self._print_project_mode_csv(results, base_time)
        else:
            self._print_project_csv(results, base_time)
