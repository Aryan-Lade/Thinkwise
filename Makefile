"""
Makefile for Blind Spot AI Thinking Companion
"""

.PHONY: help install test test-unit test-integration lint lint-check lint-fix format format-check \
        build run clean docker-build docker-run docker-push deploy logs

# Project variables
PROJECT_NAME = blind-spot
VERSION = 1.0.0
DOCKER_IMAGE = $(PROJECT_NAME)
DOCKER_TAG = $(VERSION)
PYTHON = python3
PIP = pip3

# Help target
help:
	@echo "Blind Spot AI Thinking Companion - Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  help                    Show this help message"
	@echo ""
	@echo "Development:"
	@echo "  install                 Install dependencies"
	@echo "  test                    Run all tests"
	@echo "  test-unit               Run unit tests only"
	@echo "  test-integration        Run integration tests only"
	@echo "  lint                    Run linting (ruff)"
	@echo "  lint-check              Check linting without fixing"
	@echo "  lint-fix                Automatically fix linting issues"
	@echo "  format                  Format code (black)"
	@echo "  format-check            Check formatting without changing"
	@echo ""
	@echo "Build & Run:"
	@echo "  build                   Build the application"
	@echo "  run                     Run the application locally"
	@echo "  clean                   Clean build artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build            Build Docker image"
	@echo "  docker-run              Run Docker container"
	@echo "  docker-push             Push Docker image to registry"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy                  Deploy to Google Cloud Run"
	@echo "  logs                    View Cloud Run logs"
	@echo ""

# Development targets
install:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

test: test-unit test-integration

test-unit:
	$(PYTHON) -m pytest tests/unit/ -v

test-integration:
	$(PYTHON) -m pytest tests/integration/ -v

lint:
	$(PYTHON) -m ruff check . --fix

lint-check:
	$(PYTHON) -m ruff check .

lint-fix:
	$(PYTHON) -m ruff check . --fix

format:
	$(PYTHON) -m black .

format-check:
	$(PYTHON) -m black --check .

# Build targets
build:
	@echo "Building $(PROJECT_NAME) v$(VERSION)"
	@echo "No build step required for Python application"

run:
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

# Docker targets
docker-build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_IMAGE):latest

docker-run:
	docker run -p 8080:8080 \
		-e GEMINI_API_KEY=$(GEMINI_API_KEY) \
		-e ENVIRONMENT=development \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

docker-push:
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_IMAGE):latest

# Deployment targets
deploy:
	gcloud run deploy $(PROJECT_NAME) \
		--source . \
		--platform managed \
		--region asia-south1 \
		--allow-unauthenticated \
		--set-secrets=GEMINI_API_KEY=GEMINI_API_KEY \
		--max-instances=10 \
		--min-instances=0 \
		--cpu=1 \
		--memory=512Mi \
		--timeout=300s

logs:
	gcloud run services logs $(PROJECT_NAME) --region asia-south1

# Test coverage
coverage:
	$(PYTHON) -m pytest --cov=app --cov-report=term-missing --cov-report=html:htmlcov tests/

# Security check
security-check:
	bandit -r app/ -f txt -o security-report.txt
	@echo "Security check complete. See security-report.txt"

# Dependency check
deps-check:
	$(PIP) list --outdated
	@echo "Check above for outdated dependencies"

# CI/CD target for GitHub Actions
ci: test lint-check format-check security-check
	@echo "CI checks passed"