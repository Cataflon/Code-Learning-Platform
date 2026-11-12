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

## Pasul 2 · Autentificare, roluri și scheletul frontend

- Autentificare fără sesiune pe server: token JWT (HS256) cu `sub`, `role` și `exp`, valabil 60 de minute; fără refresh token în MVP.
- Parolele sunt hash-uite cu Argon2id prin `pwdlib`; minimum 8 caractere. Login-ul întoarce același mesaj pentru email necunoscut și parolă greșită.
- D5: contul de profesor cere codul de invitație din `TEACHER_INVITE_CODE`. D7: token-ul stă în `localStorage` (simplu, dar expus la XSS; alternativa cu cookie `httpOnly` ar cere protecție CSRF).
- Login-ul folosește formularul OAuth2 (`username` poartă emailul), ca butonul „Authorize” din Swagger să funcționeze.
- Regulile de acces stau în dependențe: fără token 401, rol greșit 403, resursă din alt curs 404 (ca să nu se afle că există). Studentul primește 404 și pentru o temă nepublicată.
- Matricea de permisiuni e un singur test parametrizat, cu o linie pe (actor, metodă, cale); orice rută nouă adaugă linii.
- Au intrat și rutele de profil din „Interfață ↔ API”: `PATCH /users/me`, `POST /users/me/password`, `DELETE /courses/{id}/enrollment`, `POST /courses/{id}/join-code`.
- Frontend: `apiFetch` adaugă token-ul și face logout la 401; `AuthContext` reîncarcă profilul după refresh; `ProtectedRoute` trimite vizitatorul la login și rolul greșit la pagina lui.
- Componentele comune (`ui.jsx`, `VerdictSquares`, `states.jsx`) reproduc stilul machetelor; iconițele vin din `lucide-react` (dependență în plus față de tabelul de tehnologii).
- Formularul de înregistrare nu are machetă: folosește același cadru ca pagina Sign in.

## Pasul 3 · Trimiteri și evaluare, prototip

- `Runner` e un `typing.Protocol`: serviciul de evaluare depinde de formă (`run(code, stdin, limits) -> RunResult`), nu de o implementare. Runner-ul se obține dintr-o singură dependență, `get_runner()`.
- `SubprocessRunner` e doar prototip local: nu e sandbox, nu aplică limita de memorie și nu se folosește cu cod necunoscut.
- D4: teste pe stdin și stdout. D13: comparația ignoră spațiile de la capătul liniilor și liniile goale de la final. D14: scorul e procentul din greutatea testelor trecute.
- Verdictul se decide într-o funcție pură, în ordinea: timp depășit, memorie depășită, cod de ieșire diferit de 0, apoi compararea outputului.
- Evaluarea salvează câte un `TestResult` imediat după fiecare test; o excepție din runner duce trimiterea în `error`, niciodată blocată în `running`.
- Pentru student, un test ascuns apare ca „Hidden test #n”, fără input, output așteptat, output obținut sau stderr. Indiciul apare doar dacă testul a picat.
- O trimitere e refuzată cu 409 dacă termenul a trecut sau nu mai sunt încercări (`max_submissions`), și cu 422 dacă tema nu are teste sau codul trece de 64 KB.
- `error_excerpt` rezumă primul traceback (de exemplu `IndexError, line 4`).
- În acest pas `POST .../submissions` e sincron și răspunde 201 cu rezultatele; Pasul 5 îl face asincron (202).
- Indexurile pe `submissions` și `test_results` din „Modelul de date” sunt deja în migrarea `0002`.

## Pasul 4 · Sandbox Docker

