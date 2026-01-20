# PDF Editor Roadmap

This document outlines the strategic evolution of the PDF Editor capabilities within DocNexus.

## Phase 1: The Foundation (Universal IO & Annotation)
**Goal:** Enable viewing and basic annotation (Drawing/Stamping) without changing the underlying text.

*   **Architecture**:
    *   [x] **Universal IO**: Backend routes (`/raw/`, `/preview`) to handle binary PDF data.
    *   [ ] **Frontend Slots**: `view.html` must support dynamic injection of Editor UIs (replacing the default Markdown editor).
    *   [ ] **Plugin Structure**: Standalone `pdf_editor` plugin containing `pdf-lib.js` or `jspdf`.

*   **Features**:
    *   **Native Preview**: Uses browser's built-in PDF viewer (iframe) or PDF.js for rendering.
    *   **Overlay Canvas**: A transparent layer over the PDF for drawing signatures, highlights, or boxes.
    *   **"Save" Strategy**: Flattens the canvas (image) onto the PDF pages using `pdf-lib` and saves as a new version.

## Phase 2: Interactive Manipulation (Page Ops)
**Goal:** Allow users to organize the document structure.

*   **Libraries**: `pdf-lib` (JavaScript) is excellent for this.
*   **Features**:
    *   **Page Reordering**: Drag-and-drop UI to change page order.
    *   **Merge/Split**: Combine multiple PDFs or extract pages.
    *   **Rotate**: Fix scanned document orientation.
    *   **Metadata Editing**: Modify Title, Author, Subject fields.

## Phase 3: Content Editing (The "Holy Grail")
**Goal:** Direct text and image manipulation within the PDF (Adobe Acrobat style).

*   **Challenges**: font embedding, content reflow, complex vector streams.
*   **Strategy**:
    *   **Text Patching**: Whiten out existing text and overlay new text (visual hack).
    *   **Form Filling**: First-class support for AcroForms.
    *   **Image Replacement**: Swap images while preserving layout.

## Phase 4: Full "Office-Suite" Capabilities
**Goal:** Conversion and Optical Character Recognition (OCR).

*   **OCR**: Integate `tesseract.js` (client-side) or `pytesseract` (server-side) to make scanned PDFs searchable.
*   **Conversion**: PDF <-> Word/Markdown (using `pdf2docx` or `pandoc`).

---
**Technical Note on "Universal Editor"**:
The `view.html` template now uses `get_slots('EDITOR_CONTAINER')`. This allows *any* plugin (PDF, CSV, Image Editor) to inject its own dedicated UI toolset when its file type is detected, ensuring DocNexus is future-proof for any format.
