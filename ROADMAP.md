# DocNexus Core Technical Roadmap

This roadmap outlines the architectural evolution of the DocNexus Open Source project. Our goal is to transform the core into a versatile **Microkernel Platform** for document processing.

## 🚀 Phase 1: Extensibility (current focus)

We are moving away from hardcoded logic to a modular architecture.

* **Plugin Registry**: A standardized way to register features.
* **UI Slots**: Define "injection points" in the UI for plugins to add widgets (Sidebars, Menu items).
* **Theme System**: Allow plugins to provide complete visual overhauls.

## 🛠 Phase 2: The Pipeline Architecture

Document rendering will move to a `Middleware` pipeline pattern.

* **Render Pipeline**: `Input -> Middleware[] -> Output`.
* **Benefit**: Developers can inject steps to specialized processing (e.g., "Sanitize HTML", "Auto-link Tickets", "Extract Metadata") without forking the core.

## 🧠 Phase 3: The "Blank Slate" Microkernel

We aim to decouple the "Markdown" logic from the "App" logic.

* **Universal Document Model (UDM)**: A structured object representation of documents.
* **Manifest-driven UI**: A VS Code-style architecture where the UI is composed entirely of contributions from (default) plugins.
* **Model Context Protocol (MCP)**: Native support for connecting documents to external data models.