- `DockerRunner` implementează aceeași interfață `Runner`; în afară de `runner/factory.py`, niciun alt cod nu s-a schimbat.
- Un container nou pe test, șters în `finally`, cu eticheta `autograder=1`; după fiecare test Docker se verifică automat că nu a rămas niciunul.
- Limitele (D12): fără rețea, memorie și swap egale cu limita temei, 0,5 CPU, 64 de procese, rootfs doar pentru citire cu `/tmp` de 16 MB în memorie, `cap_drop=ALL`, `no-new-privileges`, uid 10001, loguri limitate la 1 MB, output trunchiat la 64 KB.
- D9 (vezi `docs/adr/0001-livrare-cod.md`): codul ajunge în container printr-un director temporar montat doar pentru citire. `put_archive` nu merge cu rootfs `read_only`.
- Memoria depășită se detectează din `State.OOMKilled` sau din codul de ieșire 137 atunci când nu noi am oprit containerul. În CI (Linux, cgroup v2) fanionul `OOMKilled` a rămas o dată fals deși nucleul omorâse procesul, de aceea nu ne bazăm doar pe el. După un timeout, 137 vine din `kill()`-ul nostru și nu se consideră memorie. Comanda folosește `exec`, ca Python să fie procesul principal.
- Timpul raportat e durata containerului (`StartedAt`–`FinishedAt`); așteptarea maximă e limita temei plus marja de pornire de 2 s.
- `RUNNER=docker` e implicit; `RUNNER=subprocess` e refuzat la validarea configurării dacă `ENV` nu e `dev`.
- Un semafor global (`MAX_CONCURRENT_RUNS`, implicit 2) limitează evaluările simultane, deci și containerele.
- D10: backend-ul rămâne pe gazdă; Python 3.12 în sandbox, fără biblioteci externe.
- Suita de contract rulează aceleași 14 programe pe ambele runner-e; suita adversarială are 16 teste. În CI se construiește imaginea și se rulează și testele cu markerul `docker`.

## Pasul 5 · Execuție asincronă și pagina temei

- `POST /assignments/{id}/submissions` creează trimiterea `queued`, programează `run_submission` cu `BackgroundTasks` și răspunde 202 imediat (măsurat: circa 40 ms). Clientul interoghează `GET /submissions/{id}` o dată pe secundă până la `done` sau `error`.
- D8: `BackgroundTasks` cu semafor, fără worker separat. `run_submission` primește doar id-ul, deci poate fi mutată într-un worker fără modificări.
- Funcția din fundal își deschide propria sesiune de bază de date: sesiunea cererii se închide odată cu răspunsul.
- Semaforul (`MAX_CONCURRENT_RUNS`, implicit 2) e ținut pe toată durata unei evaluări. O trimitere rulează testele pe rând, deci semaforul limitează și numărul de containere.
- La pornire (`lifespan`), trimiterile rămase `queued` sau `running` devin `error` cu mesaj clar, iar containerele de sandbox rămase de la un server oprit forțat sunt șterse. Verificat manual: server oprit în timpul unei rulări, apoi repornit.
- Între două trimiteri ale aceluiași student la aceeași temă trebuie să treacă `MIN_SUBMISSION_INTERVAL_S` (implicit 5 secunde), altfel 429 cu antetul `Retry-After`.
- D16: fără buton separat de rulare de probă; doar „Submit”.
- Pagina temei urmează macheta 03: enunț în Markdown (`react-markdown`, fără HTML brut), exemple din testele publice, editor Monaco, pătrățelele de verdict, rezultatul pe test cu concept, timp și indiciu.
- Monaco e împachetat local (doar nucleul și gramatica Python) și încărcat leneș, ca demo-ul să meargă fără internet. Ciorna stă doar în `localStorage`, iar interfața spune asta.
- Diferență față de machetă: la un test public picat se afișează în plus input-ul, outputul așteptat și cel obținut. Rândul „Limit on n” din machetă nu are câmp în backend; limitele problemei se scriu în enunț.
- Pagina „Courses” a studentului nu are machetă: listează cursurile cu temele publicate și formularul de înscriere, din aceleași componente.
- Proxy-ul Vite țintește `127.0.0.1`, nu `localhost`: pe Windows, `localhost` încearcă întâi IPv6 și adaugă circa 2 secunde la fiecare conexiune nouă.
