# Single entry point for the local stack. See docs/infra/setup.md.
.DEFAULT_GOAL := help
.PHONY: help setup up up-d down logs migrate makemigrations superuser shell-backend clean

COMPOSE := docker compose
RUN_BACKEND := $(COMPOSE) run --rm backend

help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  %-16s %s\n", $$1, $$2}'

setup: ## First-time setup on a fresh clone (env file, build, migrate, superuser)
	bash scripts/init.sh

up: ## Start the stack in the foreground
	$(COMPOSE) up

up-d: ## Start the stack detached
	$(COMPOSE) up -d

down: ## Stop the stack (keeps the database volume)
	$(COMPOSE) down

logs: ## Follow logs for all services
	$(COMPOSE) logs -f

migrate: ## Apply database migrations
	$(RUN_BACKEND) python manage.py migrate

makemigrations: ## Generate migrations for model changes
	$(RUN_BACKEND) python manage.py makemigrations

superuser: ## Create a Django superuser
	$(RUN_BACKEND) python manage.py createsuperuser

shell-backend: ## Open a Django shell in the backend image
	$(RUN_BACKEND) python manage.py shell

clean: ## Stop the stack AND DROP THE DATABASE VOLUME (destructive)
	$(COMPOSE) down -v
