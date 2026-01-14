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
| **Alerts** | `<div class="admonition">` | Convert to `Table` (1x1). Inject `w:shd` (Shading) for BG. Force Emoji font for icon. | Supports `div` bg/border natively. |
| **Math** | `<span class="katex">` | Extract TeX source. Wrap in `Code Block` (Gray BG). | Render formatting or image (Current WIP). |
| **Highlights** | `<mark>` | Map `bg-color` to `WD_COLOR` Highlight enum. | Supports `background-color` natively. |
| **Icons** | CSS `::before` (Mask) | Hard replace with Emoji text (ℹ️) in HTML transform. | Supports CSS pseudo-elements. |

## Troubleshooting Word Export
-   **Missing Colors**: `htmldocx` ignores most `background-color`. Use `SafeHtmlToDocx` overrides to inject `w:shd`.
-   **Missing Icons**: Word doesn't support CSS masks. Use Emojis in the text transformation.
-   **Crashes**: `htmldocx` crashes on empty styles or 3-digit hex codes. Sanitize your HTML styles before passing them.
