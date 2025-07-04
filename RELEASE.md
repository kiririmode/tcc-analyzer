# Release Process

This document describes how to create releases for TCC Analyzer using GitHub Actions.

## Overview

The release process is fully automated using GitHub Actions. When you push a version tag, the system will:

1. 🏗️ **Build** executables for Linux, Windows, and macOS
2. 🧪 **Test** each executable for basic functionality
3. 📦 **Package** executables in platform-appropriate formats
4. 📝 **Generate** release notes from git history
5. 🚀 **Create** a GitHub Release with all assets

## Quick Release Process

### 1. Prepare for Release

```bash
# Ensure you're on main branch and up to date
git checkout main
git pull origin main

# Run final tests locally
uv run --frozen pytest
uv run --frozen pre-commit run --all-files

# Verify build works locally
uv run python scripts/build-executable.py
./dist/tcc-analyzer --version
```

### 2. Create and Push Version Tag

```bash
# Create a version tag (follow semantic versioning)
git tag v1.0.0

# Push the tag to trigger release
git push origin v1.0.0
```

### 3. Monitor Release Process

1. Go to **Actions** tab in GitHub repository
2. Watch the "Build and Release" workflow
3. Verify all platform builds succeed
4. Check the created release in **Releases** section

## Version Tag Format

Use [Semantic Versioning](https://semver.org/) format:

- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.0.1` - Patch release (bug fixes)
- `v1.0.0-beta.1` - Pre-release (marked as prerelease)
- `v1.0.0-rc.1` - Release candidate

## Testing Release Workflow

Before creating an actual release, you can test the process:

### Manual Test Workflow

1. Go to **Actions** → **Test Release Workflow**
2. Click **Run workflow**
3. Enter a test version (e.g., `v1.0.0-test`)
4. Run and verify all steps work correctly

This tests the build process without creating an actual release.

## Release Assets

Each release includes executables for all supported platforms:

### Linux (x64)
- **File**: `tcc-analyzer-linux-x64.tar.gz`
- **Extract**: `tar -xzf tcc-analyzer-linux-x64.tar.gz`
- **Run**: `./tcc-analyzer --help`

### Windows (x64)
- **File**: `tcc-analyzer-windows-x64.exe.zip`
- **Extract**: Use built-in Windows extraction or 7-Zip
- **Run**: `tcc-analyzer.exe --help`

### macOS (x64)
- **File**: `tcc-analyzer-macos-x64.tar.gz`
- **Extract**: `tar -xzf tcc-analyzer-macos-x64.tar.gz`
- **Run**: `./tcc-analyzer --help`

## Release Notes

Release notes are automatically generated and include:

- 📋 **Version information** and download links
- 🚀 **Quick start instructions** for each platform
- 📝 **Changelog** from git commits since last release
- 🔧 **System requirements** and compatibility info
- 📖 **Links** to documentation and repository

## Versioning Strategy

### Version Bumping

Update version in relevant files before tagging:

```bash
# Update CLI version (if needed)
# Edit src/tcc_analyzer/cli.py:
@click.version_option(version="1.1.0", package_name="tcc-analyzer")

# Update pyproject.toml version (if needed)
# Edit pyproject.toml:
version = "1.1.0"
```

### Release Cadence

Suggested release schedule:
- **Major releases**: Every 6-12 months
- **Minor releases**: Every 1-3 months
- **Patch releases**: As needed for critical bug fixes
- **Pre-releases**: For testing major changes

## Troubleshooting

### Build Failures

If a platform build fails:

1. Check the **Actions** tab for error details
2. Common issues:
   - Missing dependencies in `build.spec`
   - Import errors (check `hiddenimports`)
   - Platform-specific code issues

### Release Creation Failures

If release creation fails:
1. Verify the tag exists and follows correct format
2. Check repository permissions (need `contents: write`)
3. Ensure no release already exists for that tag

### Asset Upload Issues

If assets fail to upload:
1. Check file paths in workflow
2. Verify artifacts were created correctly
3. Check file size limits (100MB per file)

## Manual Release (Fallback)

If automated release fails, you can create manually:

### 1. Build Locally on Each Platform

```bash
# On Linux
uv run python scripts/build-executable.py --platform linux
cd dist && tar -czf tcc-analyzer-linux-x64.tar.gz tcc-analyzer

# On Windows
uv run python scripts/build-executable.py --platform windows
# Zip the tcc-analyzer.exe file

# On macOS
uv run python scripts/build-executable.py --platform macos
cd dist && tar -czf tcc-analyzer-macos-x64.tar.gz tcc-analyzer
```

### 2. Create GitHub Release

1. Go to **Releases** → **Create a new release**
2. Choose or create the version tag
3. Write release notes (use automated template as reference)
4. Upload the three platform archives
5. Publish the release

## Security Considerations

### Code Signing

- **Windows**: Consider code signing for wider distribution
- **macOS**: Code signing required for non-developer distribution
- **Linux**: No code signing required

### Checksums

For enhanced security, consider adding checksums:

```bash
# Generate SHA256 checksums
sha256sum tcc-analyzer-*.tar.gz tcc-analyzer-*.zip > checksums.txt
```

## Release Checklist

Before each release:

- [ ] All tests pass (`uv run --frozen pytest`)
- [ ] Code quality checks pass (`uv run --frozen pre-commit run --all-files`)
- [ ] Version updated in relevant files
- [ ] CHANGELOG.md updated (if maintained)
- [ ] Documentation updated for new features
- [ ] Local build test successful
- [ ] Breaking changes documented

After release:
- [ ] Verify all platform downloads work
- [ ] Test executables on actual target systems
- [ ] Update any deployment documentation
- [ ] Announce release (if applicable)

## Automation Improvements

Future enhancements could include:
- Automatic version bumping based on conventional commits
- Integration with package managers (Homebrew, Chocolatey, etc.)
- Docker image releases
- Automatic security scanning of releases
