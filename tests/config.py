
# Global configuration for Test Suite
# Use this module to centralize port, host, and URL definitions
# to ensure consistency across python-based tests and external runners.

TEST_HOST = "localhost"
TEST_PORT = 8000
BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"

# Timeouts
SERVER_START_TIMEOUT = 10
REQUEST_TIMEOUT = 5
