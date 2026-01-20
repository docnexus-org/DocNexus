# DocNexus Core Technical Roadmap

This roadmap outlines the architectural evolution of the DocNexus Open Source project. Our goal is to transform the core into a versatile **Microkernel Platform** for document processing.

## ✅ Phase 1: Extensibility (Completed/Maintenance)
We have successfully transitioned to a modular architecture.
*   **Plugin Registry**: fully implemented (`docnexus.features.registry`).
*   **UI Slots**: Functional injection points (`HEADER_RIGHT`, `EXPORT_MENU`).
*   **Exports**: PDF and Word export plugins are deployed and stable.

## 🚀 Phase 2: Ecosystem & Refinement (Current Focus)
We are now focusing on enriching the default experience and handling technical debt.
*   **Default Plugins**:
    *   **Themes & Icons**: Break out hardcoded themes into installable plugins.
    *   **Sidebar Enhancements**: Implement "Left/Right Shuffle" arrow for instant layout adjustment.
    *   **Editor Reliability**: Investigate backup file retention and save/zip conflicts.
*   **Advanced Features**:
    *   **RAG / Chat-with-Doc**: A local-first AI plugin to chat with the open document.
    *   **PDF Export v2**: Refine the export processing for better layout fidelity.
    *   **Smart Conversion (Experimental)**:
        *   **ASCII to Table**: Convert ASCII art tables to Markdown tables.
        *   **SIP Signaling**: Convert text-based flows to Mermaid sequence diagrams.
        *   **Network Topology**: Convert text description to node diagrams.
    *   **Universal Editor (In Progress)**:
        *   **Slots**: Decouple the editor UI. Support `EDITOR_CONTAINER` injection for PDF/Image editing.
        *   **PDF Editing**: Native-like PDF manipulation using `pdf-lib` via the new slot architecture.
        *   **Toolbar API**: Future API for plugins to register buttons (Save, Undo, Tools) in the main header.

## 🛠 Phase 3: The Pipeline Architecture (Inspired by UnifiedJS)
We will transition from monolithic rendering to a `Middleware` pipeline pattern, treating documents as data streams.
*   **Architecture**: `Parser (Markdown -> AST)` -> `Transformers (AST Modification)` -> `Compiler (AST -> HTML/PDF/DOCX)`.
*   **AST Standard**: Adopt **MDAST** (Markdown Abstract Syntax Tree) as the internal representation.
*   **Use Cases**:
    *   **Auto-Linker**: Middleware to detect "JIRA-123" and wrap it in a link node.
    *   **Sanitizer**: Middleware to strip dangerous JS nodes before compilation.
    *   **Metadata Extractor**: Middleware to harvest Frontmatter for an indexing service.

## 🧠 Phase 4: The Microkernel & Manifest (Inspired by VS Code)
We aim to decouple the "App" from its features, making the core a lightweight plugin runner.
*   **Contribution Points**: Move hardcoded menus/sidebars to a declarative `manifest.json` model (e.g., `contributes.views`, `contributes.commands`).
*   **Activation Events**: Plugins will lazy-load based on events (e.g., `onCommand:export`, `onFileType:markdown`).
*   **Universal Document Model (UDM)**:
    *   Abstract `File` access into a `Vault` interface (Inspired by Obsidian).
    *   Allow plugins to implement "Virtual File Systems" (e.g., GitHub, S3, SQL Database).
*   **Model Context Protocol (MCP)**: Native support for connecting documents to external AI models for RAG.

## 📢 Outreach
*   **Showcase**: Prepare assets for LinkedIn and GitHub launch.