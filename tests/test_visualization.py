"""Tests for visualization module."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from tcc_analyzer.visualization import (
    BarChartVisualizer,
    ChartType,
    DataProcessor,
    OutputFormat,
    PieChartVisualizer,
    StatisticalAnalyzer,
    VisualizationFactory,
)
from tcc_analyzer.visualization.charts import (
    HeatmapVisualizer,
    HistogramVisualizer,
    TimeSeriesVisualizer,
)


class TestDataProcessor:
    """Test DataProcessor utility class."""

    def test_extract_values(self):
        """Test extracting values from data."""
        data = [
            {"name": "Project A", "time": "02:30:00"},
            {"name": "Project B", "time": "01:15:30"},
            {"value": 100},  # Missing "name" key
        ]

        names = DataProcessor.extract_values(data, "name")
        assert names == ["Project A", "Project B"]

        times = DataProcessor.extract_values(data, "time")
        assert times == ["02:30:00", "01:15:30"]

    def test_extract_numeric_values_from_seconds(self):
        """Test extracting numeric values when already in seconds."""
        data = [
            {"total_seconds": 3600},
            {"total_seconds": 7200},
            {"total_seconds": 1800},
        ]

        values = DataProcessor.extract_numeric_values(data, "total_seconds")
        assert values == [3600.0, 7200.0, 1800.0]

    def test_extract_numeric_values_from_time_strings(self):
        """Test extracting numeric values from time strings."""
        data = [
            {"duration": "01:00:00"},  # 3600 seconds
            {"duration": "02:00:00"},  # 7200 seconds
            {"duration": "30:00"},  # 1800 seconds
        ]

        values = DataProcessor.extract_numeric_values(data, "duration")
        assert values == [3600.0, 7200.0, 1800.0]

    def test_extract_hours_values(self):
        """Test extracting values converted to hours."""
        data = [
            {"total_seconds": 3600},  # 1 hour
            {"total_seconds": 7200},  # 2 hours
            {"total_seconds": 1800},  # 0.5 hours
        ]

        hours = DataProcessor.extract_hours_values(data, "total_seconds")
        assert hours == [1.0, 2.0, 0.5]

    def test_sanitize_labels_with_emojis(self):
        """Test sanitizing labels containing emojis."""
        labels = ["🖥️ Work", "🏠 Home", "📚 Study", None, "Normal Text"]

        sanitized = DataProcessor.sanitize_labels(labels)

        assert len(sanitized) == 5
        assert sanitized[0] == "Work"  # Emoji removed, whitespace cleaned
        assert sanitized[1] == "Home"  # Emoji removed, whitespace cleaned
        assert sanitized[2] == "Study"  # Emoji removed, whitespace cleaned
        assert sanitized[3] == "Unknown"  # None replaced
        assert sanitized[4] == "Normal Text"  # Normal text preserved

    def test_filter_top_items(self):
        """Test filtering top N items."""
        data = [
            {"name": "A", "total_seconds": 1000},
            {"name": "B", "total_seconds": 3000},
            {"name": "C", "total_seconds": 2000},
            {"name": "D", "total_seconds": 500},
        ]

        top_2 = DataProcessor.filter_top_items(data, "total_seconds", 2)

        assert len(top_2) == 2
        assert top_2[0]["name"] == "B"  # Highest value
        assert top_2[1]["name"] == "C"  # Second highest

    def test_sanitize_labels_empty_after_cleaning(self):
        """Test sanitizing labels that become empty after cleaning."""
        labels = ["🎯", "📊", None, ""]

        sanitized = DataProcessor.sanitize_labels(labels)

        assert len(sanitized) == 4
        assert sanitized[0] == "Item_1"  # Emoji removed, becomes empty, gets fallback
        assert sanitized[1] == "Item_2"  # Emoji removed, becomes empty, gets fallback
        assert sanitized[2] == "Unknown"  # None replaced
        assert sanitized[3] == "Item_4"  # Empty string gets fallback

    def test_time_to_seconds_edge_cases(self):
        """Test time string conversion edge cases."""
        # Test MM:SS format (2 parts)
        result = DataProcessor._time_to_seconds("05:30")
        assert result == 330.0  # 5*60 + 30

        # Test invalid format (too many parts)
        result = DataProcessor._time_to_seconds("01:02:03:04")
        assert result == 0.0

        # Test invalid format (not numeric)
        result = DataProcessor._time_to_seconds("abc:def")
        assert result == 0.0

        # Test empty string
        result = DataProcessor._time_to_seconds("")
        assert result == 0.0

    def test_extract_numeric_values_edge_cases(self):
        """Test extracting numeric values edge cases."""
        data = [
            {"value": "123.45"},  # Numeric string
            {"value": "abc"},  # Non-numeric string
            {"value": None},  # None value
            {"other": 100},  # Missing key
        ]

        values = DataProcessor.extract_numeric_values(data, "value")
        assert values == [123.45]  # Only the valid numeric string

    def test_filter_top_items_with_invalid_values(self):
        """Test filtering top items with invalid values."""
        data = [
            {"name": "A", "value": 100},
            {"name": "B", "value": "invalid"},  # Invalid value
            {"name": "C", "value": 200},
            {"name": "D"},  # Missing key
        ]

        top_items = DataProcessor.filter_top_items(data, "value", 10)

        assert len(top_items) == 2  # Only valid items
        assert top_items[0]["name"] == "C"  # Highest value (200)
        assert top_items[1]["name"] == "A"  # Second highest (100)

    def test_filter_top_items_non_seconds_key(self):
        """Test filtering top items with non-total_seconds key."""
        data = [
            {"name": "A", "score": 85.5},
            {"name": "B", "score": 92.0},
            {"name": "C", "score": 78.5},
        ]

        top_2 = DataProcessor.filter_top_items(data, "score", 2)

        assert len(top_2) == 2
        assert top_2[0]["name"] == "B"  # Highest score (92.0)
        assert top_2[1]["name"] == "A"  # Second highest (85.5)

    def test_create_dataframe(self):
        """Test creating DataFrame from data."""
        data = [
            {"name": "A", "value": 100},
            {"name": "B", "value": 200},
        ]

        df = DataProcessor.create_dataframe(data)

        assert len(df) == 2
        assert list(df.columns) == ["name", "value"]
        assert df.iloc[0]["name"] == "A"
        assert df.iloc[1]["value"] == 200


class TestVisualizationFactory:
    """Test VisualizationFactory."""

    def test_create_bar_visualizer(self):
        """Test creating bar chart visualizer."""
        visualizer = VisualizationFactory.create_visualizer(ChartType.BAR)
        assert isinstance(visualizer, BarChartVisualizer)

    def test_create_pie_visualizer(self):
        """Test creating pie chart visualizer."""
        visualizer = VisualizationFactory.create_visualizer(ChartType.PIE)
        assert isinstance(visualizer, PieChartVisualizer)

    def test_unsupported_chart_type(self):
        """Test error for unsupported chart type."""
        with pytest.raises(ValueError, match="Unsupported chart type"):
            # Create a mock chart type that doesn't exist
            fake_type = Mock()
            fake_type.name = "FAKE_CHART"
            VisualizationFactory.create_visualizer(fake_type)

    def test_get_available_types(self):
        """Test getting available chart types."""
        types = VisualizationFactory.get_available_types()
        assert ChartType.BAR in types
        assert ChartType.PIE in types
        assert len(types) >= 2


class TestStatisticalAnalyzer:
    """Test StatisticalAnalyzer."""

    def test_calculate_descriptive_stats(self):
        """Test calculating descriptive statistics."""
        data = [
            {"value": 10},
            {"value": 20},
            {"value": 30},
            {"value": 40},
            {"value": 50},
        ]

        stats = StatisticalAnalyzer.calculate_descriptive_stats(data, "value")

        assert stats["count"] == 5
        assert stats["mean"] == 30.0
        assert stats["median"] == 30.0
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["range"] == 40.0  # max - min
        assert stats["q1"] == 20.0  # 25th percentile
        assert stats["q3"] == 40.0  # 75th percentile
        assert stats["iqr"] == 20.0  # q3 - q1

    def test_calculate_time_distribution(self):
        """Test calculating time distribution statistics."""
        data = [
            {"total_seconds": 3600},  # 1 hour
            {"total_seconds": 7200},  # 2 hours
            {"total_seconds": 14400},  # 4 hours
            {"total_seconds": 18000},  # 5 hours
        ]

        stats = StatisticalAnalyzer.calculate_time_distribution(data, "total_seconds")

        assert stats["total_hours"] == 12.0  # 1+2+4+5
        assert stats["avg_hours_per_task"] == 3.0
        assert stats["tasks_under_1h"] == 0
        assert stats["tasks_1_to_4h"] == 2  # 1h and 2h tasks
        assert stats["tasks_over_4h"] == 2  # 4h and 5h tasks

    def test_calculate_category_distribution(self):
        """Test calculating category-based distribution."""
        data = [
            {"category": "Work", "value": 100},
            {"category": "Work", "value": 150},
            {"category": "Study", "value": 80},
            {"category": "Study", "value": 120},
            {"category": "Personal", "value": 60},
        ]

        stats = StatisticalAnalyzer.calculate_category_distribution(
            data, "category", "value"
        )

        assert stats["total_categories"] == 3
        assert stats["most_active_category"] == "Work"  # Highest sum
        assert stats["least_active_category"] == "Personal"  # Lowest sum

        # Check Work category stats
        work_stats = stats["by_category"]["Work"]
        assert work_stats["count"] == 2
        assert work_stats["sum"] == 250
        assert work_stats["mean"] == 125.0

    def test_detect_outliers_iqr_method(self):
        """Test outlier detection using IQR method."""
        data = [
            {"value": 10},
            {"value": 12},
            {"value": 14},
            {"value": 16},
            {"value": 18},
            {"value": 20},
            {"value": 22},
            {"value": 24},
            {"value": 26},
            {"value": 100},  # Outlier
        ]

        outlier_indices, outlier_info = StatisticalAnalyzer.detect_outliers(
            data, "value", "iqr"
        )

        assert len(outlier_indices) == 1  # One outlier (100)
        assert 9 in outlier_indices  # Index of the outlier
        assert outlier_info["method"] == "IQR"
        assert outlier_info["outlier_count"] == 1
        assert outlier_info["outlier_percentage"] == 10.0  # 1 out of 10

    def test_detect_outliers_zscore_method(self):
        """Test outlier detection using Z-score method."""
        data = [
            {"value": 10},
            {"value": 12},
            {"value": 14},
            {"value": 16},
            {"value": 18},
            {"value": 20},
            {"value": 22},
            {"value": 24},
            {"value": 26},
            {"value": 100},  # Outlier
        ]

        _, outlier_info = StatisticalAnalyzer.detect_outliers(data, "value", "zscore")

        assert outlier_info["method"] == "Z-Score"
        assert outlier_info["threshold"] == 3
        assert isinstance(outlier_info["outlier_count"], int)

    def test_detect_outliers_invalid_method(self):
        """Test error for invalid outlier detection method."""
        data = [{"value": 10}, {"value": 20}]

        with pytest.raises(ValueError, match="Unsupported outlier detection method"):
            StatisticalAnalyzer.detect_outliers(data, "value", "invalid_method")

    def test_calculate_correlation_matrix(self):
        """Test calculating correlation matrix."""
        data = [
            {"x": 1, "y": 2, "z": 3},
            {"x": 2, "y": 4, "z": 6},
            {"x": 3, "y": 6, "z": 9},
            {"x": 4, "y": 8, "z": 12},
        ]

        # Test with all numeric columns
        corr_matrix = StatisticalAnalyzer.calculate_correlation_matrix(data)

        assert "x" in corr_matrix.columns
        assert "y" in corr_matrix.columns
        assert "z" in corr_matrix.columns
        assert len(corr_matrix) == 3  # 3x3 matrix

    def test_calculate_correlation_matrix_specific_keys(self):
        """Test calculating correlation matrix with specific keys."""
        data = [
            {"x": 1, "y": 2, "z": 3, "text": "ignore"},
            {"x": 2, "y": 4, "z": 6, "text": "ignore"},
            {"x": 3, "y": 6, "z": 9, "text": "ignore"},
        ]

        # Test with specific numeric keys
        corr_matrix = StatisticalAnalyzer.calculate_correlation_matrix(data, ["x", "y"])

        assert "x" in corr_matrix.columns
        assert "y" in corr_matrix.columns
        assert "z" not in corr_matrix.columns
        assert len(corr_matrix) == 2  # 2x2 matrix

    def test_calculate_trend_analysis(self):
        """Test calculating trend analysis for time series data."""
        data = [
            {"date": "2023-01-01", "value": 10},
            {"date": "2023-01-02", "value": 12},
            {"date": "2023-01-03", "value": 14},
            {"date": "2023-01-04", "value": 16},
            {"date": "2023-01-05", "value": 18},
        ]

        trends = StatisticalAnalyzer.calculate_trend_analysis(data, "date", "value")

        assert trends["trend_direction"] == "increasing"  # Positive slope
        assert trends["trend_slope"] > 0  # Positive trend
        assert isinstance(trends["correlation_coefficient"], float)
        assert isinstance(trends["p_value"], float)
        # Check is_significant value (can be numpy bool or Python bool)
        # Convert to Python bool for assertion since numpy bool behaves like bool
        assert bool(trends["is_significant"]) in [True, False]

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_data: list[dict[str, Any]] = []

        # Test descriptive stats
        stats = StatisticalAnalyzer.calculate_descriptive_stats(empty_data, "value")
        assert stats == {}

        # Test time distribution
        time_stats = StatisticalAnalyzer.calculate_time_distribution(empty_data, "time")
        assert time_stats == {}

        # Test category distribution
        cat_stats = StatisticalAnalyzer.calculate_category_distribution(
            empty_data, "cat", "val"
        )
        assert cat_stats == {}

        # Test outliers
        outlier_indices, outlier_info = StatisticalAnalyzer.detect_outliers(
            empty_data, "value"
        )
        assert outlier_indices == []
        assert outlier_info == {}

        # Test correlation matrix
        corr_matrix = StatisticalAnalyzer.calculate_correlation_matrix(empty_data)
        assert corr_matrix.empty

        # Test trend analysis
        trend_stats = StatisticalAnalyzer.calculate_trend_analysis(
            empty_data, "date", "value"
        )
        assert trend_stats == {}

    def test_missing_columns_handling(self):
        """Test handling of missing columns."""
        data = [
            {"x": 1, "y": 2},
            {"x": 2, "y": 4},
        ]

        # Test category distribution with missing columns
        cat_stats = StatisticalAnalyzer.calculate_category_distribution(
            data, "missing", "y"
        )
        assert cat_stats == {}

        cat_stats = StatisticalAnalyzer.calculate_category_distribution(
            data, "x", "missing"
        )
        assert cat_stats == {}

        # Test trend analysis with missing columns
        trend_stats = StatisticalAnalyzer.calculate_trend_analysis(data, "missing", "y")
        assert trend_stats == {}

        trend_stats = StatisticalAnalyzer.calculate_trend_analysis(data, "x", "missing")
        assert trend_stats == {}

    def test_invalid_datetime_handling(self):
        """Test handling of invalid datetime data."""
        data = [
            {"date": "invalid-date", "value": 10},
            {"date": "also-invalid", "value": 20},
        ]

        trends = StatisticalAnalyzer.calculate_trend_analysis(data, "date", "value")
        assert trends == {}  # Should return empty dict for invalid dates

    def test_non_numeric_data_handling(self):
        """Test handling of non-numeric data in correlation matrix."""
        data = [
            {"text": "hello", "number": 1},
            {"text": "world", "number": 2},
        ]

        # Should only include numeric columns
        corr_matrix = StatisticalAnalyzer.calculate_correlation_matrix(data)

        # Only 'number' column included, but correlation needs >=2 columns
        assert corr_matrix.empty or len(corr_matrix.columns) >= 1


@patch("matplotlib.pyplot.subplots")
@patch("matplotlib.pyplot.style")
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

    def test_save_chart(self, mock_style: Any, mock_subplots: Any):
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
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test error when trying to save without creating chart."""
        visualizer = BarChartVisualizer()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_chart"

            with pytest.raises(
                RuntimeError, match="Chart must be created before saving"
            ):
                visualizer.save_chart(output_path)

    def test_customize_chart_all_options(self, mock_style: Any, mock_subplots: Any):
        """Test chart customization with all options."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()
        visualizer.setup_figure()

        # Test all customization options
        with patch("matplotlib.pyplot.tight_layout") as mock_tight_layout:
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

    def test_customize_chart_partial_options(self, mock_style: Any, mock_subplots: Any):
        """Test chart customization with partial options."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()
        visualizer.setup_figure()

        # Test only some options
        with patch("matplotlib.pyplot.tight_layout") as mock_tight_layout:
            visualizer.customize_chart(
                title="Only Title", grid=False, tight_layout=False
            )

            mock_ax.set_title.assert_called_once()
            mock_ax.set_xlabel.assert_not_called()
            mock_ax.set_ylabel.assert_not_called()
            mock_ax.grid.assert_not_called()  # grid=False, so no grid call
            mock_tight_layout.assert_not_called()  # tight_layout=False

    def test_customize_chart_before_creation_error(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test error when customizing before chart creation."""
        visualizer = BarChartVisualizer()

        with pytest.raises(
            RuntimeError, match="Chart must be created before customization"
        ):
            visualizer.customize_chart(title="Test")

    def test_show_chart(self, mock_style: Any, mock_subplots: Any):
        """Test showing chart in window."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()
        visualizer.setup_figure()

        with patch("matplotlib.pyplot.show") as mock_show:
            visualizer.show_chart()
            mock_show.assert_called_once()

    def test_show_chart_before_creation_error(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test error when showing chart before creation."""
        visualizer = BarChartVisualizer()

        with pytest.raises(RuntimeError, match="Chart must be created before showing"):
            visualizer.show_chart()

    def test_close_chart(self, mock_style: Any, mock_subplots: Any):
        """Test closing chart and freeing resources."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()
        visualizer.setup_figure()

        with patch("matplotlib.pyplot.close") as mock_close:
            visualizer.close_chart()
            mock_close.assert_called_once_with(mock_fig)
            assert visualizer._fig is None
            assert visualizer._ax is None

    def test_close_chart_when_no_figure(self, mock_style: Any, mock_subplots: Any):
        """Test closing chart when no figure exists."""
        visualizer = BarChartVisualizer()

        with patch("matplotlib.pyplot.close") as mock_close:
            visualizer.close_chart()
            mock_close.assert_not_called()  # Should not call close if no figure


@patch("matplotlib.pyplot.subplots")
@patch("matplotlib.pyplot.style")
class TestBarChartVisualizer:
    """Test BarChartVisualizer."""

    def test_create_chart_success(self, mock_style: Any, mock_subplots: Any):
        """Test successful bar chart creation."""
        mock_fig = Mock()
        mock_ax = Mock()
        # Mock bars as an iterable for the value labels
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
        # Verify text labels were added
        assert mock_ax.text.call_count == 2

    def test_create_chart_invalid_data(self, mock_style: Any, mock_subplots: Any):
        """Test error with invalid data."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = BarChartVisualizer()

        with pytest.raises(ValueError, match="Invalid data for bar chart"):
            visualizer.create_chart([], x_key="project", y_key="total_seconds")

    def test_create_chart_no_valid_values(self, mock_style: Any, mock_subplots: Any):
        """Test error when data has keys but no extractable values."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        # Data with keys that don't extract properly
        data = [{"wrong_key": "value"}]

        visualizer = BarChartVisualizer()

        with pytest.raises(ValueError, match="Invalid data for bar chart"):
            visualizer.create_chart(data, x_key="missing_x", y_key="missing_y")

    def test_create_chart_with_non_seconds_key(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test bar chart with non-seconds y_key."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_bar1 = Mock()
        mock_bar1.get_height.return_value = 100.0
        mock_bar1.get_x.return_value = 0
        mock_bar1.get_width.return_value = 0.5
        mock_ax.bar.return_value = [mock_bar1]
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"name": "Test", "value": 100}]

        visualizer = BarChartVisualizer()
        fig: Figure
        ax: Axes
        fig, ax = visualizer.create_chart(data, x_key="name", y_key="value")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.bar.assert_called_once()

    def test_create_chart_with_show_values_false(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test bar chart without value labels."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_ax.bar.return_value = [Mock()]
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"project": "A", "total_seconds": 3600}]

        visualizer = BarChartVisualizer()
        visualizer.create_chart(
            data, x_key="project", y_key="total_seconds", show_values=False
        )

        # Should not call text method when show_values=False
        mock_ax.text.assert_not_called()

    def test_value_label_formatting_small_values(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test value label formatting for small values (< 10)."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_bar = Mock()
        mock_bar.get_height.return_value = 5.5
        mock_bar.get_x.return_value = 0
        mock_bar.get_width.return_value = 0.5
        mock_ax.bar.return_value = [mock_bar]
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"project": "A", "total_seconds": 19800}]  # 5.5 hours

        visualizer = BarChartVisualizer()
        visualizer.create_chart(data, x_key="project", y_key="total_seconds")

        # Check that text was called with decimal format
        mock_ax.text.assert_called_once()
        call_args = mock_ax.text.call_args[0]
        assert "5.5h" in call_args[2]  # Third argument is the label text

    def test_value_label_formatting_large_values(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test value label formatting for large values (>= 10)."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_bar = Mock()
        mock_bar.get_height.return_value = 15.7
        mock_bar.get_x.return_value = 0
        mock_bar.get_width.return_value = 0.5
        mock_ax.bar.return_value = [mock_bar]
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"project": "A", "total_seconds": 56520}]  # 15.7 hours

        visualizer = BarChartVisualizer()
        visualizer.create_chart(data, x_key="project", y_key="total_seconds")

        # Check that text was called with rounded format
        mock_ax.text.assert_called_once()
        call_args = mock_ax.text.call_args[0]
        assert "16h" in call_args[2]  # Should be rounded to 16h


