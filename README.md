# Code Learning Platform

Platformă web de programare cu autograder. Profesorul creează cursuri, teme și teste legate de
concepte și încarcă materialele de curs. Studentul trimite cod Python, care rulează izolat în
Docker, primește un verdict pe fiecare test și vede, pe concepte, unde greșește și ce pagini din
curs să recitească. Opțional, testele unei teme se pot genera cu AI.

## Ce face

- **Student:** se înscrie la curs cu un cod, scrie codul în browser (Monaco), primește verdictul pe
  fiecare test în câteva secunde, vede raportul pe concepte („Where you go wrong”), citește
  materialele în Learn și primește paginile recomandate după un test picat.
- **Profesor:** cursuri, teme, teste cu concepte, ponderi și teste ascunse, materiale PDF/PPTX
  legate de teme și teste, statistici pe clasă, generarea testelor cu AI (ciorne aprobate de el).
- **Admin tehnic:** lista tuturor conturilor, roluri, conturi dezactivate, parole temporare și
  coduri de invitație pentru profesori.

## Arhitectura pe scurt

```text
browser (React + Vite, tema 8-bit)
   │  /api/v1  (JSON, JWT)
FastAPI ── servicii ── SQLAlchemy ── PostgreSQL
   │
   ├─ Runner ── DockerRunner: un container de unică folosință pe test
   │             (fără rețea, rădăcină read-only, limite de timp, memorie, CPU și procese)
   ├─ FileStore + LibreOffice: materialele PDF/PPTX din uploads/
   └─ LLMClient: Gemini / NVIDIA / Claude, doar pentru generarea testelor (opțional)
```

Trimiterile rulează în fundal: API-ul răspunde imediat cu 202, iar pagina face polling până la
rezultat. Detaliile și deciziile sunt în [docs/decizii.md](docs/decizii.md), contractul API în
[docs/api.md](docs/api.md), lista de securitate în [docs/securitate.md](docs/securitate.md).

## Pornire în dezvoltare (implicit)

Ai nevoie de Docker Desktop, Python 3.12+ și Node 22. Baza de date rulează în Docker, backend-ul
și frontend-ul pe calculatorul tău:

```bash
docker compose up -d db                      # 1. PostgreSQL pe localhost:5433
docker build -t autograder-python sandbox    # 2. imaginea în care rulează codul studenților
cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -e ".[dev]"
alembic upgrade head && python -m scripts.seed && python -m scripts.seed_demo   # 3. tabele + date
uvicorn app.main:app --reload                # 4. http://localhost:8000/docs
```

Pe Linux/macOS, activarea mediului este `source .venv/bin/activate`. În alt terminal:

```bash
cd frontend && npm install && npm run dev    # 5. http://localhost:5173
```

Conturi create de seed (parola `parola123` la toate):

| Rol | Email |
| --- | --- |
| profesor | `maria.ionescu@utcluj.ro` |
| studenți | `andrei.pop@student.utcluj.ro`, `ana.recursion@student.utcluj.ro` și încă 8 în cursul demo |
| admin | `admin@utcluj.ro` |

## Demo într-o singură comandă (profilul `demo`)

Pentru un calculator fără Python sau Node, totul rulează în containere:

```bash
docker compose --profile demo up --build     # prima dată durează câteva minute
```

Aplicația e pe http://localhost:8080, cu datele demo încărcate. Cheile AI, dacă vrei generarea
testelor, se pun în `backend/.env` (vezi mai jos); profilul le citește de acolo.

> **Atenție — `docker.sock`.** În profilul `demo`, backend-ul pornește containerele sandbox prin
> socket-ul Docker al gazdei (`/var/run/docker.sock`). Accesul la acest socket echivalează cu
> drepturi de administrator pe calculator: cine controlează backend-ul controlează gazda. Folosește
> profilul doar pe calculatorul tău, niciodată pe un server accesibil altora. În modul de
> dezvoltare, backend-ul rulează pe gazdă și problema nu apare (decizia D10).

## Teste

```bash
cd backend && ruff check . && ruff format --check . && pytest   # fără Docker: pytest -m "not docker"
cd frontend && npm run lint && npm test && npm run build
```

CI-ul (GitHub Actions) rulează aceleași comenzi, cu PostgreSQL ca serviciu, testele de izolare a
sandbox-ului cu Docker și verificarea profilului `demo`. `docs/api.md` se regenerează cu
`python -m scripts.export_openapi`; un test cade dacă a rămas în urmă față de rute.

## Configurare

Toate setările vin din variabile de mediu sau din `backend/.env` (vezi
[.env.example](.env.example)); niciun secret nu stă în cod. Cele mai importante: `DATABASE_URL`,
`JWT_SECRET`, `CORS_ORIGINS`, limitele sandbox-ului (`SANDBOX_*`, `MAX_CONCURRENT_RUNS`) și
limitele de cereri (`RATE_LIMIT_*`). Fiecare răspuns are antetul `X-Request-ID`, care apare și în
fiecare linie de log a cererii.

## Materiale de curs

Fișierele încărcate stau în `uploads/` (în afara git-ului; în profilul demo, într-un volum).
Pentru previzualizarea PPTX trebuie [LibreOffice](https://www.libreoffice.org/download/); pe
Windows se găsește singur în `C:\Program Files\LibreOffice`, altfel se setează `SOFFICE_PATH`.
Imaginea Docker a backend-ului îl conține deja. Fără LibreOffice, PDF-urile merg normal, iar un
PPTX e refuzat cu un mesaj clar.

## Administrare

Contul `admin` vede toți utilizatorii, le poate schimba rolul, îi poate dezactiva sau le poate da
o parolă temporară și generează codurile de invitație cu care se înregistrează profesorii.
Primul admin se creează din terminal:

```bash
cd backend
python -m app.cli create-admin admin@exemplu.ro "Nume Admin"   # cere parola
```

## Teste generate cu AI (opțional)

Profesorul scrie titlul și enunțul și apasă „Generate tests with AI”. Modelul scrie soluția de
referință și intrările testelor, iar, separat și în paralel, o a doua soluție independentă.
Ieșirile așteptate nu vin de la model: soluția rulează în sandbox pe fiecare intrare. Soluția
trebuie să treacă exemplul din enunț, iar testele la care cele două soluții diferă sunt marcate
„solutions disagree”. Dacă profesorul lipește propria soluție, modelul propune doar intrările.
Testele generate sunt ciorne până când profesorul le aprobă.

Funcția apare doar dacă `backend/.env` conține o cheie. Implicit se folosește Gemini, cu o cheie
gratuită de pe [aistudio.google.com](https://aistudio.google.com) („Get API key”):

```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=...              # nu se pune niciodată în git
```

Modelul implicit e `gemini-3.5-flash`; când e aglomerat (503), se trece automat pe
`gemini-3.5-flash-lite` și `gemini-3.1-flash-lite`. Alternative: `AI_PROVIDER=nvidia` cu
`NVIDIA_API_KEY` sau `AI_PROVIDER=anthropic` cu `ANTHROPIC_API_KEY` (Claude).

## Limite cunoscute

- Doar Python 3.12, cu biblioteca standard.
- Un singur proces de backend: trimiterile din fundal, semaforul sandbox-ului și limitele de
  cereri stau în memorie.
- Pe varianta gratuită, generarea cu AI depinde de cât de aglomerat e furnizorul.
- Documentația completă a proiectului: [docs/masterprompt.md](docs/masterprompt.md) (planul),
  [docs/cerinte.md](docs/cerinte.md), [docs/decizii.md](docs/decizii.md).
