.PHONY: help install test lint format coverage clean docker-build docker-up docker-down restart logs check-cache

help:
	@echo "FHBG Eligibility Bot — Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Development:"
	@echo "  make install       Install Python dependencies"
	@echo "  make test          Run pytest suite with verbose output"
	@echo "  make coverage      Generate HTML coverage report"
	@echo "  make lint          Run Ruff linter"
	@echo "  make format        Auto-format code with Black and Ruff"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker images"
	@echo "  make docker-up     Start services (Rasa + Action Server)"
	@echo "  make docker-down   Stop and remove containers"
	@echo "  make docker-restart Restart services (recreates containers)"
	@echo "  make logs          Tail logs from all services"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean         Remove caches, reports, and build artifacts"
	@echo "  make check-cache   Verify rule cache exists; re-scrape if missing"
	@echo "  make reset-db      (Future) Reset any persistent storage"
	@echo ""
	@echo "Quick Demo:"
	@echo "  make demo-cli      Run the interactive CLI"
	@echo "  make demo-rasa     Start Rasa shell (requires docker-up first)"
	@echo ""
	@echo "For more info, see README.md and docs/"

install:
	pip install -r requirements.txt

test:
	pytest -v

coverage:
	pytest --cov=src --cov-report=html
	@echo "HTML coverage report generated in htmlcov/index.html"

lint:
	ruff check .
	@echo "Linting passed."

format:
	black .
	ruff format .
	@echo "Code formatted with Black and Ruff."

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Services started. Rasa at http://localhost:5005"
	@echo "Action server at http://localhost:5055"
	@echo "Use 'make logs' to view output."

docker-down:
	docker-compose down
	@echo "Services stopped."

docker-restart: docker-down docker-up

logs:
	docker-compose logs -f

check-cache:
	@if [ ! -f src/data/nsw_rules.json ]; then \
		echo "Cache missing. Running scraper..."; \
		python scripts/scrape_nsw_rules.py; \
	else \
		echo "Cache present. Use 'make clean' to force re-scrape."; \
	fi

clean:
	@echo "Cleaning up..."
	rm -rf reports/
	rm -rf .rasa/
	rm -rf models/
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f src/data/nsw_rules.json
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@echo "Clean complete."

demo-cli:
	python src/chatbot/cli.py

demo-rasa:
	@echo "Ensure Rasa and action server are running first:"
	@echo "  make docker-up"
	@echo "Then run: rasa shell --debug"

.PHONY: all
