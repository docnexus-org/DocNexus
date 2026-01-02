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

def log(msg, color=Colors.OKBLUE):
    print(f"{color}{msg}{Colors.ENDC}")

def run(cmd, cwd=PROJECT_ROOT, capture=False):
    """Run a command safely."""
    cmd_str = " ".join([str(x) for x in cmd])
    log(f"Running: {cmd_str}", Colors.OKCYAN)
    try:
        if capture:
            return subprocess.check_output(cmd, cwd=cwd, text=True)
        return subprocess.check_call(cmd, cwd=cwd)
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
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        log("Venv already exists.", Colors.OKGREEN)

    # 2. Install Deps
    log("Installing dependencies...")
    run([str(PYTHON_EXEC), "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools"])
    run([str(PYTHON_EXEC), "-m", "pip", "install", "-e", "."])
    run([str(PYTHON_EXEC), "-m", "pip", "install", "pyinstaller"])
    
    log("Setup complete!", Colors.BOLD)

def build():
    """Build the standalone executable."""
    log("Building DocNexus...")
    
    # Get Version
    try:
        init_file = PROJECT_ROOT / "docnexus" / "__init__.py"
        with open(init_file) as f:
            for line in f:
                if "__version__" in line:
                    version = line.split("'")[1]
                    break
    except Exception:
        version = "0.0.0"
        
    app_name = f"DocNexus_v{version}"
    
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
        
        # We need the hook to be visible. PyInstaller looks in current dir? 
        # Or we can specify --additional-hooks-dir.
        # Let's assume the hook file inside build/ is sufficient if we point the hook path there.
        # But simpler: PyInstaller's `hook-docnexus.plugins_dev.py` mechanism works via
        # runtime hook or just hidden import discovery if configured.
        # The previous Powershell script relied on just existence.
        # To be robust, let's allow PyInstaller to just find it via sys.path (cmd includes PROJECT_ROOT)
    
    # Entry Point
    cmd.append(str(PROJECT_ROOT / "docnexus" / "app.py"))
    
    run(cmd)
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
    parser = argparse.ArgumentParser(description="DocNexus Build System")
    parser.add_argument("command", choices=["setup", "build", "clean", "run", "release"], help="Command to run")
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    
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

if __name__ == "__main__":
    main()
