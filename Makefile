# DocNexus Makefile (Cross-Platform Wrapper)

.PHONY: setup build clean run help

PYTHON_SYS := python3
BUILD_SCRIPT := scripts/build.py

help:
	@echo "Available commands:"
	@echo "  make setup   - Create venv and install dependencies"
	@echo "  make build   - Build standalone binary"
	@echo "  make run     - Run from source"
	@echo "  make clean   - Clean artifacts"

setup:
	$(PYTHON_SYS) $(BUILD_SCRIPT) setup

build:
	$(PYTHON_SYS) $(BUILD_SCRIPT) build

clean:
	$(PYTHON_SYS) $(BUILD_SCRIPT) clean

run:
	$(PYTHON_SYS) $(BUILD_SCRIPT) run
