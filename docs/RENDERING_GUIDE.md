# DocNexus Copy-to-Clipboard & Export Architecture

## Philosophy: Uniformity through HTML
DocNexus relies on a "Single Source of Truth" philosophy. The HTML rendered in the web view (via `python-markdown`) is the definitive representation of the content. ALL export plugins (PDF, Word, etc.) must strive to reproduce this visual fidelity by interpreting the standard HTML structure and CSS styles.

## Rendering Pipeline

1.  **Markdown Parsing**: `python-markdown` + Extensions (Admonitions, Math, etc.) -> Standard HTML.
2.  **Web View**: Displays HTML with `theme.css`. Perfect fidelity using Chromium engine.
3.  **Export Plugins**:
    - **Input**: The same Standard HTML.
    - **Transformation**: A `transform_html_for_[service]` function cleans/simplifies HTML for specific renderer limitations (e.g., removing complex `div` nesting for `htmldocx`).
    - **Rendering**: The external library (`htmldocx`, `xhtml2pdf`) processes the simplified HTML.

## Developer Guidelines for New Features

When adding a new feature (e.g., a new Alert type), follow this checklist to ensure uniformity:

### 1. Web Implementation
-   Define the HTML output.
-   Add CSS in `theme.css`.
-   Verify it looks good in the App.

### 2. Export Support (Word/PDF)
Do NOT assume the export library supports your CSS.
-   **Check**: Does `htmldocx` support `flex`, `grid`, `::before`, or your specific `background-color`? (Spoiler: Usually No).
-   **Transform**: Update `docnexus/plugins/word_export/plugin.py` -> `transform_html_for_word`.
    -   *Example*: Convert `<div class="admonition">` to `<table>` because Word handles tables better than divs.
    -   *Example*: Convert `<span class="math">` to `<code>` block if the library doesn't support complex layout.
-   **Inject**: If the library ignores CSS (like Backgrounds in Word), override the parser.
    -   Subclass the parser (e.g., `SafeHtmlToDocx`).
    -   Inject native XML properties (`w:shd`, `w:rFonts`) corresponding to your CSS styles.

## Common Rendering Patterns

| Feature | HTML | Word Strategy | PDF Strategy |
| :--- | :--- | :--- | :--- |
| **Alerts** | `<div class="admonition">` | Convert to `Table` (1x1). Inject `w:shd` (Shading) for BG. Force Emoji font for icon. | Convert to `Table` (1x1). Flatten content to `inline` flow. |
| **Math** | `<span class="katex">` | Extract TeX source. Wrap in `Code Block` (Gray BG). | Extract TeX source. Wrap in `Code Block` (Gray BG). |
| **Highlights** | `<mark>` | Map `bg-color` to `WD_COLOR` Highlight enum. | Supports `background-color` natively. |
| **Icons** | CSS `::before` (Mask) | Hard replace with Emoji text (ℹ️) in HTML transform. | **Base64 Images**: Text Emojis fail in PDF. We inject `<img>` with Base64 PNGs. |

## Advanced Rendering Strategies (v1.2.6+)

### 1. PDF: The Table Wrapper Strategy (Emoji Fix)
**Problem**: The `xhtml2pdf` engine uses a legacy layout implementation that clips text containing emojis when they appear inside standard block elements (`<p>`, `<div>`, `<li>`), especially if `line-height` is tight.
**Solution**: We implemented a **Table Wrapper** strategy.
-   **Mechanism**: A pre-processing step wraps any block element containing emojis into a borderless, 1x1 table.
-   **Why it works**: Tables in `xhtml2pdf` trigger a different layout calculation mode that respects container boundaries more strictly, preventing the clipping overflow.
-   **Trade-off**: Slightly increased DOM complexity, but effectively invisible to the end user.

### 2. Word: Advanced Navigation (Footnotes)
**Problem**: `htmldocx` does not natively support the internal linking required for Footnotes (jumping from `fnref:1` to `fn:1` and back). It preserves the `href` but fails to create the *target* bookmark.
**Solution**: Custom OXML Injection.
-   **Mechanism**: We override `handle_starttag` to intercept named anchors (`<a name="fn:1">`).
-   **Injection**: We explicitly inject `w:bookmarkStart` and `w:bookmarkEnd` nodes into the `python-docx` paragraph object.
-   **Sanitization**: Bookmark names must be alphanumeric. We hash/sanitize IDs (e.g. `fn:1` -> `fn_1`) to ensure Word accepts them.

### 3. Mermaid: Browser Snapshotting (WYSIWYG)
**Problem**: Converting Mermaid.js (SVG) to PDF server-side is fragile. `canvg` (JS canvas rasterizer) fails on complex text, opacity, and foreignObjects.
**Solution**: Browser-as-Renderer.
-   **Mechanism**:
    1.  The User Interface renders the diagram perfectly using the browser's SVG engine.
    2.  Before export, a script captures this logical SVG and draws it to a high-resolution HTML5 Canvas.
    3.  The canvas is converted to a Base64 PNG.
    4.  We swap the live `<svg>` with this static `<img>` in the DOM clone sent to the server.
-   **Result**: The PDF generator (`xhtml2pdf`) sees a simple Image, ensuring 100% visual fidelity with what the user saw on screen.

## Troubleshooting Word Export
-   **Missing Colors**: `htmldocx` ignores most `background-color`. Use `SafeHtmlToDocx` overrides to inject `w:shd`.
-   **Missing Icons**: Word doesn't support CSS masks. Use Emojis in the text transformation.
-   **Crashes**: `htmldocx` crashes on empty styles or 3-digit hex codes. Sanitize your HTML styles before passing them.
