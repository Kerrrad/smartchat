install:
	pip install -e .[dev]

run:
	uvicorn app.main:app --reload

worker:
	celery -A app.workers.celery_app.celery_app worker --loglevel=info

migrate:
	alembic upgrade head

seed:
	python -m app.seed

test:
	pytest

compose-up:
	docker-compose up --build

