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

## Pasul 6 · Dashboard student și vederi profesor

- Datele agregate se calculează în backend, în `services/dashboard_service.py`: o pagină cere un singur endpoint, nu zeci de cereri mici.
- `GET /me/dashboard` întoarce temele publicate ale cursurilor studentului (ordonate după termen), cel mai bun scor, pătrățelele ultimei încercări, ultimele cinci trimiteri și cifrele din antet. `concepts_to_review` există în răspuns, dar rămâne gol până la Pasul 7.
- `GET /assignments/{id}/stats` folosește, pentru fiecare student înscris, **cea mai bună trimitere terminată** (`DISTINCT ON (student_id)`, ordonat după scor și dată): din ea vin rata de trecere pe test, distribuția scorurilor (0–25, 26–50, 51–75, 76–99, 100) și scorul mediu. Numărătorile folosesc `COUNT(*) FILTER (WHERE ...)`.
- Studenții care au părăsit cursul nu mai apar în statistici și în lista de trimiteri (join cu `enrollments`); trimiterile lor rămân în baza de date.
- `GET /assignments/{id}/submissions` întoarce acum pentru ambele roluri aceeași formă: `{items, total, page, page_size, counts}`. Studentul își vede doar trimiterile lui; profesorul are filtrele `verdict` (all, correct, partial, wrong, running), căutarea `q` după nume și paginarea. În căutare, `%` și `_` sunt tratate ca text.
- Lista de teme a profesorului are în plus `submitted_count`, `enrolled_count` și `result_buckets` (complet, parțial, zero), calculate dintr-o singură interogare pe curs.
- Au intrat și `GET /courses/{id}/stats` și `GET /users/me/activity?weeks=14` (un singur `GROUP BY` pe zi, în UTC). `concepts_mastered` rămâne 0 până la Pasul 7.
- Nu a fost nevoie de o migrare nouă: indexurile cerute aici există din migrarea `0002`.
- Frontend: dashboard-ul studentului (macheta 02), profilul (09), pagina cursului pentru profesor (10), editorul de temă cu `TestCaseForm` (12) și pagina de trimiteri cu statistici (14). Distribuția scorurilor e desenată cu Recharts și are un dublu text pentru cititoare de ecran.
- Pagina cursului are un rând de file cu o singură filă, Assignments; fila Materials vine în Pasul 8.
- Editorul salvează într-un singur pas: întâi detaliile temei, apoi testele (cele noi se creează, cele existente se actualizează, cele scoase din formular se șterg).
- Ecrane fără machetă, făcute din aceleași componente: „My courses” al profesorului (carduri și formular de curs nou) și fereastra cu codul unei trimiteri, deschisă din linkul „Code”.
- Diferențe față de machete: câmpul de indiciu apare la orice test, nu doar la cele ascunse (backend-ul îl acceptă pe toate); fiecare test are buton de ștergere; pagina cursului nu are butoane de ștergere pentru curs sau temă, deși rutele există.

## Plan · Pasul 9 nou: teste generate cu Claude (17.11.2026)

- Planul primește un pas nou, Pasul 9 („Teste generate cu Claude, legate automat de materiale”), după Pasul 8. Vechiul Pasul 9 (calitate și livrare) devine Pasul 10, vechiul Pasul 10 (predare) devine Pasul 11. Pasul 9 începe doar după ce pașii 0-8 sunt gata; MVP-ul nu depinde de el.
- D25: Claude prin SDK-ul oficial `anthropic`, model din `AI_MODEL` (implicit `claude-sonnet-5-5`), cheia în `ANTHROPIC_API_KEY`, niciodată în frontend sau în git. Revizuit pe 18.11.2026 (vezi „Pasul 9 · revizuire”).
- D26: `expected_output` se obține rulând soluția de referință în sandbox, nu din răspunsul modelului. Revizuit pe 18.11.2026: soluția e a profesorului.
- D27: paginile candidate se caută cu full-text search din PostgreSQL (`tsvector`, dicționar `simple`), fără embeddings.
- D28: testele generate sunt ciorne până la aprobarea profesorului; evaluarea le ignoră.
- D29: funcția e opțională: fără cheie, butonul nu apare și endpoint-urile răspund 503.
- Ajustări față de documentul primit, ca să se potrivească cu codul existent: rutele stau sub `/api/v1`; lista testelor e `GET /assignments/{id}/test-cases` (nu `/tests`); evaluarea e în `submission_service`, nu într-un `GradingService`; profesorul altui curs primește 404, nu 403 (convenția proiectului); dependința se adaugă în `pyproject.toml`; joburile blocate se recuperează la pornire, ca trimiterile. Constrângerea „fără chei API” din context devine „fără chei API obligatorii”.

