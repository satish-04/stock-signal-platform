.PHONY: init up down logs test lint format health seed signals
init:
	@test -f .env || cp .env.example .env
	docker compose build
up:
	docker compose up -d
down:
	docker compose down
logs:
	docker compose logs -f api worker
test:
	docker compose run --rm api pytest -q
lint:
	docker compose run --rm api ruff check app tests
format:
	docker compose run --rm api ruff format app tests
health:
	curl -fsS http://localhost:8080/health | python3 -m json.tool
seed:
	curl -fsS -X POST http://localhost:8080/api/v1/dev/seed | python3 -m json.tool

signals:
	curl -fsS 'http://localhost:8080/api/v1/signals?limit=20' | python3 -m json.tool
