.PHONY: dev test migrate migrations shell

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=app

migrate:
	alembic upgrade head

migrations:
	alembic revision --autogenerate -m "$(name)"

shell:
	python -c "from app.database import SessionLocal; db=SessionLocal()"
