# DocNexus - Complete Guide

**Version 1.2.4**

A professional, enterprise-grade documentation platform with a modern UI, integrated editing, smart diagrams, and robust export capabilities.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Editing & Management](#editing--management)
- [Exporting](#exporting)
- [Plugins](#plugins)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Technical Architecture](#technical-architecture)

---

## Features

### Core Features
- 📄 **Universal Format** - Renders Markdown (.md) and Word (.docx) files natively.
- ✏️ **Live Editing** - Integrated WYSIWYG editor for Markdown files.
- 🔍 **Smart Navigation** - Tree-based sidebar navigation and automatic Table of Contents.
- 🎨 **Theme Toggle** - Professional Light/Dark modes with glassmorphism UI.
- 📱 **Responsive** - Adapts layout for mobile, tablet, and desktop.
- 🔌 **Plugin System** - Extensible architecture for adding features and UI slots.

### Intelligent Conversions
- **Smart Sequence Diagrams**: Auto-converts text interactions into Mermaid sequence diagrams.
- **Smart Topology**: Transforms ASCII network diagrams into visual topology graphs.
- **Smart Tables**: Formats ASCII tables into sortable data grids.

### Export Capabilities
- **Word Export (.docx)**: High-fidelity export including images, tables, and clickable Table of Contents.
  - *Note: SVG images are automatically filtered out to ensure compatibility.*
- **PDF Export**: Browser-based PDF generation (Ctrl+P) or server-side (plugin dependent).

---

## Quick Start

### Windows (One-Click)
Double-click `make.cmd` in the project root:
```cmd
make run      # Starts the server at http://localhost:8000
make build    # Creates a standalone executable in build/output/
```

### CLI
```bash
pip install docnexus
docnexus start
```

---

## Usage Guide

### Organizing Documentation
DocNexus uses a file-system based approach. Simply place your files in the `examples/` or `markdown_files/` directory (configurable).

```
root/
├── Getting Started/
│   ├── Installation.md
│   └── Config.md
├── API/
│   └── Endpoints.md
└── Welcome.md
```

### Editing Documents
DocNexus v1.2.4 supports in-browser editing for Markdown files.
1. Navigate to any `.md` file.
2. Click the **Edit** (Pen) icon in the top header.
3. Use the WYSIWYG editor to make changes.
4. Click **Save** to persist changes to disk.

### Exporting Documents
You can export any document for offline sharing:
1. Click the **Download** icon in the header.
2. Select **Word (.docx)** or **PDF**.
   - **Word**: Generates a native `.docx` file with styles, images, and TOC.
   - **PDF**: Uses print-to-pdf styling.

> **Note on Images**: For robust Word exports, avoid using SVG images (badges), as Word does not support them natively. DocNexus will replace them with placeholders to prevent errors.

---

## Plugins

DocNexus uses a **Passive Plugin Architecture**. Plugins are located in `docnexus/plugins/`.

### Built-in Plugins
- **word_export**: Handles `.docx` generation.
- **auth**: (Optional) Provides user authentication.

### Installing Plugins
Simply drop the plugin folder into `docnexus/plugins/`. The system auto-discovers features.

---

## Configuration

Settings are managed in `docnexus/config.py` or via environment variables.

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Web server port | 8000 |
| `DOCS_DIR` | Directory to scan | `./` |
| `THEME` | Default UI theme | `light` |

---

## Troubleshooting

### "Export Error" in Word
- **Cause**: Often caused by incompatible image formats (SVG) or unreachable external URLs.
- **Solution**: v1.2.4 automatically handles these by using placeholders. Check the document for `[Export Error]` text for specific traceback details.

### "UnrecognizedImageError"
- **Cause**: `python-docx` cannot read the image format.
- **Solution**: Ensure you are using the latest version of DocNexus which filters unsupported formats.

### Missing Table of Contents
Ensure your Markdown headers (`#`, `##`) are properly formatted. The TOC is generated automatically from these headers.

---

## Technical Architecture

- **Backend**: Flask 3.3.0
- **Frontend**: Jinja2 + Vanilla JS + Tailwind-inspired CSS
- **Registry**: Singleton `PluginRegistry` (`docnexus.features.registry`)
- **Dependency Injection**: `docnexus.core.loader` injects dependencies into plugins.

### Version 1.2.4 Changelog
- **Unified Registry**: Solved split-brain issues between Core and feature plugins.
- **Word Export**: Added robust image handling (timeout, SVG filter) and TOC integration.
- **UI**: Added `docnexus/templates/view.html` specific slots (`EXPORT_MENU`, `HEADER_RIGHT`).
