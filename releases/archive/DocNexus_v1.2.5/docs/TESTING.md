# Testing Guide

## Running Tests

We provide a consistent way to run tests using the `make.cmd` utility.

### Basic Usage

Run all tests with coverage report:
```powershell
.\make.ps1 test
```

### Advanced Usage

Run a specific test module:
```powershell
.\make.ps1 test tests.test_features
```

Run a specific test file:
```powershell
.\make.ps1 test tests/test_plugin_integration.py
```

### Test Results

Every test run generates a `test_results.txt` file in the project root containing:
*   Pass/Fail status of each test.
*   Full output/tracebacks for failures.
*   Code Coverage report (percentage of code executed).

## Adding Tests

1.  Create a new test file in `tests/` starting with `test_`.
2.  Import `unittest`.
3.  Define a class inheriting from `unittest.TestCase`.
4.  Run it using `.\make.ps1 test tests.test_your_file`.

## Test Infrastructure

*   **Runner**: `scripts/run_tests.py` (Unittest) OR `pytest` (Recommended for new tests)
*   **Libraries**: `unittest`, `pytest`, `coverage`

## Current Test Modules (`tests/`)

| Module | Purpose |
| :--- | :--- |
| `test_features.py` | Core Feature Manager lifecycle and state transitions. |
| `test_loader.py` | Dependency Injection logic and plugin discovery. |
| `test_registry.py` | Unified Registry (Feature registration & slots). |
| `test_extensions_api.py` | Endpoints for installing/uninstalling plugins. |
| `test_plugin_integration.py` | End-to-end flow of loading a dummy plugin. |
| `test_pdf_safe_mode.py` | **[NEW]** Verifies PDF Safe Mode CSS sanitization logic. |
| `test_export_headless.py` | Mocked export tests. |

## running with Pytest (Recommended)

Run all tests:
```bash
python -m pytest
```

Run specific test:
```bash
python -m pytest tests/test_pdf_safe_mode.py
```
