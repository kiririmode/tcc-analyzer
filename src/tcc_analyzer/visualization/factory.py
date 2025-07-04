"""Factory class for creating visualizers."""

from typing import Any, ClassVar

from .base import BaseVisualizer, ChartType
from .charts import (
    BarChartVisualizer,
    HeatmapVisualizer,
    HistogramVisualizer,
    PieChartVisualizer,
    TimeSeriesVisualizer,
)


class VisualizationFactory:
    """Factory for creating visualization instances."""

    _visualizers: ClassVar[dict[ChartType, type[BaseVisualizer]]] = {
        ChartType.BAR: BarChartVisualizer,
        ChartType.PIE: PieChartVisualizer,
        ChartType.LINE: TimeSeriesVisualizer,
        ChartType.HISTOGRAM: HistogramVisualizer,
        ChartType.HEATMAP: HeatmapVisualizer,
    }

    @classmethod
    def create_visualizer(cls, chart_type: ChartType, **kwargs: Any) -> BaseVisualizer:
        """Create a visualizer instance.

        Args:
            chart_type: Type of chart to create
            **kwargs: Arguments to pass to visualizer constructor

        Returns:
            Visualizer instance

        Raises:
            ValueError: If chart type is not supported

        """
        if chart_type not in cls._visualizers:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        visualizer_class = cls._visualizers[chart_type]
        return visualizer_class(**kwargs)

    @classmethod
    def get_available_types(cls) -> list[ChartType]:
        """Get list of available chart types."""
        return list(cls._visualizers.keys())

    @classmethod
    def register_visualizer(
        cls, chart_type: ChartType, visualizer_class: type[BaseVisualizer]
    ) -> None:
        """Register a new visualizer class.

        Args:
            chart_type: Chart type to register
            visualizer_class: Visualizer class to register

        """
        cls._visualizers[chart_type] = visualizer_class
