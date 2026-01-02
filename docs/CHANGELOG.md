# Changelog

All notable changes to this project will be documented in this file.

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
