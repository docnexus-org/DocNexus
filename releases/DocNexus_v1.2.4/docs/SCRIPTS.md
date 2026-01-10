# Scripts & Utilities

This folder (`scripts/`) contains core utility scripts used for building and testing the DocNexus application.

## 1. `run_tests.py`
**Use Case:** The central entry point for running the automated test suite.
- **Function**:
    - Sets up the python environment (adds project root to `sys.path`).
    - Kills any existing process occupying the test port (Default: 8000) to ensure a clean environment.
    - Invokes `pytest` to discover and run all tests in the `tests/` directory.
    - Pipes output to both the console and `tests/latest_results.log`.
- **Usage**: `python scripts/run_tests.py` (or via `.\make.ps1 test`)

## 2. `build.py`
**Use Case:** The main build script for creating the standalone executable (Frozen App).
- **Function**:
    - wrappers PyInstaller with specific configuration.
    - Handles "Split-Brain" bundling:
        - Bundles `plugins` (Production) into the executable (`_MEIPASS`).
        - Excludes `plugins_dev` (Development).
    - Collects hidden imports for dynamic plugins (e.g., `xhtml2pdf`, `reportlab`).
    - managing assets and version resources.
- **Usage**: `python scripts/build.py` (or via `.\make.ps1 build`)

## Other Utilities (Moved)
- **Asset Generator**: Moved to `tools/asset_generator.py`. Used for generating favicon/icons from a master logo.
- **Plugin Scaffolding**: Moved to `tests/scripts/generate_dummy_plugin.py`. Used for internal regression testing.
