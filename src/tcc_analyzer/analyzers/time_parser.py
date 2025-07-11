"""Time parsing and validation utilities for TaskChute Cloud logs."""

from datetime import timedelta

import pandas as pd

from .constants import (
    MAX_MINUTES_SECONDS,
    MAX_TIME_PARTS,
    MIN_TIME_PARTS,
    REQUIRED_DIGIT_LENGTH,
)


class TimeParser:
    """Parser for time duration strings and time-related calculations."""

    @staticmethod
    def parse_time_duration(time_str: str | float) -> timedelta:
        """Parse time duration string (HH:MM or HH:MM:SS) to timedelta."""
        if pd.isna(time_str) or time_str == "":  # type: ignore
            return timedelta(0)

        if not isinstance(time_str, str):
            return timedelta(0)

        return TimeParser._parse_time_string(time_str)

    @staticmethod
    def _parse_time_string(time_str: str) -> timedelta:
        """Parse time string and return timedelta."""
        try:
            parts = time_str.split(":")

            if not TimeParser._is_valid_time_format(parts):
                return timedelta(0)

            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2]) if len(parts) >= MAX_TIME_PARTS else 0

            if not TimeParser._is_valid_time_range(minutes, seconds):
                return timedelta(0)

            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except (ValueError, IndexError):
            return timedelta(0)

    @staticmethod
    def _is_valid_time_format(parts: list[str]) -> bool:
        """Check if time parts have valid format."""
        if len(parts) < MIN_TIME_PARTS or len(parts) > MAX_TIME_PARTS:
            return False
        if (
            len(parts[0]) != REQUIRED_DIGIT_LENGTH
            or len(parts[1]) != REQUIRED_DIGIT_LENGTH
        ):
            return False
        if len(parts) == MAX_TIME_PARTS and len(parts[2]) != REQUIRED_DIGIT_LENGTH:
            return False
        return True

    @staticmethod
    def _is_valid_time_range(minutes: int, seconds: int) -> bool:
        """Check if time values are within valid range."""
        return minutes < MAX_MINUTES_SECONDS and seconds < MAX_MINUTES_SECONDS

    @staticmethod
    def format_duration(duration: timedelta) -> str:
        """Format timedelta as HH:MM string."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"

    @staticmethod
    def calculate_percentage(duration: timedelta, base_time_str: str) -> float:
        """Calculate percentage of duration against base time."""
        base_duration = TimeParser.parse_time_duration(base_time_str)
        if base_duration.total_seconds() == 0:
            return 0.0
        return (duration.total_seconds() / base_duration.total_seconds()) * 100
