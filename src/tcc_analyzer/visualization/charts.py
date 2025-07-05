"""Concrete chart visualizers for different chart types."""

from typing import Any

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle

from .base import BaseVisualizer, DataProcessor


class ChartStyleMixin:
    """Mixin class for common chart styling methods."""

    def _get_common_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get common styling parameters shared across chart types."""
        return {
            "color": kwargs.get("color", "steelblue"),
            "alpha": kwargs.get("alpha", 0.8),
            "edgecolor": kwargs.get("edgecolor", "black"),
            "linewidth": kwargs.get("linewidth", 0.5),
        }

    def _get_bar_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get bar-specific styling parameters."""
        return self._get_common_styling(**kwargs)

    def _get_histogram_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get histogram-specific styling parameters."""
        styling = self._get_common_styling(**kwargs)
        styling["alpha"] = kwargs.get("alpha", 0.7)  # Slightly different default
        return styling

    def _get_line_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get line-specific styling parameters."""
        return {
            "color": kwargs.get("color", "steelblue"),
            "linewidth": kwargs.get("linewidth", 2),
            "linestyle": kwargs.get("linestyle", "-"),
            "alpha": kwargs.get("alpha", 0.8),
        }

    def _get_marker_styling(self, **kwargs: Any) -> dict[str, Any]:
        """Get marker-specific styling parameters."""
        return {
            "color": kwargs.get("marker_color", "darkblue"),
            "size": kwargs.get("marker_size", 50),
            "alpha": kwargs.get("marker_alpha", 0.6),
            "marker": kwargs.get("marker_style", "o"),
        }


class BarChartVisualizer(BaseVisualizer, ChartStyleMixin):
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
        fig, ax = self.setup_figure()

        # Extract data
        raw_labels = DataProcessor.extract_values(data, x_key)
        labels = DataProcessor.sanitize_labels(raw_labels)

        # Use hours instead of seconds for better readability
        if y_key == "total_seconds":
            values = DataProcessor.extract_hours_values(data, y_key)
        else:
            values = DataProcessor.extract_numeric_values(data, y_key)

        if not labels or not values:
            raise ValueError("Invalid data for bar chart")

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


class HistogramVisualizer(BaseVisualizer, ChartStyleMixin):
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
        fig, ax = self.setup_figure()

        # Extract numeric values (use hours for better readability)
        # For histograms, x_key contains the value_key
        value_key = x_key
        if value_key == "total_seconds":
            values = DataProcessor.extract_hours_values(data, value_key)
        else:
            values = DataProcessor.extract_numeric_values(data, value_key)

        if not values:
            raise ValueError("No numeric values found for histogram")

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
