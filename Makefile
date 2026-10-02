.PHONY: init up down build logs test lint format health seed seed-weak seed-strong seed-bearish signals scan scan-results migrate migration dashboard
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

scan:
	curl -fsS -X POST http://localhost:8080/api/v1/scanner/options | python3 -m json.tool

scan-results:
	curl -fsS http://localhost:8080/api/v1/scanner/options/latest | python3 -m json.tool

build:
	docker compose build

seed-weak:
	curl -fsS -X POST 'http://localhost:8080/api/v1/dev/seed?profile=weak' | python3 -m json.tool

seed-strong:
	curl -fsS -X POST 'http://localhost:8080/api/v1/dev/seed?profile=strong' | python3 -m json.tool

seed-bearish:
	curl -fsS -X POST 'http://localhost:8080/api/v1/dev/seed?profile=bearish' | python3 -m json.tool

migrate:
	docker compose run --rm api alembic upgrade head

migration:
	docker compose run --rm api alembic revision --autogenerate -m "$(m)"

dashboard:
	open http://localhost:8090
