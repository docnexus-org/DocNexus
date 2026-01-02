# Build System Documentation

DocNexus uses a PowerShell-based build system (`make.ps1`) to handle dependencies, environment setup, and compilation.

## The "Dual-Mode" Build System
The build system detects whether the proprietary `plugins_dev` directory is present and adjusts accordingly:
1.  **Open Source Mode**: Default. Builds the Core engine only.
2.  **Mixed Mode**: If `docnexus/plugins_dev` exists (as a folder or symlink), it is bundled into the final executable.

> **Note**: This allows a single codebase to produce both the OSS Community Edition and the Premium Enterprise Edition.

---

## Prerequisites
*   Windows 10/11
*   Python 3.10+
*   PowerShell 5.0+

## Quick Commands
All commands are run via `.\make.ps1` in the project root.

| Command | Description |
| :--- | :--- |
| `.\make.ps1 setup` | Creates `build/venv` and installs dependencies. Run this first. |
| `.\make.ps1 build` | Compiles the standalone `.exe` using PyInstaller. |
| `.\make.ps1 start` | Runs the compiled executable (if exists). |
| `.\make.ps1 run` | Runs the application from source (Development Mode). |
| `.\make.ps1 clean` | Removes build artifacts (`dist/`, `build/`). |
| `.\make.ps1 clean-all` | Removes everything including `venv`. (Factory Reset). |

---

## Detailed Build Process

### 1. Setup (`make.ps1 setup`)
*   Checks for Python installation.
*   Creates a virtual environment at `build/venv`.
*   Upgrades `pip` and installs requirements from `setup.py`.

### 2. Compilation (`make.ps1 build`)
*   Uses **PyInstaller** to package the app into a single file.
*   **Artifact Path**: `build/output/DocNexus_vX.X.X.exe`.
*   **Plugins Dev**: Checks for `docnexus/plugins_dev`. If found:
    *   Adds the directory to PyInstaller's data paths.
    *   Uses a runtime hook (`build/hook-docnexus.plugins_dev.py`) to force-include all Python submodules in that directory.

### 3. Release (`make.ps1 release`)
*   Runs a `build`.
*   Zips the executable along with `docs/` and `LICENSE`.
*   Places the zip in `build/output/release/`.

## Troubleshooting

**"PyInstaller not found"**
*   Run `.\make.ps1 setup` again to repair the environment.

**"ImportError: No module named docnexus.plugins_dev"**
*   This is expected in **Open Source Mode**. The code handles this gracefully using `try/except` blocks in the loader.
