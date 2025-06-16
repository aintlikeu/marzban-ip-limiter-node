# Makefile for Marzban Node Agent

.PHONY: help install build test clean run docker-build docker-run docker-stop health-check

# Default target
help: ## Show this help message
	@echo "Marzban Node Agent - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation and setup
install: ## Install dependencies and setup the project
	pip install -r config/requirements.txt
	pip install -r tests/requirements.txt
	chmod +x scripts/*.sh
	chmod +x run.py

install-dev: ## Install development dependencies
	pip install -r config/requirements.txt
	pip install -r tests/requirements.txt
	pip install black flake8 mypy

# Build and packaging
build: ## Build the Docker image
	docker build -t marzban-node-agent:latest -f docker/Dockerfile .

build-dev: ## Build development Docker image
	docker build -t marzban-node-agent:dev -f docker/Dockerfile --target development .

# Testing
test: ## Run all tests
	python -m pytest tests/ -v

test-unit: ## Run unit tests only
	python -m pytest tests/test_*.py -v

test-integration: ## Run integration tests
	python -m pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	python -m pytest tests/ --cov=src/node_agent --cov-report=html --cov-report=term

# Code quality
lint: ## Run code linting
	flake8 src/
	black --check src/
	mypy src/

format: ## Format code with black
	black src/
	black tests/

# Running the application
run: ## Run the agent directly (for development)
	./run.py

run-dev: ## Run with development settings
	LOG_LEVEL=DEBUG ./run.py

# Docker operations
docker-build: build ## Alias for build

docker-run: ## Run the agent in Docker
	docker-compose -f docker/docker-compose.standalone.yml up -d

docker-stop: ## Stop the Docker containers
	docker-compose -f docker/docker-compose.standalone.yml down

docker-logs: ## Show Docker container logs
	docker-compose -f docker/docker-compose.standalone.yml logs -f

docker-restart: ## Restart Docker containers
	docker-compose -f docker/docker-compose.standalone.yml restart

# Health and monitoring
health-check: ## Run health check
	./scripts/health-check.sh

health-check-quiet: ## Run health check in quiet mode
	./scripts/health-check.sh --quiet

health-check-json: ## Run health check with JSON output
	./scripts/health-check.sh --json

# Configuration
config-validate: ## Validate configuration
	python -c "import sys; sys.path.append('src'); from node_agent.config import ConfigService; ConfigService.load_from_env(); print('✅ Configuration is valid')"

config-example: ## Create example configuration
	cp config/.env.example .env
	@echo "✅ Created .env file from example. Please edit it with your settings."

# Installation scripts
install-system: ## Install system-wide using install script
	sudo ./scripts/install.sh

# Clean up
clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

clean-docker: ## Clean up Docker images and containers
	docker-compose -f docker/docker-compose.standalone.yml down --rmi all --volumes
	docker system prune -f

# Development helpers
dev-setup: ## Setup development environment
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && make install-dev
	make config-example
	@echo "✅ Development environment ready!"
	@echo "Activate with: source venv/bin/activate"

dev-redis: ## Start Redis container for development
	docker run -d --name redis-dev -p 6379:6379 redis:7-alpine
	@echo "✅ Redis dev container started on port 6379"

dev-redis-stop: ## Stop Redis development container
	docker stop redis-dev && docker rm redis-dev
	@echo "✅ Redis dev container stopped"

# Documentation
docs-serve: ## Serve documentation locally
	python -m http.server 8000 --directory docs/
	@echo "📚 Documentation available at http://localhost:8000"

# Release helpers
release-build: ## Build release artifacts
	make clean
	make test
	make build
	@echo "✅ Release build complete"

release-tag: ## Create a new release tag
	@read -p "Enter version (e.g., v1.0.1): " version; \
	git tag -a $$version -m "Release $$version"; \
	git push origin $$version; \
	echo "✅ Tagged release $$version"

# Debugging
debug-logs: ## Show detailed logs for debugging
	LOG_LEVEL=DEBUG ./run.py

debug-redis: ## Test Redis connection
	python -c "import sys; sys.path.append('src'); import asyncio; import redis.asyncio as redis; from node_agent.config import ConfigService; config = ConfigService.load_from_env(); client = redis.from_url(config.central_redis_url); asyncio.run(client.ping()); print('✅ Redis connection successful'); asyncio.run(client.close())"

debug-log-parser: ## Test log parser with sample data
	python -c "import sys; sys.path.append('src'); from node_agent.log_parser import create_log_entry; result = create_log_entry('2024/01/15 10:30:45 [info] accepted connection from 192.168.1.100 email: test@example.com', 'test-node', 'Test Node'); print('✅ Log parser working:', result is not None)"

# Status and information
status: ## Show project status
	@echo "📊 Marzban Node Agent Status"
	@echo "=========================="
	@echo ""
	@echo "🐳 Docker:"
	@docker --version 2>/dev/null || echo "  ❌ Docker not available"
	@docker-compose --version 2>/dev/null || echo "  ❌ Docker Compose not available"
	@echo ""
	@echo "🐍 Python:"
	@python --version 2>/dev/null || echo "  ❌ Python not available"
	@echo ""
	@echo "📁 Project files:"
	@ls -la src/node_agent/*.py | wc -l | awk '{print "  📄 Source files: " $$1}'
	@ls -la tests/*.py | wc -l | awk '{print "  🧪 Test files: " $$1}'
	@echo ""
	@echo "🔧 Configuration:"
	@if [ -f .env ]; then echo "  ✅ .env file exists"; else echo "  ❌ .env file missing"; fi
	@echo ""
	@echo "🐳 Container status:"
	@docker ps | grep marzban-node-agent || echo "  ❌ Container not running"

info: status ## Alias for status

# Uninstall and cleanup
uninstall: ## Uninstall the agent from system
	sudo ./scripts/uninstall.sh

uninstall-force: ## Force uninstall without confirmation
	sudo ./scripts/uninstall.sh --force

uninstall-local: ## Remove local development environment
	make clean
	make clean-docker
	rm -f .env
	@echo "✅ Local environment cleaned"
