# Code Learning Platform

Platformă web de programare cu autograder: profesorul creează teme cu teste, studentul trimite cod
Python rulat izolat în Docker și află, pe concepte, unde greșește.

## Pornire în dezvoltare

```bash
docker compose up -d db                      # PostgreSQL pe localhost:5433
cd backend
python -m venv .venv
.venv\Scripts\activate                       # Windows; pe Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload                # http://localhost:8000/docs
```

În alt terminal:

```bash
cd frontend
npm install
npm run dev                                  # http://localhost:5173
```

## Teste

```bash
cd backend && ruff check . && pytest
cd frontend && npm test
```

Documentația proiectului este în [docs/](docs/): [masterprompt.md](docs/masterprompt.md) (sursa adevărului),
[cerinte.md](docs/cerinte.md), [decizii.md](docs/decizii.md).
