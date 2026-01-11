# Build System Documentation

DocNexus uses a **cross-platform build system** centered around Python. This ensures that builds are consistent whether you are on Windows, Linux, or macOS.

> **Architecture**: All logic resides in `scripts/build.py`. 
> *   **Windows**: The `make.ps1` script wraps this Python logic.
> *   **Linux/Mac**: The `Makefile` wraps this Python logic.
>
> **Single Source of Truth**: The version is defined in `docnexus/version_info.py` and propagated to the build system and application automatically.

---

## 🚀 Quick Start

| OS | Command | Description |
| :--- | :--- | :--- |
| **Windows** | `.\make.ps1 setup` | Setup venv and deps |
| **Linux/Mac** | `make setup` | Setup venv and deps |

### Building the App
To create a standalone executable:

**Windows**:
```powershell
.\make.ps1 build
```

**Linux / Mac**:
```bash
make build
```
The output file will be in `build/output/`.

---

## The "Dual-Mode" Build System
The build system automatically detects if you have the proprietary source code:
1.  **Open Source Mode**: Default. Builds the Core engine only.
2.  **Premium Mode**: If `docnexus/plugins_dev` exists, it is bundled into the final executable.

---

## Advanced Usage

### Clean Artifacts
Remove all build caches, temporary files, and output binaries.
*   **Windows**: `.\make.ps1 clean`
*   **Linux**: `make clean`

### Run from Source
Run the application directly without packaging.
*   **Windows**: `.\make.ps1 run`
*   **Linux**: `make run`

---

## Troubleshooting

**"Venv not found"**
*   Run `make setup` (or `.\make.ps1 setup`) first.

**"Permission Denied" (Linux)**
*   Ensure `scripts/build.py` is executable: `chmod +x scripts/build.py`.
