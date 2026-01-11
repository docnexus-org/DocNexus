# DocNexus Architecture & Logic Flows

This document provides a deep dive into the internal architecture, versioning logic, and data rendering flows of DocNexus v1.2.0+.

---

## 1. Functional Layout (Block Design)

The application consists of three primary functional blocks: the **Input Processor**, the **Core Kernel**, and the **Output Generators**.

```mermaid
graph LR
    subgraph InputSources ["Block 1: Input Sources"]
        FS[Filesystem<br/>(.md Files)]
        Remote[Remote Sources<br/>(Future: S3/Git)]
        User[User Input<br/>(Editor/Settings)]
    end

    subgraph CoreKernel ["Block 2: Core Kernel"]
        Router[Flask Router<br/>(API/Views)]
        Loader[Module Loader<br/>(Discovery)]
        Registry[Feature Registry<br/>(Database)]
        Manager[Feature Facade<br/>(Logic)]
        Pipeline[Render Pipeline<br/>(Execution Chain)]
    end

    subgraph OutputEngines ["Block 3: Output Engines"]
        HTML[Web Engine<br/>(Jinja2 + Theme)]
        PDF[PDF Engine<br/>(xhtml2pdf)]
        DOCX[Word Engine<br/>(python-docx)]
    end

    FS --> Router
    User --> Router
    Loader -->|Populates| Registry
    Registry -->|Feeds| Manager
    Manager -->|Configures| Pipeline
    Router -->|Triggers| Pipeline
    Pipeline -->|Content| HTML
    Pipeline -->|Content| PDF
    Pipeline -->|Content| DOCX
```

---

## 2. Low Level Architecture (Class Design)

The system relies on a strictly typed (checked at runtime) relationship between the **Manager**, **Registry**, and **Features**.

```mermaid
classDiagram
    class FeatureManager {
        -List[Feature] _features
        -PluginRegistry _registry
        +refresh()
        +get_export_handler(ext)
        +build_pipeline()
        +is_feature_installed(feature)
        +register(feature)
        +get_features_by_type(type)
    }

    class PluginRegistry {
        -List[Any] _plugins
        -Dict _custom_slots
        -List _blueprints
        +register(plugin)
        +register_blueprint(bp)
        +get_all_plugins()
        +register_slot(name, content)
    }

    class PluginState {
        -Set installed_plugins
        -Path config_path
        +get_instance()
        +is_plugin_installed(id)
        +set_plugin_installed(id, bool)
        +_load_state()
        +_save_state()
    }

    class Feature {
        +String name
        +Callable handler
        +FeatureState state
        +FeatureType type
        +Dict meta
    }

    class FeatureType {
        <<Enumeration>>
        ALGORITHM
        UI_EXTENSION
        EXPORT_HANDLER
    }

    FeatureManager --> PluginRegistry : Observes
    FeatureManager --> PluginState : Validates
    PluginRegistry *-- Feature : Stores Plugins that yield Features
    Feature *-- FeatureType : Categorization
```

---

## 3. Detailed Logic Flows

### A. Application Startup (Deep Dive)
How the application initializes, handling both frozen (PyInstaller) and source environments.

```mermaid
sequenceDiagram
    participant Boot as __main__
    participant App as app.py
    participant Loader as core.loader
    participant State as PluginState
    participant Reg as PluginRegistry
    participant FM as FeatureManager

    Boot->>App: create_app()
    App->>App: setup_logging()
    
    rect rgb(240, 240, 240)
        note right of App: Plugin System Init
        App->>Reg: Instantiate Registry (Singleton)
        App->>Loader: load_plugins(registry)
        
        Loader->>Loader: Determine Paths (sys._MEIPASS vs CWD)
        
        loop Every Plugin Folder
            Loader->>State: is_plugin_installed(id)?
            alt Installed / Pre-installed
                Loader->>Loader: import_module(plugin.py)
                Loader->>Loader: Extract PLUGIN_METADATA
                Loader->>Reg: register(plugin_module)
                
                opt Has Blueprint
                   Loader->>Reg: register_blueprint(bp)
                end
            else Disabled
                Loader->>App: Log "Skipping Disabled Plugin"
            end
        end
    end

    App->>Reg: register_blueprints(flask_app)
    
    rect rgb(230, 245, 255)
        note right of App: Feature Integration
        App->>FM: Instantiate FeatureManager(registry)
        App->>FM: refresh()
        FM->>Reg: get_all_plugins()
        FM->>FM: Flatten Plugins -> List[Feature]
        FM->>FM: Apply Priority Overrides
        FM->>App: Ready (Features Loaded)
    end
    
    App->>App: run_server()
```

### B. Document Rendering Pipeline
The core loop: transforming Markdown source into the HTML viewed by the user.

