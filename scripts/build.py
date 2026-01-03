#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import argparse
import platform
from pathlib import Path

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BUILD_DIR = PROJECT_ROOT / "build"
OUTPUT_DIR = BUILD_DIR / "output"
VENV_DIR = BUILD_DIR / "venv"

# OS-Specific Paths
IS_WINDOWS = sys.platform.startswith("win")
PYTHON_EXEC = VENV_DIR / "Scripts" / "python.exe" if IS_WINDOWS else VENV_DIR / "bin" / "python3"
PYINSTALLER_EXEC = VENV_DIR / "Scripts" / "pyinstaller.exe" if IS_WINDOWS else VENV_DIR / "bin" / "pyinstaller"

# Colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    if IS_WINDOWS: # Simple disable for stock cmd (PowerShell handles it mostly fine now)
        try:
            import colorama
            colorama.init()
        except ImportError:
            pass

# --- Globals ---
LOG_FILE_HANDLE = None

def log(msg, color=Colors.OKBLUE):
    """Log message to console and optionally to file."""
    # Console output with color
    print(f"{color}{msg}{Colors.ENDC}")
    
    # File output (clean text)
    if LOG_FILE_HANDLE:
        try:
            # Strip ANSI codes for log file
            clean_msg = msg
            LOG_FILE_HANDLE.write(f"{clean_msg}\n")
            LOG_FILE_HANDLE.flush()
        except Exception:
            pass

def run(cmd, cwd=PROJECT_ROOT, capture=False):
    """Run a command safely."""
    cmd_str = " ".join([str(x) for x in cmd])
    log(f"Running: {cmd_str}", Colors.OKCYAN)
    
    # Determine stdout/stderr targets
    stdout_target = LOG_FILE_HANDLE if LOG_FILE_HANDLE else None
    stderr_target = LOG_FILE_HANDLE if LOG_FILE_HANDLE else None

    try:
        if capture:
            return subprocess.check_output(cmd, cwd=cwd, text=True)
        
        # If logging to file, we redirect stdout/stderr there. 
        # Note: This effectively silences console output for the subprocess.
        return subprocess.check_call(cmd, cwd=cwd, stdout=stdout_target, stderr=stderr_target)
    except subprocess.CalledProcessError as e:
        log(f"Error running command: {cmd_str}", Colors.FAIL)
        sys.exit(e.returncode)

# --- Tasks ---

def clean():
    """Remove build artifacts."""
    log("Cleaning build artifacts...", Colors.WARNING)
    dirs_to_clean = [OUTPUT_DIR, BUILD_DIR / "temp", BUILD_DIR / "spec"]
    for d in dirs_to_clean:
        if d.exists():
            log(f"Removing {d}")
            shutil.rmtree(d, ignore_errors=True)

def setup():
    """Create virtual environment and install dependencies."""
    log("Setting up build environment...")
    
    # 1. Create Venv
    if not VENV_DIR.exists():
        log(f"Creating venv at {VENV_DIR}", Colors.OKGREEN)
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)], stdout=LOG_FILE_HANDLE, stderr=LOG_FILE_HANDLE)
    else:
        log("Venv already exists.", Colors.OKGREEN)

    # 2. Install Deps
    log("Installing dependencies...")
    run([str(PYTHON_EXEC), "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools"])
    run([str(PYTHON_EXEC), "-m", "pip", "install", "-e", "."])
    run([str(PYTHON_EXEC), "-m", "pip", "install", "pyinstaller"])
    
    log("Setup complete!", Colors.BOLD)