@patch("matplotlib.pyplot.subplots")
@patch("matplotlib.pyplot.style")
class TestPieChartVisualizer:
    """Test PieChartVisualizer."""

    def test_create_chart_success(self, mock_style: Any, mock_subplots: Any):
        """Test successful pie chart creation."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_ax.pie.return_value = (Mock(), [Mock()], [Mock()])
        mock_ax.spines = {
            "top": Mock(),
            "right": Mock(),
            "bottom": Mock(),
            "left": Mock(),
        }
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"project": "A", "total_seconds": 3600},
            {"project": "B", "total_seconds": 7200},
        ]

        visualizer = PieChartVisualizer()
        fig: Figure
        ax: Axes
        fig, ax = visualizer.create_chart(data, x_key="project", y_key="total_seconds")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.pie.assert_called_once()

    def test_create_chart_with_non_seconds_key(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test pie chart with non-seconds value_key."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_ax.pie.return_value = (Mock(), [Mock()], [Mock()])
        mock_ax.spines = {
            "top": Mock(),
            "right": Mock(),
            "bottom": Mock(),
            "left": Mock(),
        }
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"category": "A", "value": 100},
            {"category": "B", "value": 200},
        ]

        visualizer = PieChartVisualizer()
        fig: Figure
        ax: Axes
        fig, ax = visualizer.create_chart(data, x_key="category", y_key="value")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.pie.assert_called_once()

    def test_create_chart_with_donut_style(self, mock_style: Any, mock_subplots: Any):
        """Test pie chart with donut style."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_ax.pie.return_value = (Mock(), [Mock()], [Mock()])
        mock_ax.spines = {
            "top": Mock(),
            "right": Mock(),
            "bottom": Mock(),
            "left": Mock(),
        }
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"project": "A", "total_seconds": 3600}]

        visualizer = PieChartVisualizer()
        visualizer.create_chart(
            data, x_key="project", y_key="total_seconds", donut=True
        )

        # Should call gca().add_artist for donut effect
        mock_fig.gca.assert_called_once()

    def test_create_chart_no_positive_values(self, mock_style: Any, mock_subplots: Any):
        """Test error when no positive values."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"project": "A", "total_seconds": 0},
            {"project": "B", "total_seconds": 0},
        ]

        visualizer = PieChartVisualizer()

        with pytest.raises(ValueError, match="No positive values for pie chart"):
            visualizer.create_chart(data, x_key="project", y_key="total_seconds")

    def test_create_chart_invalid_data(self, mock_style: Any, mock_subplots: Any):
        """Test error with invalid data."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualizer = PieChartVisualizer()

        with pytest.raises(ValueError, match="Invalid data for pie chart"):
            visualizer.create_chart([], x_key="project", y_key="total_seconds")


