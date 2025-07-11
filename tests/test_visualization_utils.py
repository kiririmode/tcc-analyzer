"""Tests for visualization utility classes and functions."""

import pytest

from tcc_analyzer.visualization import (
    BarChartVisualizer,
    ChartType,
    DataProcessor,
    PieChartVisualizer,
    StatisticalAnalyzer,
    VisualizationFactory,
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
            {"duration": "00:30:00"},  # 1800 seconds
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
        # Test HH:MM format (2 parts)
        result = DataProcessor._time_to_seconds("05:30")
        assert result == 19800.0  # 5*3600 + 30*60

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
            {"x": 1, "y": 2, "z": 3},
            {"x": 4, "y": 5, "z": 6},
        ]

        df = DataProcessor.create_dataframe(data)

        assert df.shape == (2, 3)
        assert list(df.columns) == ["x", "y", "z"]
        assert df.iloc[0]["x"] == 1
        assert df.iloc[1]["z"] == 6

    def test_create_dataframe_empty_data(self):
        """Test creating DataFrame from empty data."""
        df = DataProcessor.create_dataframe([])
        assert df.empty

    def test_create_dataframe_mixed_keys(self):
        """Test creating DataFrame with mixed keys."""
        data = [
            {"a": 1, "b": 2},
            {"a": 3, "c": 4},  # Different keys
        ]

        df = DataProcessor.create_dataframe(data)

        # Should handle mixed keys gracefully
        assert "a" in df.columns
        assert len(df) == 2


class TestVisualizationFactory:
    """Test VisualizationFactory."""

    def test_create_visualizer_bar_chart(self):
        """Test creating bar chart visualizer."""
        visualizer = VisualizationFactory.create_visualizer(ChartType.BAR)
        assert isinstance(visualizer, BarChartVisualizer)

    def test_create_visualizer_pie_chart(self):
        """Test creating pie chart visualizer."""
        visualizer = VisualizationFactory.create_visualizer(ChartType.PIE)
        assert isinstance(visualizer, PieChartVisualizer)

    def test_create_visualizer_unsupported_type(self):
        """Test error with unsupported chart type."""
        with pytest.raises(ValueError, match="Unsupported chart type"):
            VisualizationFactory.create_visualizer("unsupported_type")  # type: ignore


class TestStatisticalAnalyzer:
    """Test StatisticalAnalyzer."""

    def test_statistical_analyzer_exists(self):
        """Test that StatisticalAnalyzer class exists and is importable."""
        assert StatisticalAnalyzer is not None

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

        # Test basic stats are present
        assert "mean" in stats
        assert "std" in stats
        assert "count" in stats

    def test_calculate_correlation_matrix(self):
        """Test calculating correlation matrix."""
        data = [
            {"x": 1, "y": 2, "z": 3},
            {"x": 2, "y": 4, "z": 6},
            {"x": 3, "y": 6, "z": 9},
        ]

        corr_matrix = StatisticalAnalyzer.calculate_correlation_matrix(data)

        # Should be a DataFrame or similar structure
        assert corr_matrix is not None
