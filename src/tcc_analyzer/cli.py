"""Command line interface for TCC Analyzer."""

import click
from pathlib import Path
from typing import Optional

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
    type=click.Choice(["time", "name"]),
    default="time",
    help="Sort results by time or project/mode name",
)
@click.option(
    "--reverse",
    is_flag=True,
    help="Reverse the sort order",
)
@click.option(
    "--group-by",
    type=click.Choice(["project", "mode"]),
    default="project",
    help="Group results by project or mode",
)
def task(
    csv_file: Path,
    output_format: str,
    sort_by: str,
    reverse: bool,
    group_by: str,
) -> None:
    """Analyze TaskChute Cloud task logs and show project-wise or mode-wise time allocation."""
    analyzer = TaskAnalyzer(csv_file)
    
    if group_by == "mode":
        results = analyzer.analyze_by_mode(sort_by=sort_by, reverse=reverse)
    else:
        results = analyzer.analyze_by_project(sort_by=sort_by, reverse=reverse)
    
    if output_format == "table":
        analyzer.display_table(results, analysis_type=group_by)
    elif output_format == "json":
        analyzer.display_json(results, analysis_type=group_by)
    elif output_format == "csv":
        analyzer.display_csv(results, analysis_type=group_by)


if __name__ == "__main__":
    main()