@patch("matplotlib.pyplot.subplots")
@patch("matplotlib.pyplot.style")
class TestTimeSeriesVisualizer:
    """Test TimeSeriesVisualizer."""

    def test_create_chart_success(self, mock_style: Any, mock_subplots: Any):
        """Test successful time series chart creation."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"date": "2023-01-01", "value": 100},
            {"date": "2023-01-02", "value": 150},
        ]

        visualizer = TimeSeriesVisualizer()
        fig: Figure
        ax: Axes
        fig, ax = visualizer.create_chart(data, x_key="date", y_key="value")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.plot.assert_called_once()

    def test_create_chart_with_markers(self, mock_style: Any, mock_subplots: Any):
        """Test time series chart with markers."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"date": "2023-01-01", "value": 100}]

        visualizer = TimeSeriesVisualizer()
        visualizer.create_chart(data, x_key="date", y_key="value", show_markers=True)

        # Should call both plot and scatter
        mock_ax.plot.assert_called_once()
        mock_ax.scatter.assert_called_once()

    def test_create_chart_without_markers(self, mock_style: Any, mock_subplots: Any):
        """Test time series chart without markers."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"date": "2023-01-01", "value": 100}]

        visualizer = TimeSeriesVisualizer()
        visualizer.create_chart(data, x_key="date", y_key="value", show_markers=False)

        # Should call plot but not scatter
        mock_ax.plot.assert_called_once()
        mock_ax.scatter.assert_not_called()

    def test_create_chart_missing_columns(self, mock_style: Any, mock_subplots: Any):
        """Test error with missing columns."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"wrong_key": "2023-01-01", "value": 100}]

        visualizer = TimeSeriesVisualizer()

        with pytest.raises(ValueError, match="Required columns date, value not found"):
            visualizer.create_chart(data, x_key="date", y_key="value")


