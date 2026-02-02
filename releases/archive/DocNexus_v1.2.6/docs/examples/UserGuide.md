# DocNexus - Complete Guide Complete

**Version 1.0.0**

A professional, lightweight web-based markdown documentation viewer with a modern UI, theme toggle, and smart navigation features.

* help
* *Ok*
* **Please**

***

## Table of Contents

* [Features](#features)
* [Quick Start](#quick-start)
* [Installation](#installation)
* [Usage Guide](#usage-guide)
* [Configuration](#configuration)
* [Troubleshooting](#troubleshooting)
* [FAQ](#faq)
* [Technical Architecture](#technical-architecture)

***

## Features

### Core Features

* 📄 **Automatic Markdown Rendering** \- Converts \.md and \.markdown files to beautifully formatted HTML
* 📁 **Folder Organization** \- Automatically organizes files by folder with collapsible sections
* 🔍 **Smart Navigation** \- Clickable table of contents with automatic section expansion
* 🎨 **Theme Toggle** \- Switch between light and dark themes with persistent preference
* 📱 **Responsive Design** \- Adapts to any screen size with tile\-based grid layout
* ⚡ **One-Click Startup** \- Simple batch script to launch the server and browser

### Document Features

* Collapsible H1 and H2 sections
* Syntax-highlighted code blocks
* Formatted tables, lists, and blockquotes
* Smooth scrolling and animations
* File metadata display (size, modified date)

### Standard Processing Features (Always Active)

Every document automatically receives these enhancements:

#### 1. **Intelligent Table of Contents (TOC)**

* **Universal Algorithm**: Tree-based TOC generation works with any document structure
* **Automatic Numbering**: Clean section numbers (1, 1.1, 1.2, 2, 2.1, etc.)
* **Visual Hierarchy**: Progressive font sizing and indentation by nesting level
* **Collapsible Sections**: Toggle buttons on items with children
* **Smart Cleanup**: Removes markdown formatting (\*\*bold\*\*, \`code\`) and numeric prefixes from TOC text
* **Proper Nesting**: Handles all heading levels (H1→H2→H3→H4→H5→H6)
* **No Duplicates**: Prevents multiple sections numbered "1" in complex documents

#### 2. **Heading Normalization**

* Detects ATX headings (`# Title`), Setext headings (`Title\n===`), Title Case, and numbered formats
* Adds consistent anchor IDs for deep linking
* Handles numeric prefixes (1., 2.1), Roman numerals (I., II.), and letter lists (A., B.)

#### 3. **Attribute Sanitization**

* Removes stray `{#anchor}` tags from appearing in document text
* Keeps anchors only in headings for proper navigation
* Prevents anchor IDs from showing as literal text

#### 4. **Code Block Detection**

* Automatically identifies code block types: programming code, sequence diagrams, network diagrams
* Enables smart conversion features when toggled on

### Experimental Features (Smart Toggle)

Enable with **?smart=true** query parameter:

#### **SMART\_TABLES** ✅ Production

* Converts ASCII tables (space-separated columns) to proper Markdown tables
* Auto-detects column boundaries
* Creates formatted headers with separators

#### **SMART\_SEQUENCE\_DIAGRAMS** ✅ Production

* Auto-converts text-based message flows to Mermaid sequence diagrams
* Recognizes standard interactions and protocol messages
* Detects response codes and status updates
* Context-aware: only converts when heading suggests signaling/flow content
* Excludes programming code to prevent data loss

#### **SMART\_TOPOLOGY** 🚧 Work in Progress

* Converts ASCII network diagrams to Mermaid flowcharts
* Current: Basic node detection
* Planned: Connection parsing, port mapping, protocol labels, bidirectional flows

### Markdown Support

* Tables with proper formatting
* Fenced code blocks with language-specific highlighting
* Definition lists and footnotes
* Auto-generated table of contents
* Inline and block-level formatting

***

## Quick Start

### For Windows Users (Easiest Method)

1. **Double-click** `start.bat` in the project folder
2. The script will:
    * Check for Python installation
    * Install required dependencies
    * Start the server
    * Open your browser to http://localhost:8000

That's it! Your documentation viewer is now running.

### Manual Start

```powershell
# Install dependencies
pip install -r requirements.txt

# Start the server
python run.py
```

Then open your browser to: http://localhost:8000

***

## Installation

### Prerequisites

* **Python 3.7 or higher** - [Download Python](https://www.python.org/downloads/)
* **pip** (included with Python)
* **Web Browser** (Chrome, Firefox, Edge, Safari)

### Step-by-Step Installation Steps

1. **Download/Clone the Project**

    ```powershell
    # If using git
    git clone <repository-url>
    cd DocNexus
    ```
2. **Verify Python Installation**

    ```powershell
    python --version
    # Should show Python 3.7 or higher
    ```
3. **Install Dependencies**

    ```powershell
    pip install -r requirements.txt
    ```

    This installs:
    * Flask 3.0.0 - Web framework
    * markdown 3.5.1 - Markdown processor
    * Pygments 2.17.2 - Syntax highlighting
    * pymdown-extensions 10.7 - Additional markdown features
4. **Verify Installation**

    ```powershell
    python run.py
    ```

    You should see:

    ```
    * Running on http://127.0.0.1:8000
    * Debug mode: on
    ```

***

## Usage Guide

### Adding Your Documentation

1. **Place markdown files** in the `markdown_files/` directory

    ```
    markdown_files/
    ├── getting-started.md
    ├── api-reference.md
    └── tutorials/
        ├── basics.md
        └── advanced.md
    ```
2. **Supported file extensions**: `.md` and `.markdown`
3. **Files appear automatically** \- No configuration needed\!

### Organizing with Folders

Create subfolders to organize your documentation:

```
markdown_files/
├── installation/
│   ├── windows.md
│   └── linux.md
├── guides/
│   ├── beginner.md
│   └── advanced.md
└── api/
    └── reference.md
```

The viewer will:

* Group files by folder
* Show folder names as headers
* Display file count per folder
* Allow collapsing/expanding each folder

### Navigating Documents

#### File Browser (Home Page)

* **Click folder headers** to expand/collapse folders
* **Click file cards** to view the document
* **View metadata** \- File size and last modified date shown on each card

#### Document Viewer

* **Back button** \- Return to file browser
* **Collapsible sections** \- Click H1/H2 headers to collapse content
* **Table of contents** \- Click any TOC entry to jump to that section
* **Theme toggle** \- Switch between light/dark mode \(top\-right corner\)

### Using the Theme Toggle

1. **Click the theme button** in the top-right corner
    * 🌙 Moon icon = Switch to Dark mode
    * ☀️ Sun icon = Switch to Light mode
2. **Your preference is saved** automatically and persists across sessions

***

## Configuration

### Server Configuration

Edit `DocNexus/app.py` to customize:

```python
# Change port (default: 8000)
app.run(host='0.0.0.0', port=8000, debug=True)

# Disable debug mode for production
app.run(host='0.0.0.0', port=8000, debug=False)
```

### Markdown Files Location

By default, files are read from `markdown_files/` directory. To change, edit `md_viewer/app.py`:

```python
# Modify the MD_FOLDER constant
MD_FOLDER = PROJECT_ROOT / 'markdown_files'
```

### Supported Markdown Extensions

The viewer enables these markdown extensions by default:

* `fenced_code` \- Code blocks with triple backticks
* `tables` \- GitHub\-style tables
* `nl2br` \- Newlines to line breaks
* `sane_lists` \- Better list handling
* `codehilite` \- Code syntax highlighting
* `toc` \- Table of contents generation
* `extra` \- Extra features \(definition lists\, footnotes\, etc\.\)
* `attr_list` \- HTML attributes in markdown

### Customizing Appearance

#### Colors and Theme

Edit `md_viewer/templates/index.html` or `md_viewer/templates/view.html` to modify CSS variables:

```css
:root {
    --primary: #6366f1;        /* Primary color */
    --secondary: #ec4899;      /* Secondary color */
    --background: #ffffff;     /* Background color */
    --text-primary: #0f172a;   /* Text color */
    /* ... more variables ... */
}
```

#### Grid Layout

Modify the tile layout in `md_viewer/templates/index.html`:

```css
.file-grid {
    grid-template-columns: repeat(4, 1fr);  /* 4 columns */
    gap: 20px;
}
```

***

## Troubleshooting

### Server Won't Start

**Problem**: `python: command not found` or `python is not recognized`

**Solution**:

* Install Python from [python.org](https://www.python.org/downloads/)
* Ensure "Add Python to PATH" is checked during installation
* Restart your terminal/command prompt

***

**Problem**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:

```powershell
pip install -r requirements.txt
```

***

**Problem**: Port 8000 is already in use

**Solution**:

1. Change the port in `run.py`:

    ```python
    app.run(debug=True, host='localhost', port=8001)
    ```
2. Or kill the process using port 8000:

    ```powershell
    # Windows
    netstat -ano | findstr :8000
    taskkill /PID <process_id> /F
    ```

***

### Files Not Showing

**Problem**: My markdown files don't appear in the browser

**Solution**:

1. Verify files are in `markdown_files/` directory
2. Check file extensions are `.md` or `.markdown`
3. Refresh your browser (F5)
4. Check terminal for error messages

***

### Markdown Not Rendering Correctly

**Problem**: Tables or code blocks don't display properly

**Solution**:

1. Ensure you're using proper markdown syntax
2. For tables, verify proper alignment:

    ```markdown
    | Header 1 | Header 2 |
    |----------|----------|
    | Cell 1   | Cell 2   |
    ```
3. For code blocks, use triple backticks:

    ```markdown
    ```python
    print("Hello World")
    ```

    ```
    
    ```

***

### Theme Not Persisting

**Problem**: Theme resets to light mode after closing browser

**Solution**:

* Check browser's localStorage is enabled
* Try a different browser
* Clear browser cache and cookies

***

## FAQ

### Q: Can I use this for large documentation sets?

**A**: Yes! The viewer efficiently handles hundreds of markdown files with recursive folder scanning.

***

### Q: Does it support images in markdown?

**A**: Yes! Use standard markdown image syntax:

```markdown
![Alt text](path/to/image.png)
```

Place images in the `markdown_files/` directory or use absolute URLs.

***

### Q: Can I edit markdown files through the web interface?

**A**: No, version 1.0.0 is read-only. Edit files with your preferred text editor, and they'll update automatically when you refresh the browser.

***

### Q: Is this suitable for production/team use?

**A**: This version is designed for local/individual use. For production:

* Disable debug mode: `app.run(debug=False)`
* Use a production WSGI server like Gunicorn
* Add authentication if exposing to network

***

### Q: Can I customize the look and feel?

**A**: Yes! The CSS is in the `md_viewer/templates/` HTML files. Modify the `:root` CSS variables to change colors, fonts, spacing, etc.

***

### Q: What markdown syntax is supported?

**A**: Full CommonMark + GitHub Flavored Markdown including:

* Headers, paragraphs, emphasis
* Lists (ordered, unordered, nested)
* Links and images
* Code blocks with syntax highlighting
* Tables
* Blockquotes
* Horizontal rules
* Definition lists
* Footnotes

***

## Technical Architecture

### Technology Stack

* **Backend**: Flask 3.0.0 (Python web framework)
* **Markdown Processing**: Python-Markdown 3.5.1
* **Syntax Highlighting**: Pygments 2.17.2 + Highlight.js
* **Frontend**: Vanilla JavaScript, HTML5, CSS3
* **Fonts**: Inter (UI), JetBrains Mono (code)
* **Templating**: Jinja2

### File Structure

```
DocNexus/
├── DocNexus/                # Main package
│   ├── __init__.py          # Version info
│   ├── app.py               # Flask application
│   ├── cli.py               # CLI interface
│   └── templates/           # HTML templates
│       ├── index.html       # File browser
│       ├── view.html        # Document viewer
│       └── docs.html        # Documentation page
├── markdown_files/          # Your markdown files
├── doc/                     # Project documentation
│   ├── USER_GUIDE.md       # This file
│   ├── CHANGELOG.md        # Release history
│   └── VERSION.md          # Version management
├── run.py                   # Launch script
├── start.bat               # Windows startup
├── setup.py                # Package setup
├── requirements.txt        # Dependencies
└── README.md               # Quick reference
```

### How It Works

1. **File Discovery**: Scans `markdown_files/` recursively using `Path.rglob('*.md')`
2. **Metadata Collection**: Gathers file size, modified date, folder structure
3. **Rendering**:
    * Index page lists all files grouped by folder
    * View page converts markdown to HTML with extensions
4. **Client-Side**: JavaScript adds interactivity (collapsible sections, TOC, theme toggle)
5. **Theme System**: CSS variables + data attributes for light/dark switching

### Key Functions

**Backend (app.py)**:

* `get_markdown_files()` \- Recursively scans for markdown files
* `convert_md_to_html()` \- Converts markdown to HTML with extensions
* Route handlers for `/` (index), `/file/<path>` (viewer), `/docs` (documentation)

**Frontend JavaScript**:

* `toggleTheme()` \- Switches between light/dark themes
* `toggleFolder()` \- Expands/collapses folder sections
* `makeClickable()` \- Makes TOC entries navigable
* `findHeaderByText()` \- Smart header matching for TOC

### Performance Considerations

* Files are read on-demand (not cached in memory)
* Recursive scanning is fast for typical documentation sets (<1000 files)
* No database required - pure filesystem-based
* Client-side rendering for interactive features

***

## Support & Contribution

### Getting Help

1. Check this documentation
2. Review the [CHANGELOG.md](CHANGELOG.md) for known issues
3. Examine browser console for JavaScript errors
4. Check Flask terminal output for backend errors

### Reporting Issues

When reporting issues, include:

* Operating System and version
* Python version (`python --version`)
* Browser and version
* Error messages (terminal + browser console)
* Steps to reproduce

***

## License

This project is internal tooling for documentation management.

***

**Version**: 1.0.0**Last Updated**: December 25, 2025**Maintained By**: DocNexus Maintainers