## Pasul 7 · Concepte și raportul „unde greșești”

- D17: pentru fiecare student și temă contează cea mai recentă trimitere terminată (`done`), aleasă cu `DISTINCT ON (student_id, assignment_id)`. Trimiterile `error`, `queued` sau `running` nu contează, la fel temele nepublicate și studenții care au părăsit cursul.
- `report_service` e împărțit în două: `fetch_concept_rows` e singura funcție care interoghează baza (lanțul submissions → test_results → test_cases → test_case_concepts → concepts), iar `classify`, `aggregate_concepts` și `aggregate_class` sunt funcții pure, testate pe rânduri scrise de mână.
- Rata pe concept = teste trecute / teste, fără ponderi; un test cu două concepte contează la amândouă. Nivelurile: sub 50% `review`, de la 50% la sub 80% `progress`, de la 80% `mastered`; pragurile sunt în configurare (`CONCEPT_REVIEW_BELOW`, `CONCEPT_MASTERED_FROM`).
- Raportul clasei face media ratelor fiecărui student (nu a tuturor testelor la un loc), ca un student cu multe teste să nu cântărească mai mult decât ceilalți, și numără câți studenți sunt la `review` și câți la `mastered`.
- Testele ascunse apar în raportul studentului doar ca „Hidden test #n”, numerotate pe temă ca în rezultate.
- Golurile lăsate în Pasul 6 sunt completate: „To review” din dashboard (primele 3 concepte la `review`, din toate cursurile) și „concepts mastered” din profil.
- Frontend: pagina „Where you go wrong” (`/report`, cu alegerea cursului în adresă, `?course=`) și raportul clasei pentru profesor (`/courses/{id}/report`, o filă nouă lângă Assignments). Graficele Recharts au bare orizontale, cel mai slab concept sus, și un text echivalent pentru cititoare de ecran; nivelul e scris mereu, nu doar colorat.
- Pe telefon, nivelul trece sub numele conceptului și coloanele secundare se ascund, ca pagina să nu facă scroll orizontal.
- Cardul „Course summaries and practice questions” din macheta 05 nu există (decizie de dinainte de Pasul 0).
- `scripts/seed_demo.py` creează cursul „Python Basics (demo)” (cod `DEMOPY26`) cu trei studenți: Ana (bună la recursivitate, slabă la liste), Bogdan (slab aproape peste tot) și Carmen (bună peste tot). Fiecare are și o încercare mai veche, mai slabă, care nu trebuie să conteze.

## Pasul 8 · Materiale, Learn și recomandări

