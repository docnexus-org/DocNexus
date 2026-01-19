# Plugin Development Guide

Welcome to the DocNexus Plugin Ecosystem! This guide provides a comprehensive overview of how to build, test, and publish plugins for DocNexus v1.2.4+.

## 1. The "Passive" Philosophy

DocNexus uses a **Passive Plugin Architecture**. This means your plugin should ideally **NOT** import any code from the `docnexus` package directly if possible. Instead, the Core application **injects** the necessary classes and API handles into your plugin at runtime.

**Why?**
- **Stability**: Prevents "Split-Brain" issues where your plugin uses a different version of a class than the Core.
- **Portability**: Your plugin works on any version of DocNexus that supports the API protocol.
- **Sandboxing**: Errors in your plugin are less likely to crash the whole application.

### Dependency Injection
When DocNexus loads your plugin, the Loader injects core dependencies directly into your plugin's namespace:
- `Feature`
- `FeatureType`
- `FeatureState`
- `PluginRegistry`

You can access these via `globals().get('Feature')` (Pure Passive) OR via standard imports (Modern Convenience) if your IDE requires it (e.g., `from docnexus.features.registry import Feature`). The runtime ensures they resolve to the same classes.

## 2. Anatomy of a Plugin

A plugin is a self-contained folder inside `docnexus/plugins/`.

**Directory Structure:**
```text
docnexus/
└── plugins/
    └── my_awesome_plugin/   <-- Your unique plugin ID
        ├── plugin.py        <-- [REQUIRED] Core logic and registration
        ├── installer.py     <-- [OPTIONAL] Installation & verification logic
        ├── requirements.txt <-- [OPTIONAL] Python dependencies
        ├── ENABLED          <-- [GENERATED] Marker file indicating active state
        └── assets/          <-- [OPTIONAL] Images, templates, etc.
```

## 3. The `plugin.py` Contract

The `plugin.py` file is the entry point. It **must** define a `PLUGIN_METADATA` dictionary and expose a `get_features()` function.

## 3.1 Metadata (Required)
The `PLUGIN_METADATA` dictionary is used by the **Extensions Marketplace** to display your plugin and by the **Loader** to determine default state.

```python
PLUGIN_METADATA = {
    'name': 'My Plugin',
    'description': 'A short description for the marketplace.',
    'category': 'editor',  # Options: 'editor', 'export', 'theme', 'utility'
    'icon': 'fa-puzzle-piece', # FontAwesome class (e.g., fa-file-pdf)
    'preinstalled': False,     # Set True ONLY if bundled with Core
    'version': '1.0.0'
}
```

## 3.2 The `get_features()` Function
### `get_features()`
Returns a list of `Feature` objects.

```python
# plugin.py
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def get_features():
    """
    Entry point called by DocNexus Loader.
    Returns a list of Feature objects.
    """
    
    # Access Injected Classes (Passive Style)
    _Feature = globals().get('Feature')
    _FeatureType = globals().get('FeatureType')
    _FeatureState = globals().get('FeatureState')
    
    # Or Standard Import Style (also supported in v1.2.4+)
    # from docnexus.features.registry import Feature, FeatureType ...

    # Check activation state (commonly via ENABLED file)
    is_active = (Path(__file__).parent / "ENABLED").exists()
    
    return [
        _Feature(
            name="my_custom_export",
            feature_type=_FeatureType.EXPORT_HANDLER,
            handler=export_logic,
            state=_FeatureState.BETA,
            meta={
                "label": "My Custom Format (.xyz)",
                "extension": "xyz",   # EXTENSION WITHOUT DOT
                "installed": is_active,
                "description": "Exports to XYZ format.",
                "version": "1.0.0"
            }
        )
    ]

def export_logic(content_html, output_path, meta):
    # Implementation...
    pass
```

### Dependency Definition
If your plugin requires external libraries (e.g., `pandas`), define a global `DEPENDENCIES` list in `plugin.py`:
```python
DEPENDENCIES = ["pandas", "requests"]
```

## 4. The `installer.py` Contract

If your plugin requires installation (downloading binaries, setting up environment, or user opt-in), include an `installer.py`.

### `install()`
Must return a tuple: `(success: bool, message: str)`.

```python
# installer.py
from pathlib import Path

def install():
    try:
        # 1. Perform checks (e.g. check for binary)
        # 2. Touch ENABLED file to activate
        (Path(__file__).parent / "ENABLED").touch()
        
        return True, "Plugin installed successfully."
    except Exception as e:
        return False, f"Installation failed: {e}"
```

