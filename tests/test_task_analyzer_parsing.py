"""Tests for TaskAnalyzer parsing and time calculation functionality."""

import math
from datetime import timedelta
from pathlib import Path

import pytest
from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzerParsing:
    """Test class for TaskAnalyzer parsing functionality."""

    def test_parse_time_duration_valid(self) -> None:
        """Test parsing valid time duration strings."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test HH:MM:SS format
        assert analyzer._parse_time_duration("01:30:45") == timedelta(
            hours=1, minutes=30, seconds=45
        )
        assert analyzer._parse_time_duration("00:00") == timedelta(0)
        assert analyzer._parse_time_duration("12:59:59") == timedelta(
            hours=12, minutes=59, seconds=59
        )

        # Test HH:MM format (seconds omitted)
        assert analyzer._parse_time_duration("01:30") == timedelta(
            hours=1, minutes=30, seconds=0
        )
        assert analyzer._parse_time_duration("08:00") == timedelta(
            hours=8, minutes=0, seconds=0
        )
        assert analyzer._parse_time_duration("00:45") == timedelta(
            hours=0, minutes=45, seconds=0
        )

    def test_parse_time_duration_invalid(self) -> None:
        """Test parsing invalid time duration strings."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        assert analyzer._parse_time_duration("") == timedelta(0)
        assert analyzer._parse_time_duration("invalid") == timedelta(0)
        assert analyzer._parse_time_duration("1:2") == timedelta(0)  # Not HH:MM format
        assert analyzer._parse_time_duration("25:70") == timedelta(0)  # Invalid minutes
        assert analyzer._parse_time_duration("abc:def") == timedelta(0)  # Non-numeric
        assert analyzer._parse_time_duration("12:60") == timedelta(
            0
        )  # Minutes out of range
        assert analyzer._parse_time_duration("12:59:60") == timedelta(
            0
        )  # Seconds out of range

    def test_parse_time_duration_nan(self) -> None:
        """Test parsing NaN values."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test with float NaN which is more common in real data
        assert analyzer._parse_time_duration(math.nan) == timedelta(0)

    def test_parse_time_duration_float_input(self) -> None:
        """Test parsing float input."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Float values should return timedelta(0)
        assert analyzer._parse_time_duration(123.45) == timedelta(0)

    def test_format_duration(self) -> None:
        """Test formatting timedelta objects."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        assert (
            analyzer._format_duration(timedelta(hours=1, minutes=30, seconds=45))
            == "01:30"
        )
        assert analyzer._format_duration(timedelta(0)) == "00:00"

    def test_calculate_percentage(self) -> None:
        """Test percentage calculation against base time."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test basic percentage calculation
        duration = timedelta(hours=1)  # 1 hour
        base_time = "08:00"  # 8 hours
        percentage = analyzer._calculate_percentage(duration, base_time)
        assert percentage == 12.5  # 1/8 * 100 = 12.5%

        # Test 100% case
        duration = timedelta(hours=8)
        percentage = analyzer._calculate_percentage(duration, base_time)
        assert percentage == 100.0

        # Test zero base time (edge case)
        percentage = analyzer._calculate_percentage(duration, "00:00")
        assert percentage == 0.0

    def test_parse_tag_names(self) -> None:
        """Test parsing tag names from string."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Test empty string
        assert analyzer._parse_tag_names("") == []

        # Test single tag
        assert analyzer._parse_tag_names("work") == ["work"]

        # Test multiple tags separated by comma
        assert analyzer._parse_tag_names("work,personal") == ["work", "personal"]

        # Test tags with spaces
        assert analyzer._parse_tag_names("work, personal, health") == [
            "work",
            "personal",
            "health",
        ]

        # Test tags with extra spaces
        assert analyzer._parse_tag_names("  work  ,  personal  ") == [
            "work",
            "personal",
        ]

        # Test NaN input
        import pandas as pd

        assert analyzer._parse_tag_names(pd.NA) == []
        assert analyzer._parse_tag_names(math.nan) == []

    def test_base_time_without_seconds(self) -> None:
        """Test handling base time without seconds."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Create test results
        results = [
            {
                "project": "Work",
                "total_time": "04:00",
                "total_seconds": 14400,
                "task_count": "10",
            }
        ]

        # Test with base time without seconds (HH:MM format)
        results_with_percentage = analyzer._add_percentage_to_results(
            results, "08:00"
        )

        assert len(results_with_percentage) == 1
        assert results_with_percentage[0]["percentage"] == "50.0%"