- Trei tabele noi (migrarea `0003`): `materials`, `assignment_materials`, `test_case_materials`. Fișierele stau pe disc, în `uploads/` (D21, în `.gitignore`); în baza de date rămân doar metadatele.
- `FileStore` e singurul cod care atinge discul: numele sunt `uuid4` + extensie, generate de server, și sunt verificate cu o expresie regulată înainte de orice acces. Nimic venit de la client (nume de fișier, titlu) nu devine cale.
- Încărcarea se citește în bucăți de 1 MB și se oprește la 20 MB (413), indiferent de antetul `Content-Length`. Tipul se decide după primii octeți (`%PDF-`, sau o arhivă ZIP care conține `ppt/presentation.xml`), nu după extensie (415). Un PDF stricat sau cu parolă dă 422.
- Un PPTX e verificat înainte de conversie: cel mult 2000 de intrări și 200 MB despachetat (arhivă bombă → 415). Conversia (D20) e sincronă, cu LibreOffice headless, profil temporar propriu, timeout de 60 s și una singură odată. Dacă eșuează, 422 și nimic nu rămâne pe disc. **LibreOffice nu e instalat pe calculatorul de dezvoltare**: până la instalare, un PPTX primește 422 cu mesaj clar, iar testul cu conversie reală (marker `libreoffice`) e sărit.
- Servirea: `/preview` trimite PDF-ul inline, `/file` originalul ca attachment cu numele curățat; ambele cu `X-Content-Type-Options: nosniff` și doar pentru membrii cursului. `uploads/` nu e servit static.
- La ștergerea unui material sau a unui curs, rândurile dispar prin cascade, iar fișierele se șterg după commit, ca o eroare de disc să nu strice o tranzacție terminată.
- Legăturile cu temele și testele se înlocuiesc complet cu `PUT`, într-o singură tranzacție. Paginile (D23) se validează cu `parse_pages` (numere și intervale, în limitele documentului, fără intervale inversate; gol = tot materialul) și se salvează normalizate („12-15, 18”). Un material din alt curs dă 422.
- Recomandările (`build_recommendations`, funcție pură): pentru fiecare test picat, materialele testului; dacă nu are, cele ale temei. Un material apare o dată, cu paginile unite, sortat după câte teste picate îl cer. Se calculează la cerere, nu se salvează. Testele ascunse apar ca „Hidden test #n”.
- Extinderi de contract aprobate: `Material.category` (`lecture`/`lab`) pentru filtrele din Learn și `used_in` în lista de materiale (studenții văd doar temele publicate). Adăugate în acest pas, ca să existe datele de care ecranele au nevoie: `GET /materials/{id}` (pentru vizualizator) și câmpul `materials` pe testele văzute de profesor (pentru editorul de legături).
- Frontend în stilul 8-bit din prototip: Learn (carduri cu copertă generată din culoarea cursului și recomandarea după ultima încercare), pagina cursului cu filtrele All/Lectures/Labs, vizualizatorul cu react-pdf (pagina din adresă `?page=`, paginile recomandate `?rec=` evidențiate, săgețile tastaturii), popup-ul „Review before your next attempt” (o singură dată pe trimitere, ținut minte în `sessionStorage`; butonul „Recommended pages” îl redeschide), cardul „Study materials” pe pagina temei, fila Materials a profesorului și editorul „Study materials” pentru temă și teste.
- Din prototip nu s-au construit progresul de citire, vizitele și capitolele: nu au sursă în backend.
- `scripts/seed_demo.py` adaugă la cursul din seed „Lecture 4: Loops and digit extraction” (PDF de 28 de pagini, generat în script), legat de toată tema și, cu paginile 12-15, de testul ascuns. PPTX-ul demo se adaugă doar dacă LibreOffice e instalat.

## Pasul 9 · Teste generate cu Claude, legate automat de materiale

