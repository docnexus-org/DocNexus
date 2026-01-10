# DocNexus Architecture & Logic Flows

This document provides a deep dive into the internal architecture, versioning logic, and data rendering flows of DocNexus v1.2.0.

---

## 1. Versioning Architecture
We adhere to a **Single Source of Truth (SSOT)** robust versioning strategy to ensure consistency across the Python package, built executable, and user interface.

### The Source of Truth
*   **File**: `docnexus/version_info.py`
*   **Content**: `__version__ = '1.2.x'`
*   **Role**: This is the *only* place the version number is hardcoded.
*   **Sync**: The root `VERSION` file is automatically updated from this source during build.

### The Propagation Flow
1.  **Package Init**: `docnexus/__init__.py` imports `__version__` from `version_info.py`.
2.  **Runtime App**: `docnexus/app.py` imports `docnexus.version_info` to populate the `VERSION` constant.
3.  **Build System**: `scripts/build.py` reads `version_info.py` directly from the filesystem to name the executable (e.g., `DocNexus_v1.2.0.exe`).
4.  **User Interface**:
    *   `app.py` injects `version` into the global Jinja2 template context via `inject_global_context()`.
    *   **Components**: `templates/components/header_brand.html` renders `{{ version }}`. Since the context is global, this works on *every* page (Docs, View, Index).

### Robustness & Safety Nets
To prevent "blank version" errors in frozen environments (PyInstaller):
*   **Hidden Import**: The build script explicitly forces `--hidden-import docnexus.version_info`.
*   **Startup Logging**: `app.py` logs the loaded version to stdout for debugging.
*   **Fail-Safe**: If `version_info` cannot be imported (critical failure), `app.py` falls back to `1.2.0-fallback` to prevent crash, though this path should theoretically be unreachable in a valid build.

---

## 2. Data Rendering Flow
How a Markdown file on disk becomes a rich HTML page in your browser.

### A. Discovery Phase
1.  **Loader**: `app.py` scans the active workspace (`MD_FOLDER`) for `.md` files.
2.  **Router**:
    *   `@app.route('/')`: Lists files.
    *   `@app.route('/view/<path:filename>')`: Handles rendering.

### B. Rendering Pipeline (`docnexus/core/renderer.py`)
When a file is requested:
1.  **Read**: content is read as UTF-8.
2.  **Pipeline Construction**: `FeatureManager` builds a processing pipeline based on enabled features (Standard vs Experimental).
    *   *Standard*: TOC generation, ID normalization, Attribute sanitization.
    *   *Premium/Smart*: (If enabled) SIP/Topology diagrams, Advanced tables.
3.  **Processing**: The content passes through the pipeline, transforming raw Markdown -> Enhanced Markdown -> HTML.
4.  **Template Rendering**:
    *   The HTML is passed to `view.html`.
    *   Global Context (Version, Theme) is injected.
    *   `header_brand.html` renders the logo/version.
    *   `settings_menu.html` renders the configuration UI.
5.  **Client-Side Polish**:
    *   `theme.js` initializes syntax highlighting (`highlight.js`).
    *   TOC scroll-spy logic activates.

---

## 3. Module Breakdown

### `docnexus.core`
The engine room.
*   `renderer.py`: Orchestrates the markdown-to-html conversion.
*   `loader.py`: Handles plugin discovery, dependency injection, and loading in both Dev and Frozen environments.
*   `state.py`: Manages the persistence of plugin states (Enabled/Disabled) via `plugins.json`.

### `docnexus.features`
The "Plugin" system for core features.
*   **Registry**: Manages what features are active (Unified Registry pattern).
*   **FeatureManager**: The global access point (`FEATURES` in `app.py`) that acts as a facade.
*   **Passive Architecture**: Plugins do not import from `docnexus`; dependencies are injected by the Loader.
*   **Standard**: Baseline features (TOC, Headers).
*   **Smart**: Advanced AI/Regex features (currently strictly separated).

### `docnexus.plugins`
User-installable extensions.
*   **Isolation**: Each plugin is its own package.
*   **Safe Mode**: Export plugins (esp. PDF) operate in a "Safe Mode" that strips complex web CSS to prevent engine crashes.

### `docnexus.templates`
Jinja2 HTML templates.
*   **`components/`**: Reusable UI blocks (headers, settings, footers).
*   **`view.html`**: The complex document viewer.
*   **`docs.html`**: The internal documentation viewer.

### `scripts/`
Build and Automation.
*   **`build.py`**: The master build script. Handles venv setup, dependencies, and PyInstaller configuration.
