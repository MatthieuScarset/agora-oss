.PHONY: help install doc-build doc-serve doc-deploy doc-view clean

# Virtual environment configuration
VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
MKDOCS := $(VENV)/bin/mkdocs

# Default target
help:
	@echo "Agora OSS"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install        Install dependencies"
	@echo "  doc-build      Build documentation site"
	@echo "  doc-serve      Serve documentation locally (development)"
	@echo "  doc-deploy     Deploy documentation to GitHub Pages"
	@echo "  doc-view       Build and open documentation in browser"
	@echo "  clean          Remove build artifacts"
	@echo "  help           Show this help message"
	@echo ""

# Install virtual env
install: $(VENV)/bin/activate
	@echo "Installing dependencies..."
	. $(VENV)/bin/activate && uv sync
	@echo "✓ Dependencies installed"

$(VENV)/bin/activate:
	@echo "Creating virtual environment..."
	uv venv $(VENV)

# Build documentation site
doc-build:
	@echo "Building documentation..."
	. $(VENV)/bin/activate && $(MKDOCS) build
	@echo "✓ Documentation built in ./site/"

# Serve documentation locally (default: http://localhost:8000)
doc-serve:
	@echo "Serving documentation locally..."
	@echo "Open http://localhost:8000 in your browser"
	. $(VENV)/bin/activate && $(MKDOCS) serve

# Deploy documentation to GitHub Pages
doc-deploy: doc-build
	@echo "Deploying documentation to GitHub Pages..."
	. $(VENV)/bin/activate && $(MKDOCS) gh-deploy
	@echo "✓ Documentation deployed"

# View documentation after building
doc-view: doc-build
	@echo "Opening documentation..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open site/index.html; \
	elif command -v open > /dev/null; then \
		open site/index.html; \
	else \
		echo "Please open site/index.html in your browser"; \
	fi


# Clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf site/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"