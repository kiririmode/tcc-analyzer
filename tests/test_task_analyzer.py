"""Tests for TaskAnalyzer."""

import pytest
import tempfile
import pandas as pd
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tcc_analyzer.analyzers.task_analyzer import TaskAnalyzer


class TestTaskAnalyzer:
    """Test class for TaskAnalyzer."""

    def test_parse_time_duration_valid(self):
        """Test parsing valid time duration strings."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        
        assert analyzer._parse_time_duration("01:30:45") == timedelta(hours=1, minutes=30, seconds=45)
        assert analyzer._parse_time_duration("00:00:00") == timedelta(0)
        assert analyzer._parse_time_duration("12:59:59") == timedelta(hours=12, minutes=59, seconds=59)

    def test_parse_time_duration_invalid(self):
        """Test parsing invalid time duration strings."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        
        assert analyzer._parse_time_duration("") == timedelta(0)
        assert analyzer._parse_time_duration("invalid") == timedelta(0)
        assert analyzer._parse_time_duration("1:2") == timedelta(0)

    def test_parse_time_duration_nan(self):
        """Test parsing NaN values."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        
        assert analyzer._parse_time_duration(pd.NA) == timedelta(0)

    def test_format_duration(self):
        """Test formatting timedelta objects."""
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        
        assert analyzer._format_duration(timedelta(hours=1, minutes=30, seconds=45)) == "01:30:45"
        assert analyzer._format_duration(timedelta(0)) == "00:00:00"
        assert analyzer._format_duration(timedelta(hours=24, minutes=0, seconds=1)) == "24:00:01"

    def test_analyze_by_project(self):
        """Test project analysis with sample data."""
        # Create sample CSV data
        csv_data = """タイムライン日付,タスクID,タスク名,プロジェクトID,プロジェクト名,モードID,モード名,タグID,タグ名,ルーチンID,ルーチン名,見積時間,実績時間,開始日時,終了日時,リンク,アイコン,カラー,お気に入り
2025-07-01,task1,Task 1,prj1,Project A,mode1,Mode 1,,,,,00:10:00,00:15:00,2025-07-01 09:00:00,2025-07-01 09:15:00,,,,0
2025-07-01,task2,Task 2,prj1,Project A,mode1,Mode 1,,,,,00:05:00,00:10:00,2025-07-01 09:15:00,2025-07-01 09:25:00,,,,0
2025-07-01,task3,Task 3,prj2,Project B,mode2,Mode 2,,,,,00:30:00,00:30:00,2025-07-01 10:00:00,2025-07-01 10:30:00,,,,0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_data)
            csv_path = Path(f.name)
        
        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_project()
            
            assert len(results) == 2
            
            # Check Project A (should have 00:25:00 total)
            project_a = next(r for r in results if r["project"] == "Project A")
            assert project_a["total_time"] == "00:25:00"
            assert project_a["task_count"] == "2"
            
            # Check Project B (should have 00:30:00 total)
            project_b = next(r for r in results if r["project"] == "Project B")
            assert project_b["total_time"] == "00:30:00"
            assert project_b["task_count"] == "1"
            
        finally:
            csv_path.unlink()

    def test_analyze_by_project_sort_by_name(self):
        """Test project analysis with name sorting."""
        csv_data = """タイムライン日付,タスクID,タスク名,プロジェクトID,プロジェクト名,モードID,モード名,タグID,タグ名,ルーチンID,ルーチン名,見積時間,実績時間,開始日時,終了日時,リンク,アイコン,カラー,お気に入り
2025-07-01,task1,Task 1,prj1,Z Project,mode1,Mode 1,,,,,00:10:00,00:15:00,2025-07-01 09:00:00,2025-07-01 09:15:00,,,,0
2025-07-01,task2,Task 2,prj2,A Project,mode2,Mode 2,,,,,00:05:00,00:10:00,2025-07-01 09:15:00,2025-07-01 09:25:00,,,,0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
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

    def test_display_json_output(self, capsys):
        """Test JSON output format."""
        results = [
            {"project": "Test Project", "total_time": "01:30:00", "task_count": "5", "total_seconds": 5400}
        ]
        
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results)
        
        captured = capsys.readouterr()
        assert "Test Project" in captured.out
        assert "01:30:00" in captured.out
        assert "5" in captured.out

    def test_display_csv_output(self, capsys):
        """Test CSV output format."""
        results = [
            {"project": "Test Project", "total_time": "01:30:00", "task_count": "5", "total_seconds": 5400}
        ]
        
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results)
        
        captured = capsys.readouterr()
        assert "Project,Total Time,Task Count" in captured.out
        assert "Test Project,01:30:00,5" in captured.out

    def test_analyze_by_mode(self):
        """Test mode analysis with sample data."""
        # Create sample CSV data
        csv_data = """タイムライン日付,タスクID,タスク名,プロジェクトID,プロジェクト名,モードID,モード名,タグID,タグ名,ルーチンID,ルーチン名,見積時間,実績時間,開始日時,終了日時,リンク,アイコン,カラー,お気に入り
