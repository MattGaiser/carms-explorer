.PHONY: up down etl test lint docs dev install report \
       deploy-init deploy-plan deploy-apply deploy-destroy \
       prod-up prod-down prod-logs

# Docker Compose
up:
	docker compose -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down

build:
	docker compose -f docker/docker-compose.yml build

logs:
	docker compose -f docker/docker-compose.yml logs -f

# ETL
etl:
	docker compose -f docker/docker-compose.yml exec dagster_code \
		dagster job execute -j full_refresh -m carms.etl.definitions

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/carms --cov-report=term-missing --cov-fail-under=70

# Code quality
lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

# Documentation
docs:
	mkdocs serve -f docs/mkdocs.yml

# Local development
install:
	pip install -e ".[api,dagster,agent,rag,dashboard,docs,dev]"

dev:
	uvicorn carms.api.main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	streamlit run src/carms/dashboard/app.py --server.port 8501

report:
	quarto render reports/program_landscape.qmd --to html

# Terraform (GCE deployment)
deploy-init:
	cd terraform && terraform init

deploy-plan:
	cd terraform && terraform plan

deploy-apply:
	cd terraform && terraform apply

deploy-destroy:
	cd terraform && terraform destroy

# Production (docker-compose on EC2)
prod-up:
	docker compose -f docker/docker-compose.prod.yml up -d

prod-down:
	docker compose -f docker/docker-compose.prod.yml down

prod-logs:
	docker compose -f docker/docker-compose.prod.yml logs -f
