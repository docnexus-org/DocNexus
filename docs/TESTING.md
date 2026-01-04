# Testing Guide

## Running Tests

We provide a consistent way to run tests using the `make.cmd` utility.

### Basic Usage

Run all tests with coverage report:
```cmd
.\make.cmd test
```

### Advanced Usage

Run a specific test module:
```cmd
.\make.cmd test tests.test_features
```

Run a specific test file:
```cmd
.\make.cmd test tests/test_plugin_integration.py
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
4.  Run it using `.\make.cmd test tests.test_your_file`.

## Test Infrastructure

*   **Runner**: `scripts/run_tests.py`
*   **Libraries**: `unittest`, `coverage`
*   **Fixtures**: `tests/fixtures/` contains dummy assets (like `dummy_plugin`) for integration tests.
