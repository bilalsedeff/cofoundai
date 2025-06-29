
# CoFound.ai Local Development Makefile

.PHONY: help build up down logs shell test clean

# Default target
help:
	@echo "CoFound.ai Local Development Commands:"
	@echo "  make build    - Build all Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make logs     - Show logs for all services"
	@echo "  make shell    - Open shell in backend container"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up Docker resources"
	@echo "  make reset    - Reset database and start fresh"

# Build all Docker images
build:
	docker-compose build

# Start all services
up:
	docker-compose --env-file local-dev.env up -d
	@echo "Services starting..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:5000"
	@echo "Chroma DB: http://localhost:8000"

# Stop all services
down:
	docker-compose down

# Show logs
logs:
	docker-compose logs -f

# Open shell in backend container
shell:
	docker-compose exec backend bash

# Run tests
test:
	docker-compose exec backend python -m pytest cofoundai/tests/ -v

# Clean up Docker resources
clean:
	docker-compose down -v
	docker system prune -f

# Reset database and start fresh
reset:
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 10
	docker-compose up -d

# Install local dependencies (for development outside Docker)
install:
	pip install -r requirements.txt

# Run locally (without Docker)
local:
	export $$(cat local-dev.env | grep -v '^#' | xargs) && python start_backend.py
