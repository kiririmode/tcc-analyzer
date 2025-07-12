"""Concrete chart visualizers for different chart types."""

from typing import Any, ClassVar

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from .base import BaseVisualizer, DataProcessor


class ChartStyleMixin:
    """Mixin class for common chart styling methods."""

    # Style defaults for different chart types
    _STYLE_DEFAULTS: ClassVar[dict[str, dict[str, Any]]] = {
        "common": {
            "color": "steelblue",
            "alpha": 0.8,
            "edgecolor": "black",
            "linewidth": 0.5,
        },
        "bar": {
            "alpha": 0.8,
        },
        "histogram": {
            "alpha": 0.7,
        },
        "line": {
            "color": "steelblue",
            "linewidth": 2,
            "linestyle": "-",
            "alpha": 0.8,
        },
        "marker": {
            "color": "darkblue",
            "size": 50,
            "alpha": 0.6,
            "marker": "o",
        },
    }

    def _get_styling(self, style_type: str, **kwargs: Any) -> dict[str, Any]:
        """Get styling parameters for specified chart type."""
        if style_type == "common":
            return self._get_common_styling(**kwargs)
        elif style_type == "line":
            return self._get_line_styling(**kwargs)
        elif style_type == "marker":
            return self._get_marker_styling(**kwargs)
        else:
            # For bar, histogram, and other types that use common styling
            return self._get_common_styling_with_overrides(style_type, **kwargs)

    def _get_common_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get common styling parameters shared across chart types."""
        defaults = self._STYLE_DEFAULTS["common"]
        return {key: kwargs.get(key, default) for key, default in defaults.items()}

    def _get_common_styling_with_overrides(
        self, style_type: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Get common styling with type-specific overrides."""
        styling = self._get_common_styling(**kwargs)

        # Apply type-specific overrides
        if style_type in self._STYLE_DEFAULTS:
            type_defaults = self._STYLE_DEFAULTS[style_type]
            for key, default in type_defaults.items():
                styling[key] = kwargs.get(key, default)

        return styling

    def _get_line_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get line-specific styling parameters."""
        defaults = self._STYLE_DEFAULTS["line"]
        return {key: kwargs.get(key, default) for key, default in defaults.items()}

    def _get_marker_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get marker-specific styling parameters."""
        defaults = self._STYLE_DEFAULTS["marker"]
        # Handle special marker parameter mapping
        return {
            "color": kwargs.get("marker_color", defaults["color"]),
            "s": kwargs.get(
                "marker_size", defaults["size"]
            ),  # matplotlib uses 's' for scatter size
            "alpha": kwargs.get("marker_alpha", defaults["alpha"]),
            "marker": kwargs.get("marker_style", defaults["marker"]),
        }

    # Convenience methods for backward compatibility
    def _get_bar_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get bar-specific styling parameters."""
        return self._get_styling("bar", **kwargs)

    def _get_histogram_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get histogram-specific styling parameters."""
        return self._get_styling("histogram", **kwargs)