```mermaid
sequenceDiagram
    participant Browser
    participant Route as /file/{path}
    participant FM as FeatureManager
    participant RP as run_pipeline
    participant MD as render_baseline (Markdown)
    participant Post as process_links

    Browser->>Route: GET /file/docs/guide.md
    
    Route->>Route: Check File Size & Type
    
    rect rgb(240, 240, 240)
        note right of Route: Pipeline Construction
        Route->>FM: build_pipeline()
        FM-->>Route: List[Callable]
    end
    
    Route->>RP: run_pipeline(text, steps)
    loop Every Feature
        RP->>RP: Apply feature.handler(text)
    end
    RP-->>Route: processed_markdown
    
    Route->>MD: render_baseline(processed_markdown)
    MD->>MD: Markdown(extensions=[...])
    MD->>MD: convert()
    MD-->>Route: html_content, toc
    
    rect rgb(230, 255, 230)
        note right of Route: Post Processing
        Route->>Post: process_links_in_html(html)
        Post-->>Route: final_html
    end
    
    Route-->>Browser: Render view.html (content=final_html)
```

### C. Export Request Flow
The user clicks "Export to PDF". The system must locate the correct handler, ensure it's allowed, and execute it safe-mode.

```mermaid
sequenceDiagram
    participant Client as Browser
    participant API as /game/export/{fmt}
    participant FM as FeatureManager
    participant Plugin as Word/PDF Plugin
    participant SafeMode as CSS Sanitizer

    Client->>API: GET /view?export=pdf
    API->>FM: get_export_handler('pdf')
    
    loop Search Feature List
        FM->>FM: features.find(type=EXPORT, name='pdf')
        alt Found Candidate
            FM->>FM: is_feature_installed(candidate)?
            alt Installed
                FM-->>API: Return Handler
            else Uninstalled
                FM-->>API: Return None
                API-->>Client: 404 "Plugin Missing"
            end
        end
    end

    API->>Plugin: handler(html_content)
    
    rect rgb(255, 230, 230)
        note right of Plugin: Safe Mode (PDF Only)
        Plugin->>SafeMode: strip_external_css()
        SafeMode-->>Plugin: clean_html
    end
    
    Plugin->>Plugin: Generate Binary (xhtml2pdf / python-docx)
    Plugin-->>API: File Bytes
    API-->>Client: Download (Attachment)
```

### D. Extension Management Flow
User installs an extension via the Marketplace UI.

```mermaid
sequenceDiagram
    participant UI as Extension Page
    participant API as /api/install
    participant State as PluginState
    participant Loader as core.loader
    participant FM as FeatureManager

    UI->>API: POST /api/plugins/install/my_theme
    
    API->>State: set_plugin_installed('my_theme', True)
    State->>State: Write to plugins.json
    
    rect rgb(240, 255, 240)
        note right of API: Hot Reload
        API->>Loader: load_single_plugin('my_theme')
        Loader->>Loader: import_module()
        Loader->>Loader: register()
        
        API->>FM: refresh()
        FM->>FM: Re-scan Registry
        FM->>FM: Enable associated features
    end
    
    API-->>UI: 200 OK
    UI->>UI: Show Toast "Installed Successfully"
```

---

## 4. Versioning Architecture
We adhere to a **Single Source of Truth (SSOT)** robust versioning strategy.

### The Source of Truth
*   **File**: `docnexus/version_info.py`
*   **Content**: `__version__ = '1.2.x'`
*   **Role**: This is the *only* place the version number is hardcoded.
*   **Sync**: The root `VERSION` file is automatically updated from this source during build.

### The Propagation Flow
1.  **Package Init**: `docnexus/__init__.py` imports `__version__` from `version_info.py`.
2.  **Runtime App**: `docnexus/app.py` imports `docnexus.version_info` to populate the `VERSION` constant.
3.  **Build System**: `scripts/build.py` reads `version_info.py` directly from the filesystem to name the executable (e.g., `DocNexus_v1.2.0.exe`).
4.  **User Interface**: `app.py` injects `version` into the global Jinja2 template context.

---

## 5. Module Breakdown

### `docnexus.core`
The engine room.
*   `renderer.py`: Orchestrates the markdown-to-html conversion.
*   `loader.py`: Handles plugin discovery, dependency injection, and loading in both Dev and Frozen environments.
*   `state.py`: Manages the persistence of plugin states (Enabled/Disabled) via `plugins.json`.

### `docnexus.features`
The "Plugin" system for core features.
*   **Registry**: Singleton managing active features.
*   **FeatureManager**: The global access point (`FEATURES`) acting as a facade.
*   **Standard**: Baseline features (TOC, Headers).
*   **Smart**: Advanced AI/Regex features.

### `docnexus.plugins`
User-installable extensions isolated in their own packages.
*   **Bundled**: Essential plugins (Word Export, Auth) shipped with the exe.
*   **Dev**: Optional/Premium plugins.
