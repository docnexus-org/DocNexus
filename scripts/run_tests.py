import unittest
import sys
import os
import argparse
import time
from pathlib import Path
import coverage

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_tests(test_path=None, output_file=None):
    """
    Run tests with coverage and output results to file.
    """
    # Initialize Coverage
    cov = coverage.Coverage(source=['docnexus'], omit=['*/tests/*', '*/venv/*'])
    cov.start()

    # Discover Tests
    loader = unittest.TestLoader()
    start_dir = PROJECT_ROOT / 'tests'
    
    if test_path:
        # Run specific test file or case
        # If test_path is a file path relative to project
        target = PROJECT_ROOT / test_path
        if target.exists() and target.is_file():
            # Convert file path to module name
            module_name = test_path.replace(os.sep, '.').replace('.py', '')
            suite = loader.loadTestsFromName(module_name)
        else:
            # Try loading as dotted name
            suite = loader.loadTestsFromName(test_path)
    else:
        # Run all tests
        suite = loader.discover(str(start_dir))

    # Output Buffer
    output_stream = sys.stderr
    if output_file:
        output_stream = open(output_file, 'w')
        output_stream.write(f"Test Run: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        output_stream.write("="*40 + "\n")

    # Run Tests
    runner = unittest.TextTestRunner(stream=output_stream, verbosity=2)
    result = runner.run(suite)

    # Stop Coverage
    cov.stop()
    cov.save()

    # Report Coverage
    if output_file:
        output_stream.write("\n" + "="*40 + "\n")
        output_stream.write("Coverage Report:\n")
        cov.report(file=output_stream)
        output_stream.close()
        print(f"Test results saved to {output_file}")
    
    cov.report() # Also print to console

    return result.wasSuccessful()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DocNexus Test Runner")
    parser.add_argument('test_target', nargs='?', help="Specific test file or module (optional)")
    parser.add_argument('--output', '-o', default='test_results.txt', help="Output file for test report")
    
    args = parser.parse_args()
    
    # Check dependencies (simplified, assuming handled by environment)
    
    success = run_tests(args.test_target, args.output)
    sys.exit(0 if success else 1)
