.PHONY: up down build test logs clean hooks

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

test:
	docker compose --profile tools run --build --rm test

logs:
	docker compose logs -f

hooks:
	pre-commit install

clean:
	docker compose down -v
