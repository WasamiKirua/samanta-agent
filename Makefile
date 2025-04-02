ifeq (,$(wildcard .env))
$(error .env file is missing. Please create one based on .env.example)
endif

include .env

CHECK_DIRS := .

ava-build-qdrant:
	docker compose --profile qdrant_db build

ava-build-weaviate:
	docker compose --profile weaviate_db build

ava-run-qdrant:
	docker compose -f docker-compose.yml -f docker-compose.override.yml.qdrant --profile qdrant_db up

ava-run-weaviate:
	docker compose -f docker-compose.yml -f docker-compose.override.yml.weaviate --profile weaviate_db up

ava-stop:
	docker compose stop

ava-delete:
	@if [ -d "long_term_memory" ]; then rm -rf long_term_memory; fi
	@if [ -d "short_term_memory" ]; then rm -rf short_term_memory; fi
	@if [ -d "generated_images" ]; then rm -rf generated_images; fi
	docker compose down

format-fix:
	uv run ruff format $(CHECK_DIRS) 
	uv run ruff check --select I --fix $(CHECK_DIRS)

lint-fix:
	uv run ruff check --fix $(CHECK_DIRS)

format-check:
	uv run ruff format --check $(CHECK_DIRS) 
	uv run ruff check -e $(CHECK_DIRS)
	uv run ruff check --select I -e $(CHECK_DIRS)

lint-check:
	uv run ruff check $(CHECK_DIRS)