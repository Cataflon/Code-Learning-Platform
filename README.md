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

Profesorul scrie titlul și enunțul și apasă „Generate tests with AI”. Modelul scrie soluția de
referință și intrările testelor, iar într-o cerere separată o a doua soluție, independentă.
Ieșirile așteptate nu vin de la model: soluția rulează în sandbox-ul Docker pe fiecare intrare.
Soluția trebuie să treacă exemplul din enunț, iar testele la care cele două soluții dau
rezultate diferite sunt marcate „solutions disagree”. Dacă profesorul lipește propria soluție,
modelul propune doar intrările. Testele generate sunt ciorne până când profesorul le aprobă.

Funcția apare doar dacă `backend/.env` conține o cheie. Implicit se folosește Gemini, cu o cheie
gratuită de pe [aistudio.google.com](https://aistudio.google.com) („Get API key”):

```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=...              # nu se pune niciodată în git
```

Modelul implicit e `gemini-3.5-flash`; când e aglomerat (503), se trece automat pe
`gemini-3.5-flash-lite` și `gemini-3.1-flash-lite`. Alternative: `AI_PROVIDER=nvidia` cu
`NVIDIA_API_KEY` (catalogul NVIDIA) sau `AI_PROVIDER=anthropic` cu `ANTHROPIC_API_KEY` (Claude).