- Migrarea `0004`: tabelele `generation_jobs` și `material_pages` (coloană `tsv` generată din text cu `to_tsvector('simple', ...)`, index GIN), coloanele `source`, `review_status`, `generation_job_id`, `ai_rationale` pe `test_cases` și `text_pages` pe `materials`. Testele existente devin automat `manual` și `approved`.
- `LLMClient` e o interfață, ca `Runner`: `ClaudeClient` (SDK-ul oficial `anthropic`) și `FakeLLMClient` (răspunsuri scrise dinainte, folosit în toate testele; niciun test nu ajunge la rețea și niciun test nu vede o cheie reală, nici dacă `.env` are una).
- `ClaudeClient` cere răspunsul ca JSON constrâns de o schemă (structured outputs), cu timeout `AI_TIMEOUT_S` și 2 reîncercări cu așteptare exponențială la 429/5xx (făcute de SDK). Are activată reluarea pe alt model dacă un filtru de siguranță refuză cererea (`fallbacks: "default"`); un refuz final sau un răspuns tăiat la `max_tokens` e o eroare, nu se parsează pe jumătate. Un răspuns invalid se mai cere o dată, apoi jobul trece în `error`. Efortul modelului se poate regla din `AI_EFFORT` (implicit `high`).
- D26 în cod: modelul nu scrie ieșiri. Soluția de referință rulează în sandbox pe fiecare intrare, prin același `Runner` și același semafor ca trimiterile; ieșirea ei devine `expected_output`. Intrările pe care soluția dă eroare sau depășește limitele se elimină (`tests_kept < tests_proposed`). Primul test rulează de două ori; ieșiri diferite = soluție nedeterministă = job `error`.
- Conceptele propuse se potrivesc cu cele ale cursului fără diacritice și fără majuscule; numele necunoscute se ignoră, nu se creează.
- D28: ciornele nu contează nicăieri: evaluarea, scorul, `total_count`, lista de teste a studentului, statisticile, raportul pe concepte și recomandările folosesc doar testele aprobate. În editor, ciornele stau într-un panou separat, nu în formular, pentru că salvarea formularului șterge testele care lipsesc din el.
- D27: paginile candidate se caută cu `ts_rank` pe `tsvector`. Abatere de la document: în loc de `plainto_tsquery` (care cere ca o pagină să conțină **toate** cuvintele, deci aproape nu găsește nimic) se folosește `to_tsquery` cu cuvintele legate prin SAU; paginile cu mai multe cuvinte comune ies primele. Cuvintele trec printr-un filtru (doar litere și cifre, minimum 3), deci nu pot strica interogarea.
- Propunerea de material se păstrează doar dacă materialul e din cursul temei, a fost printre candidați, iar paginile respectă formatul D23 și există în PDF. Textul paginilor intră în prompt marcat ca date, nu ca instrucțiuni.
- Textul paginilor se extrage în fundal după fiecare încărcare; pentru fișierele mai vechi există `POST /materials/{id}/reindex` și `python -m app.cli reindex-materials`. Un PDF fără text (scanat) are `text_pages = 0`, iar fila Materials scrie „No text found, link pages manually”.
- Faza jobului („Writing reference solution”, „Running in sandbox”, „Linking materials”) se deduce din câmpurile deja completate (`tests_proposed`, `tests_kept`), fără o coloană nouă. Câmp adăugat: `tests_requested`, ca jobul din fundal să știe câte teste s-au cerut.
- Securitate și cost: un singur job activ pe temă (409), cel mult `AI_MAX_JOBS_PER_HOUR` pe profesor (429), enunțul trimis e tăiat la 8 000 de caractere, codul studenților nu se trimite niciodată. Cheia stă doar în `.env`, ca `SecretStr`, și nu apare în răspunsuri (verificat de un test). Tokenii se salvează pe job și se văd lângă soluția de referință.
- Fără cheia furnizorului ales (`NVIDIA_API_KEY` sau, cu `AI_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`), `GET /config` spune `ai_available: false`, butonul nu apare, iar rutele de generare răspund 503 (D29).
- Model implicit la prima versiune: `claude-sonnet-5-5`; după revizuire, un model din catalogul NVIDIA (acum `qwen/qwen3-next-80b-a3b-instruct`). Se schimbă din `AI_MODEL`.
- Diagrame: cazul de utilizare „Generare teste cu AI” (cu actorul secundar API-ul modelului) și secvența 7e în `docs/uml/secventa-generare-teste.puml`. Diagramele de clase și ER se desenează în Pasul 11, odată cu restul.

