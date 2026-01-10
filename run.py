#!/usr/bin/env python
"""
Launcher script for Markdown Documentation Viewer
This script can be run directly without package installation.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from docnexus.app import app, VERSION

if __name__ == '__main__':
    # Debug mode ON by default (development)
    # Set PRODUCTION=true environment variable for production/release mode
    debug_mode = os.getenv('PRODUCTION', 'False').lower() != 'true'
    
    print(f"\n" + "="*60)
    print(f"  DocNexus - The Ultimate All-in-One Document Engine v{VERSION}")
    print("="*60)
    print(f"\n  Server running at: http://localhost:8000")
    print(f"  Smart Conversion: Toggle in document view")
    print(f"  Markdown Files: ./examples/ (Dev) or ./workspace/ (Prod)")
    print(f"  Documentation: ./docs/")
    print(f"  Debug Mode: {'ON' if debug_mode else 'OFF'}")
    print(f"\n  Press Ctrl+C to stop the server\n")
    print("="*60 + "\n")
    print()
    
    app.run(debug=debug_mode, host='localhost', port=8000)
