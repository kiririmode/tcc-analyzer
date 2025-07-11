"""Command line interface for TCC Analyzer."""

import re
from pathlib import Path
from typing import Any

import click

try:
    # Try absolute import first (works when package is installed)
    from tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer
    from tcc_analyzer.visualization import (
        ChartType,
        OutputFormat,
        VisualizationFactory,
    )
    from tcc_analyzer.visualization.base import DataProcessor
except ImportError:
    # Fall back to relative import (works in development/test environments)
    from .analyzers.task_analyzer import TaskAnalyzer
    from .visualization import ChartType, OutputFormat, VisualizationFactory
    from .visualization.base import DataProcessor


@click.group()
@click.version_option(version="1.0.0", package_name="tcc-analyzer")
def main() -> None:
    """TCC Analyzer - A Python CLI tool for analyzing TaskChute Cloud logs."""
    pass


@main.command()
@click.argument(
    "csv_files", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path)
)
@click.option(
    "--output-format",
    type=click.Choice(["table", "json", "csv", "slack"]),
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
@click.option(
    "--chart",
    type=click.Choice(["bar", "pie", "line", "histogram", "heatmap"]),
    help="Generate chart visualization (saves to file)",
)
@click.option(
    "--chart-output",
    type=click.Path(path_type=Path),
    help="Output file for chart (default: auto-generated based on analysis type)",
)
@click.option(
    "--chart-format",
    type=click.Choice(["png", "svg", "pdf", "show"]),
    default="png",
    help="Chart output format (default: png)",
)
@click.option(
    "--tag-filter",
    type=str,
    help="Filter tasks by tag name (exact match)",
)
def task(
    csv_files: tuple[Path, ...],
    output_format: str,
    sort_by: str,
    reverse: bool,
    group_by: str,
    base_time: str | None,
    chart: str | None,
    chart_output: Path | None,
    chart_format: str,
    tag_filter: str | None,
) -> None:
    """Analyze TaskChute Cloud task logs with project/mode/project-mode grouping."""
    # Validate base_time format if provided
    _validate_base_time(base_time)

    # Initialize analyzer with CSV files
    analyzer = _create_analyzer(csv_files)

    # Apply tag filter if specified
    if tag_filter:
        analyzer.set_tag_filter(tag_filter)

    # Perform analysis based on group_by parameter
    analysis_methods = {
        "mode": analyzer.analyze_by_mode,
        "project-mode": analyzer.analyze_by_project_mode,
    }
    analysis_method = analysis_methods.get(group_by, analyzer.analyze_by_project)
    results = analysis_method(sort_by=sort_by, reverse=reverse)

    # Always add total row and percentages
    results = analyzer.add_total_row_and_percentages(results, group_by)

    # Display results in requested format
    display_methods = {
        "json": analyzer.display_json,
        "csv": analyzer.display_csv,
        "slack": analyzer.display_slack,
    }
    display_method = display_methods.get(output_format, analyzer.display_table)
    display_method(results, analysis_type=group_by, base_time=base_time)

    # Generate chart if requested
    if chart:
        primary_file = csv_files[0]
        _generate_chart(
            results, chart, chart_output, chart_format, group_by, primary_file
        )


def _validate_base_time(base_time: str | None) -> None:
    """Validate base_time format if provided."""
    if base_time is not None:
        # Validate base_time format with strict HH:MM or HH:MM:SS pattern
        is_valid_format = bool(
            re.match(r"^\d{2}:\d{2}(:\d{2})?$", base_time)
            and base_time not in {"00:00", "00:00:00"}
        )

        if not is_valid_format:
            click.echo(
                f"Error: Invalid base time format '{base_time}'. "
                f"Use HH:MM format (e.g., '08:00').",
                err=True,
            )
            raise click.Abort()


def _create_analyzer(csv_files: tuple[Path, ...]) -> TaskAnalyzer:
    """Create TaskAnalyzer instance from CSV files."""
    if len(csv_files) == 1:
        return TaskAnalyzer(csv_files[0])
    else:
        return TaskAnalyzer(list(csv_files))


def _generate_chart(
    results: list[dict[str, Any]],
    chart_type: str,
    output_path: Path | None,
    output_format: str,
    group_by: str,
    csv_file: Path,
) -> None:
    """Generate chart visualization from analysis results."""
    try:
        # Map string to ChartType enum
        chart_type_map = {
            "bar": ChartType.BAR,
            "pie": ChartType.PIE,
            "line": ChartType.LINE,
            "histogram": ChartType.HISTOGRAM,
            "heatmap": ChartType.HEATMAP,
        }

        chart_enum = chart_type_map[chart_type]

        # Create visualizer
        visualizer = VisualizationFactory.create_visualizer(
            chart_enum, figsize=(12, 8), style="seaborn-v0_8"
        )

        # Generate output path if not provided
        if output_path is None:
            output_path = Path(f"{csv_file.stem}_{group_by}_{chart_type}")

        # Create chart based on type
        if chart_type == "bar":
            _create_bar_chart(visualizer, results, group_by)
        elif chart_type == "pie":
            _create_pie_chart(visualizer, results, group_by)
        elif chart_type == "line":
            _create_line_chart(visualizer, results, group_by)
        elif chart_type == "histogram":
            _create_histogram_chart(visualizer, results, group_by)
        elif chart_type == "heatmap":
            _create_heatmap_chart(visualizer, results, group_by)

        # Save or show chart
        if output_format == "show":
            visualizer.show_chart()
        else:
            format_enum = OutputFormat(output_format)
            visualizer.save_chart(output_path, format_enum)
            click.echo(f"Chart saved to: {output_path}.{output_format}")

        # Clean up
        visualizer.close_chart()

    except Exception as e:
        click.echo(f"Error generating chart: {e}", err=True)
        raise click.Abort() from e


def _get_chart_config(group_by: str) -> dict[str, Any]:
    """Get chart configuration based on group_by parameter."""
    if group_by == "project":
        return {"key": "project", "title_prefix": "Project", "label": "Project"}
    elif group_by == "mode":
        return {"key": "mode", "title_prefix": "Mode", "label": "Mode"}
    else:  # project-mode
        return {
            "key": "project_mode",
            "title_prefix": "Project-Mode",
            "label": "Project-Mode",
        }


def _create_bar_chart(
    visualizer: Any, results: list[dict[str, Any]], group_by: str
) -> None:
    """Create bar chart visualization."""
    config = _get_chart_config(group_by)

    visualizer.create_chart(results, x_key=config["key"], y_key="total_seconds")
    visualizer.customize_chart(
        title=f"Time Spent by {config['title_prefix']}",
        xlabel=config["label"],
        ylabel="Time (hours)",
        xtick_rotation=45,
    )


def _create_pie_chart(
    visualizer: Any, results: list[dict[str, Any]], group_by: str
) -> None:
    """Create pie chart visualization."""
    config = _get_chart_config(group_by)
    top_results = DataProcessor.filter_top_items(results, "total_seconds", 10)

    visualizer.create_chart(
        top_results, x_key=config["key"], y_key="total_seconds", donut=False
    )
    visualizer.customize_chart(
        title=f"Time Distribution by {config['title_prefix']} (Top 10)"
    )


def _create_line_chart(
    visualizer: Any, results: list[dict[str, Any]], group_by: str
) -> None:
    """Create line chart visualization."""
    config = _get_chart_config(group_by)

    click.echo(
        "Warning: Line charts require time-series data. Using simplified visualization."
    )

    time_data: list[dict[str, Any]] = []
    for i, result in enumerate(results):
        seconds = result.get("total_seconds", 0)
        hours = seconds / 3600 if isinstance(seconds, int | float) else 0
        time_data.append({"time": f"Period {i + 1}", "value": hours})

    visualizer.create_chart(time_data, x_key="time", y_key="value")
    visualizer.customize_chart(
        title=f"Time Trends by {config['title_prefix']}",
        xlabel="Time Period",
        ylabel="Time (hours)",
    )


def _create_histogram_chart(
    visualizer: Any, results: list[dict[str, Any]], group_by: str
) -> None:
    """Create histogram visualization."""
    visualizer.create_chart(results, x_key="total_seconds", y_key="")
    visualizer.customize_chart(
        title=f"Time Distribution Histogram ({group_by.title()})",
        xlabel="Time (hours)",
        ylabel="Frequency",
    )


def _create_heatmap_chart(
    visualizer: Any, results: list[dict[str, Any]], group_by: str
) -> None:
    """Create heatmap visualization."""
    visualizer.create_chart(results, x_key="", y_key="")
    visualizer.customize_chart(title=f"Correlation Heatmap ({group_by.title()})")


if __name__ == "__main__":
    main()
