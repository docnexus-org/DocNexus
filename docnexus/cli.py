#!/usr/bin/env python
"""
Command-line interface for Markdown Documentation Viewer
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import docnexus
sys.path.insert(0, str(Path(__file__).parent.parent))

from docnexus.version_info import __version__, __build_timestamp__, __build_type__

def print_version():
    """Print version information."""
    print(f"DocNexus v{__version__}")
    print(f"Build: {__build_timestamp__}")
    print(f"Build Type: {__build_type__}")
    # Description removed to keep it clean, or keep it if preferred.
    # print(f"{__description__}")


def start_server(args):
    """Start the Flask server."""
    from docnexus.app import app
    
    
    host = args.host
    port = args.port or 8000
    debug = args.debug
    
    print(f"Starting DocNexus v{__version__}")
    print(f"Server: http://{host}:{port}")
    print(f"Documentation: http://{host}:{port}/docs")
    print("Press Ctrl+C to stop")
    print()
    
    app.run(host=host, port=port, debug=debug)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description=f'DocNexus v{__version__}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  docnexus --version              Show version information
  docnexus start                  Start server on localhost:8000
  docnexus start --port 8080      Start server on port 8080
  docnexus start --debug          Start server in debug mode
        """
    )
    
    parser.add_argument(
        '--version', '-v',
        action='store_true',
        help='Show version information'
    )
    
    # Determine default host based on build type
    # Always default to 0.0.0.0 to support both Localhost and Public IP access
    default_host = '0.0.0.0'
    
    # Global server arguments
    parser.add_argument(
        '--host',
        type=str,
        default=default_host,
        help=f'Host to bind to (default: {default_host})'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='Port to bind to (default: 8000)'
    )
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Run in debug mode'
    )
    
    # Optional subcommands (keep start for backward compatibility if needed, but make it optional)
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command (optional alias)
    start_parser = subparsers.add_parser('start', help='Start the documentation server')
    # Note: we don't strictly need to add args to start_parser if we handle it at top level,
    # but for strict correctness if user types "start --port", we might need them there too.
    # Simpler: Just rely on top-level args.
    
    args = parser.parse_args()
    
    if args.version:
        print_version()
        return 0
    
    # Default behavior: Start Server
    # Whether command is 'start' or None
    if args.command == 'start' or args.command is None:
        try:
            start_server(args)
            return 0
        except KeyboardInterrupt:
            print("\nServer stopped.")
            return 0
        except Exception as e:
            if args.debug or True: # Force traceback for now
                import traceback
                traceback.print_exc()
            print(f"Error starting server: {e}", file=sys.stderr)
            return 1
            
    return 0


if __name__ == '__main__':
    # PyInstaller support for Windows
    import multiprocessing
    multiprocessing.freeze_support()
    sys.exit(main())
