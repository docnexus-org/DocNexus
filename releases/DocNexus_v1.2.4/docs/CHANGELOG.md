# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.4] - 2026-01-10
### Fixed
- **Editor Plugin**: Fixed critical `Feature` signature mismatch that prevented the Editor from loading in the bundled release (added `state` and `feature_type` args).
- **Blueprint Registration**: Fixed `loader.py` missing the Editor API blueprint due to variable naming mismatch.
- **Plugin Detection**: Fixed critical regression where Export plugins (Word/PDF) were incorrectly reported as "Missing" even when installed. The issue was due to the backend verifying logic not syncing with the persisted plugin state.
- **Startup Crash**: Fixed `AttributeError` in `PluginState` and `UnboundLocalError` in `Loader` that caused the application to crash or fail to load plugins at startup.
- **PDF Export**: Fixed a `SyntaxError` in the PDF Export plugin that prevented it from loading.
- **Visuals**: Updated toast notifications in extensions page to use a premium, theme-aware design.
- **Cleanup**: Resolved JavaScript syntax errors in the Extensions Marketplace that caused UI hangs.
- **Documentation**: Comprehensive update of README, Architecture, and Developer guides to reflect v1.2.4 changes.
### Added
- **Toast Notifications**: Replaced browser alerts with a modern, non-blocking toast notification system (Success/Error/Info) in the Extensions Marketplace.
- **Professional UI**: Updated "Extension Required" and "Uninstall Confirmation" modals to use a clean, solid "Professional Card" aesthetic (removing glassmorphism) with refined spacing and typography.
- **Hot-Reload**: Implemented true hot-reload for extensions. Installing an extension immediately activates it, and uninstalling immediately deactivates it without requiring a server restart.
- **Architectural Refactor**: Moved backend Editor logic (`save_document`) to a bundled plugin (`docnexus.plugins.editor`), validating the core-as-plugins architecture.

### Fixed
- **Uninstall Logic**: Fixed critical bug where uninstalling a plugin did not remove it from active memory, allowing it to function until restart. Now forces a module reload.
- **Extensions Page**: Fixed layout corruption (garbage code at bottom) and duplicate script logic that broke the "Disable" button interaction.
- **UI Spacing**: Tightened metrics for all application modals to be sleek and effective.

## [v1.2.3] - 2026-01-05

- **Testing**: Overhauled testing workflow. Switched to `pytest` (via `scripts/run_tests.py`), enabled single-command execution (`make test`), and centralized output to `tests/latest_results.log`.

### Security
- **PDF Export**: Implemented "Nuclear Safe Mode" that rigidly strips all external stylesheets and inline styles to prevent `xhtml2pdf` crashes on modern CSS variables.

### Fixed
- **Word Export**: Fixed `UnrecognizedImageError` by filtering SVG images and handling external image timeouts gracefully.
- **Word Export Content**: Fixed missing Table of Contents in exported files.
- **Word Export Navigation**: Fixed internal TOC links to correctly navigate to document sections.
- **Registry**: Resolved "Split-Brain" issue by unifying key classes in `docnexus.features.registry`.
- **UI**: Restored missing UI slots (`HEADER_RIGHT`, `EXPORT_MENU`).
- **Legacy Tests**: Updated legacy test suite (`test_loader`, `test_registry`) to align with the Phase 1 "Passive" Plugin Architecture (Duck Typing, Singleton Registry).

## [v1.2.3] - 2026-01-04
- **Pipeline Backbone**: Implemented `Pipeline` class to construct and execute sequences of `ALGORITHM` features.
- **Plugin Loader**: Updated `loader.py` to support `sys._MEIPASS`, enabling plugins bundled with PyInstaller to be correctly discovered at runtime.

### Added
- **Plugin Interface**: Added `get_features() -> List[Any]` to `PluginInterface` to support algorithm exposure.

### Fixed
- **App Initialization**: Resolved critical startup order issues in `app.py` to ensure plugins are loaded before feature manager refresh.

## [v1.2.2] - 2026-01-03

