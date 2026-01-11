# Plugin System Architecture (v1.2.0)

## 1. Core Philosophy (Hybrid Model)
Inspired by VS Code and Obsidian, we will use a hybrid approach to handle the constraints of a frozen PyInstaller application:
1.  **"Batteries Included, but Sleeping"**: Heavy Python dependencies (like `python-pptx`) are **bundled** in the main executable but unused/hidden until a plugin activates them.
2.  **"Download on Demand"**: Large external binaries (like `wkhtmltopdf`) are **downloaded** only when the user explicitly enables the feature.
3.  **"Dynamic Glue"**: The actual logic connecting the UI to these libraries lives in lightweight Python scripts (`plugin.py`) downloaded from repositories (Public or Private).

## 2. Architecture Components

### A. Plugin Directory (`~/.docnexus/plugins/`)
We will add this directory to `sys.path` at application startup.
Structure:
```text
plugins/
  ├── manifest.json         # Registry of installed plugins
  ├── pdf_pro/              # Plugin ID
  │     ├── plugin.py       # Main entry point (loaded dynamically)
  │     └── manifest.json   # Plugin metadata
  └── ppt_connect/
        └── plugin.py
```

### B. The `PluginManager`
A singleton class responsible for:
1.  **Discovery**: Fetching available plugins from `https://raw.githubusercontent.com/docnexus-org/registry/main/plugins.json`.
2.  **Installation**: Downloading plugin code (Zip/Git) to the plugin directory.
3.  **Loading**: Using `importlib` to load `plugin.py` modules from the directory.
4.  **Binary Management**: Helper methods to check/download tools like `wkhtmltopdf` to `~/.docnexus/bin/`.

## 3. Specific Plugin Designs

### Feature 1: PDF Import/Export (External Tool)
*   **Type**: `tool-wrapper`
*   **Installation**: Downloads a small `plugin.py` script.
*   **Activation**:
    1.  User clicks "Enable".
    2.  Plugin checks for `~/.docnexus/bin/wkhtmltopdf.exe`.
    3.  **If missing**: Triggers a built-in download task (VS Code style) to fetch the portable binary (~40MB) from a trusted CDN.
    4.  **If present**: Registers the `Export to PDF` menu item and `/export-pdf` route handler.

### Feature 2: PPT Support (Private Repo + Bundled Lib)
*   **Type**: `bundled-lib` w/ Private Code
*   **Prerequisite**: `python-pptx` is added to `DocNexus` build (hidden import).
*   **Installation**:
    1.  User enters **Repo URL** and **Auth Token** in Settings.
    2.  App fetches the plugin code (logic to read/write PPTX) from the private repo.
*   **Runtime**:
    1.  `PluginManager` imports `ppt_plugin.plugin`.
    2.  The script does `import pptx`. This SUCCEEDS because `pptx` is frozen in the EXE.
    3.  The script registers `Import PPT` and `Export PPT` features.

## 4. Security
*   **Sandboxing**: None (Python limits). We trust the user to only install plugins from sources they trust (Private Repos or our Official Registry).
*   **Verification**: Official plugins are checksum-verified.

## 5. UI/UX
*   **Settings > Extensions**: A card-based layout showing Available vs Installed.
*   **Status**: "Enabled", "Disabled", "Missing Dependency" (e.g. "Click to download PDF Engine").

# Plugin System Architecture (v1.2.4 Refinement)

## 1. Shift to "Bundled Passive" Model
In v1.2.0, we planned to download binaries like `wkhtmltopdf` on demand.
In v1.2.4, we pivoted to a **Bundled Passive** model:
1.  **Bundled**: Core tools (PDF/Word export) are critical. We now bundle `xhtml2pdf` and `docx` directly in the executable.
2.  **Passive**: Even bundled code is "hidden" behind the Plugin abstraction. The core `app.py` doesn't import them.
3.  **State Management**: `PluginState` allows users to disable bundled features, keeping the runtime footprint minimal if unused.

## 2. Why?
*   **Reliability**: Removing reliance on external downloads (CDNs, network issues) ensures the app "just works" offline.
*   **Consistency**: We control the exact version of the export engines.
*   **Simplicity**: Users don't need to "Install" basic features; they just Toggle them.
