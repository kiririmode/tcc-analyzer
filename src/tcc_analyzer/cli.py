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
    help="Sort results by time or project name",
)
@click.option(
    "--reverse",
    is_flag=True,
    help="Reverse the sort order",
)
def task(
    csv_file: Path,
    output_format: str,
    sort_by: str,
    reverse: bool,
) -> None:
    """Analyze TaskChute Cloud task logs and show project-wise time allocation."""
    analyzer = TaskAnalyzer(csv_file)
    results = analyzer.analyze_by_project(sort_by=sort_by, reverse=reverse)
    
    if output_format == "table":
        analyzer.display_table(results)
    elif output_format == "json":
        analyzer.display_json(results)
    elif output_format == "csv":
        analyzer.display_csv(results)


if __name__ == "__main__":
    main()