### Added
- **Phase 1: UI Slots System**: Implemented `PluginRegistry` support for injecting content into predefined UI slots (`HEADER_RIGHT`, `SIDEBAR_BOTTOM`, etc.).
- **Phase 1: React Integration**: Added support for mounting React components into UI slots using `plugin-loader.js`.
- **Phase 1: Split-Env Loader**: Implemented dual-mode plugin loading (development `plugins_dev` vs. production bundled plugins).

### Fixed
- **Critical Stability**: Fixed a major bug where double instantiation of the Flask application caused context processors (like `get_slots`) to be lost, leading to 500 Internal Server Errors.
- **Build System**: Improved robustness of `clean` operation to handle file locks on Windows (`shutil.rmtree` enhancement).

## [v1.2.0] - 2026-01-02

### Added
- **Plugin System Infrastructure**: Added "Extensions" marketplace UI in Settings.
- **Extensions UI**: Functional filter buttons (Featured, Export Tools, Themes, etc.) and real-time search filtering.
- **UI Consistency**: Standardized the Settings icon across the entire application to use the premium circular design.
- **Theme Consistency**: Unified header and brand styling across Main and Extensions pages. Fixed Theme Toggle on Extensions page.
- **Build System**: Added `make freeze` command to lock dependencies.
- **Build System**: Added `make freeze` command to lock dependencies.
- **Dependency**: Bundled `python-pptx`, `pymdown-extensions`, `Pygments` (highlighting), `htmldocx` (Word export), and `mammoth` (Word import) to prevent runtime issues.

### Fixed
- **Runtime Stability**: Fixed `TemplateNotFound` crash in standalone executable by correcting Flask path resolution for frozen environments.
- **Distribution**: Fixed missing `examples` and `docs` folders in the built executable.
- **Build System**: Removed interactive prompts from build script for cleaner automation.
- **Build System**: Added auto-kill logic to terminate previous instances before building.
- **Build System**: Added `--log` flag to capture build output to `build/build.log`.
- **UI**: Fixed visibility issue for "Save Changes" button in Workspace Settings (Light Mode).
- **UI**: Fixed text cursor appearing on static elements (enabled native-app feel).
- **UI**: Standardized version badge style on Documentation page.
- **UI**: Added consistent DocNexus branding (Logo + Name + Version) to Documentation and Viewer pages headers.
- **core**: Refactored branding logic into shared component (`components/header_brand.html`) and enabled global version context.
- **core**: Established Single Source of Truth for versioning (`docnexus/version_info.py`) and robustified build config.
- **core**: Fixed version fallback logic and added startup logging for better troubleshooting.
- **docs**: Major overhaul of project documentation (`README`, `STRUCTURE`, `BUILD`) and added `DOCNEXUS_ARCHITECTURE.md`.



## [v1.1.4] - 2026-01-02

### Added
- **Full-Text Search**: Enhanced search to browse through the content of documents (.md, .txt) in the workspace, not just filenames.
- **Search Feedback**: Added loading spinner to search icon during backend search operations.

### Fixed
- **Search Visibility**: Fixed white-on-white text issue in the search bar when using Light Mode.



## [v1.1.3] - 2026-01-02

### Added
- **Open Single File**: Added "Open File" button (Browse File) in the header to view specific documents without changing the workspace.
- **File Preview**: Implemented `/preview` support for dragging/dropping or selecting single files.



## [v1.1.2] - 2026-01-02

### Added
- **Sidebar Table of Contents**: Added a dynamic, sticky Table of Contents on the View page with nested indentation and scroll-spy highlighting.
- **Configurable Workspace**: New settings UI to change the active workspace folder directly from the application.
- **Documentation Access**: Added direct link to documentation in the header.
- **Configurable Table of Contents**: Added "Settings" menu allowing users to toggle the TOC position (Left/Right). Preference is persisted.
- **TOC Aesthetics**: Implemented direction-aware active indicator ("slider") and professional gradient styling.
- **In-Place Editor**: Implemented a rich WYSIWYG editor (Toast UI) allowing direct editing of Markdown files with "Save" and "Cancel" functionality. Includes Safe Mode read-only protection for Word documents.
- **Shared Settings Component**: Centralized the Settings Menu into a reusable component (`settings_menu.html`, `settings_menu.css`) to eliminate code duplication.