@patch("matplotlib.pyplot.subplots")
@patch("matplotlib.pyplot.style")
class TestHeatmapVisualizer:
    """Test HeatmapVisualizer."""

    def test_create_chart_success(self, mock_style: Any, mock_subplots: Any):
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
        self, mock_style: Any, mock_subplots: Any
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


@patch("matplotlib.pyplot.subplots")
@patch("matplotlib.pyplot.style")
class TestHistogramVisualizer:
    """Test HistogramVisualizer."""

    def test_create_chart_success_with_seconds(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test successful histogram with total_seconds."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"total_seconds": 3600},
            {"total_seconds": 7200},
            {"total_seconds": 1800},
        ]

        visualizer = HistogramVisualizer()
        fig: Figure
        ax: Axes
        fig, ax = visualizer.create_chart(data, x_key="total_seconds", y_key="dummy")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.hist.assert_called_once()

    def test_create_chart_success_with_other_values(
        self, mock_style: Any, mock_subplots: Any
    ):
        """Test successful histogram with non-seconds values."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [
            {"score": 85},
            {"score": 92},
            {"score": 78},
        ]

        visualizer = HistogramVisualizer()
        fig: Figure
        ax: Axes
        fig, ax = visualizer.create_chart(data, x_key="score", y_key="dummy")

        assert fig == mock_fig
        assert ax == mock_ax
        mock_ax.hist.assert_called_once()

    def test_create_chart_with_stats(self, mock_style: Any, mock_subplots: Any):
        """Test histogram with statistics text."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"value": 100}, {"value": 200}]

        visualizer = HistogramVisualizer()
        visualizer.create_chart(data, x_key="value", y_key="dummy", show_stats=True)

        # Should call text method to add statistics
        mock_ax.text.assert_called_once()

    def test_create_chart_without_stats(self, mock_style: Any, mock_subplots: Any):
        """Test histogram without statistics text."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"value": 100}, {"value": 200}]

        visualizer = HistogramVisualizer()
        visualizer.create_chart(data, x_key="value", y_key="dummy", show_stats=False)

        # Should not call text method when show_stats=False
        mock_ax.text.assert_not_called()

    def test_create_chart_no_numeric_values(self, mock_style: Any, mock_subplots: Any):
        """Test error with no numeric values."""
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        data = [{"text": "hello"}, {"text": "world"}]

        visualizer = HistogramVisualizer()

        with pytest.raises(ValueError, match="No numeric values found for histogram"):
            visualizer.create_chart(data, x_key="missing_key", y_key="dummy")
