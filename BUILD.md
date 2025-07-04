# Building Executables

This document describes how to build standalone executables for TCC Analyzer using PyInstaller.

## Overview

TCC Analyzer can be built into standalone executables for:
- 🐧 **Linux** (x86_64, ARM64)
- 🪟 **Windows** (x86_64)
- 🍎 **macOS** (Intel, Apple Silicon)

## Quick Start

### Prerequisites

1. **Python 3.10+** installed on your system
2. **uv** package manager (or pip as fallback)
3. **PyInstaller** (automatically installed via dev dependencies)

### Build Command

```bash
# Build for current platform (auto-detect)
uv run python scripts/build-executable.py

# Build for specific platform
uv run python scripts/build-executable.py --platform linux
uv run python scripts/build-executable.py --platform windows
uv run python scripts/build-executable.py --platform macos
```

### Output

The executable will be created in the `dist/` directory:
- **Linux/macOS**: `dist/tcc-analyzer`
- **Windows**: `dist/tcc-analyzer.exe`

## Platform-Specific Notes

### Linux
- ✅ Native builds supported
- 📦 Executable size: ~37MB
- 🔧 Dependencies: glibc 2.17+ (most modern distributions)
- 🚀 Portable: Can run on other Linux systems with compatible glibc

### Windows
- ✅ Native builds supported on Windows
- 📦 Executable size: ~40MB (estimated)
- 🔧 Dependencies: None (fully self-contained)
- 🚀 Portable: Runs on Windows 10+ without Python installation

### macOS
- ✅ Native builds supported on macOS
- 📦 Executable size: ~38MB (estimated)
- 🔧 Dependencies: macOS 10.15+ (Catalina)
- 🚀 Portable: Runs on compatible macOS versions
- ⚠️ **Code signing**: Required for distribution (see below)

## Cross-Compilation Limitations

**Important**: PyInstaller cannot cross-compile. You must build on the target platform:

- Build **Linux** executables → on Linux systems
- Build **Windows** executables → on Windows systems
- Build **macOS** executables → on macOS systems

### GitHub Actions (Recommended)

For automated builds across all platforms, use GitHub Actions:

```yaml
# .github/workflows/build-executables.yml
name: Build Executables
on: [push, pull_request]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}

    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install uv
      run: pip install uv

    - name: Install dependencies
      run: uv sync --dev

    - name: Build executable
      run: uv run python scripts/build-executable.py

    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: tcc-analyzer-${{ runner.os }}
        path: dist/tcc-analyzer*
```

## Build Configuration

### PyInstaller Spec File

The build is configured via `build.spec`:

```python
# Key configuration options:
- Entry point: src/tcc_analyzer/__main__.py
- Console app: True (CLI application)
- One file: True (single executable)
- UPX compression: Enabled (if available)
- Hidden imports: Pandas, Rich, Click dependencies
```

### Customization

To modify the build:

1. **Change executable name**: Edit `name` in `build.spec`
2. **Add data files**: Add to `datas` list in `build.spec`
3. **Exclude modules**: Add to `excludes` list to reduce size
4. **Icon**: Add `icon='path/to/icon.ico'` (Windows) or `.icns` (macOS)

### Size Optimization

Current optimizations:
- ✅ UPX compression enabled
- ✅ Unnecessary modules excluded (tkinter, matplotlib, jupyter, etc.)
- ✅ One-file bundle (no separate DLLs)

Potential additional optimizations:
- 📦 Use `--strip` for debug symbols (Linux/macOS)
- 🗜️ Custom UPX settings
- 📋 More aggressive module exclusion

## Troubleshooting

### Common Issues

1. **Import errors in executable**
   ```
   ImportError: No module named 'xyz'
   ```
   **Solution**: Add missing module to `hiddenimports` in `build.spec`

2. **Large executable size**
   ```
   Executable is over 100MB
   ```
   **Solution**: Add more modules to `excludes` list

3. **Slow startup time**
   ```
   Executable takes 5+ seconds to start
   ```
   **Solution**: Consider two-file mode or reduce dependencies

4. **macOS security warnings**
   ```
   "App cannot be opened because developer cannot be verified"
   ```
   **Solution**: Code sign the executable or ask users to bypass security

### Debug Mode

For troubleshooting build issues:

```bash
# Enable debug mode in build.spec
debug=True

# Run with verbose logging
uv run python -m PyInstaller --debug=all build.spec
```

### Testing

Always test the executable thoroughly:

```bash
# Basic functionality
./dist/tcc-analyzer --help
./dist/tcc-analyzer --version

# Test with real data
./dist/tcc-analyzer task sample_data.csv --output-format table
./dist/tcc-analyzer task sample_data.csv --base-time 08:00
```

## Distribution

### Linux
- 📦 Package as `.tar.gz` or `.zip`
- 🐧 Consider creating `.deb` or `.rpm` packages
- 📋 Include README with glibc requirements

### Windows
- 📦 Package as `.zip` or create installer with NSIS/Inno Setup
- 🪟 Consider Windows Store packaging
- 🔐 Code signing recommended for wider distribution

### macOS
- 📦 Package as `.dmg` with drag-to-Applications
- 🍎 Code signing **required** for non-developer distribution
- 🏪 Consider Mac App Store submission
- 📋 Notarization required for macOS 10.15+

## Development Workflow

1. **Make changes** to source code
2. **Test locally** with `uv run python -m tcc_analyzer.cli`
3. **Run tests** with `uv run pytest`
4. **Build executable** with build script
5. **Test executable** functionality
6. **Commit changes** and push
7. **CI builds** executables for all platforms
8. **Download artifacts** from CI for distribution

## Performance Considerations

### Startup Time
- **Cold start**: 2-3 seconds (one-time PyInstaller overhead)
- **Warm start**: < 1 second (subsequent runs)

### Memory Usage
- **Base usage**: ~50MB (Python runtime + dependencies)
- **Peak usage**: Depends on CSV file size and analysis complexity

### File Size vs Performance Trade-offs
- **One-file**: Larger size (~37MB), slower startup, easier distribution
- **One-dir**: Smaller core (~5MB), faster startup, multiple files

For this CLI tool, one-file mode is preferred for ease of distribution.