### Changed
- **UI Standardization**: Unified the styling of Theme Toggle, "Back to Hub" buttons, and Icons across Index, Docs, and View pages.
- **Sidebar Improvements**: Refined Table of Contents with visual hierarchy (tree lines, indentation), direction-aware styling, and a sleek, custom scrollbar.
- **Settings Menu Layout**: Enforced 'Outfit' font and Grid layout for the Settings Menu to ensure pixel-perfect consistency and alignment across all pages.
- **Top Button Revamp**: Transformed "Go to Top" button into a cleaner, circular glassmorphic FAB (42x42px) with FontAwesome arrow icon.
- **Edit Logic**: Improved UX by allowing the "Edit" button to toggle/cancel the editor if clicked while the editor is already open.
- **Icon Standardization**: Migrated remaining view-page icons to FontAwesome (`fas`) to ensuring uniform style and weight across the application.
- **Header Metadata**: Enhanced document header to display file size and last modification date alongside the filename.


### Fixed
- **View Page Edit/Save**: Fixed the "Edit" button selector and rectified backend save logic to support nested document paths.
- **Build System**: Resolved `python-dotenv` build warnings and cleaned up root directory clutter.
- **Workspace Configuration**: Fixed path resolution issues that caused "Workspace not configured" errors.
- **Documentation Link**: Fixed 404 error by correctly routing to the `docs` directory.
- **Port Conflict**: Improved startup reliability by handling previous instances.
- **HTML Stability**: Resolved severe corruption in `view.html`, fixed syntax errors in `docs.html` (malformed braces) and `index.html` (error handling logic).
- **Code Hygiene**: Removed unused Modal CSS and standardized theme toggle implementation across all pages to eliminate warnings.
- **TOC Logic**: Fixed critical bug where TOC position toggle failed on `docs.html` due to conflicting default classes.
- **Visual Alignment**: Resolved spacing and alignment discrepancies in settings submenu toggles.
- **Export Functionality**: Fixed broken PDF/Word export actions in `view.html` by correcting ID selectors and updating icons.
- **JS Stability**: Fixed critical JavaScript syntax error in `view.html` that caused interactive buttons (Edit, Top, Export) to fail.
- **PDF Export**: Fixed clientswide error handling to display alert messages instead of downloading corrupt files when export fails (e.g. missing wkhtmltopdf).

## [v1.0.1] - 2025-12-28

### Added
- **Project Rename**: Officially renamed from "OmniDoc" to "**DocNexus**".
- **Bootstrap Icons**: Integration of Bootstrap Icons for consistent, high-quality SVG iconography across the application.
- **Mobile Optimization**: improved responsive design with adaptive margins and typography scaling for mobile devices.
- **Unified UI**: Standardized "glassmorphic" button styling for Edit, Export, Theme Toggle, and Top buttons.

### Changed
- **Theme Toggle**: Improved icon logic to show the *target* state (Sun icon when Dark, Moon icon when Light) for better UX.
- **Icons**: Replaced all remaining emojis with professional SVG icons.
- **Margins**: Optimized document viewing margins (15% on desktop -> 5% on mobile).

### Fixed
- **URL Cleanliness**: Removed ephemeral `?smart=false` query parameter from document URLs.
- **Smart Feature**: Removed experimental "Smart Toggle" feature code and UI elements (deferred to v1.1).
- **Navigation**: Fixed floating "Top" button icon and styling.
- **Theme Icon**: Fixed critical bug where theme toggle displayed a music note icon instead of a moon icon due to Unicode mismatch.
- **Layout Redesign**: Implemented modern, centered document layout (max-width 1000px) with fixed 32px padding, replacing inconsistent percentage-based margins.
- **Project Structure**: Renamed `doc` to `docs` (standard) and refactored sample content from `workspace` to `examples` (source) -> `workspace` (release).

## [v1.0.0] - 2025-12-28
- Initial Release
