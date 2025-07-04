"""Command line interface for TCC Analyzer."""

import re
from pathlib import Path

import click

from .analyzers.task_analyzer import TaskAnalyzer


@click.group()
@click.version_option()
def main() -> None:
    """TCC Analyzer - A Python CLI tool for analyzing TaskChute Cloud logs."""
    pass


@main.command()
@click.argument("csv_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format for the analysis results",
)
@click.option(
    "--sort-by",
    type=click.Choice(["time", "project", "mode"]),
    default="time",
    help="Sort results by time, project name, or mode name",
)
@click.option(
    "--reverse",
    is_flag=True,
    help="Reverse the sort order",
)
@click.option(
    "--group-by",
    type=click.Choice(["project", "mode", "project-mode"]),
    default="project",
    help="Group results by project, mode, or project-mode combination",
)
@click.option(
    "--base-time",
    type=str,
    help="Base time (HH:MM or HH:MM:SS) to calculate percentage against",
)
def task(
    csv_file: Path,
    output_format: str,
    sort_by: str,
    reverse: bool,
    group_by: str,
    base_time: str | None,
) -> None:
    """Analyze TaskChute Cloud task logs with project/mode/project-mode grouping."""
    analyzer = TaskAnalyzer(csv_file)

    # Validate base_time format if provided
    if base_time is not None:
        # Validate base_time format with strict HH:MM or HH:MM:SS pattern
        is_valid_format = bool(
            re.match(r"^\d{2}:\d{2}(:\d{2})?$", base_time)
            and base_time not in {"00:00", "00:00:00"}
        )

        if not is_valid_format:
            click.echo(
                f"Error: Invalid base time format '{base_time}'. "
                f"Use HH:MM or HH:MM:SS format (e.g., '08:00' or '08:00:00').",
                err=True,
            )
            raise click.Abort()

    if group_by == "mode":
        results = analyzer.analyze_by_mode(sort_by=sort_by, reverse=reverse)
    elif group_by == "project-mode":
        results = analyzer.analyze_by_project_mode(sort_by=sort_by, reverse=reverse)
    else:
        results = analyzer.analyze_by_project(sort_by=sort_by, reverse=reverse)

    if output_format == "table":
        analyzer.display_table(results, analysis_type=group_by, base_time=base_time)
    elif output_format == "json":
        analyzer.display_json(results, analysis_type=group_by, base_time=base_time)
    elif output_format == "csv":
        analyzer.display_csv(results, analysis_type=group_by, base_time=base_time)


if __name__ == "__main__":
    main()