class ChartCreationMixin:
    """Mixin class for common chart creation patterns."""

    def _prepare_chart_data(
        self, data: list[dict[str, Any]], x_key: str, y_key: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Prepare common chart data with validation."""
        fig, ax = self.setup_figure()  # type: ignore[attr-defined]

        result: dict[str, Any] = {"fig": fig, "ax": ax}

        # Extract x-axis data (labels)
        if x_key:
            raw_labels = DataProcessor.extract_values(data, x_key)
            labels = DataProcessor.sanitize_labels(raw_labels)
            result["labels"] = labels

            # For charts that use x_key as value_key (like histogram)
            if not y_key:
                if x_key == "total_seconds":
                    values = DataProcessor.extract_hours_values(data, x_key)
                else:
                    values = DataProcessor.extract_numeric_values(data, x_key)
                result["values"] = values

        # Extract y-axis data (values)
        if y_key:
            if y_key == "total_seconds":
                values = DataProcessor.extract_hours_values(data, y_key)
            else:
                values = DataProcessor.extract_numeric_values(data, y_key)
            result["values"] = values

        return result

    def _validate_chart_data(
        self, prepared_data: dict[str, Any], chart_type: str
    ) -> None:
        """Validate prepared chart data."""
        if chart_type in ["bar", "line"] and (
            not prepared_data.get("labels") or not prepared_data.get("values")
        ):
            raise ValueError(f"Invalid data for {chart_type} chart")
        elif chart_type == "histogram" and not prepared_data.get("values"):
            raise ValueError("No numeric values found for histogram")
        elif chart_type == "pie" and not prepared_data.get("values"):
            raise ValueError("Invalid data for pie chart")

    def _create_chart_with_common_pattern(
        self,
        data: list[dict[str, Any]],
        x_key: str,
        y_key: str,
        chart_type: str,
        **kwargs: Any,
    ) -> tuple[dict[str, Any], Figure, Axes]:
        """Prepare and validate chart data using common pattern."""
        prepared = self._prepare_chart_data(data, x_key, y_key, **kwargs)
        self._validate_chart_data(prepared, chart_type)
        return prepared, prepared["fig"], prepared["ax"]


class BarChartVisualizer(BaseVisualizer, ChartStyleMixin, ChartCreationMixin):
    """Bar chart visualizer for categorical data."""

    def create_chart(
        self, data: list[dict[str, Any]], x_key: str, y_key: str, **kwargs: Any
    ) -> tuple[Figure, Axes]:
        """Create a bar chart.

        Args:
            data: Analysis results data
            x_key: Key for x-axis labels
            y_key: Key for y-axis values
            **kwargs: Additional chart parameters

        Returns:
            Tuple of (figure, axes)

        """
        # Use common pattern
        prepared, fig, ax = self._create_chart_with_common_pattern(
            data, x_key, y_key, "bar", **kwargs
        )
        labels, values = prepared["labels"], prepared["values"]

        # Create bar chart
        bars = ax.bar(labels, values, **self._get_bar_styling(**kwargs))  # type: ignore[misc]

        # Add value labels on bars if requested
        if kwargs.get("show_values", True):
            self._add_value_labels(ax, bars, values)

        return fig, ax

    def _add_value_labels(self, ax: Axes, bars: Any, values: list[float]) -> None:
        """Add value labels on top of bars."""
        for bar, value in zip(bars, values, strict=False):
            height = bar.get_height()
            # Format value with decimal if < threshold, else rounded
            value_threshold = 10
            if value < value_threshold:
                label = f"{value:.1f}h"
            else:
                label = f"{value:.0f}h"

            ax.text(  # type: ignore[misc]
                bar.get_x() + bar.get_width() / 2,
                height,
                label,
                ha="center",
                va="bottom",
                fontsize=10,
            )


class PieChartVisualizer(BaseVisualizer):
    """Pie chart visualizer for proportional data."""

    def create_chart(
        self, data: list[dict[str, Any]], x_key: str, y_key: str, **kwargs: Any
    ) -> tuple[Figure, Axes]:
        """Create a pie chart.

        Args:
            data: Analysis results data
            x_key: Key for slice labels (label_key)
            y_key: Key for slice values (value_key)
            **kwargs: Additional chart parameters

        Returns:
            Tuple of (figure, axes)

        """
        fig, ax = self.setup_figure()

        # Extract and process data
        labels, values = self._extract_pie_data(data, x_key, y_key)

        # Create pie chart with styling
        pie_result = self._create_pie_with_styling(ax, labels, values, **kwargs)

        # Customize text appearance
        self._customize_pie_text(pie_result)

        # Apply chart styling
        self._apply_pie_chart_styling(ax, fig, **kwargs)

        return fig, ax

    def _extract_pie_data(
        self, data: list[dict[str, Any]], x_key: str, y_key: str
    ) -> tuple[tuple[Any, ...], tuple[float, ...]]:
        """Extract and filter data for pie chart."""
        raw_labels = DataProcessor.extract_values(data, x_key)
        labels = DataProcessor.sanitize_labels(raw_labels)

        # Use hours instead of seconds for better readability
        if y_key == "total_seconds":
            values = DataProcessor.extract_hours_values(data, y_key)
        else:
            values = DataProcessor.extract_numeric_values(data, y_key)

        if not labels or not values:
            raise ValueError("Invalid data for pie chart")

        # Filter out zero values
        filtered_data = [
            (label, value)
            for label, value in zip(labels, values, strict=False)
            if value > 0
        ]
        if not filtered_data:
            raise ValueError("No positive values for pie chart")

        filtered_labels, filtered_values = zip(*filtered_data, strict=False)
        return filtered_labels, filtered_values

    def _create_pie_with_styling(
        self,
        ax: Axes,
        labels: tuple[Any, ...],
        values: tuple[float, ...],
        **kwargs: Any,
    ) -> tuple[Any, ...]:
        """Create pie chart with styling."""
        pie_style = self._get_pie_styling(**kwargs)
        return ax.pie(  # type: ignore[misc]
            values, labels=labels, autopct="%1.1f%%", **pie_style
        )

    def _customize_pie_text(self, pie_result: tuple[Any, ...]) -> None:
        """Customize text appearance for pie chart."""
        # Handle both 2-tuple and 3-tuple returns from pie()
        pie_tuple_length = 3
        if len(pie_result) == pie_tuple_length:
            _, texts, autotexts = pie_result
        else:
            _, texts = pie_result
            autotexts = []

        # Customize percentage text
        for autotext in autotexts:  # type: ignore[misc]
            autotext.set_color("white")  # type: ignore[misc]
            autotext.set_fontweight("bold")  # type: ignore[misc]
            autotext.set_fontsize(9)  # type: ignore[misc]

        # Customize label text
        for text in texts:  # type: ignore[misc]
            text.set_fontsize(10)  # type: ignore[misc]
            text.set_fontweight("normal")  # type: ignore[misc]

    def _apply_pie_chart_styling(self, ax: Axes, fig: Figure, **kwargs: Any) -> None:
        """Apply styling to pie chart."""
        ax.axis("equal")  # Equal aspect ratio ensures circular pie

        # Remove axes spines for cleaner look
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Optional: Create donut chart effect
        if kwargs.get("donut", False):
            centre_circle = Circle((0, 0), 0.70, fc="white")
            fig.gca().add_artist(centre_circle)

    def _get_pie_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get pie chart styling parameters."""
        # Modern flat design color palette
        default_colors = [
            "#4285F4",  # Google Blue
            "#EA4335",  # Google Red
            "#34A853",  # Google Green
            "#FBBC05",  # Google Yellow
            "#9C27B0",  # Material Purple
            "#FF9800",  # Material Orange
            "#607D8B",  # Material Blue Grey
            "#795548",  # Material Brown
            "#E91E63",  # Material Pink
            "#009688",  # Material Teal
            "#673AB7",  # Material Deep Purple
            "#FF5722",  # Material Deep Orange
        ]

        return {
            "colors": kwargs.get("colors", default_colors),
            "explode": kwargs.get("explode", None),
            "shadow": False,  # No shadow for modern flat design
            "startangle": kwargs.get("startangle", 90),
            "counterclock": False,  # Clockwise for consistency
            "wedgeprops": {"edgecolor": "white", "linewidth": 1.5, "antialiased": True},
            "textprops": {"fontsize": 10, "fontweight": "normal"},
            "pctdistance": 0.85,  # Move percentage labels closer to edge
            "labeldistance": 1.05,  # Position category labels slightly outside
        }


class TimeSeriesVisualizer(BaseVisualizer, ChartStyleMixin):
    """Time series line chart visualizer."""

    def create_chart(
        self, data: list[dict[str, Any]], x_key: str, y_key: str, **kwargs: Any
    ) -> tuple[Figure, Axes]:
        """Create a time series line chart.

        Args:
            data: Analysis results data
            x_key: Key for x-axis (time) values
            y_key: Key for y-axis values
            **kwargs: Additional chart parameters

        Returns:
            Tuple of (figure, axes)

        """
        fig, ax = self.setup_figure()

        # Create DataFrame for easier time series handling
        df = DataProcessor.create_dataframe(data)

        if x_key not in df.columns or y_key not in df.columns:
            raise ValueError(f"Required columns {x_key}, {y_key} not found in data")

        # Convert x-axis to datetime if needed
        if df[x_key].dtype == "object":
            df[x_key] = pd.to_datetime(df[x_key], errors="coerce")

        # Sort by time
        df = df.sort_values(x_key)  # type: ignore[misc]

        # Create line plot
        ax.plot(df[x_key], df[y_key], **self._get_line_styling(**kwargs))  # type: ignore[misc]

        # Add markers if requested
        if kwargs.get("show_markers", True):
            ax.scatter(df[x_key], df[y_key], **self._get_marker_styling(**kwargs))  # type: ignore[misc]

        # Format x-axis for dates
        if pd.api.types.is_datetime64_any_dtype(df[x_key]):  # type: ignore[misc]
            fig.autofmt_xdate()

        return fig, ax


class HeatmapVisualizer(BaseVisualizer):
    """Heatmap visualizer for correlation matrices."""

    def create_chart(
        self, data: list[dict[str, Any]], x_key: str, y_key: str, **kwargs: Any
    ) -> tuple[Figure, Axes]:
        """Create a heatmap.

        Args:
            data: Analysis results data
            x_key: Not used for heatmaps but required by interface
            y_key: Not used for heatmaps but required by interface
            **kwargs: Additional chart parameters

        Returns:
            Tuple of (figure, axes)

        """
        fig, ax = self.setup_figure()

        # Convert to DataFrame
        df = DataProcessor.create_dataframe(data)

        # Convert potential numeric string columns to numeric
        for col in df.columns:
            if col in ["task_count", "total_seconds", "percentage"]:
                # Try to convert string percentages and counts to numeric
                if df[col].dtype == "object":
                    # Remove % sign and convert to float
                    if col == "percentage":
                        # Type: ignore for pandas overload complexity
                        df[col] = pd.to_numeric(  # type: ignore[assignment]
                            df[col].str.replace("%", ""), errors="coerce"
                        )
                    else:
                        df[col] = pd.to_numeric(df[col], errors="coerce")  # type: ignore[assignment]

        # Select only numeric columns for correlation
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        min_columns_required = 2
        if len(numeric_columns) < min_columns_required:
            raise ValueError("Need at least 2 numeric columns for heatmap")

        # Calculate correlation matrix
        corr_matrix = df[numeric_columns].corr()

        # Create heatmap
        sns.heatmap(  # type: ignore[misc]
            corr_matrix,
            annot=kwargs.get("show_values", True),
            cmap=kwargs.get("colormap", "coolwarm"),
            center=kwargs.get("center", 0),
            square=kwargs.get("square", True),
            fmt=kwargs.get("format", ".2f"),
            ax=ax,
        )

        return fig, ax


class HistogramVisualizer(BaseVisualizer, ChartStyleMixin, ChartCreationMixin):
    """Histogram visualizer for distribution analysis."""

    def create_chart(
        self, data: list[dict[str, Any]], x_key: str, y_key: str, **kwargs: Any
    ) -> tuple[Figure, Axes]:
        """Create a histogram.

        Args:
            data: Analysis results data
            x_key: Key for values to create histogram (value_key)
            y_key: Not used for histograms but required by interface
            **kwargs: Additional chart parameters

        Returns:
            Tuple of (figure, axes)

        """
        # For histograms, x_key contains the value_key - use common pattern
        prepared, fig, ax = self._create_chart_with_common_pattern(
            data, x_key, "", "histogram", **kwargs
        )
        values = prepared["values"]

        # Create histogram
        ax.hist(  # type: ignore[misc]
            values, bins=kwargs.get("bins", 30), **self._get_histogram_styling(**kwargs)
        )

        # Add statistics text if requested
        if kwargs.get("show_stats", True):
            self._add_statistics_text(ax, values)

        return fig, ax

    def _add_statistics_text(self, ax: Axes, values: list[float]) -> None:
        """Add statistics text to histogram."""
        mean_val = np.mean(values)
        std_val = np.std(values)

        # Format statistics with appropriate units (hours)
        stats_text = f"Mean: {mean_val:.1f}h\nStd: {std_val:.1f}h"
        ax.text(  # type: ignore[misc]
            0.7,
            0.9,
            stats_text,
            transform=ax.transAxes,
            verticalalignment="top",
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
        )
