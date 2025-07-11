#!/usr/bin/env python3
"""Cross-platform executable builder for TCC Analyzer.

This script builds executables for different platforms using PyInstaller.
Note: Cross-compilation limitations - you can only build for the platform
you're running on.

Usage:
    python scripts/build-executable.py [--platform TARGET_PLATFORM]

    TARGET_PLATFORM options:
    - auto (default): Detect current platform and build for it
    - linux: Build for Linux
    - windows: Build for Windows
    - macos: Build for macOS
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_current_platform() -> str:
    """Detect the current platform."""
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    else:
        raise ValueError(f"Unsupported platform: {system}")


def get_executable_name(target_platform: str) -> str:
    """Get the appropriate executable name for the target platform."""
    if target_platform == "windows":
        return "tcc-analyzer.exe"
    else:
        return "tcc-analyzer"


def _clean_previous_builds(dist_dir: Path) -> None:
    """Clean previous build artifacts."""
    if dist_dir.exists():
        print("Cleaning previous builds...")
        shutil.rmtree(dist_dir)


def _run_pyinstaller(spec_file: Path, project_root: Path) -> None:
    """Run PyInstaller with the given spec file."""
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file),
    ]

    print(f"Running: {' '.join(cmd)}")

    subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, check=True)  # noqa: S603


def _test_executable(executable_path: Path) -> bool:
    """Test the built executable for basic functionality."""
    print("Testing executable...")
    # Increase timeout for Windows executables which may take longer to start
    timeout_seconds = 30
    test_result = subprocess.run(  # noqa: S603
        [str(executable_path), "--help"],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return test_result.returncode == 0


def _print_success_message(
    executable_name: str, target_platform: str, executable_path: Path, size_mb: float
) -> None:
    """Print success message with build details."""
    print("Executable test passed!")
    print("\n" + "=" * 50)
    print(f"SUCCESS: {executable_name} built for {target_platform}")
    print(f"Location: {executable_path}")
    print(f"Size: {size_mb:.1f} MB")
    print("=" * 50)


def build_executable(target_platform: str) -> None:
    """Build executable for the specified platform."""
    project_root = Path(__file__).parent.parent
    spec_file = project_root / "build.spec"
    dist_dir = project_root / "dist"

    print(f"Building executable for {target_platform}...")
    print(f"Project root: {project_root}")
    print(f"Spec file: {spec_file}")

    # Verify we're on the right platform for building
    current_platform = get_current_platform()
    if target_platform not in ("auto", current_platform):
        print(
            f"WARNING: Cannot cross-compile from {current_platform} "
            f"to {target_platform}"
        )
        print(f"Building for current platform ({current_platform}) instead")
        target_platform = current_platform

    if target_platform == "auto":
        target_platform = current_platform

    _clean_previous_builds(dist_dir)

    try:
        _run_pyinstaller(spec_file, project_root)
        print("Build completed successfully!")

        # Find the built executable
        executable_name = get_executable_name(target_platform)
        executable_path = dist_dir / executable_name

        if executable_path.exists():
            size_mb = executable_path.stat().st_size / (1024 * 1024)
            print(f"Executable created: {executable_path}")
            print(f"Size: {size_mb:.1f} MB")

            if _test_executable(executable_path):
                _print_success_message(
                    executable_name, target_platform, executable_path, size_mb
                )
            else:
                print("ERROR: Executable test failed!")
        else:
            print(
                f"ERROR: Executable not found at expected location: {executable_path}"
            )

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Build failed with return code {e.returncode}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        sys.exit(1)


def main() -> None:
    """Run the main executable builder."""
    parser = argparse.ArgumentParser(
        description="Build TCC Analyzer executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Platform Support:
  Linux:   Native builds supported
  Windows: Native builds supported
  macOS:   Native builds supported

Note: Cross-compilation is not supported. You must build on the target platform.

Examples:
  python scripts/build-executable.py                    # Auto-detect platform
  python scripts/build-executable.py --platform linux  # Build for Linux
  python scripts/build-executable.py --platform windows # Build for Windows
  python scripts/build-executable.py --platform macos   # Build for macOS
        """,
    )

    parser.add_argument(
        "--platform",
        choices=["auto", "linux", "windows", "macos"],
        default="auto",
        help="Target platform (default: auto-detect)",
    )

    args = parser.parse_args()

    print("TCC Analyzer Executable Builder")
    print("=" * 40)

    build_executable(args.platform)


if __name__ == "__main__":
    main()
