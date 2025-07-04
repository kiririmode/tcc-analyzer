#!/usr/bin/env python3
"""Entry point for TCC Analyzer executable.

This module serves as the main entry point for PyInstaller builds.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Now we can import and run the main CLI
if __name__ == "__main__":
    from tcc_analyzer.cli import main

    main()