## Pasul 9 · revizuire (18.11.2026): soluția profesorului, catalogul NVIDIA

- D26 revizuit: modelul nu mai scrie cod. Profesorul lipește soluția lui de referință în editor, lângă buton; `POST /assignments/{id}/generate-tests` o primește în `reference_solution` (obligatorie, 422 dacă lipsește sau e goală) și o salvează pe job în `reference_code`. Modelul primește enunțul și soluția și întoarce doar `{tests: [...]}` (intrări, concepte, ascuns, pondere, motiv). Restul regulilor rămân: soluția rulează în sandbox pe fiecare intrare, intrările pe care pică se elimină, primul test rulează de două ori.
- Motivul: platforma e gândită ca elevul să scrie cod, iar AI-ul doar să ajute la teste. O soluție scrisă de model poate fi greșită, iar ieșirile ei ar deveni teste greșite; soluția profesorului e sursa de adevăr.
- D25 revizuit: furnizorul implicit e catalogul NVIDIA (build.nvidia.com), care dă o cheie gratuită pentru dezvoltare. Endpoint-ul e compatibil OpenAI, deci `NvidiaClient` folosește SDK-ul oficial `openai` cu `AI_BASE_URL=https://integrate.api.nvidia.com/v1`. Model ales inițial: `meta/llama-3.3-70b-instruct` (urmează bine instrucțiunile și răspunde în JSON; nu mai trebuie să scrie cod). Claude rămâne disponibil cu `AI_PROVIDER=anthropic` și `ANTHROPIC_API_KEY`; ambele chei sunt `SecretStr` și nu apar în răspunsuri, loguri sau git.
- Endpoint-ul NVIDIA nu are câmp pentru o schemă JSON, așa că schema intră în mesajul de sistem, răspunsul se curăță (bloc ```json sau text în jur) și se validează cu Pydantic; un răspuns invalid sau tăiat se mai cere o dată, apoi jobul trece în `error`. Temperatura e 0.2, ca intrările să fie stabile.
- Faza „Writing reference solution” devine „Proposing test inputs”.
- Modelul implicit devine `nvidia/nemotron-3-ultra-550b-a55b` (tot 18.11.2026). `meta/llama-3.3-70b-instruct` nu mai are endpoint gratuit (doar parteneri cu plată), iar `qwen/qwen3-next-80b-a3b-instruct` răspunde 410 (retras). Din lista întoarsă de `GET /v1/models` pentru cheia proiectului, Nemotron 3 Ultra a dat JSON corect cel mai repede; Mistral Large 4 a mers, dar în 80 s, iar GLM 5.3 Flash și Kimi K3.1 n-au răspuns. Se schimbă din `AI_MODEL`, fără cod nou.
- Ajustări după verificarea reală: modelul scria literal intrarea „mare” (zeci de mii de numere) și răspunsul se tăia, deci promptul limitează fiecare intrare la 2000 de caractere („mare” = valori mari sau o listă de zeci până la câteva sute de elemente). `max_tokens` urcă la 8192, pentru că modelele care gândesc consumă o parte din el înainte de JSON. `AI_TIMEOUT_S` implicit urcă la 120 s. O schemă impusă prin `response_format` nu ajută pe acest endpoint (răspunsul se umflă până la limită), deci rămâne schema în prompt, cu validare și o reîncercare.
- Verificarea reală (cursul „Procedural Programming”, 3 teme: suma cifrelor, al doilea maxim, cuvinte palindrom): 8 din 8 intrări păstrate la fiecare, ieșiri corecte, legare de pagini la 8, 4 și 4 ciorne. Durata: 161-251 s, peste ținta de 2 minute: aproape tot timpul e legarea, un apel pe test. Pasul următor: un singur apel de legare pentru toate testele.
