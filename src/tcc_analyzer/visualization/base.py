"""Base classes and interfaces for visualization."""

import re
import warnings
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.axes import Axes
from matplotlib.figure import Figure


class ChartType(Enum):
    """Supported chart types."""

    BAR = "bar"
    PIE = "pie"
    LINE = "line"
    HISTOGRAM = "histogram"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class OutputFormat(Enum):
    """Supported output formats."""

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    SHOW = "show"  # Display in window


class BaseVisualizer(ABC):
    """Abstract base class for all visualizers."""

    def __init__(
        self, figsize: tuple[int, int] = (10, 6), style: str = "default"
    ) -> None:
        """Initialize the visualizer.

        Args:
            figsize: Figure size as (width, height)
            style: Matplotlib style to use

        """
        self.figsize = figsize
        self.style = style
        self._fig: Figure | None = None
        self._ax: Axes | None = None

    def setup_figure(self) -> tuple[Figure, Axes]:
        """Set up the matplotlib figure and axes."""
        plt.style.use(self.style)

        # Get available fonts and use safe defaults
        available_fonts = [f.name for f in font_manager.fontManager.ttflist]

        # Priority list of fonts that handle Unicode well
        preferred_fonts = ["DejaVu Sans", "Liberation Sans", "Arial", "Helvetica"]
        safe_fonts = [font for font in preferred_fonts if font in available_fonts]

        # Fallback to generic sans-serif if no preferred fonts available
        if not safe_fonts:
            safe_fonts = ["sans-serif"]

        plt.rcParams["font.family"] = safe_fonts
        plt.rcParams["axes.unicode_minus"] = False

        # Suppress all font-related warnings
        warnings.filterwarnings(
            "ignore", message="Glyph .* missing from font.*", category=UserWarning
        )
        warnings.filterwarnings(
            "ignore", message="findfont: Font family.*not found.*", category=UserWarning
        )

        self._fig, self._ax = plt.subplots(figsize=self.figsize)
        return self._fig, self._ax

    @abstractmethod
    def create_chart(
        self, data: list[dict[str, Any]], **kwargs: Any
    ) -> tuple[Figure, Axes]:
        """Create the chart from data.

        Args:
            data: Analysis results data
            **kwargs: Additional chart-specific parameters

        Returns:
            Tuple of (figure, axes)

        """
        pass

    def customize_chart(
        self,
        title: str | None = None,
        xlabel: str | None = None,
        ylabel: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Customize chart appearance.

        Args:
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            **kwargs: Additional customization options

        """
        if self._ax is None:
            raise RuntimeError("Chart must be created before customization")

        if title:
            self._ax.set_title(title, fontsize=14, fontweight="bold")
        if xlabel:
            self._ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            self._ax.set_ylabel(ylabel, fontsize=12)

        # Apply additional customizations
        self._apply_custom_styling(**kwargs)

    def _apply_custom_styling(self, **kwargs: Any) -> None:
        """Apply custom styling options."""
        if not self._ax:
            return

        # Grid
        if kwargs.get("grid", True):
            self._ax.grid(True, alpha=0.3)

        # Tick rotation
        if "xtick_rotation" in kwargs:
            self._ax.tick_params(axis="x", rotation=kwargs["xtick_rotation"])
        if "ytick_rotation" in kwargs:
            self._ax.tick_params(axis="y", rotation=kwargs["ytick_rotation"])

        # Tight layout
        if kwargs.get("tight_layout", True):
            plt.tight_layout()

    def save_chart(
        self, output_path: Path, format: OutputFormat = OutputFormat.PNG, dpi: int = 300
    ) -> None:
        """Save chart to file.

        Args:
            output_path: Output file path
            format: Output format
            dpi: Resolution for raster formats

        """
        if self._fig is None:
            raise RuntimeError("Chart must be created before saving")

        # Ensure proper file extension
        output_path = output_path.with_suffix(f".{format.value}")

        self._fig.savefig(
            output_path,
            format=format.value,
            dpi=dpi,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )

    def show_chart(self) -> None:
        """Display chart in window."""
        if self._fig is None:
            raise RuntimeError("Chart must be created before showing")
        plt.show()

    def close_chart(self) -> None:
        """Close the chart and free resources."""
        if self._fig is not None:
            plt.close(self._fig)
            self._fig = None
            self._ax = None


class DataProcessor:
    """Utility class for processing analysis data for visualization."""

    @staticmethod
    def sanitize_labels(labels: list[Any]) -> list[str]:
        """Sanitize labels by handling Unicode characters and emojis."""
        return [
            DataProcessor._sanitize_single_label(label, i)
            for i, label in enumerate(labels)
        ]

    @staticmethod
    def _sanitize_single_label(label: Any, index: int) -> str:
        """Sanitize a single label."""
        if label is None:
            return "Unknown"

        label_str = str(label)

        # Remove emoji and problematic Unicode characters
        emoji_pattern = r"[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]"
        cleaned = re.sub(emoji_pattern, "", label_str)

        # Remove any remaining non-printable characters except basic ASCII
        cleaned = re.sub(r"[^\x20-\x7E\u00A0-\u024F\u1E00-\u1EFF]", "", cleaned)

        # Clean up extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Provide fallback if string becomes empty
        if not cleaned:
            cleaned = f"Item_{index + 1}"

        return cleaned

    @staticmethod
    def extract_values(data: list[dict[str, Any]], key: str) -> list[Any]:
        """Extract values for a specific key from analysis data."""
        return [item.get(key) for item in data if key in item]

    @staticmethod
    def extract_numeric_values(data: list[dict[str, Any]], key: str) -> list[float]:
        """Extract numeric values, converting time strings to seconds."""
        values = []
        for item in data:
            if key not in item:
                continue

            converted_value = DataProcessor._convert_to_numeric(item[key])
            if converted_value is not None:
                values.append(converted_value)

        return values

    @staticmethod
    def _convert_to_numeric(value: Any) -> float | None:
        """Convert a value to numeric format."""
        if isinstance(value, str):
            # Handle time duration strings (HH:MM:SS)
            if ":" in value:
                return DataProcessor._time_to_seconds(value)
            # Handle numeric strings
            elif value.replace(".", "").isdigit():
                return float(value)
        elif isinstance(value, int | float):
            return float(value)
        return None

    @staticmethod
    def extract_hours_values(data: list[dict[str, Any]], key: str) -> list[float]:
        """Extract numeric values, converting time strings to hours."""
        seconds_values = DataProcessor.extract_numeric_values(data, key)
        # Convert seconds to hours
        return [seconds / 3600 for seconds in seconds_values]

    @staticmethod
    def _time_to_seconds(time_str: str) -> float:
        """Convert time string (HH:MM:SS) to seconds."""
        try:
            parts = time_str.split(":")
            # Constants for time part counts
            time_parts_hh_mm_ss = 3
            time_parts_mm_ss = 2

            if len(parts) == time_parts_hh_mm_ss:
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == time_parts_mm_ss:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            else:
                return 0.0
        except (ValueError, IndexError):
            return 0.0

    @staticmethod
    def create_dataframe(data: list[dict[str, Any]]) -> pd.DataFrame:
        """Convert analysis data to pandas DataFrame."""
        return pd.DataFrame(data)

    @staticmethod
    def filter_top_items(
        data: list[dict[str, Any]], value_key: str, n: int = 10
    ) -> list[dict[str, Any]]:
        """Filter top N items by value."""
        numeric_values = []
        for item in data:
            if value_key in item:
                try:
                    if value_key == "total_seconds":
                        numeric_values.append((item, int(item[value_key])))
                    else:
                        numeric_values.append((item, float(item[value_key])))
                except (ValueError, TypeError):
                    continue

        # Sort by value and return top N
        sorted_items = sorted(numeric_values, key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:n]]
