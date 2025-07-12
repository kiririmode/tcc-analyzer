"""Data loading utilities for TaskChute Cloud CSV files."""

from pathlib import Path

import pandas as pd


class DataLoader:
    """Handles loading and parsing of TaskChute Cloud CSV files."""

    def __init__(self, csv_files: Path | list[Path]) -> None:
        """Initialize the data loader with CSV file(s)."""
        if isinstance(csv_files, Path):
            self.csv_files = [csv_files]
        else:
            self.csv_files = csv_files
        self._data: pd.DataFrame | None = None

    def load_data(self) -> pd.DataFrame:
        """Load and parse the CSV data."""
        if self._data is None:
            dataframes: list[pd.DataFrame] = []
            for csv_file in self.csv_files:
                df = self._read_csv_file(str(csv_file))
                dataframes.append(df)

            # Combine all dataframes
            if len(dataframes) == 1:
                self._data = dataframes[0]
            else:
                self._data = pd.concat(dataframes, ignore_index=True)

        return self._data

    def _read_csv_file(self, csv_file: str | Path) -> pd.DataFrame:
        """Read a single CSV file with fallback encoding."""
        try:
            # Read CSV with UTF-8 encoding, handling BOM
            df = pd.read_csv(csv_file, encoding="utf-8-sig")  # type: ignore
            return self._parse_csv_dates(df)
        except UnicodeDecodeError:
            # Fallback to Shift-JIS if UTF-8 fails
            df = pd.read_csv(csv_file, encoding="shift-jis")  # type: ignore
            return self._parse_csv_dates(df)

    def _parse_csv_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse date columns in CSV data."""
        if "開始日時" in df.columns and "終了日時" in df.columns:
            df["開始日時"] = pd.to_datetime(df["開始日時"])  # type: ignore
            df["終了日時"] = pd.to_datetime(df["終了日時"])  # type: ignore
        return df
