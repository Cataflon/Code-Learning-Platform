# Jurnal de decizii

Câte un rezumat scurt pe pas: ce s-a construit și de ce. Deciziile mari au și un ADR în `docs/adr/`.

## Înainte de Pasul 0 · corecturi în document (12.11.2026)

- Un singur nume pentru starea temei: `is_published` (coloană și câmp API).
- `full_name` peste tot, inclusiv în `PATCH /users/me`.
- `max_submissions` are implicit 10 (ca în macheta 03).
- Pagina de curs a profesorului are file din Pasul 6; fila Materials apare în Pasul 8.
- Cardul „Course summaries and practice questions” din macheta 05 se scoate: nu există o etapă următoare.
- Contractul se extinde pentru macheta 07: `Material.category` (`lecture` sau `lab`) și `used_in` în lista de materiale.
- Cele 6 endpoint-uri din „Interfață ↔ API” sunt trecute și în tabelul „Contractul API”.
- Regula de git s-a schimbat: fiecare pas are ramura lui, împinsă pe GitHub; merge-ul în `main` îl face proprietarul.

## Pasul 0 · Fundații

- Monorepo cu `backend/` (FastAPI) și `frontend/` (React + Vite); PostgreSQL 16 rulează prin docker-compose.
- Backend-ul rulează pe gazdă, într-un `venv`, ca să fie ușor de depanat; doar baza de date e în container.
- PostgreSQL e publicat pe portul gazdă **5433**, pentru că 5432 era ocupat de un PostgreSQL instalat local.
- Python 3.15 pe calculatorul de dezvoltare (documentul cerea 3.12; `requires-python >= 3.12`, iar CI rulează pe 3.12). Imaginea sandbox rămâne pe 3.12.
- Configurarea vine din variabile de mediu prin `pydantic-settings`; `.env` nu intră în git.
- În dezvoltare, Vite trimite `/api` și `/health` prin proxy către backend, deci browserul vede o singură origine și nu apar probleme CORS.
- D3 = JavaScript, D11 = Tailwind CSS 3 (documentul cere `tailwind.config.js`, formatul versiunii 3), D1 = engleză în cod și interfață.
- Culorile și fonturile variantei D sunt definite o singură dată în `frontend/tailwind.config.js`; fonturile vin din pachetele `@fontsource`, ca demo-ul să meargă fără internet.
