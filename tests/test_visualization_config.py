"""Tests for visualization configuration and base functionality."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from tcc_analyzer.visualization import (
    BarChartVisualizer,
    OutputFormat,
)


@patch("tcc_analyzer.visualization.base.plt.subplots")
@patch("tcc_analyzer.visualization.base.plt.style")
class TestBaseVisualizer:
    """Test BaseVisualizer functionality."""

    def test_setup_figure(self, mock_style: Any, mock_subplots: Any):
        """Test figure setup."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()
        fig: Figure
        ax: Axes
        fig, ax = visualizer.setup_figure()

        assert fig == mock_fig
        assert ax == mock_ax
        mock_style.use.assert_called_once()
        mock_subplots.assert_called_once()

    def test_save_chart(self, _mock_style: Any, mock_subplots: Any):
        """Test saving chart to file."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()
        visualizer.setup_figure()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_chart"
            visualizer.save_chart(output_path, OutputFormat.PNG)

            mock_fig.savefig.assert_called_once()
            # Check that the path has the correct extension
            call_args = mock_fig.savefig.call_args[0]
            assert str(call_args[0]).endswith(".png")

    def test_chart_must_be_created_before_saving(
        self, _mock_style: Any, _mock_subplots: Any
    ):
        """Test error when trying to save without creating chart."""
        visualizer = BarChartVisualizer()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_chart"

            with pytest.raises(
                RuntimeError, match="Chart must be created before saving"
            ):
                visualizer.save_chart(output_path)

    def test_customize_chart_all_options(self, _mock_style: Any, mock_subplots: Any):
        """Test chart customization with all options."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()
        visualizer.setup_figure()

        # Test all customization options
        with patch(
            "tcc_analyzer.visualization.base.plt.tight_layout"
        ) as mock_tight_layout:
            visualizer.customize_chart(
                title="Test Title",
                xlabel="X Label",
                ylabel="Y Label",
                grid=True,
                xtick_rotation=45,
                ytick_rotation=90,
                tight_layout=True,
            )

            # Verify all methods were called
            mock_ax.set_title.assert_called_once_with(
                "Test Title", fontsize=14, fontweight="bold"
            )
            mock_ax.set_xlabel.assert_called_once_with("X Label", fontsize=12)
            mock_ax.set_ylabel.assert_called_once_with("Y Label", fontsize=12)
            mock_ax.grid.assert_called_once_with(True, alpha=0.3)
            mock_ax.tick_params.assert_any_call(axis="x", rotation=45)
            mock_ax.tick_params.assert_any_call(axis="y", rotation=90)
            mock_tight_layout.assert_called_once()

    def test_show_chart(self, _mock_style: Any, mock_subplots: Any):
        """Test showing chart."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()
        visualizer.setup_figure()

        with patch("tcc_analyzer.visualization.base.plt.show") as mock_show:
            visualizer.show_chart()
            mock_show.assert_called_once()

    def test_chart_must_be_created_before_showing(
        self, _mock_style: Any, _mock_subplots: Any
    ):
        """Test error when trying to show without creating chart."""
        visualizer = BarChartVisualizer()

        with pytest.raises(RuntimeError, match="Chart must be created before showing"):
            visualizer.show_chart()
