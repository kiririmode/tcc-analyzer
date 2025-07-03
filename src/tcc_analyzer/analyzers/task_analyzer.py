"""Task analyzer for TaskChute Cloud logs."""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.table import Table


class TaskAnalyzer:
    """Analyzer for TaskChute Cloud task logs."""
    
    def __init__(self, csv_file: Path) -> None:
        """Initialize the analyzer with a CSV file."""
        self.csv_file = csv_file
        self.console = Console()
        self._data: Optional[pd.DataFrame] = None
    
    def _load_data(self) -> pd.DataFrame:
        """Load and parse the CSV data."""
        if self._data is None:
            try:
                # Read CSV with UTF-8 encoding, handling BOM
                self._data = pd.read_csv(
                    self.csv_file,
                    encoding="utf-8-sig",
                    parse_dates=["開始日時", "終了日時"]
                )
            except UnicodeDecodeError:
                # Fallback to Shift-JIS if UTF-8 fails
                self._data = pd.read_csv(
                    self.csv_file,
                    encoding="shift-jis",
                    parse_dates=["開始日時", "終了日時"]
                )
        return self._data
    
    def _parse_time_duration(self, time_str: str) -> timedelta:
        """Parse time duration string (HH:MM:SS) to timedelta."""
        if pd.isna(time_str) or time_str == "":
            return timedelta(0)
        
        try:
            parts = time_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except (ValueError, IndexError):
            return timedelta(0)
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format timedelta as HH:MM:SS string."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def analyze_by_project(
        self, 
        sort_by: str = "time", 
        reverse: bool = False
    ) -> List[Dict[str, str]]:
        """Analyze tasks by project and return aggregated results."""
        data = self._load_data()
        
        # Group by project name and calculate total time
        project_times: Dict[str, timedelta] = {}
        project_task_counts: Dict[str, int] = {}
        
        for _, row in data.iterrows():
            project_name = row["プロジェクト名"]
            actual_time = row["実績時間"]
            
            # Skip rows without project name
            if pd.isna(project_name) or project_name == "":
                continue
            
            duration = self._parse_time_duration(actual_time)
            
            if project_name not in project_times:
                project_times[project_name] = timedelta(0)
                project_task_counts[project_name] = 0
            
            project_times[project_name] += duration
            project_task_counts[project_name] += 1
        
        # Convert to list of dictionaries
        results = []
        for project_name, total_time in project_times.items():
            results.append({
                "project": project_name,
                "total_time": self._format_duration(total_time),
                "total_seconds": int(total_time.total_seconds()),
                "task_count": str(project_task_counts[project_name])
            })
        
        # Sort results
        if sort_by == "time":
            results.sort(key=lambda x: x["total_seconds"], reverse=reverse)
        else:  # sort by name
            results.sort(key=lambda x: x["project"], reverse=reverse)
        
        return results
    
    def analyze_by_mode(
        self, 
        sort_by: str = "time", 
        reverse: bool = False
    ) -> List[Dict[str, str]]:
        """Analyze tasks by mode and return aggregated results."""
        data = self._load_data()
        
        # Group by mode name and calculate total time
        mode_times: Dict[str, timedelta] = {}
        mode_task_counts: Dict[str, int] = {}
        
        for _, row in data.iterrows():
            mode_name = row["モード名"]
            actual_time = row["実績時間"]
            
            # Skip rows without mode name
            if pd.isna(mode_name) or mode_name == "":
                continue
            
            duration = self._parse_time_duration(actual_time)
            
            if mode_name not in mode_times:
                mode_times[mode_name] = timedelta(0)
                mode_task_counts[mode_name] = 0
            
            mode_times[mode_name] += duration
            mode_task_counts[mode_name] += 1
        
        # Convert to list of dictionaries
        results = []
        for mode_name, total_time in mode_times.items():
            results.append({
                "mode": mode_name,
                "total_time": self._format_duration(total_time),
                "total_seconds": int(total_time.total_seconds()),
                "task_count": str(mode_task_counts[mode_name])
            })
        
        # Sort results
        if sort_by == "time":
            results.sort(key=lambda x: x["total_seconds"], reverse=reverse)
        else:  # sort by name
            results.sort(key=lambda x: x["mode"], reverse=reverse)
        
        return results
    
    def display_table(self, results: List[Dict[str, str]], analysis_type: str = "project") -> None:
        """Display results as a rich table."""
        if analysis_type == "mode":
            table = Table(title="TaskChute Cloud - Mode Time Analysis")
            table.add_column("Mode", style="cyan", no_wrap=True)
            column_key = "mode"
        else:
            table = Table(title="TaskChute Cloud - Project Time Analysis")
            table.add_column("Project", style="cyan", no_wrap=True)
            column_key = "project"
        
        table.add_column("Total Time", style="green")
        table.add_column("Task Count", style="yellow")
        
        for result in results:
            table.add_row(
                result[column_key],
                result["total_time"],
                result["task_count"]
            )
        
        self.console.print(table)
    
    def display_json(self, results: List[Dict[str, str]], analysis_type: str = "project") -> None:
        """Display results as JSON."""
        # Remove internal fields for JSON output
        json_results = []
        for result in results:
            if analysis_type == "mode":
                json_results.append({
                    "mode": result["mode"],
                    "total_time": result["total_time"],
                    "task_count": int(result["task_count"])
                })
            else:
                json_results.append({
                    "project": result["project"],
                    "total_time": result["total_time"],
                    "task_count": int(result["task_count"])
                })
        
        print(json.dumps(json_results, ensure_ascii=False, indent=2))
    
    def display_csv(self, results: List[Dict[str, str]], analysis_type: str = "project") -> None:
        """Display results as CSV."""
        if analysis_type == "mode":
            print("Mode,Total Time,Task Count")
            for result in results:
                print(f"{result['mode']},{result['total_time']},{result['task_count']}")
        else:
            print("Project,Total Time,Task Count")
            for result in results:
                print(f"{result['project']},{result['total_time']},{result['task_count']}")