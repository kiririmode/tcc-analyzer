"""Statistical analysis utilities for visualization data."""

import warnings
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats  # type: ignore[import]

from .base import DataProcessor


class StatisticalAnalyzer:
    """Statistical analysis for task data."""

    @staticmethod
    def _validate_and_extract_values(
        data: list[dict[str, Any]], value_key: str
    ) -> list[float]:
        """Extract and validate numeric values from data.

        Args:
            data: Analysis results data
            value_key: Key for values to extract

        Returns:
            List of numeric values, empty if invalid data

        """
        return DataProcessor.extract_numeric_values(data, value_key)

    @staticmethod
    def _ensure_valid_data(values: list[float]) -> bool:
        """Check if values are valid for statistical analysis.

        Args:
            values: List of numeric values

        Returns:
            True if values are valid, False otherwise

        """
        return bool(values)

    @staticmethod
    def _apply_statistical_analysis(
        data: list[dict[str, Any]],
        value_key: str,
        analysis_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Apply statistical analysis with common validation pattern.

        Args:
            data: Analysis results data
            value_key: Key for values to analyze
            analysis_func: Function to apply analysis
            *args: Additional positional arguments for analysis_func
            **kwargs: Additional keyword arguments for analysis_func

        Returns:
            Result of analysis_func or default empty result

        """
        values = StatisticalAnalyzer._validate_and_extract_values(data, value_key)

        # Check for return_tuple before validation to handle empty data case
        return_tuple = kwargs.pop("return_tuple", False)

        if not StatisticalAnalyzer._ensure_valid_data(values):
            # Return appropriate empty result based on analysis type
            if return_tuple:
                return [], {}
            return {}

        return analysis_func(values, *args, **kwargs)

    @staticmethod
    def _compute_descriptive_stats(values: list[float]) -> dict[str, float]:
        """Compute descriptive statistics from values."""
        return {
            "count": len(values),
            "mean": np.mean(values),
            "median": np.median(values),
            "mode": stats.mode(values, keepdims=True)[0][0],  # type: ignore[misc]
            "std": np.std(values),
            "var": np.var(values),
            "min": np.min(values),
            "max": np.max(values),
            "range": np.max(values) - np.min(values),
            "q1": np.percentile(values, 25),
            "q3": np.percentile(values, 75),
            "iqr": np.percentile(values, 75) - np.percentile(values, 25),
            "skewness": stats.skew(values),  # type: ignore[misc]
            "kurtosis": stats.kurtosis(values),  # type: ignore[misc]
        }

    @staticmethod
    def calculate_descriptive_stats(
        data: list[dict[str, Any]], value_key: str
    ) -> dict[str, float]:
        """Calculate descriptive statistics.

        Args:
            data: Analysis results data
            value_key: Key for values to analyze

        Returns:
            Dictionary of statistics

        """
        return StatisticalAnalyzer._apply_statistical_analysis(
            data, value_key, StatisticalAnalyzer._compute_descriptive_stats
        )

    @staticmethod
    def _compute_time_distribution(values: list[float]) -> dict[str, Any]:
        """Compute time distribution from values."""
        # Convert to hours for better interpretation
        hours = [v / 3600 for v in values]

        return {
            "total_hours": sum(hours),
            "avg_hours_per_task": np.mean(hours),
            "median_hours_per_task": np.median(hours),
            "std_hours": np.std(hours),
            "min_hours": np.min(hours),
            "max_hours": np.max(hours),
            "tasks_under_1h": sum(1 for h in hours if h < 1),
            "tasks_1_to_4h": sum(1 for h in hours if 1 <= h < 4),  # noqa: PLR2004
            "tasks_over_4h": sum(1 for h in hours if h >= 4),  # noqa: PLR2004
        }

    @staticmethod
    def calculate_time_distribution(
        data: list[dict[str, Any]], time_key: str
    ) -> dict[str, Any]:
        """Calculate time-based distribution statistics.

        Args:
            data: Analysis results data
            time_key: Key for time values

        Returns:
            Dictionary of time distribution statistics

        """
        return StatisticalAnalyzer._apply_statistical_analysis(
            data, time_key, StatisticalAnalyzer._compute_time_distribution
        )

    @staticmethod
    def calculate_category_distribution(
        data: list[dict[str, Any]], category_key: str, value_key: str
    ) -> dict[str, Any]:
        """Calculate category-based distribution.

        Args:
            data: Analysis results data
            category_key: Key for category values
            value_key: Key for values to aggregate

        Returns:
            Dictionary of category distribution

        """
        df = DataProcessor.create_dataframe(data)

        if category_key not in df.columns or value_key not in df.columns:
            return {}

        # Group by category and calculate stats
        grouped = df.groupby(category_key)[value_key].agg(  # type: ignore[misc]
            ["count", "sum", "mean", "std", "min", "max"]
        )

        # Calculate percentages
        total = df[value_key].sum()
        grouped["percentage"] = (grouped["sum"] / total) * 100

        return {
            "by_category": grouped.to_dict("index"),  # type: ignore[misc]
            "total_categories": len(grouped),
            "most_active_category": grouped["sum"].idxmax(),
            "least_active_category": grouped["sum"].idxmin(),
            "avg_tasks_per_category": grouped["count"].mean(),
        }

    @staticmethod
    def _compute_outliers(
        values: list[float], method: str = "iqr"
    ) -> tuple[list[int], dict[str, Any]]:
        """Compute outliers from values."""
        if method == "iqr":
            return StatisticalAnalyzer._detect_outliers_iqr(values)
        elif method == "zscore":
            return StatisticalAnalyzer._detect_outliers_zscore(values)
        else:
            raise ValueError(f"Unsupported outlier detection method: {method}")

    @staticmethod
    def detect_outliers(
        data: list[dict[str, Any]], value_key: str, method: str = "iqr"
    ) -> tuple[list[int], dict[str, Any]]:
        """Detect outliers in data.

        Args:
            data: Analysis results data
            value_key: Key for values to analyze
            method: Outlier detection method ('iqr' or 'zscore')

        Returns:
            Tuple of (outlier_indices, outlier_info)

        """
        return StatisticalAnalyzer._apply_statistical_analysis(
            data,
            value_key,
            StatisticalAnalyzer._compute_outliers,
            method,
            return_tuple=True,
        )

    @staticmethod
    def _detect_outliers_iqr(values: list[float]) -> tuple[list[int], dict[str, Any]]:
        """Detect outliers using IQR method."""
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_indices = [
            i for i, v in enumerate(values) if v < lower_bound or v > upper_bound
        ]

        outlier_info = {
            "method": "IQR",
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_count": len(outlier_indices),
            "outlier_percentage": (len(outlier_indices) / len(values)) * 100,
        }

        return outlier_indices, outlier_info

    @staticmethod
    def _detect_outliers_zscore(
        values: list[float],
    ) -> tuple[list[int], dict[str, Any]]:
        """Detect outliers using Z-score method."""
        z_scores = np.abs(stats.zscore(values))  # type: ignore[misc]
        threshold = 3

        outlier_indices = [i for i, z in enumerate(z_scores) if z > threshold]

        outlier_info = {
            "method": "Z-Score",
            "threshold": threshold,
            "outlier_count": len(outlier_indices),
            "outlier_percentage": (len(outlier_indices) / len(values)) * 100,
        }

        return outlier_indices, outlier_info

    @staticmethod
    def calculate_correlation_matrix(
        data: list[dict[str, Any]], numeric_keys: list[str] | None = None
    ) -> pd.DataFrame:
        """Calculate correlation matrix for numeric columns.

        Args:
            data: Analysis results data
            numeric_keys: Specific keys to include (None for all numeric)

        Returns:
            Correlation matrix as DataFrame

        """
        df = DataProcessor.create_dataframe(data)

        # Select numeric columns
        if numeric_keys:
            numeric_df = df[numeric_keys]
        else:
            numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.empty:
            return pd.DataFrame()

        return numeric_df.corr()

    @staticmethod
    def calculate_trend_analysis(
        data: list[dict[str, Any]], time_key: str, value_key: str
    ) -> dict[str, Any]:
        """Calculate trend analysis for time series data.

        Args:
            data: Analysis results data
            time_key: Key for time values
            value_key: Key for values to analyze

        Returns:
            Dictionary of trend analysis

        """
        df = DataProcessor.create_dataframe(data)

        if time_key not in df.columns or value_key not in df.columns:
            return {}

        # Convert time to datetime with warning suppression
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Could not infer format")
            df[time_key] = pd.to_datetime(df[time_key], errors="coerce")

        df = df.dropna(subset=[time_key, value_key])  # type: ignore[misc]

        if df.empty:
            return {}

        # Sort by time
        df = df.sort_values(time_key)  # type: ignore[misc]

        # Calculate linear trend
        x = np.arange(len(df))
        y = df[value_key].values  # type: ignore[misc]

        # Use tuple unpacking for scipy.stats.linregress
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)  # type: ignore[misc]

        # Calculate moving averages
        df["ma_7"] = df[value_key].rolling(window=7).mean()
        df["ma_30"] = df[value_key].rolling(window=30).mean()

        return {
            "trend_slope": slope,
            "trend_intercept": intercept,
            "correlation_coefficient": r_value,
            "p_value": p_value,
            "standard_error": std_err,
            "trend_direction": "increasing" if slope > 0 else "decreasing",  # type: ignore[misc]
            "trend_strength": abs(r_value),  # type: ignore[misc]
            "is_significant": p_value < 0.05,  # type: ignore[misc]  # noqa: PLR2004
            "moving_avg_7": df["ma_7"].iloc[-1]
            if not df["ma_7"].isna().all()
            else None,
            "moving_avg_30": df["ma_30"].iloc[-1]
            if not df["ma_30"].isna().all()
            else None,
        }