def kill_existing_process(app_name):
    """Kill the running executable if it exists."""
    exe_name = f"{app_name}.exe" if IS_WINDOWS else app_name
    log(f"Ensuring {exe_name} is not running...", Colors.WARNING)
    try:
        if IS_WINDOWS:
            subprocess.call(["taskkill", "/F", "/IM", exe_name], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        else:
            subprocess.call(["pkill", "-f", exe_name], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except Exception:
        pass

def build():
    """Build the standalone executable."""
    # Get Version (duplicate logic, but needed for name)
    try:
        init_file = PROJECT_ROOT / "docnexus" / "version_info.py"
        with open(init_file) as f:
            for line in f:
                if "__version__" in line:
                    version = line.split("'")[1]
                    break
    except Exception:
        version = "0.0.0"
    app_name = f"DocNexus_v{version}"
    
    kill_existing_process(app_name)
    
    log("Building DocNexus...")
    
    # Base PyInstaller Args
    cmd = [
        str(PYINSTALLER_EXEC),
        "--noconfirm",
        "--clean",
        "--name", app_name,
        "--onefile",
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(BUILD_DIR / "temp"),
        "--specpath", str(BUILD_DIR / "spec"),
        "--paths", str(PROJECT_ROOT),
        "--icon", str(PROJECT_ROOT / "docnexus" / "static" / "logo.ico"),
        "--add-data", f"{PROJECT_ROOT / 'docnexus' / 'templates'}{os.pathsep}docnexus/templates",
        "--add-data", f"{PROJECT_ROOT / 'docnexus' / 'static'}{os.pathsep}docnexus/static",
    ]

    # Hidden Imports
    hidden_imports = [
        "docnexus.version_info",
        "docnexus.features", "docnexus.features.smart_convert",
        "engineio.async_drivers.threading",
        "pymdownx", "pymdownx.betterem", "pymdownx.superfences",
        "pymdownx.tabbed", "pymdownx.details", "pymdownx.magiclink",
        "pymdownx.tasklist", "pymdownx.arithmatex", "pymdownx.highlight",
        "pymdownx.inlinehilite", "pymdownx.keys", "pymdownx.smartsymbols",
        "pymdownx.snippets", "pymdownx.tilde", "pymdownx.caret",
        "pymdownx.mark", "pymdownx.emoji", "pymdownx.saneheaders"
    ]
    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # Premium Plugin Logic
    plugins_dev = PROJECT_ROOT / "docnexus" / "plugins_dev"
    if plugins_dev.exists():
        log(" [PREMIUM] Detected plugins_dev. Including in build...", Colors.OKGREEN)
        cmd.extend(["--add-data", f"{plugins_dev}{os.pathsep}docnexus/plugins_dev"])
        
    # Entry Point (Switch to CLI for correct arg parsing)
    cmd.append(str(PROJECT_ROOT / "docnexus" / "cli.py"))
    
    run(cmd)
    
    # Copy Examples Folder for Distribution
    examples_src = PROJECT_ROOT / "examples"
    examples_dst = OUTPUT_DIR / "examples"
    if examples_src.exists():
        log(f"Copying examples to dist: {examples_dst}", Colors.OKGREEN)
        if examples_dst.exists():
            shutil.rmtree(examples_dst)
        shutil.copytree(examples_src, examples_dst)

    # Copy Docs Folder for Distribution
    docs_src = PROJECT_ROOT / "docs"
    docs_dst = OUTPUT_DIR / "docs"
    if docs_src.exists():
        log(f"Copying docs to dist: {docs_dst}", Colors.OKGREEN)
        if docs_dst.exists():
            shutil.rmtree(docs_dst)
        shutil.copytree(docs_src, docs_dst)
        
    log(f"Build Complete: {OUTPUT_DIR / app_name}", Colors.OKGREEN)

def release():
    """Build and Zip."""
    build()
    log("Creating Release Zip...")
    # TODO: Implement zipping logic similar to make.ps1
    pass

def run_dev():
    """Run from source."""
    run([str(PYTHON_EXEC), str(PROJECT_ROOT / "run.py")])

# --- Main CLI ---

def main():
    global LOG_FILE_HANDLE
    parser = argparse.ArgumentParser(description="DocNexus Build System")
    parser.add_argument("command", choices=["setup", "build", "clean", "run", "release"], help="Command to run")
    parser.add_argument("--log", action="store_true", help="Enable logging to build/build.log")
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    
    if args.log:
        log_path = BUILD_DIR / "build.log"
        print(f"Logging enabled. Writing to {log_path}")
        LOG_FILE_HANDLE = open(log_path, "w", encoding="utf-8")

    try:
        if args.command == "setup":
            setup()
        elif args.command == "clean":
            clean()
        elif args.command == "build":
            if not PYTHON_EXEC.exists():
                print("Error: Venv not found. Run 'setup' first.")
                sys.exit(1)
            build()
        elif args.command == "run":
            run_dev()
        elif args.command == "release":
            release()
    finally:
        if LOG_FILE_HANDLE:
            LOG_FILE_HANDLE.close()

if __name__ == "__main__":
    main()
