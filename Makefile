# Agent-Earns Makefile
# Usage: make <command>

.PHONY: help install install-dev run test lint format check setup migrate backup campaign

PYTHON := python
PIP := pip

help:
	@echo ""
	@echo "Agent-Earns Command Reference"
	@echo "=============================="
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install dev dependencies"
	@echo "  make setup        First-time setup wizard"
	@echo "  make run          Start the agent + dashboard"
	@echo "  make test-run     Run one test cycle and exit"
	@echo "  make test         Run full test suite"
	@echo "  make lint         Run ruff linter"
	@echo "  make format       Auto-format code with ruff"
	@echo "  make check        Lint + type check"
	@echo "  make migrate      Run database migrations"
	@echo "  make backup       Backup database"
	@echo "  make apis         Test all API connections"
	@echo "  make leads        Run lead finder module only"
	@echo "  make campaign     Mock E2E campaign (1 lead, Instantly)"
	@echo "  make dashboard    Start dashboard only (no agent)"
	@echo ""

install:
	$(PIP) install uv
	uv pip install -r requirements.txt
	playwright install chromium

install-dev:
	$(PIP) install uv
	uv pip install -r requirements.txt
	uv pip install -r requirements-dev.txt
	playwright install chromium

setup:
	$(PYTHON) scripts/setup.py

run:
	$(PYTHON) main.py

test-run:
	$(PYTHON) main.py --test --verbose

test:
	pytest tests/ -v --cov=. --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check . --fix

format:
	ruff format .

check:
	ruff check .
	mypy . --ignore-missing-imports

migrate:
	$(PYTHON) scripts/init_db.py

backup:
	$(PYTHON) scripts/backup_db.py

apis:
	$(PYTHON) scripts/test_all_apis.py

leads:
	$(PYTHON) main.py --module leads --verbose

campaign:
	$(PYTHON) scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 1 --instantly

dashboard:
	$(PYTHON) main.py --no-agent --verbose

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
