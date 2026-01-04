# Plugin Architecture (v1.2.4)

This document outlines the architecture for the DocNexus Plugin System, updated in v1.2.4.

## Core Concepts

The plugin system has been refactored to use a **Unified Registry** and **Dependency Injection** to ensure stability and resolving "Split-Brain" issues.

### 1. Unified Registry (`docnexus.features.registry`)

*   **Location**: `docnexus/features/registry.py`
*   **Role**: A single source of truth for both "Features" (Algorithms) and "UI Slots". 
*   **Legacy**: `docnexus/core/registry.py` has been removed.

### 2. Dependency Injection (The Loader)

*   **Logic**: `docnexus/core/loader.py`
*   **Mechanism**: The loader injects core dependencies (`PluginRegistry`, `Feature`, `FeatureType`, `FeatureState`) directly into the plugin's namespace before execution.
*   **Benefit**: Plugins do not need to import these classes, preventing "Class Identity Mismatch" issues where a plugin's `Feature` class differs from the App's `Feature` class.

### 3. Passive Plugins (No Interface)

Plugins no longer need to inherit from `PluginInterface`. They simplest need to expose a `get_features()` function.

```python
# plugin.py
def get_features():
    # Classes are injected!
    _Feature = globals().get('Feature')
    return [
        _Feature("MyFeature", handler, ...)
    ]
```

### 4. UI Slots (`register_slot`)

Plugins can inject content into predefined UI areas.
*   **Method**: `PluginRegistry().register_slot(slot_name, html_content)`
*   **Slots**: `HEADER_RIGHT`, `SIDEBAR_BOTTOM`, `EXPORT_MENU`, etc.

### 5. Export Handlers

Plugins registering `EXPORT_HANDLER` features take over `/api/export/<ext>` routes.
*   **Robustness**: The build system now bundles `python-docx` for reliable Word exports.
*   **Image Handling**: Export plugins must robustly handle image paths, especially in frozen (executable) environments.

## Directory Structure
*   `docnexus/core/loader.py`: The Scanner & Injector.
*   `docnexus/features/registry.py`: The Unified Registry & Feature Manager.
