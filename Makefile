.PHONY: up down build test logs clean

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

clean:
	docker compose down -v
