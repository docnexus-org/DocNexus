import sys
import pytest
from pathlib import Path
import datetime
import subprocess
import re
import time

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
try:
    from tests.config import TEST_PORT, SERVER_START_TIMEOUT
except ImportError:
    print("Warning: Could not import tests.config. Using defaults.")
    TEST_PORT = 8000
    SERVER_START_TIMEOUT = 10

TESTS_DIR = PROJECT_ROOT / 'tests'
OUTPUT_FILE = TESTS_DIR / 'latest_results.log'

def run_tests_with_pytest(args):
    """
    Runs all tests using pytest and pipes output to tests/latest_results.log.
    """
    print(f"Running tests via Pytest...")
    print(f"Output will be saved to: {OUTPUT_FILE}")

    # We will use simple stdout/stderr redirection at the Python level
    # because pytest writes to sys.stdout/sys.stderr
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Test Run: {datetime.datetime.now()}\n")
        f.write("="*60 + "\n\n")
        f.flush()
        
        # Redirection Context
        class Tee(object):
            def __init__(self, *files):
                self.files = files
            def write(self, obj):
                for f in self.files:
                    f.write(obj)
                    f.flush()
            def flush(self):
                for f in self.files:
                    f.flush()
            def isatty(self):
                return False

        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # We redirect stdout/stderr to both console AND file
        sys.stdout = Tee(sys.stdout, f)
        sys.stderr = Tee(sys.stderr, f)
        
        try:
            # Run Pytest on 'tests' directory
            # We add '-ra' to show summary of (r)easons for (a)ll except passed
            exit_code = pytest.main(["-v", "-ra", str(TESTS_DIR)] + args)
        finally:
            # Restore
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            
        f.write("\n" + "="*60 + "\n")
        f.write(f"Run Completed. Exit Code: {exit_code}\n")
        
    return exit_code == 0

def kill_process_on_port(port):
    """
    Finds and kills any process listening on the specified port (Windows only).
    """
    print(f"Checking for processes on port {port}...")
    try:
        # Find PID using netstat
        CMD_FIND = f"netstat -ano | findstr :{port}"
        
        # We use shell=True to allow piping logic
        output = subprocess.check_output(CMD_FIND, shell=True).decode()
        
        if not output:
            print(f"No process found on port {port}.")
            return

        lines = output.strip().split('\n')
        killed_pids = set()

        for line in lines:
            # content looks like:  TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       1234
            parts = re.split(r'\s+', line.strip())
            if len(parts) > 4:
                pid = parts[-1]
                if pid not in killed_pids and pid != "0":
                    print(f"Killing PID {pid} listening on port {port}...")
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True)
                    killed_pids.add(pid)
        
        # Give OS time to release port
        time.sleep(2)
        
    except subprocess.CalledProcessError:
        # returns non-zero if findstr finds nothing
        print(f"No process found on port {port}.")
    except Exception as e:
        print(f"Warning: Failed to kill process on port {port}: {e}")

def start_server():
    """Starts the DocNexus server in a background process."""
    print(f"Starting server on port {TEST_PORT}...")
    # Adjust command if needed (e.g. using specific python env)
    # Using sys.executable ensures we use the same python as the runner (venv)
    cmd = [sys.executable, str(PROJECT_ROOT / 'run.py')]
    
    # We pipe stdout/stderr to suppress noise or capture for debugging if needed
    # using creationflags=subprocess.CREATE_NEW_PROCESS_GROUP on Windows to handle signals if needed,
    # but basic Popen should work for kill()
    process = subprocess.Popen(cmd, cwd=PROJECT_ROOT) # Inherit stdout/stderr for debugging
    return process

def wait_for_server(port, timeout=10):
    """Waits for the server to be willing to accept connections."""
    print(f"Waiting for server detection on port {port}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Try connect to port
            import socket
            with socket.create_connection(("localhost", port), timeout=1):
                print("Server is up!")
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.5)
            
    return False

if __name__ == "__main__":
    # Ensure environment is clean before starting tests
    try:
        kill_process_on_port(TEST_PORT)
    except NameError:
        kill_process_on_port(8000)

    server_process = start_server()
    
    try:
        if not wait_for_server(TEST_PORT, timeout=SERVER_START_TIMEOUT):
            print("Error: Server failed to start within timeout.")
            if server_process.poll() is not None:
                print(f"Server process exited with code {server_process.returncode}")
            server_process.terminate()
            sys.exit(1)

        # Allow passing arguments to pytest, e.g. python scripts/run_tests.py -v -k "test_something"
        args = sys.argv[1:]
        
        # Filter out 'test' if it was passed by make.cmd wrapper
        if args and args[0] == "test":
            args.pop(0)
        
        # Run tests
        success = run_tests_with_pytest(args)
        
    finally:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()
        # Double check cleanup
        kill_process_on_port(TEST_PORT)

    sys.exit(0 if success else 1)