2025-07-01,task1,Task 1,prj1,Project A,mode1,Focus Mode,,,,,00:10:00,00:15:00,2025-07-01 09:00:00,2025-07-01 09:15:00,,,,0
2025-07-01,task2,Task 2,prj1,Project A,mode1,Focus Mode,,,,,00:05:00,00:10:00,2025-07-01 09:15:00,2025-07-01 09:25:00,,,,0
2025-07-01,task3,Task 3,prj2,Project B,mode2,Meeting Mode,,,,,00:30:00,00:30:00,2025-07-01 10:00:00,2025-07-01 10:30:00,,,,0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_data)
            csv_path = Path(f.name)
        
        try:
            analyzer = TaskAnalyzer(csv_path)
            results = analyzer.analyze_by_mode()
            
            assert len(results) == 2
            
            # Check Focus Mode (should have 00:25:00 total)
            focus_mode = next(r for r in results if r["mode"] == "Focus Mode")
            assert focus_mode["total_time"] == "00:25:00"
            assert focus_mode["task_count"] == "2"
            
            # Check Meeting Mode (should have 00:30:00 total)
            meeting_mode = next(r for r in results if r["mode"] == "Meeting Mode")
            assert meeting_mode["total_time"] == "00:30:00"
            assert meeting_mode["task_count"] == "1"
            
        finally:
            csv_path.unlink()

    def test_analyze_by_mode_sort_by_name(self):
        """Test mode analysis with name sorting."""
        csv_data = """タイムライン日付,タスクID,タスク名,プロジェクトID,プロジェクト名,モードID,モード名,タグID,タグ名,ルーチンID,ルーチン名,見積時間,実績時間,開始日時,終了日時,リンク,アイコン,カラー,お気に入り
2025-07-01,task1,Task 1,prj1,Project A,mode1,Z Mode,,,,,00:10:00,00:15:00,2025-07-01 09:00:00,2025-07-01 09:15:00,,,,0
2025-07-01,task2,Task 2,prj2,Project B,mode2,A Mode,,,,,00:05:00,00:10:00,2025-07-01 09:15:00,2025-07-01 09:25:00,,,,0
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
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

    def test_display_table_mode(self):
        """Test table display for mode analysis."""
        results = [
            {"mode": "Test Mode", "total_time": "01:30:00", "task_count": "5", "total_seconds": 5400}
        ]
        
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        # This should not raise an exception
        analyzer.display_table(results, analysis_type="mode")

    def test_display_json_mode_output(self, capsys):
        """Test JSON output format for mode analysis."""
        results = [
            {"mode": "Test Mode", "total_time": "01:30:00", "task_count": "5", "total_seconds": 5400}
        ]
        
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_json(results, analysis_type="mode")
        
        captured = capsys.readouterr()
        assert "Test Mode" in captured.out
        assert "01:30:00" in captured.out
        assert "5" in captured.out

    def test_display_csv_mode_output(self, capsys):
        """Test CSV output format for mode analysis."""
        results = [
            {"mode": "Test Mode", "total_time": "01:30:00", "task_count": "5", "total_seconds": 5400}
        ]
        
        analyzer = TaskAnalyzer(Path("dummy.csv"))
        analyzer.display_csv(results, analysis_type="mode")
        
        captured = capsys.readouterr()
        assert "Mode,Total Time,Task Count" in captured.out
        assert "Test Mode,01:30:00,5" in captured.out