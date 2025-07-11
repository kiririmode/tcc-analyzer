"""Tests for TaskAnalyzer core analysis functionality."""

import tempfile
from pathlib import Path

from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzerCore:
    """Test class for TaskAnalyzer core analysis functionality."""

    def test_analyze_by_project(self) -> None:
        """Test project analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間,開始日時,終了日時\n"
            "Project A,Mode 1,00:15,2025-07-01 09:00,2025-07-01 09:15\n"
            "Project A,Mode 1,00:10,2025-07-01 09:15,2025-07-01 09:25\n"
            "Project B,Mode 2,00:30,2025-07-01 10:00,2025-07-01 10:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()

            assert len(results) == 2

            # Check Project A (should have 00:25 total)
            project_a = next(r for r in results if r["project"] == "Project A")
            assert project_a["total_time"] == "00:25"
            assert project_a["task_count"] == "2"

            # Check Project B (should have 00:30 total)
            project_b = next(r for r in results if r["project"] == "Project B")
            assert project_b["total_time"] == "00:30"
            assert project_b["task_count"] == "1"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_sort_by_project(self) -> None:
        """Test project analysis with project name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Mode 1,00:15\n"
            "A Project,Mode 2,00:10\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project(sort_by="project")

            assert len(results) == 2
            assert results[0]["project"] == "A Project"
            assert results[1]["project"] == "Z Project"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_sort_by_name(self) -> None:
        """Test project analysis with legacy name sorting (backward compatibility)."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Mode 1,00:15\n"
            "A Project,Mode 2,00:10\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project(sort_by="name")

            assert len(results) == 2
            assert results[0]["project"] == "A Project"
            assert results[1]["project"] == "Z Project"

        finally:
            csv_path.unlink()

    def test_analyze_by_mode(self) -> None:
        """Test mode analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Focus Mode,00:15\n"
            "Project A,Focus Mode,00:10\n"
            "Project B,Meeting Mode,00:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode()

            assert len(results) == 2

            # Check Focus Mode (should have 00:25 total)
            focus_mode = next(r for r in results if r["mode"] == "Focus Mode")
            assert focus_mode["total_time"] == "00:25"
            assert focus_mode["task_count"] == "2"

            # Check Meeting Mode (should have 00:30 total)
            meeting_mode = next(r for r in results if r["mode"] == "Meeting Mode")
            assert meeting_mode["total_time"] == "00:30"
            assert meeting_mode["task_count"] == "1"

        finally:
            csv_path.unlink()

    def test_analyze_by_mode_sort_by_mode(self) -> None:
        """Test mode analysis with mode name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Z Mode,00:15\n"
            "Project B,A Mode,00:10\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode(sort_by="mode")

            assert len(results) == 2
            assert results[0]["mode"] == "A Mode"
            assert results[1]["mode"] == "Z Mode"

        finally:
            csv_path.unlink()

    def test_analyze_by_mode_sort_by_name(self) -> None:
        """Test mode analysis with legacy name sorting (backward compatibility)."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Z Mode,00:15\n"
            "Project B,A Mode,00:10\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode(sort_by="name")

            assert len(results) == 2
            assert results[0]["mode"] == "A Mode"
            assert results[1]["mode"] == "Z Mode"

        finally:
            csv_path.unlink()

    def _find_project_mode_result(
        self, results: list[dict[str, str]], project: str, mode: str
    ) -> dict[str, str]:
        """Find a specific project-mode result from the analysis results."""
        return next(r for r in results if r["project"] == project and r["mode"] == mode)

    def _assert_project_mode_result(
        self,
        results: list[dict[str, str]],
        project: str,
        mode: str,
        expected_time: str,
        expected_count: str,
    ) -> None:
        """Assert that a project-mode result matches expected values."""
        result = self._find_project_mode_result(results, project, mode)
        assert result["total_time"] == expected_time
        assert result["task_count"] == expected_count

    def test_analyze_by_project_mode(self) -> None:
        """Test project-mode analysis with sample data."""
        # Create sample CSV data
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Mode 1,00:15\n"
            "Project A,Mode 2,00:10\n"
            "Project B,Mode 1,00:30\n"
            "Project A,Mode 1,00:05\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode()

            assert len(results) == 3

            # Check Project A - Mode 1 (should have 00:20 total)
            self._assert_project_mode_result(
                results, "Project A", "Mode 1", "00:20", "2"
            )

            # Check Project A - Mode 2 (should have 00:10 total)
            self._assert_project_mode_result(
                results, "Project A", "Mode 2", "00:10", "1"
            )

            # Check Project B - Mode 1 (should have 00:30 total)
            self._assert_project_mode_result(
                results, "Project B", "Mode 1", "00:30", "1"
            )

        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_sort_by_project(self) -> None:
        """Test project-mode analysis with project sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Mode 1,00:15\n"
            "A Project,Mode 1,00:10\n"
            "B Project,Mode 2,00:05\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode(sort_by="project")

            assert len(results) == 3
            assert results[0]["project"] == "A Project"
            assert results[1]["project"] == "B Project"
            assert results[2]["project"] == "Z Project"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_sort_by_mode(self) -> None:
        """Test project-mode analysis with mode sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Z Mode,00:15\n"
            "Project B,A Mode,00:10\n"
            "Project C,B Mode,00:05\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode(sort_by="mode")

            assert len(results) == 3
            assert results[0]["mode"] == "A Mode"
            assert results[1]["mode"] == "B Mode"
            assert results[2]["mode"] == "Z Mode"

        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_sort_by_name(self) -> None:
        """Test project-mode analysis with legacy name sorting."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Mode 1,00:15\n"
            "A Project,Mode 1,00:10\n"
            "B Project,Mode 2,00:05\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode(sort_by="name")

            assert len(results) == 3
            assert results[0]["project"] == "A Project"
            assert results[1]["project"] == "B Project"
            assert results[2]["project"] == "Z Project"

        finally:
            csv_path.unlink()

    def test_multiple_files_initialization(self) -> None:
        """Test initializing TaskAnalyzer with multiple CSV files."""
        csv_data1 = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Mode 1,01:30\n"
            "Project B,Mode 2,02:00\n"
        )
        csv_data2 = (
            "プロジェクト名,モード名,実績時間\n"
            "Project C,Mode 3,00:45\n"
            "Project A,Mode 1,01:00\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f1:
            f1.write(csv_data1)
            csv_path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f2:
            f2.write(csv_data2)
            csv_path2 = Path(f2.name)

        try:
            # Test with list of files
            analyzer = TaskAnalyzer([csv_path1, csv_path2])
            results = analyzer.analyze_by_project(sort_by="project")

            # Should have 3 projects (A, B, C)
            assert len(results) == 3

            # Project A should have combined time from both files
            project_a = next((r for r in results if r["project"] == "Project A"), None)
            assert project_a is not None
            assert project_a["total_seconds"] == 9000  # 1:30:00 + 1:00:00 = 2:30:00

        finally:
            csv_path1.unlink()
            csv_path2.unlink()

    def test_single_file_as_path(self) -> None:
        """Test initializing TaskAnalyzer with a single Path object."""
        csv_data = "プロジェクト名,モード名,実績時間\nProject A,Mode 1,01:30\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project(sort_by="project")

            assert len(results) == 1
            assert results[0]["project"] == "Project A"

        finally:
            csv_path.unlink()

    def test_analyze_by_mode_empty_results(self) -> None:
        """Test mode analysis with empty results."""
        csv_data = "プロジェクト名,モード名,実績時間\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode()

            assert results == []

        finally:
            csv_path.unlink()

    def test_analyze_by_project_mode_invalid_data(self) -> None:
        """Test project-mode analysis with invalid data."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            ",Mode 1,00:15\n"  # Empty project name
            "Project A,,00:10\n"  # Empty mode name
            "Project B,Mode 2,invalid_time\n"  # Invalid time format
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode()

            # Should handle invalid data gracefully
            # Results may vary based on data loading implementation
            assert isinstance(results, list)

        finally:
            csv_path.unlink()

    def test_encoding_fallback_to_shift_jis(self) -> None:
        """Test encoding fallback when UTF-8 fails."""
        # Create a CSV with Shift-JIS encoding
        csv_data = "プロジェクト名,モード名,実績時間\nテスト,モード,01:30\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="shift-jis"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            data = analyzer._load_data()

            # Should successfully load data with Shift-JIS fallback
            assert not data.empty
            assert "プロジェクト名" in data.columns

        finally:
            csv_path.unlink()

    def test_date_parsing_with_datetime_columns(self) -> None:
        """Test data loading with datetime columns."""
        csv_data = (
            "プロジェクト名,モード名,実績時間,開始日時,終了日時\n"
            "Project A,Mode 1,01:30,2025-07-01 09:00,2025-07-01 10:30\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            data = analyzer._load_data()

            # Should have parsed datetime columns
            assert not data.empty
            assert "開始日時" in data.columns
            assert "終了日時" in data.columns

        finally:
            csv_path.unlink()