**Hot Reloading**: On success, the server immediately reloads your plugin logic, making features available without a restart.

## 5. Feature Types

### UI Slot (`UI_EXTENSION`)
Inject HTML into predefined areas like Sidebar or Header.

```python
def get_features():
    _Registry = globals().get('PluginRegistry')
    reg = _Registry()
    
    html = '<div class="my-widget">Hello</div>'
    reg.register_slot('SIDEBAR_BOTTOM', html)
    
    return [] # UI extensions often don't return a formal Feature object
```

### Export Handler (`EXPORT_HANDLER`)
Handles conversion of document content.
- **Handler Signature**: `def handler(content_html: str, output_path: str, meta: dict) -> bool`
- **Meta Keys**: `extension`, `label`, `description`.

### Flask Blueprint (API Extensions)
Plugins can define a standard Flask Blueprint to expose custom API endpoints.
- **Variable Name**: Define a `blueprint` variable at the module level in `plugin.py`.
- **Loader Behavior**: The loader automatically detects this variable and registers it with the main Flask app.
- **Best Practice**: Use a unique name for your blueprint to avoid collisions (e.g., `bp_myplugin`).

```python
# plugin.py
from flask import Blueprint, jsonify

blueprint = Blueprint('my_plugin', __name__)

@blueprint.route('/api/my-custom-endpoint')
def my_endpoint():
    return jsonify({'status': 'ok'})
```

## 6. Building & Bundling

If bundling your plugin with the DocNexus Executable (PyInstaller), you must ensure all dependencies are reachable by the frozen bootloader.

### 6.1 Hidden Imports
In `scripts/build.py`, explicitly add your plugin's dependencies to the `hidden_imports` list.

```python
# scripts/build.py
hidden_imports = [ ..., "xhtml2pdf", "reportlab", "htmldocx" ]
```

### 6.2 Dynamic Submodules
For complex packages (like `reportlab` or `xhtml2pdf`) that use dynamic imports, standard hidden imports are not enough. You must collect submodules:

```python
from PyInstaller.utils.hooks import collect_submodules
# ...
for pkg in ["xhtml2pdf", "reportlab", "html5lib", "lxml", "docx", "bs4", "htmldocx"]:
    hidden_imports.extend(collect_submodules(pkg))
```

## 7. Publishing

To distribute:
1.  Ensure all code is self-contained.
2.  Remove `__pycache__` and `ENABLED` files.
3.  Zip the folder (`my_plugin.zip`). Users unzip it into their `plugins/` directory.

---
**Core Architecture Note**:
This system relies on `docnexus/core/loader.py` (The Injector) and `docnexus/features/registry.py` (The Unified Registry).

## 8. Logging Best Practices

DocNexus provides a standardized logging configuration (rotating files, 10MB limit). Plugins should **inherit** this configuration rather than setting up their own handlers.

### How to Log
Simply get a logger using `__name__` at the top of your `plugin.py` or module.

```python
import logging

# Inherits configuration from docnexus.core.logging_config
logger = logging.getLogger(__name__)

def export_logic(...):
    logger.info("Starting export...")
    try:
        # ... logic ...
        logger.debug(f"Processed chunk: {len(chunk)} bytes")
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
```

- Do not use `print()`; use `logger.info()` or `logger.debug()`.

## 9. Handling PDF Exports (Safe Mode)

If your plugin uses `xhtml2pdf`, beware that it uses a legacy CSS2 engine that **will crash** if it encounters modern CSS3 features (like `var()`, `calc()`, `clamp()`) often found in web stylesheets (`main.css`).

**The "Safe Mode" Strategy:**
Do NOT attempt to reuse the web UI stylesheets for PDF generation. Instead:
1.  **Strip External Links**: Remove all `<link rel="stylesheet">` tags from the HTML.
2.  **Strip Inline Styles**: Aggressively remove `<style>` blocks and `style="..."` attributes if they might contain variables.
3.  **Inject Safe CSS**: Provide a custom, internal stylesheet within your plugin that uses only standard CSS2 properties (e.g., standard hex colors, simple margins).

```python
# Example Safe Mode Logic
full_html = re.sub(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', '', content_html)
full_html = re.sub(r'<style\b[^>]*>.*?</style>', '', full_html, flags=re.DOTALL)
# ... apply safe internal styles ...
```
