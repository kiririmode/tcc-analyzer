"""Tests for chart visualization functionality."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from tcc_analyzer.visualization import (
    BarChartVisualizer,
    PieChartVisualizer,
)
from tcc_analyzer.visualization.charts import (
    HistogramVisualizer,
    TimeSeriesVisualizer,
)


class TestBarChartVisualizer:
    """Test BarChartVisualizer."""

    @patch("tcc_analyzer.visualization.base.plt.style.use")
    @patch("tcc_analyzer.visualization.base.plt.subplots")
    def test_create_chart_success(self, mock_subplots: Any, _mock_style: Any):
        """Test successful bar chart creation."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_bar1 = Mock()
        mock_bar1.get_height.return_value = 1.0
        mock_bar1.get_x.return_value = 0
        mock_bar1.get_width.return_value = 0.5
        mock_bar2 = Mock()
        mock_bar2.get_height.return_value = 2.0
        mock_bar2.get_x.return_value = 1
        mock_bar2.get_width.return_value = 0.5
        mock_ax.bar.return_value = [mock_bar1, mock_bar2]
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"project": "A", "total_seconds": 3600},
            {"project": "B", "total_seconds": 7200},
        ]

        visualizer = BarChartVisualizer()
        fig: Figure
        ax: Axes
        fig, ax = visualizer.create_chart(data, x_key="project", y_key="total_seconds")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.bar.assert_called_once()

    @patch("tcc_analyzer.visualization.base.plt.style.use")
    @patch("tcc_analyzer.visualization.base.plt.subplots")
    def test_create_chart_invalid_data(self, mock_subplots: Any, mock_style: Any):
        """Test error with invalid data."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()

        with pytest.raises(ValueError, match="Invalid data for bar chart"):
            visualizer.create_chart([], x_key="project", y_key="total_seconds")


class TestPieChartVisualizer:
    """Test PieChartVisualizer."""

    @patch("tcc_analyzer.visualization.base.plt.style.use")
    @patch("tcc_analyzer.visualization.base.plt.subplots")
    def test_create_chart_success(self, mock_subplots: Any, mock_style: Any):
        """Test successful pie chart creation."""
        mock_fig = Mock()
        mock_ax = Mock()
        # Mock pie() to return a 3-tuple like matplotlib does
        mock_wedges = [Mock(), Mock()]
        mock_texts = [Mock(), Mock()]
        mock_autotexts = [Mock(), Mock()]
        mock_ax.pie.return_value = (mock_wedges, mock_texts, mock_autotexts)
        # Mock spines to avoid iteration error
        mock_ax.spines.values.return_value = []
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"project": "A", "total_seconds": 3600},
            {"project": "B", "total_seconds": 7200},
        ]

        visualizer = PieChartVisualizer()
        fig, ax = visualizer.create_chart(data, x_key="project", y_key="total_seconds")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.pie.assert_called_once()

    @patch("tcc_analyzer.visualization.base.plt.style.use")
    @patch("tcc_analyzer.visualization.base.plt.subplots")
    def test_create_chart_invalid_data(self, mock_subplots: Any, mock_style: Any):
        """Test error with invalid data."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = PieChartVisualizer()

        with pytest.raises(ValueError, match="Invalid data for pie chart"):
            visualizer.create_chart([], x_key="project", y_key="total_seconds")


class TestTimeSeriesVisualizer:
    """Test TimeSeriesVisualizer."""

    @patch("tcc_analyzer.visualization.base.plt.style.use")
    @patch("tcc_analyzer.visualization.base.plt.subplots")
    def test_create_chart_success(self, mock_subplots: Any, mock_style: Any):
        """Test successful time series chart creation."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"date": "2023-01-01", "hours": 8.0},
            {"date": "2023-01-02", "hours": 6.5},
        ]

        visualizer = TimeSeriesVisualizer()
        fig, ax = visualizer.create_chart(data, x_key="date", y_key="hours")

        assert fig == mock_fig
        assert ax == mock_ax


class TestHistogramVisualizer:
    """Test HistogramVisualizer."""

    @patch("tcc_analyzer.visualization.base.plt.style.use")
    @patch("tcc_analyzer.visualization.base.plt.subplots")
    def test_create_chart_success(self, mock_subplots: Any, mock_style: Any):
        """Test successful histogram creation."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"duration": 3600},
            {"duration": 7200},
            {"duration": 1800},
        ]

        visualizer = HistogramVisualizer()
        fig, ax = visualizer.create_chart(data, x_key="duration", y_key="")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.hist.assert_called_once()

    @patch("tcc_analyzer.visualization.base.plt.style.use")
    @patch("tcc_analyzer.visualization.base.plt.subplots")
    def test_create_chart_invalid_data(self, mock_subplots: Any, mock_style: Any):
        """Test error with invalid data."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = HistogramVisualizer()

        with pytest.raises(ValueError, match="No numeric values found for histogram"):
            visualizer.create_chart([], x_key="duration", y_key="")
