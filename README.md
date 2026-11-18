# Code Learning Platform

Platformă web de programare cu autograder: profesorul creează teme cu teste, studentul trimite cod
Python rulat izolat în Docker și află, pe concepte, unde greșește.

## Pornire în dezvoltare

```bash
docker compose up -d db                      # PostgreSQL pe localhost:5433
docker build -t autograder-python sandbox    # imaginea in care ruleaza codul studentilor
cd backend
python -m venv .venv
.venv\Scripts\activate                       # Windows; pe Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head                         # creeaza tabelele
python -m scripts.seed                       # date de test (parola: parola123)
python -m scripts.seed_demo                  # curs demo pentru raport + materiale demo
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
cd backend && ruff check . && pytest          # toate; rapid, fara Docker: pytest -m "not docker"
cd frontend && npm test
```

Documentația proiectului este în [docs/](docs/): [masterprompt.md](docs/masterprompt.md) (sursa adevărului),
[cerinte.md](docs/cerinte.md), [decizii.md](docs/decizii.md).

## Materiale de curs

Fișierele încărcate stau în `uploads/` (în afara git-ului). Pentru previzualizarea PPTX trebuie
instalat [LibreOffice](https://www.libreoffice.org/download/); pe Windows se găsește singur în
`C:\Program Files\LibreOffice`, altfel se setează `SOFFICE_PATH` în `.env`. Fără LibreOffice,
PDF-urile funcționează normal, iar un PPTX este refuzat cu un mesaj clar.

## Teste generate cu AI (opțional)

Profesorul poate genera testele unei teme cu Claude. Funcția apare doar dacă `backend/.env`
conține o cheie API Anthropic:

```bash
ANTHROPIC_API_KEY=sk-ant-...   # nu se pune niciodată în git
AI_MODEL=claude-sonnet-5-5
```

Ieșirile așteptate nu vin de la model: soluția lui de referință rulează în sandbox-ul Docker.
Testele generate sunt ciorne până când profesorul le aprobă.
