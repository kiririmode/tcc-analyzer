"""Tests for TaskAnalyzer core analysis functionality."""

import tempfile
from pathlib import Path
from typing import Any

from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzerCore:
    """Test class for TaskAnalyzer core analysis functionality."""

    def _create_csv_file(self, csv_data: str) -> Path:
        """Create a temporary CSV file with given data."""
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        )
        temp_file.write(csv_data)
        temp_file.close()
        return Path(temp_file.name)

    def _cleanup_csv_file(self, csv_path: Path) -> None:
        """Clean up temporary CSV file."""
        csv_path.unlink()

    def _assert_result_count(
        self, results: list[dict[str, str]], expected_count: int
    ) -> None:
        """Assert the number of results matches expected count."""
        assert len(results) == expected_count

    def _assert_project_result(
        self,
        results: list[dict[str, str]],
        project: str,
        expected_time: str,
        expected_count: str,
    ) -> None:
        """Assert a project result matches expected values."""
        project_result = next(r for r in results if r["project"] == project)
        assert project_result["total_time"] == expected_time
        assert project_result["task_count"] == expected_count

    def _assert_mode_result(
        self,
        results: list[dict[str, str]],
        mode: str,
        expected_time: str,
        expected_count: str,
    ) -> None:
        """Assert a mode result matches expected values."""
        mode_result = next(r for r in results if r["mode"] == mode)
        assert mode_result["total_time"] == expected_time
        assert mode_result["task_count"] == expected_count

    def _assert_sorted_by_field(
        self, results: list[dict[str, str]], field: str, expected_order: list[str]
    ) -> None:
        """Assert results are sorted by field in expected order."""
        actual_order = [result[field] for result in results]
        assert actual_order == expected_order

    def _run_analysis_test(
        self, csv_data: str, analysis_method: str, expected_results: dict[str, Any]
    ) -> None:
        """Run a generic analysis test with cleanup."""
        csv_path = self._create_csv_file(csv_data)
        try:
            analyzer = TaskAnalyzer(csv_path)
            results = getattr(analyzer, analysis_method)()

            self._assert_result_count(results, expected_results["count"])

            for expected in expected_results.get("assertions", []):
                if "project" in expected:
                    self._assert_project_result(
                        results,
                        expected["project"],
                        expected["time"],
                        expected["task_count"],
                    )
                elif "mode" in expected:
                    self._assert_mode_result(
                        results,
                        expected["mode"],
                        expected["time"],
                        expected["task_count"],
                    )
        finally:
            self._cleanup_csv_file(csv_path)

    def _run_sorting_test(
        self,
        csv_data: str,
        analysis_method: str,
        sort_by: str,
        field: str,
        expected_order: list[str],
    ) -> None:
        """Run a generic sorting test with cleanup."""
        csv_path = self._create_csv_file(csv_data)
        try:
            analyzer = TaskAnalyzer(csv_path)
            results = getattr(analyzer, analysis_method)(sort_by=sort_by)
            self._assert_sorted_by_field(results, field, expected_order)
        finally:
            self._cleanup_csv_file(csv_path)

    def test_basic_analysis_functionality(self) -> None:
        """Test basic analysis functionality for projects and modes."""

        # Test project analysis
        project_csv_data = (
            "プロジェクト名,モード名,実績時間,開始日時,終了日時\n"
            "Project A,Mode 1,00:15,2025-07-01 09:00,2025-07-01 09:15\n"
            "Project A,Mode 1,00:10,2025-07-01 09:15,2025-07-01 09:25\n"
            "Project B,Mode 2,00:30,2025-07-01 10:00,2025-07-01 10:30\n"
        )

        project_expected_results = {
            "count": 2,
            "assertions": [
                {"project": "Project A", "time": "00:25", "task_count": "2"},
                {"project": "Project B", "time": "00:30", "task_count": "1"},
            ],
        }

        self._run_analysis_test(
            project_csv_data, "analyze_by_project", project_expected_results
        )

        # Test mode analysis
        mode_csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Focus Mode,00:15\n"
            "Project A,Focus Mode,00:10\n"
            "Project B,Meeting Mode,00:30\n"
        )

        mode_expected_results = {
            "count": 2,
            "assertions": [
                {"mode": "Focus Mode", "time": "00:25", "task_count": "2"},
                {"mode": "Meeting Mode", "time": "00:30", "task_count": "1"},
            ],
        }

        self._run_analysis_test(mode_csv_data, "analyze_by_mode", mode_expected_results)

    def _assert_project_mode_result(
        self,
        results: list[dict[str, str]],
        project: str,
        mode: str,
        expected_time: str,
        expected_count: str,
    ) -> None:
        """Assert that a project-mode result matches expected values."""
        result = next(
            r for r in results if r["project"] == project and r["mode"] == mode
        )
        assert result["total_time"] == expected_time
        assert result["task_count"] == expected_count

    def test_analyze_by_project_mode(self) -> None:
        """Test project-mode analysis with sample data."""
        csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Mode 1,00:15\n"
            "Project A,Mode 2,00:10\n"
            "Project B,Mode 1,00:30\n"
            "Project A,Mode 1,00:05\n"
        )

        csv_path = self._create_csv_file(csv_data)
        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode()

            self._assert_result_count(results, 3)

            self._assert_project_mode_result(
                results, "Project A", "Mode 1", "00:20", "2"
            )
            self._assert_project_mode_result(
                results, "Project A", "Mode 2", "00:10", "1"
            )
            self._assert_project_mode_result(
                results, "Project B", "Mode 1", "00:30", "1"
            )
        finally:
            self._cleanup_csv_file(csv_path)

    def test_comprehensive_sorting_functionality(self) -> None:
        """Test comprehensive sorting functionality for all analysis methods."""
        basic_csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Z Mode,00:15\n"
            "A Project,A Mode,00:10\n"
        )

        project_mode_csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Z Project,Mode 1,00:15\n"
            "A Project,Mode 1,00:10\n"
            "B Project,Mode 2,00:05\n"
        )

        mode_sorting_csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            "Project A,Z Mode,00:15\n"
            "Project B,A Mode,00:10\n"
            "Project C,B Mode,00:05\n"
        )

        # Test basic project and mode sorting
        test_cases = [
            (
                basic_csv_data,
                "analyze_by_project",
                "project",
                "project",
                ["A Project", "Z Project"],
            ),
            (
                basic_csv_data,
                "analyze_by_project",
                "name",
                "project",
                ["A Project", "Z Project"],
            ),
            (basic_csv_data, "analyze_by_mode", "mode", "mode", ["A Mode", "Z Mode"]),
            (basic_csv_data, "analyze_by_mode", "name", "mode", ["A Mode", "Z Mode"]),
            (
                project_mode_csv_data,
                "analyze_by_project_mode",
                "project",
                "project",
                ["A Project", "B Project", "Z Project"],
            ),
            (
                mode_sorting_csv_data,
                "analyze_by_project_mode",
                "mode",
                "mode",
                ["A Mode", "B Mode", "Z Mode"],
            ),
            (
                project_mode_csv_data,
                "analyze_by_project_mode",
                "name",
                "project",
                ["A Project", "B Project", "Z Project"],
            ),
        ]

        for csv_data, method, sort_by, field, expected_order in test_cases:
            self._run_sorting_test(csv_data, method, sort_by, field, expected_order)

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

        csv_path1 = self._create_csv_file(csv_data1)
        csv_path2 = self._create_csv_file(csv_data2)

        try:
            analyzer = TaskAnalyzer([csv_path1, csv_path2])
            results = analyzer.analyze_by_project(sort_by="project")

            self._assert_result_count(results, 3)

            project_a = next((r for r in results if r["project"] == "Project A"), None)
            assert project_a is not None
            assert project_a["total_seconds"] == 9000

        finally:
            self._cleanup_csv_file(csv_path1)
            self._cleanup_csv_file(csv_path2)

    def test_single_file_as_path(self) -> None:
        """Test initializing TaskAnalyzer with a single Path object."""
        csv_data = "プロジェクト名,モード名,実績時間\nProject A,Mode 1,01:30\n"

        csv_path = self._create_csv_file(csv_data)
        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project(sort_by="project")

            self._assert_result_count(results, 1)
            assert results[0]["project"] == "Project A"
        finally:
            self._cleanup_csv_file(csv_path)

    def test_edge_cases_and_invalid_data(self) -> None:
        """Test edge cases and invalid data handling."""
        # Test empty results
        empty_csv_data = "プロジェクト名,モード名,実績時間\n"
        csv_path = self._create_csv_file(empty_csv_data)
        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode()
            assert results == []
        finally:
            self._cleanup_csv_file(csv_path)

        # Test invalid data handling
        invalid_csv_data = (
            "プロジェクト名,モード名,実績時間\n"
            ",Mode 1,00:15\n"
            "Project A,,00:10\n"
            "Project B,Mode 2,invalid_time\n"
        )
        csv_path = self._create_csv_file(invalid_csv_data)
        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project_mode()
            assert isinstance(results, list)
        finally:
            self._cleanup_csv_file(csv_path)

    def test_encoding_fallback_to_shift_jis(self) -> None:
        """Test encoding fallback when UTF-8 fails."""
        csv_data = "プロジェクト名,モード名,実績時間\nテスト,モード,01:30\n"

        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="shift-jis"
        )
        temp_file.write(csv_data)
        temp_file.close()
        csv_path = Path(temp_file.name)

        try:
            analyzer = TaskAnalyzer(csv_path)
            data = analyzer._load_data()

            assert not data.empty
            assert "プロジェクト名" in data.columns
        finally:
            self._cleanup_csv_file(csv_path)

    def test_date_parsing_with_datetime_columns(self) -> None:
        """Test data loading with datetime columns."""
        csv_data = (
            "プロジェクト名,モード名,実績時間,開始日時,終了日時\n"
            "Project A,Mode 1,01:30,2025-07-01 09:00,2025-07-01 10:30\n"
        )

        csv_path = self._create_csv_file(csv_data)
        try:
            analyzer = TaskAnalyzer(csv_path)
            data = analyzer._load_data()

            assert not data.empty
            assert "開始日時" in data.columns
            assert "終了日時" in data.columns
        finally:
            self._cleanup_csv_file(csv_path)
