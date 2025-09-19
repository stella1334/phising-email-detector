# Production-ready Bank Phishing Detector with Google Gemini Integration

.PHONY: help install test run docker-build docker-run docker-compose-up docker-compose-down clean lint format docs

# Default target
help:
	@echo "Available commands:"
	@echo "  install          Install dependencies"
	@echo "  test            Run tests"
	@echo "  test-coverage   Run tests with coverage"
	@echo "  run             Run the service locally"
	@echo "  docker-build    Build Docker image"
	@echo "  docker-run      Run Docker container"
	@echo "  docker-compose-up    Start with Docker Compose"
	@echo "  docker-compose-down  Stop Docker Compose services"
	@echo "  clean           Clean up generated files"
	@echo "  lint            Run code linting"
	@echo "  format          Format code"
	@echo "  docs            Generate documentation"
	@echo "  test-api        Test API endpoints"

# Development commands
install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=models --cov=utils --cov=schemas --cov-report=html --cov-report=term

run:
	python app.py

test-api:
	./test_api.sh

# Docker commands
docker-build:
	docker build -t bank-phishing-detector .

docker-run:
	docker run -p 8000:8000 --env-file .env bank-phishing-detector

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# With nginx proxy
docker-compose-up-proxy:
	docker-compose --profile with-proxy up -d

# Code quality
lint:
	flake8 models/ utils/ schemas/ app.py --max-line-length=100 --ignore=E203,W503
	black --check models/ utils/ schemas/ app.py

mypy:
	mypy models/ utils/ schemas/ app.py --ignore-missing-imports

format:
	black models/ utils/ schemas/ app.py
	isort models/ utils/ schemas/ app.py

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf logs/*.log

# Documentation
docs:
	@echo "Documentation available at:"
	@echo "  README.md - Main documentation"
	@echo "  docs/API.md - API documentation"
	@echo "  http://localhost:8000/docs - Interactive API docs (when running)"

# Production deployment helpers
deploy-check:
	@echo "Pre-deployment checklist:"
	@echo "  ☐ Environment variables configured (.env file)"
	@echo "  ☐ Google Gemini API key set"
	@echo "  ☐ SSL certificates in place (for production)"
	@echo "  ☐ Rate limiting configured"
	@echo "  ☐ Monitoring and logging set up"
	@echo "  ☐ Health checks working"
	@echo "  ☐ Firewall rules configured"

# Security checks
security-check:
	bandit -r models/ utils/ schemas/ app.py
	safety check

# All quality checks
check-all: lint mypy test security-check
	@echo "All quality checks completed!"

# Development setup
dev-setup: install
	cp .env.example .env
	@echo "Development environment set up!"
	@echo "Please edit .env file with your API keys and configuration."

# Production setup
prod-setup:
	@echo "Setting up production environment..."
	mkdir -p logs
	mkdir -p ssl
	@echo "Production directories created."
	@echo "Please:"
	@echo "  1. Configure .env file with production settings"
	@echo "  2. Place SSL certificates in ssl/ directory"
	@echo "  3. Review nginx.conf for your domain"
	@echo "  4. Set up monitoring and alerting"
