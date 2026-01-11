# Quick Start - Development Guide

## For Developers

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd DocNexus

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running the Application
```bash
# Development mode (debug ON - DEFAULT)
python run.py

# Or use CLI
docnexus start --debug

# Production/Release mode (debug OFF)
set PRODUCTION=true
python run.py

# Custom host/port
docnexus start --host 0.0.0.0 --port 5000
```

### Code Quality
```bash
# Format code
black docnexus/

# Sort imports
isort docnexus/

# Lint
flake8 docnexus/

# Type check
mypy docnexus/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Testing
```bash
# Run all tests
pytest

# With coverage report
pytest --cov=docnexus --cov-report=html

# Run specific test file
pytest tests/test_toc.py

# Run specific test
pytest tests/test_toc.py::test_toc_basic_structure

# Watch mode (requires pytest-watch)
ptw
```

### Building
```bash
# Build standalone executable (Windows)
.\make.ps1 build

# Build standalone executable (Linux/Mac)
make build

# Output will be in build/output/
```

### Common Tasks
```bash
# Check what would change before formatting
black --check docnexus/

# Show what isort would change
isort --check-only --diff docnexus/

# Generate coverage report
pytest --cov=docnexus --cov-report=html
# Open htmlcov/index.html in browser

# Clean build artifacts
rm -rf build/ dist/ *.egg-info/  # Linux/Mac
rmdir /s build dist             # Windows
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, then commit
git add .
git commit -m "feat: add amazing feature"
# Pre-commit hooks run automatically

# Push
git push origin feature/my-feature

# Create Pull Request on GitHub
```

### Environment Variables
```bash
# Production mode (debug OFF)
export PRODUCTION=true         # Linux/Mac
set PRODUCTION=true           # Windows

# Debug mode is ON by default, no env var needed
```

## For Users

### Installation
```bash
# Install from source
pip install .

# Install in editable mode (for development)
pip install -e .
```

### Usage
```bash
# Start server
docnexus start

# With options
docnexus start --host localhost --port 8000 --debug

# Show version
docnexus --version
```

### Quick Launch (Windows)
```bash
# Double-click start.bat
# Or run:
start.bat
```

## Troubleshooting

### Import Errors
```bash
# Ensure virtual environment is activated
# Check Python version (3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Test Failures
```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv

# Run specific failing test
pytest tests/test_file.py::test_name -vv
```

### Pre-commit Issues
```bash
# Skip hooks temporarily
git commit --no-verify -m "message"

# Update hooks
pre-commit autoupdate

# Clean and reinstall
pre-commit clean
pre-commit install
```

### Port Already in Use
```bash
# Windows: Find process
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

## Project Structure
```
DocNexus/
├── docnexus/          # Main package
│   ├── app.py          # Flask application
│   ├── cli.py          # Command-line interface
│   ├── core/           # Core rendering
│   ├── features/       # Feature modules
│   └── templates/      # HTML templates
├── tests/              # Test suite
├── docs/               # Documentation
├── examples/           # Sample documents
└── releases/           # Release artifacts
```

## Resources
- **Documentation**: `docs/USER_GUIDE.md`
- **Contributing**: `CONTRIBUTING.md`
- **Changelog**: `docs/CHANGELOG.md`
- **Build Guide**: `docs/BUILD.md`
- **Standards**: `docs/OPEN_SOURCE_STANDARDS.md`
