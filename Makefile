.PHONY: \
	help \
	install \
	doc-build \
	doc-serve \
	doc-deploy \
	doc-view \
	test \
	lint \
	typecheck \
	validate-fixtures \
	check \
	precommit \
	docker-up \
	docker-down \
	docker-logs \
	docker-ps \
	docker-reset \
	bootstrap \
	smoke \
	destroy \
	db-init \
	clean

# Virtual environment configuration
VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
MKDOCS := $(VENV)/bin/mkdocs
COMPOSE := docker compose --env-file .env

# Default target
help:
	@echo "Agora OSS"
	@echo ""
	@echo "Usage: make [cmd]"
	@echo ""
	@echo "Commands:"
	@echo "  install        Install dependencies"
	@echo "  test           Run automated tests"
	@echo "  lint           Run ruff lint checks"
	@echo "  typecheck      Run mypy type checks"
	@echo "  check          Run lint, typecheck, tests, and docs build"
	@echo "  precommit      Run all pre-commit hooks"
	@echo "  clean          Remove build artifacts"
	@echo "  help           Show this help message"
	@echo ""
	@echo "Stack:"
	@echo "  docker-up      Start local docker stack"
	@echo "  docker-down    Stop local docker stack"
	@echo "  docker-logs    Tail docker stack logs"
	@echo "  docker-ps      Show docker services status"
	@echo "  docker-reset   Stop stack and remove volumes"
	@echo "  bootstrap      Run infrastructure bootstrap steps"
	@echo "  smoke          Run local stack smoke tests"
	@echo "  destroy        Destroy PostgreSQL database and volumes (with confirmation)"
	@echo "  db-init        Reinitialize PostgreSQL schemas and extensions"
	@echo ""
	@echo "Documentation:"
	@echo "  doc-build	Build documentation site"
	@echo "  doc-serve	Dislay documentation site"
	@echo "  doc-deploy	Publish documentation site"
	@echo ""

# Install virtual env
install: $(VENV)/bin/activate
	@echo "Installing dependencies..."
	. $(VENV)/bin/activate && uv sync
	@echo "✓ Dependencies installed"
	uv run pre-commit install
	make docker-up
	make bootstrap

$(VENV)/bin/activate:
	@echo "Creating virtual environment..."
	uv venv $(VENV)

update: $(VENV)/bin/activate
	@echo "Updating dependencies..."
	. $(VENV)/bin/activate && uv sync --upgrade
	@echo "✓ Dependencies updated"
	pre-commit autoupdate

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

# Run tests
test:
	@echo "Running tests..."
	. $(VENV)/bin/activate && PYTHONPATH=. uv run pytest -q
	@echo "✓ Tests passed"

# Run lint checks
lint:
	@echo "Running lint checks..."
	. $(VENV)/bin/activate && uv run ruff check .
	@echo "✓ Lint passed"

# Run static type checks
typecheck:
	@echo "Running type checks..."
	. $(VENV)/bin/activate && PYTHONPATH=. uv run mypy
	@echo "✓ Typecheck passed"

# Run full local quality gate
check: lint typecheck test doc-build
	@echo "✓ Full quality gate passed"

# Run precommit checks
precommit:
	. $(VENV)/bin/activate && uv run pre-commit run --all-files
	@echo "✓ All pre-commit checks passed"


# Docker lifecycle commands
docker-up:
	@echo "Starting local docker stack..."
	$(COMPOSE) up -d
	@echo "✓ Stack started"
	@echo ""
	@echo "Local services:"
	@echo "  Prefect UI:        http://localhost:4200"
	@echo "  MinIO API:         http://localhost:9000"
	@echo "  MinIO Console:     http://localhost:9001"
	@echo "  Frontend:          http://localhost:3000"

docker-down:
	@echo "Stopping local docker stack..."
	$(COMPOSE) down
	@echo "✓ Stack stopped"

docker-logs:
	$(COMPOSE) logs -f

docker-ps:
	$(COMPOSE) ps

docker-reset:
	@echo "Resetting local docker stack and volumes..."
	$(COMPOSE) down -v
	@echo "✓ Stack reset complete"

bootstrap:
	@echo "Running infrastructure bootstrap orchestrator..."
	./infra/bootstrap.sh

smoke:
	@echo "Running local stack smoke tests..."
	./infra/smoke_stack.sh
	@echo "✓ Smoke tests passed"

destroy:
	@echo "WARNING: This will destroy all PostgreSQL data and volumes!"
	@read -p "Are you sure? Type 'yes' to confirm: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "Destroying PostgreSQL database and volumes..."; \
		$(COMPOSE) down -v --remove-orphans; \
		echo "✓ PostgreSQL database and volumes destroyed"; \
	else \
		echo "Cancelled"; \
	fi

# Clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf site/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"
