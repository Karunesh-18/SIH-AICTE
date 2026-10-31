PY=backend/.venv/Scripts/python
.PHONY: dev seed reset test lint
dev:
	cd backend && ../$(PY) -m alembic upgrade head && ../$(PY) -m app.seed.run
	(cd backend && ../$(PY) -m uvicorn app.main:app --reload --port 8000) & (cd frontend && npm run dev)
seed:
	cd backend && ../$(PY) -m app.seed.run
reset:
	cd backend && ../$(PY) -m app.seed.run --reset
test:
	cd backend && ../$(PY) -m pytest -q
	cd frontend && npm test
lint:
	cd backend && ../$(PY) -m ruff check .
	cd frontend && npm run lint
