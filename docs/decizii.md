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

## Pasul 1 · Modelul de date și CRUD

- Șapte tabele create prin prima migrare Alembic (`0001`): users, courses, enrollments, assignments, concepts, test_cases și tabelul de legătură test_case_concepts.
- Straturi stricte: routerele validează cu scheme Pydantic și apelează servicii; doar serviciile scriu interogări; modelele descriu tabelele.
- Schemele `Read` sunt separate de modele, deci `password_hash` nu poate ajunge într-un răspuns. Studentul primește `TestCasePublicRead`, fără greutate și indiciu, și doar testele publice.
- Erorile de domeniu (`NotFoundError`, `ConflictError`, `InvalidDataError` etc.) sunt transformate într-un singur loc în JSON `{"detail", "code"}`.
- Autentificarea e un substitut: `get_current_user` citește antetul `X-Debug-User-Id` sau ia primul profesor din seed. Routerele folosesc deja dependențele `*_for_member` și `*_for_owner`, pe care Pasul 2 le umple cu verificări reale fără să atingă routerele.
- Rolul e stocat ca text (enum ne-nativ), ca migrările să nu depindă de tipuri ENUM din PostgreSQL.
- `join_code` are 8 caractere dintr-un alfabet fără 0/O și 1/I. Câmpurile cerute de machete (`color`, `max_submissions`, `hint`) sunt în model de la început.
- Testele rulează pe baza `autograder_test`, fiecare într-o tranzacție anulată la final. Un test separat aplică migrările pe o bază goală, verifică cu `alembic check` că modelele și migrările coincid, apoi face downgrade.
