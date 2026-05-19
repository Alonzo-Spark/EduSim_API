.PHONY: install db migrate seed ingest run dev setup

install:
	pip install -r requirements.txt

db:
	alembic upgrade head

migrate:
	alembic revision --autogenerate -m "$(msg)"
	alembic upgrade head

seed:
	python scripts/import_curriculum.py

ingest:
	python scripts/ingest_textbooks.py

setup: install db seed ingest
	@echo "✅ EduSim backend ready"

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --reload --port 8000
