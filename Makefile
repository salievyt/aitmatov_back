.PHONY: build up down logs migrate shell test

build:
	docker-compose build

up:
	docker-compose up -d

up-dev:
	docker-compose up -d db
	docker-compose up web

down:
	docker-compose down

down-v:
	docker-compose down -v

logs:
	docker-compose logs -f web

migrate:
	docker-compose exec web python manage.py migrate

makemigrations:
	docker-compose exec web python manage.py makemigrations

shell:
	docker-compose exec web python manage.py shell

createsuperuser:
	docker-compose exec web python manage.py createsuperuser

test:
	docker-compose exec web python manage.py test

static:
	docker-compose exec web python manage.py collectstatic --noinput
