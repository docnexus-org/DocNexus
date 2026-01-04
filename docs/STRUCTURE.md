# DocNexus - Project Structure

This document describes the standard Python project structure for DocNexus.

## Directory Layout

```
DocNexus/
├── docnexus/                 # Main application package
│   ├── __init__.py            # Package initialization
│   ├── version_info.py        # Single Source of Truth for Version
│   ├── app.py                 # Flask application setup
│   ├── cli.py                 # Command-line interface
│   ├── core/                  # Core functionality
│   │   ├── loader.py          # Plugin Loader & DI
│   │   └── renderer.py        # Markdown rendering engine
│   ├── features/              # Feature modules
│   │   ├── registry.py        # Plugin & Feature Registry
│   │   ├── standard.py        # Standard features
│   │   └── smart_convert.py   # Experimental features
│   ├── plugins/               # Bundled Plugins (Word Export, Auth, etc.)
│   └── templates/             # HTML templates (Jinja2)
│
├── docs/                      # Project documentation
│   ├── README.md              # Documentation index
│   ├── USER_GUIDE.md          # User manual
│   ├── DOCNEXUS_ARCHITECTURE.md # Architecture deep dive
│   ├── PLUGIN_DEV_GUIDE.md    # Plugin development guide
│   └── [various guides...]
│
├── scripts/                   # Build & Automation Scripts
│   ├── build.py               # Master build script (Python)
│   └── run_tests.py           # Test runner
│
├── tests/                     # Test Suite
│   ├── fixtures/              # Test assets
│   └── output/                # Test artifacts (gitignored)
│
├── build/                     # Build artifacts (gitignored)
│   ├── output/                # Final Exe & Dist
│   ├── venv/                  # Virtual Environment
│   └── temp/                  # PyInstaller temp
│
├── make.cmd                   # Windows Build Wrapper (Powershell)
├── make.ps1                   # Powershell Entry Point
├── VERSION                    # Version File (Synced via build)
├── README.md                  # Project overview
├── LICENSE                    # AGPLv3 License
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Modern packaging (PEP 518)
└── .gitignore                # Git exclusions
```

## Build Process (The `make` system)

We utilize a unified `make.cmd` wrapper around `scripts/build.py` for all lifecycle tasks.

### 1. Setup
```powershell
.\make.cmd setup  # Creates venv, installs requirements
```

### 2. Run from Source
```powershell
.\make.cmd run    # Starts local Flask development server
```

### 3. Testing
```powershell
.\make.cmd test   # Runs unittest suite
```

### 4. Build Standalone Executable
```powershell
.\make.cmd build  # Uses PyInstaller to create frozen EXE in build/output
```
*   **Version Sync**: The build process automatically reads `docnexus/version_info.py` and updates the `VERSION` file.
*   **Asset Bundling**: Templates, static assets, and bundled plugins are collected.

### 5. Launch
```powershell
.\make.cmd launch # Runs the certified build from output folder
```

### Create Release
```bash
# Build executable
pyinstaller DocPresent.spec --clean

# Create release structure
mkdir releases/v1.0.0
cp dist/DocPresent.exe releases/v1.0.0/
cp README.md releases/v1.0.0/
cp -r doc releases/v1.0.0/
cp -r workspace releases/v1.0.0/

# Create archive
cd releases
zip -r DocPresent-v1.0.0-Windows-x64.zip v1.0.0/

# Generate checksum
sha256sum DocPresent-v1.0.0-Windows-x64.zip > CHECKSUMS.txt
```

## Git Workflow

### Ignored Files (.gitignore)
- Build artifacts: `build/`, `dist/`, `*.egg-info/`
- Virtual environments: `.venv/`, `venv/`
- Python cache: `__pycache__/`, `*.pyc`
- Releases: `releases/`
- IDE configs: `.vscode/`, `.idea/`

### Tracked Files
- Source code: `doc_viewer/`
- Documentation: `docs/`, `README.md`
- Samples: `examples/`
- Configuration: `pyproject.toml`, `setup.py`, `requirements.txt`
- Build specs: `DocPresent.spec`, `MANIFEST.in`

## Standards Compliance

This project follows Python packaging best practices:

- ✅ **PEP 518** - pyproject.toml for build system
- ✅ **PEP 621** - Project metadata in pyproject.toml
- ✅ **PEP 517** - Build backend specification
- ✅ **PEP 440** - Version numbering (1.0.0)
- ✅ **Setuptools** - Package discovery and data files
- ✅ **Entry Points** - Console scripts registration
- ✅ **MANIFEST.in** - Explicit data file inclusion
- ✅ **Semantic Versioning** - Major.Minor.Patch

## Distribution Channels

### GitHub Releases
- Release archive: `DocPresent-v1.0.0-Windows-x64.zip`
- SHA256 checksums for verification
- Release notes and documentation

### PyPI (Future)
- Python wheel: `docpresent-1.0.0-py3-none-any.whl`
- Source distribution: `docpresent-1.0.0.tar.gz`
- Install via: `pip install docpresent`

### Standalone Executable
- Windows: `DocPresent.exe` (15 MB)
- No Python installation required
- All dependencies bundled

---

**Last Updated:** January 04, 2026  
**Version:** 1.2.4  
**Structure:** Hybrid (Flask App + PyInstaller Build)
