"""Tests for TaskAnalyzer filtering functionality."""

import tempfile
from pathlib import Path

import pandas as pd
from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzerFiltering:
    """Test class for TaskAnalyzer filtering functionality."""

    def test_filter_by_tag(self) -> None:
        """Test filtering data by tag."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Create test data with tags
        data = pd.DataFrame(
            {
                "プロジェクト名": ["Project A", "Project B", "Project C"],
                "モード名": ["Mode 1", "Mode 2", "Mode 3"],
                "実績時間": ["01:30", "02:00", "00:45"],
                "タグ名": ["work,urgent", "personal", "work,health"],
            }
        )

        # Test filtering by 'work' tag
        filtered = analyzer._filter_by_tag(data, "work")
        assert len(filtered) == 2  # Project A and Project C have 'work' tag

        # Test filtering by 'personal' tag
        filtered = analyzer._filter_by_tag(data, "personal")
        assert len(filtered) == 1  # Only Project B has 'personal' tag

        # Test filtering by non-existent tag
        filtered = analyzer._filter_by_tag(data, "nonexistent")
        assert len(filtered) == 0

    def test_set_tag_filter(self) -> None:
        """Test setting tag filter."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))

        # Initially no filter
        assert analyzer._tag_filter is None

        # Set filter
        analyzer.set_tag_filter("work")
        assert analyzer._tag_filter == "work"

        # Change filter
        analyzer.set_tag_filter("personal")
        assert analyzer._tag_filter == "personal"

    def test_tag_filter_integration(self) -> None:
        """Test tag filter integration with analysis."""
        # Create sample CSV data with tags
        csv_data = (
            "プロジェクト名,モード名,実績時間,タグ名\n"
            "Work Project,Focus Mode,01:30,\"work,urgent\"\n"
            "Personal Project,Reading Mode,00:45,\"personal,learning\"\n"
            "Health Project,Exercise Mode,01:00,\"health,fitness\"\n"
            "Work Project,Meeting Mode,00:30,\"work,meetings\"\n"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_data)
            csv_path = Path(f.name)

        try:
            analyzer = TaskAnalyzer(csv_path)

            # Test without filter - should get all projects
            results = analyzer.analyze_by_project()
            assert len(results) == 3  # Work, Personal, Health projects

            # Test with 'work' filter - should only get work-related tasks
            analyzer.set_tag_filter("work")
            results = analyzer.analyze_by_project()
            assert len(results) == 1  # Only Work Project

            work_project = results[0]
            assert work_project["project"] == "Work Project"
            assert work_project["total_time"] == "02:00"  # 01:30 + 00:30
            assert work_project["task_count"] == "2"

            # Test with 'personal' filter
            analyzer.set_tag_filter("personal")
            results = analyzer.analyze_by_project()
            assert len(results) == 1  # Only Personal Project

            personal_project = results[0]
            assert personal_project["project"] == "Personal Project"
            assert personal_project["total_time"] == "00:45"
            assert personal_project["task_count"] == "1"

            # Test with 'health' filter
            analyzer.set_tag_filter("health")
            results = analyzer.analyze_by_project()
            assert len(results) == 1  # Only Health Project

            health_project = results[0]
            assert health_project["project"] == "Health Project"
            assert health_project["total_time"] == "01:00"
            assert health_project["task_count"] == "1"

        finally:
            csv_path.unlink()