# ~~Verified Edits~~

# DocNexus

> \*\*The Ultimate All-in-One Document Engine.\*\**Authority. Universality. Power.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/DocNexus-org/DocNexus)

DocNexus is an enterprise-grade, open-source documentation platform designed to handle **any** input and deliver **any** output. It transforms static Markdown into a dynamic, executive-ready presentation layer with intelligent diagramming and structure awareness.

## 🔮 Future Roadmap

* **AI-Powered Generation**: Zero-touch creation of PPTs and document variations.
* **MCP Server**: Function as a Model Context Protocol (MCP) server to provide documentation context to LLMs.
* **Plugin Ecosystem**: Extensions for any data source.

## 🚀 The Verdict: Why DocNexus?

* **Scalability**: Built to evolve. Whether you're adding AI features or supporting new formats, "Omni" fits perfectly.
* **Professionalism**: An enterprise-grade solution that feels at home in the boardroom or the dev lab.
* **Clarity of Mission**: A true "one-stop shop" for documentation.

***

## ✨ Features

### 📄 Universal Format Support

DocNexus handles more than just Markdown.

* **Input Formats**: `.md`, `.txt`, and **Word Documents (.docx)**.
* **Export Capabilities**: Convert your interactive docs to **PDF** or **Word** for offline distribution.

### 🧠 Intelligent Conversions

DocNexus doesn't just display text; it understands it.

* **Smart Sequence Diagrams**: Automatically converts text-based call flows or conversations into interactive Mermaid sequence diagrams.
* **Network Topology**: Recognizes ASCII diagrams and transforms them into professional network topology visualizations.
* **Data Tables**: Instantly formats ASCII tables into sortable, clear data grids.

### 🎨 Visual Excellence

* **Glassmorphism UI**: Modern, translucent aesthetics that feel premium.
* **Smart TOC**: A universal, tree-based Table of Contents that automatically organizes even the most complex documents.
* **Syntax Highlighting**: Optimized for over 50+ languages including log files and configs.

### 🛡️ Robust & Future-Proof

* **Python 3.10+ Core**: Built on modern, stable foundations.
* **Production Ready**: Includes `make` automation for building standalone executables.
* **Universal Deployment**: Run as a CLI, a web server, or a standalone desktop app.

***

## ⚡ Quick Start

### 1-Click Run (Windows)

Double-click `start.bat` to launch the server instantly.

### CLI Installation

```bash
pip install DocNexus
DocNexus start
```

### From Source

```bash
git clone https://github.com/DocNexus-org/DocNexus.git
cd DocNexus
pip install -e .
python run.py
# or
./make.ps1 setup
./make.ps1 start
```

***

## 📚 Documentation

Detailed guides are available in the `doc/` directory:

* [User Guide](doc/USER_GUIDE.md)
* [Architecture Overview](doc/ARCHITECTURE.md)
* [Contributing Guidelines](CONTRIBUTING.md)

***

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

## 📄 License

DocNexus is proudly open source under the [MIT License](LICENSE).