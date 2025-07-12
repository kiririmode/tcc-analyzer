"""Tests for heatmap visualization functionality."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from tcc_analyzer.visualization.charts import HeatmapVisualizer


@patch("tcc_analyzer.visualization.base.plt.subplots")
@patch("tcc_analyzer.visualization.base.plt.style")
class TestHeatmapVisualizer:
    """Test HeatmapVisualizer."""

    def test_create_chart_success(self, _mock_style: Any, mock_subplots: Any):
        """Test successful heatmap creation."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"x": 1, "y": 2, "z": 3},
            {"x": 2, "y": 4, "z": 6},
            {"x": 3, "y": 6, "z": 9},
        ]

        with patch("seaborn.heatmap") as mock_heatmap:
            visualizer = HeatmapVisualizer()
            fig: Figure
            ax: Axes
            fig, ax = visualizer.create_chart(data, x_key="x", y_key="y")

            assert fig == mock_fig
            assert ax == mock_ax
            mock_heatmap.assert_called_once()

    def test_create_chart_insufficient_numeric_columns(
        self, _mock_style: Any, mock_subplots: Any
    ):
        """Test error with insufficient numeric columns."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"x": 1, "text": "hello"},
            {"x": 2, "text": "world"},
        ]

        visualizer = HeatmapVisualizer()

        with pytest.raises(
            ValueError, match="Need at least 2 numeric columns for heatmap"
        ):
            visualizer.create_chart(data, x_key="x", y_key="y")

    def test_create_chart_with_annotations(self, _mock_style: Any, mock_subplots: Any):
        """Test heatmap with annotations."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"x": 1, "y": 2, "z": 3},
            {"x": 2, "y": 4, "z": 6},
        ]

        with patch("seaborn.heatmap") as mock_heatmap:
            visualizer = HeatmapVisualizer()
            visualizer.create_chart(data, x_key="x", y_key="y", annot=True)

            # Verify annotation parameter was used
            mock_heatmap.assert_called_once()
            call_kwargs = mock_heatmap.call_args[1]
            assert call_kwargs.get("annot") is True

    def test_create_chart_missing_z_values(self, _mock_style: Any, mock_subplots: Any):
        """Test heatmap with missing z values."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"x": 1, "y": 2},
            {"x": 2, "y": 4},
        ]

        with patch("seaborn.heatmap") as mock_heatmap:
            visualizer = HeatmapVisualizer()

            # Should handle missing z values gracefully
            fig, ax = visualizer.create_chart(data, x_key="x", y_key="y")

            assert fig == mock_fig
            assert ax == mock_ax
            mock_heatmap.assert_called_once()
