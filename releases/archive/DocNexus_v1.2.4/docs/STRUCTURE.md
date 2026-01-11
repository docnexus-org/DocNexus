# DocNexus - Project Structure

This document describes the standard Python project structure for DocNexus.

## Directory Layout

```
DocNexus/
├── docnexus/                 # Main application package
│   ├── __init__.py
│   ├── version_info.py        # Single Source of Truth for Version
│   ├── app.py                 # Flask application setup
│   ├── cli.py                 # Command-line interface
│   ├── core/                  # Core functionality
│   │   ├── loader.py          # Plugin Loader & DI
│   │   ├── state.py           # Plugin State Management
│   │   └── renderer.py        # Markdown rendering engine
│   ├── features/              # Feature modules
│   │   ├── registry.py        # Plugin & Feature Registry
│   ├── plugins/               # Bundled Plugins (Word, PDF, Auth, etc.)
│   ├── plugins_dev/           # [OPTIONAL] Development Plugins (Premium)
│   └── templates/             # HTML templates (Jinja2)
│
├── docs/                      # Project documentation
│   ├── README.md
│   ├── USER_GUIDE.md
│   ├── DOCNEXUS_ARCHITECTURE.md
│   ├── PLUGIN_DEVELOPMENT.md  # Plugin development guide
│
├── scripts/                   # Build & Automation Scripts
│   ├── build.py               # Master build script (Python)
│   └── run_tests.py           # Test runner
│
├── make.ps1                   # Powershell Entry Point (Windows)
├── Makefile                   # Make Entry Point (Linux/Mac)
├── VERSION                    # Version File
├── README.md
└── LICENSE

## Build Process (The `make` system)

We utilize a unified build system driven by `scripts/build.py`.

### 1. Setup
```powershell
.\make.ps1 setup  # Creates venv, installs requirements
```

### 2. Run from Source (Dev)
```powershell
.\make.ps1 run    # Starts local backend with hot-reload
```

### 3. Testing
```powershell
.\make.ps1 test   # Runs pytest suite
```

### 4. Build Standalone Executable
```powershell
.\make.ps1 build  # Uses PyInstaller to create frozen EXE in build/output
```
*   **Version Sync**: Automatically syncs `docnexus/version_info.py` to `VERSION`.
*   **Asset Bundling**: Bundles `plugins` (and `plugins_dev` if present).
*   **Output**: `build/output/DocNexus_v1.x.x.exe`

### 5. Launch
```powershell
.\make.ps1 launch # Runs the certified build from output folder
```

### Create Release
The `build` command automatically produces a production-ready executable in `build/output`.
No manual PyInstaller steps are required.

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
