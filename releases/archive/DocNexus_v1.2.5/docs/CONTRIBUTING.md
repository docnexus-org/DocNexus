# Contributing to DocNexus

Thank you for your interest in contributing to DocNexus! We welcome contributions from everyone.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone** your fork locally:
    ```bash
    git clone https://github.com/DocNexus/DocNexus.git
    cd DocNexus
    ```
3.  **Set up the environment**:
    ```powershell
    ./make.ps1 setup
    ```

## Development Workflow

1.  Create a new branch for your feature or fix:
    ```bash
    git checkout -b feature/amazing-feature
    ```
2.  Make your changes.
3.  Run tests locally:
    ```powershell
    ./make.ps1 test
    ```
4.  Commit your changes with clear messages.

## Pull Requests

1.  Push your branch to GitHub.
2.  Open a Pull Request against the `main` branch.
3.  Describe your changes and link any relevant issues.

## Code Style

- We follow PEP 8 standards.
- Ensure all new code includes docstrings.
- Add tests for new features.

## Legal & License

### Contributor License Agreement (CLA)
By submitting a Pull Request, you agree to the terms of our [Contributor License Agreement (CLA)](CLA.md). This agreement grants us the rights to relicense your contributions, which is essential for our dual-licensing business model (Open Core + Commercial). You retain your copyright.

### License
By contributing, you agree that your contributions will be licensed under the GNU Affero General Public License v3 (AGPLv3).
