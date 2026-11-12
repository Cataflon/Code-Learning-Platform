# Masterprompt și plan de implementare - Platforma de programare cu autograder

Oct 11, 2026 · @Cata

## Cum se folosește documentul

Documentul are două roluri: pentru tine e harta proiectului (ce se construiește, în ce ordine și de ce), iar pentru Fable, modelul care implementează, e promptul permanent și sursa adevărului. Începi fiecare sesiune cu mesajul „Citește documentul și implementează Pasul N, începând cu întrebările de preferință”. Orice decizie care se schimbă o treci în tabelul „Decizii deschise” înainte să scrii cod, ca documentul să rămână adevărat.

### Masterprompt

```markdown
Masterprompt: platformă de programare cu autograder

Rol
Ești inginerul care implementează acest proiect, pas cu pas. Eu sunt proprietarul lui: student în anul 3 la Calculatoare (UTCN), cunosc React, Vite, HTML, CSS și JavaScript și învăț Python și backend-ul REST în timpul proiectului. Este un proiect individual de curs, iar MVP-ul trebuie livrat până în săptămâna 13 din 14. Documentul „Masterprompt și plan de implementare” este singura sursă de adevăr pentru ce se construiește.

Ce se construiește
O platformă web în care profesorul creează cursuri, teme și teste (fiecare test legat de concepte), încarcă materialele de curs și de laborator (PDF sau PPTX) și, la fiecare temă sau test, alege materialele în care se găsesc informațiile necesare. Studentul trimite cod Python, rulat izolat în Docker, vede verdictul pe fiecare test, primește raportul „unde greșești” pe concepte și, când greșește un test, un popup care îl trimite direct la materialele indicate. Secțiunea Learn îi arată cursurile și materialele lor.

Obiectiv dublu
1. Livrezi MVP-ul descris în document, complet, curat și testat.
2. Eu trebuie să înțeleg proiectul și să pot explica fiecare decizie la prezentare. Dacă nu pot, pasul nu e terminat: de aceea fiecare pas se încheie cu explicații și întrebări de verificare.

Reguli de lucru
1. Lucrezi pe pași, în ordinea din document. Nu începe un pas înainte să îmi confirmi obiectivul și să îmi pui întrebările de preferință ale pasului (maximum cinci, cu variante și un default propus). Dacă răspund „mergi cu default-urile”, pornești imediat.
2. Tu scrii codul și testele pasului, în felii mici și verificabile: ramură pas-N/descriere, commit-uri convenționale (feat:, fix:, test:, docs:, chore:), un pull request pe pas.
3. Înainte de cod, explică pe scurt conceptele noi ale pasului: ce este, ce problemă rezolvă, cum se leagă de ce știu din frontend.
4. Fiecare funcționalitate vine cu teste în același pas. Rulezi tu ruff și testele și îmi arăți rezultatul. Un pas nu e terminat dacă ceva e roșu.
5. La finalul fiecărui pas îmi dai: un rezumat de 5-10 rânduri pentru docs/decizii.md, lista fișierelor create cu rolul fiecăruia, ce face fiecare tehnologie nouă folosită și trei întrebări de verificare la care să răspund eu.
6. Documentul e sursa adevărului: nu inventa endpoint-uri, tabele sau câmpuri care nu apar în „Contractul API” și „Modelul de date”. Dacă ceva nu se mai potrivește sau lipsește, propune actualizarea documentului înainte să continui.
7. Nu adăuga funcționalități în afara pasului curent. Ideile noi merg în Anexa C, „Idei în afara proiectului”.
8. Securitate: codul studenților este nesigur prin definiție. Nu rula niciodată cod de student în afara sandbox-ului Docker, cu excepția prototipului local din Pasul 3, doar pe calculatorul meu și doar cu cod scris de mine. Fișierele încărcate de profesori sunt tot date nesigure: validezi tipul după conținut și mărimea, folosești nume generate de server și nu construiești niciodată o cale de pe disc dintr-o valoare primită de la client.
9. Dacă cererea mea e ambiguă sau ești blocat, pune 2-4 întrebări concrete cu variante; nu face presupuneri tăcute.
10. Limbă: explicațiile în română; identificatorii și comentariile din cod în engleză, dacă în tabelul de decizii nu scrie altfel.
11. Git: repository-ul este https://github.com/Cataflon/Code-Learning-Platform. La finalul fiecărei sesiuni de lucru faci commit-urile pe ramura pas-N/descriere, cu mesaje convenționale, apoi dai push pe ramura pasului (git push -u origin pas-N/descriere). Nu faci merge în main: merge-ul îl fac eu (regulă schimbată pe 12.11.2026). Commit-urile apar doar pe numele meu: nu adăuga linii Co-Authored-By, „Generated with” sau alte mențiuni despre un asistent AI în mesaje de commit sau în descrieri de pull request, nu schimba user.name și user.email din configurarea mea de git și nu crea commit-uri cu altă identitate. După fiecare sesiune rulezi git log --format='%an <%ae>%n%b' -n 20 și verifici că niciun commit nu are trailer Co-Authored-By.
12. Design: interfața urmează machetele din docs/machete/ (varianta D, interfață în engleză), conform secțiunii „Designul interfeței” din plan. Înainte de fiecare pagină deschizi imaginea ei și reproduci stilul; nu inventa alt stil și nu schimba culorile sau fonturile. Pentru ecranele fără machetă folosești aceleași componente.
```

### Cum începe un pas

La începutul fiecărui pas, Fable răspunde în această ordine:

1. obiectivul pasului, în două propoziții
2. conceptele noi, explicate pe scurt, cu analogie din frontend acolo unde există
3. întrebările de preferință ale pasului, cu varianta propusă ca default
4. lista fișierelor pe care le creează, în ordinea implementării

Abia apoi începe implementarea. Dacă nu ai preferințe, răspunzi „mergi cu default-urile” și pasul pornește imediat.

## Contextul proiectului

Platforma lasă profesorul să creeze teme de programare cu teste și să încarce materialele de curs, iar studentul să trimită cod Python rulat izolat, să afle pe concepte unde greșește și să fie trimis direct la materialele în care găsește explicația. Documentul descrie tot ce se construiește în acest semestru; nu există alte faze.

**Utilizatori**

- Student: se înscrie la cursuri, rezolvă teme, vede verdictul pe fiecare test și raportul „unde greșești”, învață din materialele cursurilor în secțiunea Learn și primește un popup cu materialele potrivite când greșește un test.
- Profesor: creează cursuri, teme și teste, încarcă materiale (PDF sau PPTX), alege la fiecare temă și test materialele în care se găsesc informațiile, vede trimiterile și statisticile clasei.

**Fluxul principal**

1. Profesorul creează un curs și încarcă materialele lui (cursuri și laboratoare, PDF sau PPTX).
2. Profesorul creează o temă și teste, fiecare test având una sau mai multe etichete de concept. La temă și la fiecare test bifează materialele în care se găsesc informațiile necesare, cu pagini opționale.
3. Studentul se înscrie la curs cu un cod de acces și poate parcurge materialele în secțiunea Learn.
4. Studentul trimite cod Python din browser.
5. Sistemul rulează codul într-un container izolat, test cu test.
6. Studentul vede verdictul pe fiecare test, actualizat live. La un test picat apare un popup care îl trimite la materialele asociate, deschise la pagina indicată.
7. Raportul pe concepte arată ce are de recapitulat.

**Constrângeri**

Proiect solo, 10-12 ore pe săptămână, MVP până în săptămâna 13. Doar Python, rulare locală, fără chei API și fără costuri. Demo-ul rulează pe calculatorul tău. Fișierele materialelor stau pe disc, în directorul uploads/ (volum Docker în profilul demo); conversia PPTX în PDF cere LibreOffice instalat (D20).

## Arhitectura de ansamblu

Aplicația are patru părți: interfața din browser, backend-ul FastAPI cu straturi clare, baza de date PostgreSQL și un runner care pornește containere izolate pentru codul studenților. Codul trimis de studenți nu are voie să ruleze nicăieri în afara acelor containere.

&#91;embedded content: arhitectura aplicației · 4 părți, 2 runner-e\]

Săgețile merg de sus în jos: routerele nu ating baza de date direct, iar runner-ul are două implementări. Doar `DockerRunner` e sigur pentru cod necunoscut; `SubprocessRunner` există ca prototip local, în Pasul 3.

**Ce se întâmplă la o trimitere**

1. Browserul trimite codul la `POST /assignments/{id}/submissions`, cu token-ul JWT în antet.
2. Routerul validează token-ul, rolul și înscrierea studentului la curs, apoi apelează serviciul.
3. Serviciul creează trimiterea cu statusul `queued` și programează `run_submission` în fundal; răspunsul (202) pleacă imediat.
4. Funcția din fundal marchează trimiterea `running` și, pentru fiecare test, cere `Runner`-ului să ruleze codul cu input-ul testului și cu limitele temei.
5. `DockerRunner` pornește un container izolat, așteaptă rezultatul, îl oprește și îl șterge.
6. Serviciul compară outputul cu cel așteptat, scrie un `TestResult` pe test și, la final, scorul și statusul `done`.
7. Browserul interoghează periodic `GET /submissions/{id}` și colorează testele pe măsură ce apar rezultatele.

Interfața `Runner` apare în Pasul 3, `DockerRunner` în Pasul 4, iar execuția în fundal în Pasul 5.

## Tehnologiile folosite

Fiecare tehnologie are un rol precis în proiect. Tabelele sunt harta rapidă; în fiecare pas, Fable explică în detaliu tehnologiile care apar prima dată, cu exemple din codul proiectului, ca să poți apăra orice alegere la prezentare.

**Backend**

| Tehnologie | Ce face în proiect | De ce o alegem | Alternativă |
| --- | --- | --- | --- |
| Python 3.12+ (3.15 pe calculatorul de dezvoltare; sandbox-ul rămâne 3.12) | limbajul întregului backend | type hints care ajută validarea și editorul, ecosistem mare, cerut la angajare | n/a |
| FastAPI | framework web: definești rutele ca funcții Python și primești documentația interactivă la `/docs` | validare automată din type hints, curbă de învățare blândă | Flask, Django REST Framework |
| Uvicorn | serverul care rulează aplicația FastAPI | standardul pentru FastAPI | Hypercorn, Gunicorn |
| Pydantic v2 | definește schemele cererilor și răspunsurilor și le validează | integrat cu FastAPI, un singur loc pentru regulile de validare | dataclasses cu validare manuală |
| SQLAlchemy 2.0 | ORM: mapezi tabelele pe clase Python și scrii interogări în Python | standardul din ecosistem, stil tipizat (`Mapped[...]`) | SQLModel, SQL pur |
| Alembic | migrări: istoricul schimbărilor de schemă, versionat în git | schema evoluează pe parcurs, iar migrările o fac repetabilă | `create_all` (doar prototip) |
| PostgreSQL 16 | baza de date: constrângeri, indexuri, agregări | solid, cerut în industrie, util pentru rapoarte (`DISTINCT ON`) | SQLite |
| psycopg 3 | driverul prin care SQLAlchemy vorbește cu PostgreSQL | recomandat de ecosistem | psycopg2 |
| Argon2 (prin pwdlib) | hash de parole; nu stocăm parole în clar | algoritm modern, lent intenționat, cu sare | bcrypt |
| PyJWT | creează și verifică token-urile de autentificare | mic și clar; token-ul poartă id-ul și rolul | Authlib, sesiuni cu cookie |
| pydantic-settings | citește configurarea din variabile de mediu și `.env` | separă secretele de cod și validează la pornire | python-dotenv |
| Docker Engine + SDK `docker` | rulează codul studenților în containere izolate; SDK-ul le comandă din Python | izolare reală, cu limite de resurse | VM-uri, gVisor (avansat) |
| pytest + httpx | rulează testele; `TestClient` apelează aplicația fără server | fixture-uri puternice, sintaxă simplă | unittest |
| ruff | linter și formatter pentru Python | un singur instrument rapid pentru stil și greșeli frecvente | flake8 + black |
| python-multipart | permite lui FastAPI să primească fișiere încărcate (multipart/form-data) | dependența cerută de FastAPI pentru UploadFile | n/a |
| pypdf | validează PDF-urile încărcate și numără paginile | bibliotecă Python pură, fără dependențe de sistem | PyMuPDF (licență AGPL) |
| LibreOffice (headless) | convertește PPTX în PDF la încărcare, ca toate materialele să se vadă în același vizualizator | singura cale gratuită și fiabilă de a randa PPTX pe server (decizia D20) | doar PDF în prima versiune; conversie în browser |

**Frontend și infrastructură**

| Tehnologie | Ce face în proiect | De ce o alegem | Alternativă |
| --- | --- | --- | --- |
| React + Vite | interfața; Vite pornește serverul de dezvoltare și face build-ul | le știi deja | Next.js (fără nevoie de SSR) |
| React Router | rutele din browser și paginile protejate pe rol | standard | TanStack Router |
| TanStack Query | cereri către API cu cache, reîncercări și polling (`refetchInterval`) | evită starea manuală pentru date de pe server | SWR, `fetch` + `useEffect` |
| Monaco Editor (`@monaco-editor/react`) | editorul de cod din pagina temei, același motor ca VS Code | evidențiere de sintaxă și experiență familiară | CodeMirror, `textarea` |
| Recharts | graficele din raportul pe concepte | declarativ, se potrivește cu React | Chart.js |
| Tailwind CSS (propus, vezi D11) | stilare cu clase utilitare | rapid pentru un UI curat și consecvent | CSS Modules, Mantine, MUI |
| Vitest + React Testing Library | teste pentru componente și hook-uri | merge nativ cu Vite | Jest |
| docker-compose | pornește baza de date (la final și restul) cu o comandă | mediu repetabil pe orice calculator | instalare manuală |
| GitHub Actions | rulează lintul și testele la fiecare push | CI gratuit pentru repo-uri GitHub | GitLab CI |
| react-pdf (pdfjs-dist) | vizualizatorul de PDF din pagina Learn și din popup, cu salt la o pagină indicată | randare în pagină, fără plugin-ul PDF al browserului, deci același comportament peste tot | iframe/embed cu #page=N (depinde de browser) |

## Structura repository-ului și convenții

Un singur repository cu backend, frontend și imaginea sandbox-ului. Regula de dependență pe backend merge într-o singură direcție: routere, apoi servicii, apoi modele; niciun strat nu cunoaște stratul de deasupra lui.

```text
autograder/
  backend/
    app/
      main.py              # create_app(): FastAPI, CORS, routere, handler-e de erori
      core/                # config.py, security.py, deps.py, errors.py, logging.py
      db/                  # base.py (DeclarativeBase), session.py (engine, get_db)
      models/              # SQLAlchemy: user.py, course.py, assignment.py, ...
      schemas/             # Pydantic: cereri și răspunsuri, separate de modele
      services/            # logica de business și accesul la date
      api/v1/              # routere: auth.py, courses.py, submissions.py, ...
      runner/              # base.py, subprocess_runner.py, docker_runner.py, compare.py
      storage/             # file_store.py (salvare, citire, stergere in uploads/), pptx_converter.py (LibreOffice)
    alembic/               # migrările
    scripts/               # seed.py, seed_demo.py
    tests/                 # unit/, api/, runner/, conftest.py
    pyproject.toml
  frontend/
    src/
      api/                 # client HTTP, funcții per resursă
      auth/                # AuthContext, ProtectedRoute
      components/          # componente reutilizabile
      hooks/               # useSubmission, useCourses, ...
      pages/               # o pagină per rută
  sandbox/
    Dockerfile             # imaginea in care ruleaza codul studentilor
  uploads/                 # materialele incarcate (volum Docker, in afara git)
  docs/
    cerinte.md  decizii.md  api.md  uml/  adr/  demo.md
    machete/             # PNG-urile machetelor UI (varianta D), 01-login.png ... 14-teacher-submissions.png
  docker-compose.yml
  .github/workflows/ci.yml
  README.md
```

**Convenții**

- **Straturi:** routerul primește cererea, validează cu scheme Pydantic și apelează un serviciu; serviciul conține regulile și interogările; modelele descriu doar tabelele. Un router nu scrie interogări.
- **Nume:** `snake_case` în Python, `camelCase` și `PascalCase` pentru componente în React; resurse REST la plural (`/courses`), rute sub `/api/v1`.
- **Git:** ramuri scurte `pas-N/descriere`, un pull request pe felie verticală, commit-uri în stil convențional (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
- **Erori:** răspuns JSON uniform `{"detail": "...", "code": "..."}`; coduri de status: 201 la creare, 204 la ștergere, 401 neautentificat, 403 fără drept, 404 negăsit, 409 conflict, 422 date invalide.
- **Date:** timp în UTC, format ISO 8601; liste paginate cu `limit` și `offset`.
- **Configurare:** doar prin variabile de mediu; `.env` nu intră în git, `.env.example` da.
- **Calitate:** `ruff check` și `ruff format` fără erori înainte de fiecare commit.
- Fișiere încărcate: clientul nu trimite niciodată o cale; serverul generează numele (uuid), validează tipul după primii octeți, nu după extensie, și servește fișierul doar prin endpoint-uri cu verificare de membru.

## Modelul de date

Douăsprezece tabele acoperă tot proiectul: un profesor are cursuri, un curs are teme, o temă are teste, iar o trimitere produce câte un rezultat pe test. Etichetele de concept stau pe teste și alimentează raportul din Pasul 7, iar materialele încărcate de profesor se leagă de teme și de teste prin două tabele de legătură (Pasul 8).

| Entitate | Câmpuri principale | Relații și reguli |
| --- | --- | --- |
| User | id, email (unic), full\_name, password\_hash, role (`student` sau `teacher`), created\_at | email păstrat cu litere mici; parola nu apare niciodată într-un răspuns API |
| Course | id, title, description, teacher\_id, join\_code (unic), created\_at | un profesor are mai multe cursuri; `join_code` aleatoriu, de 8 caractere, regenerabil |
| Enrollment | user\_id, course\_id, created\_at | cheie primară compusă (user\_id, course\_id); doar studenți; înscriere dublă dă 409 |
| Assignment | id, course\_id, title, description (Markdown), language (`python`), time\_limit\_ms (2000), memory\_limit\_mb (128), due\_at (opțional), is\_published, max\_submissions (10), created\_at | ștergerea cursului șterge temele (cascade); studenții văd doar temele publicate |
| Concept | id, course\_id, name | unic pe (course\_id, name); etichete libere create de profesor |
| TestCase | id, assignment\_id, name, input\_data, expected\_output, is\_hidden, weight (1), position | testele ascunse nu își expun conținutul studentului; ordinea după `position` |
| TestCaseConcept | test\_case\_id, concept\_id | tabel de legătură many-to-many: un test poate avea mai multe concepte |
| Submission | id, assignment\_id, student\_id, code, language, status (`queued`, `running`, `done`, `error`), score (0-100, nul până la final), passed\_count, total\_count, error\_message, created\_at, started\_at, finished\_at | codul are maximum 64 KB; o trimitere nu se modifică după creare, doar statusul și rezultatele |
| TestResult | id, submission\_id, test\_case\_id, verdict, actual\_output (trunchiat), stderr (trunchiat), runtime\_ms | unic pe (submission\_id, test\_case\_id); verdicte: `passed`, `wrong_answer`, `time_limit`, `memory_limit`, `runtime_error`, `internal_error` |
| Material | id, course\_id, title, category (`lecture` sau `lab`), file\_type (pdf sau pptx), original\_filename, stored\_filename (uuid generat de server), preview\_filename (PDF-ul obținut din PPTX, nul pentru PDF), size\_bytes, page\_count, uploaded\_by, created\_at | fișierul stă pe disc, în uploads/, nu în baza de date; maximum 20 MB; ștergerea cursului șterge rândurile prin cascade, iar serviciul șterge și fișierele de pe disc |
| AssignmentMaterial | assignment\_id, material\_id, pages (text opțional, de exemplu „12-15, 18”) | cheie primară compusă (assignment\_id, material\_id); materialul trebuie să fie din același curs cu tema, altfel 422; spune studentului unde să învețe pentru întreaga temă |
| TestCaseMaterial | test\_case\_id, material\_id, pages (text opțional) | cheie primară compusă (test\_case\_id, material\_id); același curs; alimentează popup-ul care apare când testul respectiv e greșit |

**Indexuri necesare**

- `submissions (student_id, assignment_id, created_at DESC)`, pentru istoricul și cea mai recentă trimitere
- `submissions (assignment_id, created_at DESC)`, pentru tabelul profesorului
- `test_results (submission_id)`, pentru pagina unei trimiteri
- `enrollments (course_id)`, pentru lista studenților unui curs
- materials (course\_id, created\_at DESC), pentru meniul de materiale al cursului
- assignment\_materials (material\_id) și test\_case\_materials (material\_id), pentru verificarea la ștergere și pentru recomandări

Ștergerile sunt definitive, cu `ON DELETE CASCADE` acolo unde copilul nu are sens fără părinte (decizia D15). Excepție: cascade-ul nu șterge fișierele din uploads/, deci MaterialService le șterge explicit când se șterge un material sau un curs.

## Contractul API

Toate rutele stau sub `/api/v1`, în afară de `/health`. „Membru” înseamnă studentul înscris la curs sau profesorul lui. O resursă din alt curs întoarce 404, nu 403, ca să nu se afle că există. Trimiterile repetate prea repede primesc 429 (Pasul 5).

| Metodă și cale | Acces | Ce face | Pas |
| --- | --- | --- | --- |
| `GET /health` | public | starea serverului | 0 |
| `POST /auth/register` | public | creează cont; rolul de profesor cere cod de invitație (D5) | 2 |
| `POST /auth/login` | public | întoarce token-ul de acces | 2 |
| `GET /users/me` | autentificat | profilul curent | 2 |
| `GET /courses` | autentificat | profesor: cursurile lui; student: cursurile la care e înscris | 1 |
| `POST /courses` | profesor | creează un curs | 1 |
| `GET /courses/{id}` | membru | detaliile cursului | 1 |
| `PATCH /courses/{id}` | profesorul cursului | modifică titlul, descrierea sau regenerează codul | 1 |
| `DELETE /courses/{id}` | profesorul cursului | șterge cursul și tot ce ține de el | 1 |
| `POST /courses/join` | student | se înscrie cu `join_code` | 1 |
| `GET /courses/{id}/students` | profesorul cursului | lista studenților | 1 |
| `GET /courses/{id}/concepts` | membru | conceptele cursului | 1 |
| `POST /courses/{id}/concepts` | profesorul cursului | creează un concept | 1 |
| `GET /courses/{id}/assignments` | membru | temele (studenții le văd doar pe cele publicate) | 1 |
| `POST /courses/{id}/assignments` | profesorul cursului | creează o temă | 1 |
| `GET /assignments/{id}` | membru | detaliile temei | 1 |
| `PATCH /assignments/{id}` | profesorul cursului | modifică sau publică tema | 1 |
| `DELETE /assignments/{id}` | profesorul cursului | șterge tema | 1 |
| `GET /assignments/{id}/test-cases` | membru | profesor: toate câmpurile; student: doar testele publice | 1 |
| `POST /assignments/{id}/test-cases` | profesorul cursului | adaugă un test cu conceptele lui | 1 |
| `PATCH /test-cases/{id}` | profesorul cursului | modifică un test | 1 |
| `DELETE /test-cases/{id}` | profesorul cursului | șterge un test | 1 |
| `POST /assignments/{id}/submissions` | student înscris | trimite cod; răspuns 201 cu rezultate în Pasul 3, 202 cu status `queued` din Pasul 5 | 3, 5 |
| `GET /assignments/{id}/submissions` | membru | student: ale lui; profesor: toate, cu filtre și paginare | 3, 6 |
| `GET /submissions/{id}` | autorul sau profesorul cursului | status și rezultate; testele ascunse apar fără conținut | 3, 5 |
| `GET /me/dashboard` | student | cursuri, teme, cel mai bun scor, ultimele trimiteri | 6 |
| `GET /assignments/{id}/stats` | profesorul cursului | rata de trecere pe test și distribuția scorurilor | 6 |
| `GET /courses/{id}/reports/concepts/me` | student înscris | raportul „unde greșești” | 7 |
| `GET /courses/{id}/reports/concepts` | profesorul cursului | raportul pe concepte pentru toată clasa | 7 |
| `PATCH /users/me` | autentificat | schimbă `full_name` | 2 |
| `POST /users/me/password` | autentificat | schimbă parola; cere parola actuală (400 dacă e greșită) | 2 |
| `DELETE /courses/{id}/enrollment` | student înscris | părăsește cursul | 2 |
| `POST /courses/{id}/join-code` | profesorul cursului | generează alt cod de înscriere | 2 |
| `GET /users/me/activity?weeks=14` | autentificat | trimiteri pe zi și totaluri | 6 |
| `GET /courses/{id}/stats` | profesorul cursului | `students`, `submissions_today`, `average_score` | 6 |
| GET /me/learn | student | cardurile cursurilor la care e înscris, cu numărul de materiale și data ultimului material | 8 |
| GET /courses/{id}/materials | membru | lista materialelor cursului: titlu, categorie, tip, număr de pagini, data încărcării și `used_in` (temele publicate de care e legat materialul, direct sau printr-un test; profesorul le vede și pe cele nepublicate, plus `test_count`) | 8 |
| POST /courses/{id}/materials | profesorul cursului | încarcă un PDF sau PPTX (multipart/form-data: file, title, category); PPTX-ul se convertește în PDF; răspuns 201 cu materialul | 8 |
| PATCH /materials/{id} | profesorul cursului | redenumește materialul | 8 |
| DELETE /materials/{id} | profesorul cursului | șterge materialul, legăturile lui cu temele și testele și fișierele de pe disc | 8 |
| GET /materials/{id}/file | membru | descarcă fișierul original (PDF sau PPTX), cu Content-Disposition și X-Content-Type-Options: nosniff | 8 |
| GET /materials/{id}/preview | membru | PDF-ul afișat în vizualizator (originalul sau varianta convertită din PPTX), inline | 8 |
| GET /assignments/{id}/materials | membru | materialele asociate temei, cu paginile indicate | 8 |
| PUT /assignments/{id}/materials | profesorul cursului | înlocuiește lista de materiale a temei: \[{material\_id, pages}\]; materiale din alt curs dau 422 | 8 |
| PUT /test-cases/{id}/materials | profesorul cursului | înlocuiește lista de materiale a unui test: \[{material\_id, pages}\] | 8 |
| GET /submissions/{id}/recommendations | autorul sau profesorul cursului | materialele de recapitulat pentru testele picate, calculate la cerere; testele ascunse apar doar ca „Test ascuns #n” | 8 |

**Forma unui răspuns de trimitere**

```json
{
  "id": 42,
  "status": "done",
  "score": 80,
  "passed_count": 4,
  "total_count": 5,
  "results": [
    {"test_case_id": 7, "name": "caz simplu", "verdict": "passed", "runtime_ms": 31},
    {"test_case_id": 9, "name": "test ascuns", "verdict": "wrong_answer", "runtime_ms": 28}
  ]
}
```

## Designul interfeței: machetele oficiale

**Varianta oficială este D** (temă întunecată, fonturile Poppins și JetBrains Mono, interfață în engleză, navigare sus în header, pătrățele colorate pentru verdictul fiecărui test). Variantele A, B și C rămân doar ca istoric de design și nu se implementează.

Machetele sunt imagini PNG, câte una pe ecran, în `docs/machete/` (arhiva `machete-ui-varianta-D.zip` primită de la proprietar, de dezarhivat acolo înainte de Pasul 2). Sursele editabile ale machetelor sunt în canvas-ul de design al proprietarului; implementatorul lucrează doar cu PNG-urile.

**Regulile pentru frontend:**

- Înainte să scrii o pagină, deschide imaginea ei din tabelul de mai jos și reproduc-o: structura, ierarhia, culorile, fonturile, colțurile rotunjite, chips-urile și șirul de pătrățele. Nu inventa alt stil.
- Culorile și fonturile se definesc o singură dată, ca teme în `tailwind.config.js` (fundal aproape negru, suprafețe puțin mai deschise, accent violet-indigo, verde pentru trecut, roșu pentru picat, galben pentru recomandări), apoi se refolosesc în toate componentele.
- Textele din interfață sunt în engleză, ca în machete. Denumirile din Pașii 5–8 scrise în română (de exemplu „Materiale recomandate”) se afișează în engleză, cu sensul din machetă (de exemplu „Recommended pages”). Codul și comentariile rămân în engleză.
- Navigarea studentului are patru intrări: Dashboard, Courses, Learn, Concept report. Profesorul are „My courses”, iar în pagina cursului filele Assignments și Materials.
- Un ecran care nu are machetă (stări goale, erori, încărcare, formularul de înregistrare, pagina 404) se desenează în același stil, din aceleași componente. Nu cere o machetă nouă și nu schimba stilul; dacă un ecran nou schimbă comportamentul, îl adaugi mai întâi în tabelul Interfață ↔ API.
- Machetele arată date de exemplu. Datele reale vin din API, iar ce nu e în machetă (paginare, stări de eroare) urmează aceleași componente.
- Dacă o machetă și descrierea unui pas se contrazic, urmează descrierea pasului pentru comportament și macheta pentru aspect, apoi notezi diferența în `docs/decizii.md`.

**Ecran, fișier și pasul în care se construiește:**

| Fișier în docs/machete/ | Ecran | Pasul |
| --- | --- | --- |
| 01-login.png | Sign in | Pasul 2 |
| 02-student-dashboard.png | Dashboard student | Pasul 6 |
| 03-student-assignment.png | Pagina temei: editor, teste, rezultate | Pasul 5 |
| 04-student-assignment-materials-popup.png | Pagina temei cu bara de materiale și popup-ul de recomandări după un test picat | Pasul 8 |
| 05-student-concept-report.png | Raportul „unde greșești” | Pasul 7 |
| 06-student-learn.png | Learn: cursurile cu materiale | Pasul 8 |
| 07-student-learn-course.png | Materialele unui curs | Pasul 8 |
| 08-student-material-viewer.png | Vizualizatorul de pagini, cu paginile recomandate evidențiate | Pasul 8 |
| 09-profile.png | Profil | Pasul 6 |
| 10-teacher-course.png | Curs (profesor): fila Assignments | Pasul 6 |
| 11-teacher-materials.png | Curs (profesor): fila Materials, încărcare și listă | Pasul 8 |
| 12-teacher-assignment-editor.png | Editor de temă și teste | Pasul 6 |
| 13-teacher-link-materials-to-tests.png | Legarea materialelor de temă și de teste, cu pagini | Pasul 8 |
| 14-teacher-submissions.png | Trimiteri și statistici | Pasul 6 |

## Interfață ↔ API: verificarea machetelor

Fiecare element din machetele UI (varianta D, cea oficială, descrisă în secțiunea „Designul interfeței”) trebuie să aibă o sursă în backend. Am trecut ecran cu ecran prin machete și prin endpoint-urile de mai sus. Ce lipsea e adăugat aici; ce nu se putea susține fără muncă disproporționată a fost scos din machete. Regula pentru restul proiectului: **nu apare nimic pe ecran fără o rută sau un câmp care îl alimentează**, iar orice element nou din UI se adaugă întâi în tabelul de mai jos.

| Ecran | Ce afișează sau face | Sursa în backend |
| --- | --- | --- |
| Autentificare | intrare, cont nou | `POST /auth/login`, `POST /auth/register` |
| Panou student | teme cu termen, scor, pătrățelele ultimei trimiteri, ultimele trimiteri, concepte de repetat, culoarea cursului | `GET /me/dashboard`, extins: `verdicts` pe fiecare temă și trimitere, `concepts_to_review` (primele 3), `course.color` |
| Pagina temei | enunț, exemple, limite, termen, trimiteri rămase | `GET /assignments/{id}` (+ `max_submissions`, `submissions_left` pentru studentul curent), `GET /assignments/{id}/test-cases` (ascunsele mascate) |
| Pagina temei | trimitere, verdict pe fiecare test, timp, concept, indiciu | `POST /assignments/{id}/submissions`, polling pe `GET /submissions/{id}`; `TestResult` include `concepts` și `hint` (doar dacă testul a picat) |
| Pagina temei | încercările anterioare cu pătrățele | `GET /assignments/{id}/submissions` (studentul își vede doar trimiterile lui), extins cu `verdicts` |
| Pagina temei | ciorna din editor | doar în browser (`localStorage`), fără backend; textul din UI spune asta explicit |
| Raport concepte | procent, nivel, testele fiecărui concept, unde ai greșit | `GET /courses/{id}/reports/concepts/me`, extins cu `tests: [{assignment_id, assignment_title, test_name, verdict}]` |
| Profil | nume, email, rol, data contului | `GET /users/me` |
| Profil | schimbă numele | **nou** `PATCH /users/me` |
| Profil | schimbă parola | **nou** `POST /users/me/password` (cere parola actuală) |
| Profil | activitate pe zile, totaluri | **nou** `GET /users/me/activity?weeks=14` |
| Profil | cursurile mele, intră în curs, părăsește cursul | `GET /courses`, `POST /courses/join`, **nou** `DELETE /courses/{id}/enrollment` |
| Profil | ieși din cont | doar în frontend: șterge token-ul (JWT fără stare, nu există logout pe server) |
| Curs (profesor) | cod de înscriere, copiere | `GET /courses/{id}`; copierea e în browser |
| Curs (profesor) | generează alt cod | **nou** `POST /courses/{id}/join-code` |
| Curs (profesor) | studenți, trimiteri azi, scor mediu | **nou** `GET /courses/{id}/stats` |
| Curs (profesor) | teme cu stare (ciornă, deschisă, încheiată), câți au predat, câți complet, parțial sau zero | `GET /courses/{id}/assignments`, extins pentru profesor cu `is_published`, `submitted_count`, `result_buckets` |
| Curs (profesor) | temă nouă, publică | `POST /courses/{id}/assignments`, `PATCH /assignments/{id}` cu `is_published: true` |
| Editor temă | detalii, limite, termen | `PATCH /assignments/{id}` |
| Editor temă | teste, pondere, ascuns, indiciu, concepte | `POST /assignments/{id}/test-cases`, `PATCH`/`DELETE /test-cases/{id}`, `GET`/`POST /courses/{id}/concepts` |
| Trimiteri (profesor) | rata de trecere pe test, distribuția scorurilor, câți au predat, câte rulează | `GET /assignments/{id}/stats`, extins cu `submitted_count`, `enrolled_count`, `running_count` și conceptele fiecărui test |
| Trimiteri (profesor) | listă cu filtre, căutare, paginare, numărători pe filtru | `GET /assignments/{id}/submissions?verdict=&q=&page=&page_size=`, răspuns cu `items`, `total`, `counts` |
| Trimiteri (profesor) | eroare la rulare, codul trimis | `GET /submissions/{id}` (cod vizibil profesorului); `Submission.error_excerpt` |
| Learn (student) | un card pe curs: titlu, profesor, număr de materiale | nou GET /me/learn |
| Learn, pagina cursului | meniul cu toate materialele cursului și deschiderea unui material | nou GET /courses/{id}/materials |
| Vizualizator material | PDF-ul deschis la pagina indicată, descărcarea originalului | nou GET /materials/{id}/preview și /file; pagina vine din rută (?page=12), nu din backend |
| Pagina temei | bara „Materiale pentru această temă” cu paginile indicate | nou GET /assignments/{id}/materials |
| Pagina temei | popup cu materialele de recapitulat după un test greșit | nou GET /submissions/{id}/recommendations |
| Curs (profesor) | fila „Materiale”: încărcare, redenumire, ștergere | nou GET/POST /courses/{id}/materials, PATCH/DELETE /materials/{id} |
| Editor temă | selectorul de materiale ale temei, cu pagini | nou GET/PUT /assignments/{id}/materials |
| Editor temă | selectorul de materiale pe fiecare test | nou PUT /test-cases/{id}/materials |

**Endpoint-uri noi (6).** Totalul crește de la 29 la 35.

- `PATCH /users/me`: schimbă `full_name`. Emailul rămâne fix, pentru că e identitatea de autentificare.
- `POST /users/me/password`: primește `current_password` și `new_password` (minimum 8 caractere). Răspunde 400 dacă parola actuală e greșită.
- `GET /users/me/activity?weeks=14`: numărul de trimiteri pe zi, plus totaluri (trimiteri, teme la 100%, concepte stăpânite). Un singur `GROUP BY date(created_at)`.
- `DELETE /courses/{id}/enrollment`: studentul părăsește cursul. Trimiterile rămân în baza de date, dar nu mai apar în rapoartele cursului.
- `GET /courses/{id}/stats`: doar pentru profesorul cursului. Întoarce `students`, `submissions_today`, `average_score`.
- `POST /courses/{id}/join-code`: generează alt cod de înscriere. Codul vechi nu mai funcționează.

**Câmpuri noi în modele.**

- `Course.color`: o culoare dintr-o paletă fixă, aleasă la creare.
- `Assignment.is_published` (implicit `false`) și `Assignment.max_submissions` (implicit 10). Studenții nu văd temele nepublicate. Starea afișată se calculează: ciornă dacă nu e publicată, deschisă până la termen, încheiată după termen.
- `TestCase.hint`: text opțional, arătat studentului doar când testul pică, chiar dacă testul e ascuns.
- `Submission.error_excerpt`: ultima linie din eroarea de rulare (de exemplu `IndexError, linia 4`), cel mult 200 de caractere.

**Câmpuri noi în răspunsuri.** Se calculează din datele existente, fără tabele noi: `verdicts` (lista de verdicte pe teste, în ordinea testelor) pe trimiteri și în panou, `submissions_left`, `result_buckets`, `counts` pe filtre și lista de teste pe concept în raport.

**Scos din machete, pentru că nu avea backend.**

- „Ai uitat parola?”: ar cere trimitere de emailuri. Rămâne pentru după MVP. Până atunci, profesorul poate reseta parola din `scripts/seed.py`.
- Fila „Studenți” din meniul profesorului: nu are pagină în MVP. `GET /courses/{id}/students` rămâne pentru export și statistici.
- Textul „salvat automat” din editor: înlocuit cu „ciorna rămâne în browser”, ca să nu sugereze o salvare pe server.

**Unde intră în pași (propunere).** Profilul și cursurile (`PATCH /users/me`, parola, părăsirea cursului, `join-code`, `color`) în pasul de autentificare și cursuri. `hint`, `error_excerpt` și `verdicts` în pașii cu runner-ul și trimiterile asincrone. Statisticile, filtrele și activitatea în pasul cu rapoartele și conceptele. Fiecare are teste API ca restul: permisiuni (student sau profesor, membru sau nu) și forma răspunsului.

Materialele (11 endpoint-uri noi, totalul ajunge la 46). Ecranele din ultimele opt rânduri ale tabelului nu au machetă în canvas: Fable le construiește după descrierea din Pasul 8, în stilul machetelor existente, iar utilizatorul le validează în browser. Detaliile contractului (validări, coduri de eroare, regula de recomandare) sunt în Pasul 8.

## Strategia de testare

Testele se scriu în același pas cu funcționalitatea, pe opt niveluri: de la funcții pure, rapide, până la demo-ul manual. Cele mai multe teste stau jos; sandbox-ul și fluxul complet au puține, dar esențiale.

| Nivel | Ce verifică | Unelte | Unde rulează |
| --- | --- | --- | --- |
| Unit | funcții pure: compararea outputului, scorul, clasificarea conceptelor, hash și JWT | pytest | local și CI |
| Servicii cu baza de date | reguli de business și interogări, pe un PostgreSQL de test; fiecare test rulează într-o tranzacție cu rollback | pytest, fixture `db_session` | local și CI |
| API | rute, coduri de status, permisiuni, formatul erorilor | pytest + `TestClient` | local și CI |
| Contract `Runner` | aceeași suită rulată pe `SubprocessRunner` și pe `DockerRunner` | pytest parametrizat, marker `docker` | local; în CI unde Docker e disponibil |
| Adversariale | bucle infinite, consum de memorie, procese multiple, acces la rețea, output uriaș | pytest, marker `docker` | local și CI |
| Frontend | componente, hook-uri, rute protejate | Vitest + React Testing Library | local și CI |
| Flux complet | de la înregistrare la raport, prin API, cu `FakeRunner` și un caz cu Docker | pytest | CI |
| Demo manual | scriptul din `docs/demo.md` | manual | înainte de predare |

**Reguli**

- **Nume și formă:** `test_<ce>_<comportament>`, cu structura aranjare, acțiune, verificare.
- **Fixture-uri comune** în `conftest.py`: `db_session`, `client`, `make_user`, `make_course`, `teacher_token`, `student_token`. Datele de test se construiesc cu funcții simple, fără bibliotecă de factories.
- **`FakeRunner`:** un runner determinist, programat să întoarcă verdictele dorite, ca testele de servicii să nu depindă de Docker.
- **Matricea de permisiuni:** un singur test parametrizat cu liniile (rol, metodă, cale, status așteptat); orice rută nouă adaugă o linie.
- **Markere:** `docker` pentru testele care cer daemonul Docker, `slow` pentru cele lente. Rularea rapidă: `pytest -m "not docker"`.
- **Acoperire:** `pytest --cov` pe `services` și `runner`, țintă orientativă 80%. Contează căile de eroare, nu cifra.
- **CI:** ruff, pytest cu serviciu PostgreSQL, vitest și build-ul frontend-ului; un push cu teste roșii nu se îmbină.
- **Bug găsit manual:** se reproduce mai întâi într-un test, apoi se repară.
- Încărcări în teste: un PDF și un PPTX minimale generate în fixture, uploads/ redirecționat spre tmp\_path; conversia reală cu LibreOffice se testează sub markerul libreoffice, restul cu un convertor fals.

## Decizii deschise

Documentul pornește de la valorile din coloana „Default propus”. Răspunde mai întâi la cele șase decizii marcate „da” la prioritar (D3, D4, D11, D18, D19, D20): primele cinci schimbă cel mai mult Pașii 0, 3 și 4, iar D20 schimbă Pasul 8 și mediul de dezvoltare. Când o decizie se schimbă, editezi rândul și pui data în coloana de alternativă.

| ID | Decizie | Default propus | Alternativă | Prioritar |
| --- | --- | --- | --- | --- |
| D1 | Limba codului și a interfeței | cod, comentarii și interfață în engleză, ca în machetele variantei D | interfață în română (machetele s-ar retraduce) |  |
| D2 | Baza de date | PostgreSQL de la început | SQLite în primele zile, mutare ulterioară |  |
| D3 | Limbajul frontend-ului | JavaScript (confirmat 12.11.2026) | TypeScript | da |
| D4 | Formatul testelor | stdin și stdout: programul citește input și afișează rezultatul | apeluri de funcții cu argumente, în stil pytest | da |
| D5 | Cont de profesor | cod de invitație din `.env` | oricine se poate înregistra ca profesor; doar prin seed |  |
| D6 | Identificatori | numere întregi autoincrement | UUID |  |
| D7 | Token-ul în browser | JWT în `localStorage` (simplu, expus la XSS) | cookie `httpOnly` (cere protecție CSRF) |  |
| D8 | Execuție asincronă | `BackgroundTasks` cu semafor | worker propriu cu coadă în baza de date; Celery cu Redis dacă încărcarea crește |  |
| D9 | Livrarea codului în container | director temporar montat doar pentru citire | `put_archive`; se decide după spike-ul din Pasul 4 |  |
| D10 | Backend în container la demo | nu: backend pe gazdă, Docker doar pentru baza de date și sandbox | da, cu `docker.sock` montat (risc de securitate) |  |
| D11 | Stilarea interfeței | Tailwind CSS 3 (confirmat 12.11.2026) | CSS propriu, Mantine sau MUI | da |
| D12 | Limite implicite sandbox | 2 s, 128 MB, 0,5 CPU, 64 de procese, output 64 KB, cod 64 KB; configurabile pe temă | alte valori |  |
| D13 | Compararea outputului | ignoră spațiile de la capătul liniilor și liniile goale de la final | exact, caracter cu caracter; comparare pe token-uri |  |
| D14 | Scorul | procent din greutatea testelor trecute | tot sau nimic; penalizare pentru termen depășit |  |
| D15 | Ștergeri | definitive, cu cascade | soft delete (`deleted_at`) |  |
| D16 | Rulare de probă | doar „Trimite” în MVP | buton „Rulează testele publice”, fără scor |  |
| D17 | Regula raportului pe concepte | contează cea mai recentă trimitere pe temă | cea mai bună trimitere sau toate |  |
| D18 | Livrabile cerute de profesor | cod, demo și diagrame UML | raport scris, prezentare, alte cerințe exacte | da |
| D19 | Mediul local | `pip` cu `venv`, Windows 11, Docker Desktop, Python 3.15; PostgreSQL din compose pe portul gazdă 5433 (confirmat 12.11.2026) | `uv`, Poetry; WSL2 pe Windows | da |
| D20 | Previzualizarea PPTX | PPTX-ul se convertește în PDF la încărcare cu LibreOffice headless (instalat local și în imaginea backend-ului) | doar PDF acceptat; PPTX doar pentru descărcare, fără previzualizare | da |
| D21 | Stocarea fișierelor | director local uploads/ (volum Docker), în afara git | S3/MinIO; coloană bytea în PostgreSQL |  |
| D22 | Vizibilitatea materialelor | vizibile imediat studenților înscriși la curs | stare ciornă/publicat, ca la teme |  |
| D23 | Formatul paginilor indicate | text liber validat, de exemplu „12-15, 18”; linkul deschide prima pagină | o singură pagină; selector vizual de pagini |  |
| D24 | Limita fișierelor încărcate | 20 MB pe fișier, doar PDF și PPTX | 50 MB; adăugarea altor formate (DOCX) |  |

## Pasul 0 · Fundații (săpt. 3)

**Obiectiv.** Un schelet care pornește cu câteva comenzi: backend care răspunde la `/health`, frontend care îl apelează, baza de date în Docker, un test verde și CI. În paralel scrii cerințele proiectului.

**Arhitectură și design**

- Monorepo cu `backend/` și `frontend/`.
- Backend-ul rulează pe calculatorul tău, într-un mediu virtual, nu în container, ca să îl poți depana ușor.
- PostgreSQL rulează prin docker-compose.
- Frontend-ul rulează cu Vite și trimite cererile către API printr-un proxy, ca să nu apară probleme CORS în dezvoltare.
- Configurarea vine din variabile de mediu.

**Cod de scris**

- `backend/pyproject.toml`: dependențele și configurările pentru ruff și pytest.
- `app/core/config.py`: `class Settings(BaseSettings)` cu `database_url`, `jwt_secret`, `env`, `cors_origins`, plus `get_settings()` cu cache.
- `app/main.py`: `create_app()` întoarce aplicația `FastAPI`, adaugă CORS și include routerele.
- `app/api/v1/health.py`: `GET /health` întoarce `{"status": "ok"}`, montat fără prefix.
- `docker-compose.yml`: serviciul `db` (imaginea `postgres:16`, volum persistent, `healthcheck`).
- `.claude/settings.json` cu `{"attribution": {"commit": "", "pr": ""}}`, ca Claude Code să nu adauge nicio mențiune despre asistent în commit-uri și pull request-uri (versiunile mai vechi folosesc `{"includeCoAuthoredBy": false}`); remote-ul origin este https://github.com/Cataflon/Code-Learning-Platform, iar push-ul îl face utilizatorul.
- `frontend/`: proiect Vite cu React; `vite.config.js` cu `server.proxy` pentru `/api` și `/health`; o pagină care afișează starea serverului.
- `.github/workflows/ci.yml`: ruff, pytest și vitest.
- `docs/cerinte.md` (12-15 user stories cu criterii de acceptare), `docs/uml/use-case.puml`, `docs/decizii.md`.

**Tehnologii explicate**

- **Mediu virtual (`venv`):** un folder cu pachetele proiectului, separat de restul sistemului; seamănă cu `node_modules`, dar îl activezi explicit.
- **`pyproject.toml`:** fișierul de configurare al proiectului Python, echivalentul lui `package.json`.
- **FastAPI și Uvicorn:** aplicația definește rutele, Uvicorn o servește (`uvicorn app.main:app --reload`); documentația interactivă apare la `/docs`.
- **Variabile de mediu și pydantic-settings:** configurarea stă în afara codului, deci același cod rulează local și în CI.
- **CORS:** browserul blochează cererile între origini diferite (`localhost:5173` către `localhost:8000`) dacă serverul nu le permite; proxy-ul Vite le face să pară aceeași origine.
- **docker-compose și `healthcheck`:** descriere declarativă a serviciilor; `healthcheck` spune când baza de date poate primi conexiuni.

**Teste**

- `tests/api/test_health.py`: `TestClient` apelează `/health` și verifică 200 și corpul.
- `tests/unit/test_config.py`: `Settings` citește valorile din variabilele de mediu.
- Frontend: un test Vitest care randează pagina cu `fetch` simulat și verifică starea afișată.
- CI rulează verde pe primul push.

**Gata când**

- [ ] `uvicorn` pornește și `/docs` se deschide
- [ ] `pytest` și `vitest` trec local
- [ ] pagina din Vite afișează starea serverului
- [ ] CI este verde
- [ ] `cerinte.md` are 12-15 user stories și diagrama de use case există
- [ ] poți explica drumul unei cereri de la browser la backend și înapoi

**Întrebări pentru tine:** D3 (JavaScript sau TypeScript), D11 (stilarea), D19 (sistemul de operare, Docker instalat, `pip` sau `uv`), D1 (limba codului). În plus: repository GitHub privat (default) sau public?

## Pasul 1 · Modelul de date și CRUD (săpt. 4)

**Obiectiv.** Toate entitățile există în baza de date, create prin migrări Alembic, iar API-ul CRUD funcționează pentru cursuri, teme, teste și concepte, verificat din Swagger și prin teste.

**Arhitectură și design**

- Straturi: router, apoi serviciu, apoi model. Schemele Pydantic (`Create`, `Update`, `Read`) sunt separate de modelele SQLAlchemy.
- `get_db` oferă o sesiune de bază de date pe cerere și o închide la final.
- Autentificarea nu există încă: `get_current_user` e un substitut care întoarce un utilizator din seed. Pasul 2 îl înlocuiește fără să schimbe routerele.
- Erorile de domeniu (`NotFoundError`, `ConflictError`) sunt transformate centralizat în răspunsuri JSON.

**Cod de scris**

- `db/base.py`: `class Base(DeclarativeBase)`. `db/session.py`: engine, `SessionLocal`, `get_db()`.
- `models/*.py`: un fișier pe entitate, cu `Mapped[...]` și `mapped_column`, relații, constrângeri de unicitate, `ondelete="CASCADE"` și enum-uri Python pentru rol și verdict.
- Alembic inițializat; prima migrare generată cu `--autogenerate` și citită manual înainte de aplicare.
- `schemas/*.py`: `CourseCreate`, `CourseRead` și celelalte, cu `model_config = ConfigDict(from_attributes=True)`.
- `services/course_service.py`, `assignment_service.py`, `test_case_service.py`, `concept_service.py`: funcții precum `create_course(db, teacher, data)`, `list_courses_for(db, user)`, `join_course(db, student, code)`.
- `api/v1/courses.py`, `assignments.py`, `test_cases.py`, `concepts.py`, conform tabelului din „Contractul API”.
- `core/errors.py`: excepțiile de domeniu și handler-ele lor.
- `scripts/seed.py`: un profesor, doi studenți, un curs, o temă cu cinci teste și trei concepte.

**Tehnologii explicate**

- **ORM și `Session`:** SQLAlchemy mapează clase pe tabele; `Session` ține obiectele încărcate și trimite modificările în bază la `commit()`, ca o unitate de lucru.
- **Încărcare leneșă și problema N+1:** accesarea unei relații poate lansa o interogare pentru fiecare rând; se evită cu `selectinload`.
- **Migrări:** `alembic revision --autogenerate` compară modelele cu baza, iar `alembic upgrade head` aplică diferențele. `create_all` nu păstrează istoric și nu modifică tabele existente.
- **Pydantic față de ORM:** modelul ORM descrie tabelul, schema descrie contractul cu clientul; separarea împiedică scurgerea câmpurilor interne, cum e `password_hash`.
- **Coduri HTTP și paginare:** 201, 204, 404, 409, 422; liste cu `limit` și `offset`.

**Teste**

- Fixture `db_session`: o tranzacție anulată la finalul fiecărui test.
- Servicii: crearea unui curs generează un `join_code` unic; înscrierea dublă ridică `ConflictError`; ștergerea cursului șterge temele și testele (cascade).
- API: calea fericită și erorile (404 pe id inexistent, 409 la conflict, 422 la date invalide).
- Migrare: un test rulează `alembic upgrade head` pe o bază goală, apoi `downgrade base`.

**Gata când**

- [ ] din Swagger creezi curs, temă și trei teste cu concepte
- [ ] `seed.py` rulează de două ori fără erori
- [ ] migrarea se aplică de la zero
- [ ] testele trec
- [ ] poți explica diferența dintre un model Pydantic și unul SQLAlchemy

**Întrebări pentru tine:** D2, D6, D15. În plus: ce câmpuri vrei pe temă (`due_at`, număr maxim de trimiteri, penalizări)? Descrierea temei în Markdown (default da)? Valorile implicite din D12 ți se potrivesc?

## Pasul 2 · Autentificare, roluri și scheletul frontend (săpt. 5)

**Obiectiv.** Înregistrare, login și rute protejate pe roluri, plus un flux de autentificare complet în browser. La final, un student nu poate face ce poate un profesor, iar testele o dovedesc.

**Arhitectură și design**

- Autentificare fără sesiune pe server: clientul trimite `Authorization: Bearer <token>`, iar token-ul JWT poartă `sub` (id-ul utilizatorului), `role` și `exp`.
- Dependențe FastAPI înlănțuite: `get_current_user`, apoi `require_role(Role.teacher)`, apoi `get_course_for_owner` și `get_course_for_member`, care verifică și apartenența la curs.
- Regulile de acces trăiesc în dependențe și servicii, nu în corpul routerelor.
- Login-ul folosește formularul standard OAuth2 (câmpul `username` poartă emailul), ca butonul „Authorize” din Swagger să funcționeze. Varianta cu corp JSON e mai simplă în frontend, dar fără acel buton.

**Cod de scris**

- `core/security.py`: `hash_password`, `verify_password`, `create_access_token(user)`, `decode_token(token)`.
- `schemas/auth.py`, `services/auth_service.py` (`register_user`, `authenticate`), `api/v1/auth.py`, `api/v1/users.py` (`GET /users/me`).
- `core/deps.py`: `get_current_user` (înlocuiește substitutul din Pasul 1), `require_role`, `get_course_for_member`, `get_course_for_owner`.
- Retrofit pe routerele din Pasul 1: fiecare rută primește dependența potrivită.
- Frontend: `src/api/client.js` (`apiFetch` adaugă token-ul și, la 401, face logout), `auth/AuthContext.jsx` (`user`, `login`, `logout`, reîncărcarea la refresh), `auth/ProtectedRoute.jsx` (acceptă o listă de roluri), paginile `LoginPage`, `RegisterPage`, `HomePage` cu meniu pe rol, `QueryClientProvider` pentru TanStack Query. Aspectul vine din docs/machete/ (01-login.png și stilul comun al celorlalte machete): temele de culoare și fonturile se definesc acum, o singură dată, în tailwind.config.js, după secțiunea „Designul interfeței”.

**Tehnologii explicate**

- **Hash față de criptare:** hash-ul e unidirecțional; verifici o parolă recalculând hash-ul, nu o poți recupera. Argon2 e lent intenționat și folosește „sare”, ca parole identice să dea hash-uri diferite.
- **JWT:** trei părți (antet, conținut, semnătură). Conținutul se poate citi de oricine, deci nu conține secrete; semnătura garantează că nu a fost modificat. Serverul nu ține sesiuni, dar nici nu poate revoca un token înainte de `exp`.
- **Autentificare și autorizare:** prima răspunde la „cine ești”, a doua la „ce ai voie”. Lipsa token-ului dă 401, rolul sau proprietatea greșită dă 403.
- **Injecția de dependențe în FastAPI (`Depends`):** o funcție declară ce are nevoie, iar framework-ul o furnizează; așa verificările se refolosesc și se înlocuiesc ușor în teste.
- **React Context și rute protejate:** starea de autentificare e disponibilă în toată aplicația, iar `ProtectedRoute` redirecționează spre login.
- **Unde ținem token-ul:** în `localStorage` e simplu, dar expus dacă apare o vulnerabilitate XSS; un cookie `httpOnly` e mai sigur la XSS, dar cere protecție CSRF (D7).

**Teste**

- Unit pe `security.py`: aceeași parolă dă hash-uri diferite, `verify_password` acceptă și respinge corect, un token expirat sau modificat e respins.
- API: înregistrare cu email duplicat dă 409, login greșit dă 401, `GET /users/me` fără token dă 401.
- Matricea de permisiuni, într-un test parametrizat (rol, metodă, cale, status așteptat): studentul nu creează cursuri, profesorul unui alt curs nu vede cursul, studentul neînscris primește 404.
- Frontend: `ProtectedRoute` redirecționează un vizitator anonim și lasă să treacă rolul potrivit; formularul de login afișează eroarea.

**Gata când**

- [ ] înregistrarea și login-ul funcționează din browser și din Swagger
- [ ] orice rută din Pasul 1 respectă rolurile din tabelul API
- [ ] matricea de permisiuni trece
- [ ] după un refresh al paginii rămâi autentificat
- [ ] poți explica ce conține token-ul și cine îl verifică

**Întrebări pentru tine:** D5 (cum se creează conturile de profesor), D7 (unde ținem token-ul). În plus: cerințe pentru parolă (minimum 8 caractere, default), durata token-ului (60 de minute, default), nevoie de „refresh token” (nu în MVP).

## Pasul 3 · Trimiteri și evaluare, prototip (săpt. 6)

**Obiectiv.** Un student trimite cod și primește verdictul pe fiecare test. Evaluatorul stă în spatele unei interfețe `Runner`, iar prototipul rulează codul cu `subprocess`, doar local.

**Arhitectură și design**

- `Runner` este o interfață: primește cod, input și limite, întoarce un `RunResult`. Serviciul de evaluare nu știe cine execută codul, deci în Pasul 4 înlocuiești implementarea fără să atingi restul.
- `evaluate_submission` parcurge testele în ordinea `position`, apelează runner-ul, transformă `RunResult` într-un verdict, salvează un `TestResult` pe test și calculează scorul.
- În acest pas trimiterea e sincronă: cererea `POST` se termină când s-au rulat toate testele (Pasul 5 o face asincronă).
- Verdictul se decide într-o funcție pură: timp depășit dă `time_limit`, memorie depășită dă `memory_limit`, cod de ieșire diferit de 0 dă `runtime_error`, apoi compararea outputului dă `passed` sau `wrong_answer`.
- Runner-ul se obține printr-o dependență `get_runner()`, ca testele să-l poată înlocui cu `FakeRunner`.

**Cod de scris**

- `models/submission.py`, `models/test_result.py` și migrarea lor.
- `runner/base.py`, în forma de mai jos.
- `runner/subprocess_runner.py`: scrie codul într-un director temporar (`tempfile.TemporaryDirectory`), rulează `subprocess.run([sys.executable, path], input=stdin, capture_output=True, text=True, timeout=...)` și prinde `TimeoutExpired`. Limita de memorie nu e aplicată în prototip.
- `runner/compare.py`: `normalize(text)` și `outputs_match(actual, expected)` conform D13.
- `services/scoring.py`: `compute_score(results, test_cases)`, procent din greutatea testelor trecute.
- `services/submission_service.py`: `create_submission`, `evaluate_submission`, `get_visible_results` (maschează testele ascunse).
- `api/v1/submissions.py`: `POST /assignments/{id}/submissions` (201, sincron), `GET /submissions/{id}`, `GET /assignments/{id}/submissions`.

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class Limits:
    time_limit_ms: int = 2000
    memory_limit_mb: int = 128
    max_output_bytes: int = 64 * 1024

@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int | None
    runtime_ms: int
    timed_out: bool = False
    memory_exceeded: bool = False

class Runner(Protocol):
    def run(self, code: str, stdin: str, limits: Limits) -> RunResult: ...
```

**Tehnologii explicate**

- **Procese, stdin, stdout, stderr și cod de ieșire:** un program primește input pe stdin, scrie rezultatul pe stdout, erorile pe stderr și se termină cu un cod; 0 înseamnă succes. Evaluarea din acest pas se bazează exact pe aceste patru lucruri.
- **Timeout:** fără el, o buclă infinită blochează serverul.
- **`typing.Protocol`:** definește o interfață prin forma ei (ce metode are), fără moștenire. Serviciul depinde de interfață, nu de implementare; aceasta e inversarea dependențelor și motivul pentru care `FakeRunner` merge în teste.
- **Funcții pure:** `normalize`, `outputs_match`, `compute_score` și maparea la verdict nu citesc din bază și nu rulează procese, deci se testează rapid și exhaustiv.
- **De ce `subprocess` nu e un sandbox:** codul rulat are aceleași drepturi ca serverul și poate citi fișiere, șterge date sau folosi rețeaua. Folosește-l doar local și doar cu cod scris de tine; nu îl expune niciodată prin rețea.

**Teste**

- Unit: `normalize` și `outputs_match` (spații la capăt de linie, linii goale la final, `\r\n`); `compute_score` (greutăți diferite, 0% și 100%); maparea la verdict pentru fiecare caz.
- `SubprocessRunner` cu programe mici: afișează un text, citește din stdin, ridică o excepție (cod de ieșire diferit de 0), `while True` (timeout).
- Servicii cu `FakeRunner`: toate verdictele posibile, scorul final, testele ascunse mascate.
- API: un student înscris trimite cod și primește 201 cu rezultate; un student neînscris primește 404; câmpurile testelor ascunse lipsesc din răspuns.

**Gata când**

- [ ] din Swagger trimiți un program corect și unul greșit și vezi verdictele potrivite
- [ ] schimbarea runner-ului se face dintr-o singură dependență
- [ ] testele trec
- [ ] poți explica de ce `subprocess` nu e suficient pentru cod necunoscut

**Întrebări pentru tine:** D4 (formatul testelor), D13 (compararea outputului), D14 (calculul scorului), D16 (buton separat pentru rulare de probă).

## Pasul 4 · Sandbox Docker (săpt. 7)

**Obiectiv.** `DockerRunner` execută codul studenților izolat, cu limite stricte, iar o suită de teste „adversariale” dovedește că izolarea ține. Este pasul cu cel mai mare risc din proiect.

**Arhitectură și design**

- Aceeași interfață `Runner` din Pasul 3; `DockerRunner` o implementează, deci niciun alt cod nu se schimbă în afară de fabrica de runner-e.
- O imagine dedicată `autograder-python`: Python slim, utilizator fără drepturi, fără alte pachete.
- Un container nou pentru fiecare test, șters imediat după rulare; limitele le aplică Docker, nu codul studentului.
- Timpul măsurat include pornirea containerului, deci limita se aplică cu o marjă fixă. O optimizare posibilă, dar nu în MVP, este un singur container pe trimitere.
- `RUNNER=docker` sau `RUNNER=subprocess` în configurare; `subprocess` e permis doar când `ENV=dev`.
- Un semafor global limitează numărul de containere simultane (default 2), ca serverul să nu fie copleșit.

**Spike la începutul pasului (D9).** Înainte de implementare, două ore pentru a verifica cum ajunge codul în container: (1) un director temporar montat doar pentru citire; (2) `put_archive` pe un container cu sistem de fișiere read-only. Verifici ce funcționează pe sistemul tău de operare și cu versiunea ta de Docker, iar decizia se notează în `docs/adr/0001-livrare-cod.md`. Un bind mount cu cale locală nu merge dacă backend-ul rulează el însuși într-un container (D10).

**Cod de scris**

- `sandbox/Dockerfile`: imagine Python slim, utilizator non-root, director de lucru `/sandbox`.
- `runner/docker_runner.py`: `DockerRunner.run(code, stdin, limits)` creează containerul cu `network_disabled=True`, `mem_limit` și `memswap_limit` egale, `nano_cpus`, `pids_limit`, `read_only=True`, `tmpfs={"/tmp": "size=16m"}`, `cap_drop=["ALL"]`, `security_opt=["no-new-privileges"]`, `user` fără drepturi și eticheta `autograder=1`. Îl pornește, așteaptă cu `container.wait(timeout=...)`, la depășire îl oprește cu `kill()`, citește rezultatul și îl șterge într-un bloc `finally`.
- Input-ul se pune într-un fișier, iar comanda e `sh -c "python /sandbox/main.py < /sandbox/input.txt"`.
- Detectarea memoriei depășite: după `container.reload()`, câmpul `attrs["State"]["OOMKilled"]`; codul de ieșire 137 singur nu ajunge, pentru că apare și la oprirea din timeout.
- Limitarea outputului la `max_output_bytes`: fie `logs(stream=True)` oprit la limită, fie `log_config` cu `max-size`, ca un program care tipărește fără oprire să nu umple discul.
- `runner/factory.py`: alege runner-ul după configurare și ține semaforul.
- `docs/adr/0001-livrare-cod.md`: rezultatul spike-ului.

**Tehnologii explicate**

- **Container față de mașină virtuală:** containerele împart nucleul sistemului de operare cu gazda. Izolarea vine din *namespaces* (procesele, rețeaua și fișierele văzute de container sunt ale lui) și din *cgroups* (limite de CPU, memorie și număr de procese).
- **Fiecare opțiune și ce atac oprește:** `network_disabled` oprește accesul la rețea; `mem_limit` oprește consumul de memorie al gazdei; `pids_limit` oprește *fork bomb*-urile; `read_only` plus `tmpfs` limitează unde se poate scrie; `cap_drop=ALL` și `no-new-privileges` taie privilegiile speciale; utilizatorul fără drepturi reduce impactul unei evadări.
- **OOM killer:** când un proces depășește memoria permisă, nucleul îl oprește; Docker raportează asta în starea containerului.
- **Curățenia containerelor:** un container rămas în urmă consumă resurse; de aceea `finally` și eticheta `autograder=1`, prin care poți număra ce a rămas.
- **`docker.sock`:** accesul la socket-ul Docker echivalează cu drepturi de administrator pe gazdă. Backend-ul care îl folosește devine o țintă, motiv pentru care demo-ul rulează local (D10).

**Teste** (marker `docker`)

- Contract: aceleași teste funcționale rulate pe `SubprocessRunner` și pe `DockerRunner`, parametrizat; ambele trebuie să dea aceleași verdicte pe programe normale.
- Adversariale: buclă infinită, oprită în limita de timp plus marja; alocare uriașă de memorie dă `memory_limit`; *fork bomb* e oprit de `pids_limit`; încercare de conectare la rețea eșuează; scriere în afara `/tmp` eșuează; output uriaș e trunchiat la limită.
- Curățenie: după fiecare test și după toată suita, nicio resursă cu eticheta `autograder=1` nu mai există.
- Configurare: `RUNNER=subprocess` e refuzat când `ENV` nu e `dev`.

**Gata când**

- [ ] toate testele adversariale trec și nu rămân containere
- [ ] contractul trece identic pe ambele runner-e
- [ ] spike-ul e documentat într-un ADR
- [ ] poți explica ce blochează fiecare opțiune de izolare

**Întrebări pentru tine:** D9, D10, D12, D19. În plus: versiunea de Python din sandbox (3.12, default) și dacă permiți biblioteci externe precum `numpy` (default: nu).

## Pasul 5 · Execuție asincronă și pagina temei (săpt. 8)

**Obiectiv.** Trimiterea întoarce imediat, evaluarea rulează în fundal, iar interfața arată live starea fiecărui test. Pagina temei, cu editor de cod, devine ecranul principal al studentului.

**Arhitectură și design**

- Ciclul de viață al unei trimiteri: `queued`, apoi `running`, apoi `done` sau `error`.
- `POST /assignments/{id}/submissions` creează rândul cu statusul `queued`, programează `run_submission(submission_id)` cu `BackgroundTasks` și răspunde 202.
- `run_submission` deschide **propria sesiune de bază de date**, pentru că sesiunea cererii se închide odată cu răspunsul. Marchează `running`, rulează testele pe rând, scrie fiecare `TestResult` imediat ce e gata (așa vede interfața progresul), apoi setează `done` și scorul.
- `GET /submissions/{id}` este endpoint-ul de polling. Clientul îl reapelează până când statusul devine `done` sau `error`.
- Recuperare după restart: la pornirea aplicației (hook `lifespan`), trimiterile rămase `queued` sau `running` sunt marcate `error` cu un mesaj clar.
- O limită simplă împotriva spam-ului: între două trimiteri ale aceluiași student la aceeași temă trece un interval minim (default 5 secunde), altfel răspunsul e 429.
- Extensie posibilă: `run_submission` primește doar un id, deci poate fi mutată ulterior într-un worker separat, fără modificări.

**Cod de scris**

- Backend: `services/submission_runner.py` (`run_submission`), semaforul din `runner/factory.py`, hook-ul `lifespan` din `main.py`, câmpurile `started_at` și `finished_at`, verificarea intervalului minim.
- `hooks/useSubmission.js`: interogare TanStack Query pe `GET /submissions/{id}`, cu `refetchInterval` care întoarce `false` când statusul e final.
- `pages/AssignmentPage.jsx`: descrierea temei (Markdown), editorul Monaco, butonul „Trimite”, lista testelor și istoricul trimiterilor.
- `components/TestResultRow.jsx` (iconiță, nume, verdict, timp) și `components/StatusBadge.jsx` (`queued`, `running`, `done`, `error`).

**Tehnologii explicate**

- **`BackgroundTasks`:** FastAPI rulează funcția după ce trimite răspunsul; o funcție sincronă merge într-un thread, deci nu blochează serverul. Limita: dacă procesul se oprește, munca se pierde, de aceea recuperarea la pornire.
- **De ce o sesiune nouă de bază de date:** sesiunea cererii aparține cererii și se închide la final; folosită în fundal ar da erori sau date nesincronizate.
- **Condiții de cursă și semafor:** mai multe trimiteri simultane ar porni prea multe containere; semaforul le pune la coadă.
- **Polling față de WebSocket sau SSE:** pentru câteva secunde de așteptare, o cerere pe secundă e suficientă și mult mai simplă; WebSocket ar aduce conexiuni persistente și reconectări.
- **TanStack Query:** ține cache-ul pe o cheie de interogare, reîncarcă periodic și se oprește când nu mai e nevoie; nu scrii manual `useEffect` cu `setInterval`.
- **Monaco Editor:** motorul editorului din VS Code; îl folosești ca pe o componentă controlată (`value`, `onChange`, `language="python"`).
- **Markdown în React:** `react-markdown` transformă textul în elemente React și nu execută HTML brut, deci descrierile scrise de profesor nu pot injecta scripturi.

**Teste**

- Servicii: `run_submission` cu `FakeRunner` trece prin `queued`, `running`, `done` și salvează rezultatele în ordine; o eroare în runner duce la `error`, nu la o trimitere blocată.
- Recuperare: o trimitere lăsată `running` devine `error` la pornirea aplicației.
- Semafor: cu un runner lent și limita 1, a doua trimitere începe abia după prima.
- API: `POST` întoarce 202 și `queued`; `GET` după finalizare întoarce `done` cu rezultate; alt student primește 404; a doua trimitere în intervalul minim primește 429.
- Frontend: `useSubmission` oprește polling-ul la statusul final; lista de teste randează corect fiecare stare.

**Gata când**

- [ ] trimiți cod din browser și vezi testele trecând pe rând
- [ ] repornești serverul în timpul unei trimiteri și starea se recuperează
- [ ] testele trec
- [ ] poți explica de ce funcția de fundal își deschide propria sesiune

**Întrebări pentru tine:** D8 (BackgroundTasks sau worker propriu), D16 (buton de rulare de probă). În plus: intervalul minim între trimiteri (5 secunde, default), număr maxim de trimiteri pe temă (10, default), temă de culori deschisă și închisă?

## Pasul 6 · Dashboard student și vederi profesor (săpt. 9)

**Obiectiv.** Fiecare rol vede ce are nevoie fără să cunoască API-ul: studentul își vede cursurile, temele și scorurile, profesorul își creează temele și testele din interfață și urmărește trimiterile clasei.

**Arhitectură și design**

- Datele agregate se calculează în backend, prin endpoint-uri de citire dedicate, nu în frontend din zeci de cereri mici.
- `GET /me/dashboard` întoarce, pentru student: cursurile, temele fiecărui curs cu cel mai bun scor și starea ultimei trimiteri, termenele apropiate și ultimele cinci trimiteri.
- Pentru profesor, pagina unui curs listează temele cu numărul de trimiteri, iar `GET /assignments/{id}/stats` întoarce rata de trecere pe test și distribuția scorurilor.
- Tabelul de trimiteri ale unei teme are paginare și filtre (student, status).
- Fiecare pagină are trei stări tratate uniform: încărcare, eroare și gol.

**Cod de scris**

- `services/dashboard_service.py`: `student_dashboard(db, student)` și `assignment_stats(db, assignment_id)`.
- `schemas/dashboard.py`, `api/v1/dashboard.py` și ruta de statistici în routerul de teme.
- Migrare cu indexurile din secțiunea „Modelul de date”.
- Frontend: `pages/StudentDashboard.jsx`, `pages/CoursePage.jsx` (vedere student și vedere profesor), `pages/teacher/AssignmentEditor.jsx`, `components/TestCaseForm.jsx` (rânduri dinamice: nume, input, output așteptat, ascuns, greutate, concepte), `components/SubmissionsTable.jsx`, `components/Pagination.jsx`, `components/LoadingState.jsx`, `components/ErrorState.jsx`, `components/EmptyState.jsx`.

**Tehnologii explicate**

- **Agregări SQL:** `GROUP BY` grupează rânduri, iar `COUNT`, `MAX` și `AVG` rezumă fiecare grup; în PostgreSQL, `COUNT(*) FILTER (WHERE ...)` numără doar rândurile care îndeplinesc o condiție, util pentru rata de trecere.
- **Cea mai recentă înregistrare dintr-un grup:** `DISTINCT ON` în PostgreSQL sau funcția fereastră `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ... DESC)`; o vei folosi și în Pasul 7.
- **Indexuri și `EXPLAIN ANALYZE`:** un index grăbește căutarea după coloanele din `WHERE` și `ORDER BY`; `EXPLAIN ANALYZE` arată dacă interogarea îl folosește.
- **Problema N+1 la nivel de API:** dacă pagina cere datele cursului prin zeci de apeluri, apare aceeași problemă ca la ORM, mutată în rețea; endpoint-urile agregate o evită.
- **Formulare cu rânduri dinamice în React:** starea e un vector de obiecte, iar adăugarea și ștergerea unui rând sunt actualizări imutabile ale vectorului.

**Teste**

- Servicii, cu date construite în test (trei studenți, două teme, scoruri cunoscute): cel mai bun scor, rata de trecere pe test și distribuția scorurilor se compară cu valori calculate de mână.
- API: un student nu vede datele altui student; profesorul altui curs primește 404; paginarea și filtrele întorc exact rândurile așteptate.
- Frontend: dashboard-ul randează corect cu date simulate și cu listă goală; `TestCaseForm` adaugă și șterge rânduri și trimite structura corectă.

**Gata când**

- [ ] ambele roluri parcurg fluxul complet doar din interfață, de la creare curs la rezultat
- [ ] numerele din dashboard coincid cu cele calculate manual
- [ ] testele trec
- [ ] poți explica interogarea din spatele `stats`

**Întrebări pentru tine:** D11 (stilarea). În plus: ce carduri și în ce ordine vrei pe dashboardul studentului? Editorul de teste: formular (default) sau import din fișier JSON ori CSV? Graficele apar acum sau doar în Pasul 7 (default: Pasul 7)?

## Pasul 7 · Concepte și raportul „unde greșești” (săpt. 10)

**Obiectiv.** Verdictele de pe teste devin informație despre învățare: pentru fiecare student, ce concepte stăpânește și ce are de recapitulat. Pasul 8 folosește aceste date ca să trimită studentul la materialul potrivit.

**Arhitectură și design**

- Un concept este o etichetă pe test (relație many-to-many), creată liber de profesor în cadrul cursului.
- Regula implicită (D17): pentru fiecare temă se ia **cea mai recentă trimitere terminată** (`done`) a studentului, ca greșelile intermediare să nu-l penalizeze. Trimiterile în eroare sunt ignorate.
- Pentru fiecare concept se numără testele etichetate și câte au trecut: `pass_rate = trecute / total`, adunate peste toate temele cursului.
- Nivelurile, cu pragurile ținute în configurare: sub 0,5 `review` („de recapitulat”), între 0,5 și 0,8 `progress`, de la 0,8 în sus `mastered`.
- Separare clară: interogarea aduce rânduri brute, iar agregarea și clasificarea sunt funcții pure. Așa logica se testează fără bază de date, iar interogarea separat.
- Raportul profesorului, pe fiecare concept: media ratelor de trecere ale studenților și câți dintre ei sunt la nivelul `review`.
- `ConceptReportService` întoarce date structurate, cu identificatori de concept și de test, ca Pasul 8 să poată lega testele picate de materialele cursului.

**Cod de scris**

- `services/report_service.py`: `fetch_concept_rows(db, student_id, course_id)`, `aggregate_concepts(rows)`, `classify(pass_rate)`, `student_concept_report(...)`, `class_concept_report(...)`.
- `schemas/report.py`: `ConceptStat` (concept, teste totale, teste trecute, `pass_rate`, nivel, testele picate) și răspunsul pe clasă.
- `api/v1/reports.py`: cele două rute din tabelul API. Testele ascunse picate apar cu tema și conceptul, fără conținutul testului.
- `scripts/seed_demo.py`, partea de rezultate: trei studenți cu profiluri diferite (unul bun la recursivitate și slab la liste, unul slab peste tot, unul bun peste tot).
- Frontend: `pages/ConceptReport.jsx` cu un grafic Recharts cu bare orizontale (rata de trecere pe concept, sortată crescător) și lista „Ce să recapitulezi”, cu linkuri către temele unde au picat testele; vederea profesorului, cu o bară pe concept pentru clasă.

**Tehnologii explicate**

- **Relația many-to-many:** un test poate avea mai multe concepte, iar un concept apare pe mai multe teste; se modelează cu tabelul de legătură `test_case_concepts` și două chei străine.
- **Join-uri în lanț:** `submissions`, apoi `test_results`, apoi `test_cases`, apoi `test_case_concepts`, apoi `concepts`; fiecare join adaugă o legătură din lanț, iar un join greșit duplică rânduri și strică numerele.
- **Cea mai recentă trimitere pe grup:** `DISTINCT ON (student_id, assignment_id)` sau `ROW_NUMBER()`, ca în Pasul 6.
- **Funcții pure față de interogări:** o funcție care primește rânduri și întoarce statistici nu depinde de bază, deci o verifici cu liste scrise de mână.
- **Recharts:** componente declarative (`BarChart`, `Bar`, `XAxis`), cu `ResponsiveContainer` pentru lățime adaptivă. Nivelul se arată și prin text, nu doar prin culoare, ca raportul să fie accesibil.

**Teste**

- `classify`: valorile de graniță 0,49, 0,5, 0,79 și 0,8 cad în nivelul corect.
- `aggregate_concepts`, cu rânduri scrise de mână: student bun la recursivitate și slab la liste dă exact rezultatul așteptat; un test cu două concepte contează la ambele.
- Regula trimiterii: o trimitere veche mai bună și una nouă mai slabă folosește pe cea nouă; o trimitere în stare `error` e ignorată.
- API: studentul vede doar propriul raport; profesorul altui curs primește 404; testele ascunse nu își dezvăluie conținutul.
- Frontend: graficul și lista randează cu date simulate și cu raport gol.

**Gata când**

- [ ] doi studenți diferiți văd concepte diferite în raport, cu datele din seed
- [ ] profesorul vede raportul pe clasă
- [ ] testele trec
- [ ] poți explica interogarea și de ce agregarea e separată de ea

**Întrebări pentru tine:** D17 (regula trimiterii). În plus: pragurile 50% și 80% ți se potrivesc? Conceptele se creează libere din editorul de teste (default) sau dintr-o listă fixă pe curs? Vrei o versiune mică a raportului și pe pagina temei? Contează greutatea testelor la calculul ratei (default: nu, doar numărul)?

## Pasul 8 · Materiale, Learn și recomandări (săpt. 11)

**Obiectiv.** Profesorul încarcă cursuri și laboratoare ca PDF sau PPTX și le leagă de teme și de teste. Studentul le găsește în rubrica Learn din header, iar după un test greșit primește un popup care îl duce direct la materialul și la paginile potrivite. Pasul adaugă 3 tabele, 11 endpoint-uri și 5 ecrane; mecanismul de evaluare rămâne neschimbat.

**Arhitectură și design**

- Fișierele stau pe disc, în uploads/ (D21). În baza de date rămân doar metadatele, în tabelele Material, AssignmentMaterial și TestCaseMaterial din Modelul de date.
- MaterialService (services/material\_service.py) conține regulile. FileStore (storage/file\_store.py) e singurul loc care atinge discul: save(stream) întoarce numele generat, open(name) și delete(name). Routerul nu atinge discul.
- Încărcarea (POST /courses/{id}/materials, multipart cu câmpurile file și title): doar profesorul cursului; fișierul se citește în bucăți cu limită de 20 MB (413 peste); tipul se stabilește după primii octeți (PDF începe cu %PDF-; PPTX e o arhivă ZIP care conține ppt/presentation.xml), nu după extensie, iar altceva dă 415; pentru PDF, pypdf îl deschide și numără paginile (fișier corupt sau cu parolă dă 422); numele de pe disc e un uuid4 generat de server; titlul se curăță de spații și are cel mult 120 de caractere.
- Conversia PPTX în PDF e sincronă (D20): profesorul așteaptă câteva secunde și vede un indicator de progres. Se folosește LibreOffice headless, cu timeout de 60 s, profil temporar propriu și cel mult o conversie pe rând. Dacă eșuează, răspunsul e 422 cu mesajul „Prezentarea nu a putut fi convertită”, iar pe disc nu rămâne nimic. Convertorul e ascuns în spatele funcției convert\_pptx\_to\_pdf(src, dst\_dir), ca testele să îl poată înlocui cu unul fals.
- Servirea: GET /materials/{id}/preview întoarce PDF-ul (originalul sau varianta convertită) cu Content-Type application/pdf, Content-Disposition inline și X-Content-Type-Options: nosniff. GET /materials/{id}/file întoarce originalul ca attachment, cu numele curată al fișierului. Ambele cer calitatea de membru al cursului; materialul altui curs dă 404. Directorul uploads/ nu se expune niciodată ca fișiere statice.
- Asocierea: PUT /assignments/{id}/materials și PUT /test-cases/{id}/materials primesc lista completă \[{material\_id, pages}\] și o înlocuiesc într-o singură tranzacție. Toate materialele trebuie să aparțină cursului temei, altfel 422. Câmpul pages se validează cu o funcție pură parse\_pages(text, page\_count): acceptă numere și intervale separate prin virgulă („12-15, 18”), în limitele documentului, fără intervale inversate; gol înseamnă întregul material (D23). Se normalizează la salvare.
- Regula de recomandare (GET /submissions/{id}/recommendations, pentru autor și pentru profesorul cursului): pentru fiecare test cu verdict diferit de passed se iau materialele testului; dacă testul nu are materiale, se iau cele ale temei. Lista se deduplică pe material (paginile se unesc), se ordonează după numărul de teste picate care cer materialul și spune care teste au dus la el. Se calculează la cerere, nu se stochează, ca să reflecte mereu asocierile curente. Testele ascunse apar doar ca „Test ascuns #n”, fără nume sau conținut. Dacă toate testele au trecut, lista e goală. Logica e o funcție pură, build\_recommendations(failed\_tests, test\_materials, assignment\_materials).
- GET /me/learn întoarce, pentru studentul autentificat, câte o intrare pe curs la care e înscris: id, titlu, profesor, material\_count, last\_material\_at. Un curs fără materiale apare cu stare goală, nu lipsește.
- Vizibilitate și ștergere (D22): materialele se văd imediat de studenții înscriși. La ștergerea unui material, baza de date șterge legăturile prin cascade, iar FileStore șterge fișierele (originalul și PDF-ul convertit) după commit, ca o eroare de disc să nu strice tranzacția.
- Securitate la încărcare: limita de 20 MB se aplică la citire, nu doar după antetul Content-Length; pentru PPTX se verifică înainte de conversie numărul de intrări din arhivă (cel mult 2000) și suma dimensiunilor necomprimate (cel mult 200 MB), ca să nu intre o arhivă bombă; numele fișierelor vin doar de la server; fiecare descărcare verifică calitatea de membru; titlul se afișează ca text, niciodată ca HTML.
- Frontend, student: rubrica Learn din header (vizibilă doar studentului) duce la pages/Learn.jsx, cu un card pe curs; cardul duce la pages/LearnCourse.jsx, cu meniul materialelor; un material se deschide în pages/MaterialViewer.jsx (react-pdf, navigare între pagini, buton de descărcare), pe ruta /learn/materials/:id?page=12, care deschide direct pagina indicată. Pe pagina temei apare bara „Materiale pentru această temă”, cu paginile indicate.
- Popup-ul (components/RecommendationDialog.jsx) apare pe pagina temei când o trimitere ajunge în starea done cu cel puțin un test picat și există recomandări. Arată materialele cu paginile și butonul „Deschide la pagina N”, se închide cu Escape, și nu mai apare pentru aceeași trimitere (se ține minte în sessionStorage, doar ca facilitate). Dacă nu există recomandări sau toate testele au trecut, nu apare nimic.
- Frontend, profesor: fila „Materiale” a cursului (listă, încărcare cu indicator de progres, redenumire, ștergere cu confirmare) și componenta MaterialPicker, folosit în editorul temei și în fiecare test, cu câmp pentru pagini și mesaj de eroare la format greșit.

**Cod de scris**

- models/material.py (Material, AssignmentMaterial, TestCaseMaterial) și migrarea Alembic corespunzătoare.
- storage/file\_store.py și storage/pptx\_converter.py.
- services/pages.py (parse\_pages) și services/material\_service.py: upload\_material, list\_materials, rename\_material, delete\_material, set\_assignment\_materials, set\_test\_case\_materials, build\_recommendations, learn\_overview.
- schemas/material.py și api/v1/materials.py, cu cele 11 rute din tabelul API.
- Infrastructură: uploads/ în .gitignore, volum în docker-compose, LibreOffice (pachetul libreoffice-impress, fără pachete recomandate) în imaginea backend-ului, variabilele UPLOAD\_DIR, MAX\_UPLOAD\_MB și PPTX\_CONVERT\_TIMEOUT\_S în .env.example.
- scripts/seed\_demo.py: două materiale de demo (un PDF mic generat în script și un PPTX), asociate unei teme și unui test, ca popup-ul să se vadă la demo.
- Frontend: api/materials.js, hooks/useMaterials.js, hooks/useRecommendations.js, paginile Learn, LearnCourse și MaterialViewer, RecommendationDialog, MaterialPicker, fila Materiale.

**Tehnologii explicate**

- multipart/form-data și UploadFile: cum primește FastAPI un fișier, de ce se citește în bucăți și ce înseamnă limita aplicată la citire.
- Tipul unui fișier după primii octeți (magic bytes), față de extensie: de ce extensia nu e o dovadă.
- Formatul PPTX: o arhivă ZIP cu fișiere XML; de aici verificările de structură și protecția împotriva arhivelor bombă.
- LibreOffice headless: soffice --headless --convert-to pdf --outdir, cu profil separat (-env:UserInstallation), ca două procese să nu se calce și ca rularea să nu depindă de profilul unui utilizator.
- FileResponse și antetele Content-Disposition (inline față de attachment) și X-Content-Type-Options.
- react-pdf: componentele Document și Page, worker-ul pdf.js și cum se configurează în Vite.
- Metoda PUT cu înlocuire în tranzacție, față de adăugare și ștergere pe rând: mai simplă și fără stări intermediare.
- Calcul la cerere față de date stocate: de ce recomandările nu se salvează.

**Teste**

- parse\_pages: „12-15, 18”, spații în plus, „5-3” respins, „0” respins, o pagină peste page\_count respinsă, text gol acceptat.
- build\_recommendations: un test picat cu materiale proprii folosește doar materialele lui; un test fără materiale folosește materialele temei; deduplicare cu unirea paginilor; ordonarea după numărul de teste; testul ascuns anonimizat; toate testele trecute dau listă goală.
- Încărcare: PDF valid dă 201; un fișier text cu extensia .pdf dă 415; peste 20 MB dă 413; PPTX valid cu convertor fals dă 201 cu preview; convertor care eșuează dă 422 și lasă uploads/ gol; student dă 403.
- Matricea de permisiuni: student din alt curs descărcă → 404; profesorul altui curs asociază → 404; material din alt curs asociat unei teme → 422; autorul trimiterii vede recomandările, alt student primește 404.
- Ștergere: materialul, legăturile lui și fișierele de pe disc dispar; ștergerea cursului curăță toate fișierele lui.
- Securitate: un titlu sau un nume de fișier cu ../ nu ajunge niciodată pe disc; răspunsurile de fișier au nosniff; o arhivă PPTX cu prea multe intrări e respinsă.
- Cu markerul libreoffice: un PPTX real mic se convertește într-un PDF cu numărul așteptat de pagini.
- Frontend: Learn cu cursuri și cu stare goală; popup-ul se deschide după o trimitere cu test picat și nu se deschide la o trimitere perfectă; linkul din popup conține ?page=; MaterialPicker respinge un câmp pages invalid.

**Gata când**

- [ ] profesorul încarcă un PDF și un PPTX, iar ambele se deschid în vizualizator
- [ ] profesorul asociază materiale, cu pagini, unei teme și unui test
- [ ] studentul vede cardul cursului în Learn și deschide un material
- [ ] după o trimitere cu un test picat apare popup-ul cu materialul și pagina corectă; la o trimitere perfectă nu apare
- [ ] fișierele nevalide sunt respinse cu un mesaj clar
- [ ] testele trec, iar cel cu LibreOffice real trece local
- [ ] poți explica de ce conversia e sincronă, cum se alege recomandarea și cum e protejată încărcarea

**Întrebări pentru tine:** D20 (PPTX prin LibreOffice) și D21-D24. În plus: popup-ul apare automat la fiecare trimitere cu greșeli (default) sau doar prin butonul „Materiale recomandate” de lângă rezultat? Studentul poate descărca originalul (default: da)? Paginile se scriu ca interval liber (default) sau ai nevoie de un selector vizual?

## Pasul 9 · Calitate, securitate și livrare locală (săpt. 12)

**Obiectiv.** Aplicația e stabilă, rezonabil de sigură pentru un proiect de curs și pornește de la zero după instrucțiunile din README. Niciun flux nou; doar consolidare.

**Arhitectură și design**

- Configurare completă prin variabile de mediu, cu `.env.example` în git și fără secrete în cod.
- Logging cu un identificator de cerere (`request id`) care apare în toate liniile unei cereri și în antetul `X-Request-ID`.
- Limite de abuz: dimensiunea codului trimis, lungimea câmpurilor text și un rate limit simplu pe login, pe trimiteri și pe încărcarea de materiale.
- Două moduri de pornire. Implicit: baza de date în compose, backend-ul și frontend-ul pe calculatorul tău. Dacă alegi D10 = da, pentru un demo de la zero, profilul `demo` din compose rulează tot în containere, cu `docker.sock` montat în backend; folosește-l doar pe un calculator personal, nu pe un server expus (D10).
- CI complet: lint, teste backend cu serviciu PostgreSQL, teste frontend și build.

**Cod de scris**

- `core/logging.py` și un middleware care generează `request id`.
- `core/rate_limit.py`: contor cu fereastră fixă, ca dependență, aplicat pe `POST /auth/login`, pe trimiteri și pe încărcarea de materiale. Ține starea în memorie și se resetează la repornire, ceea ce e suficient pentru demo.
- Validări în scheme: `max_length` pe cod (64 KB) și pe titluri, intervale pentru `time_limit_ms` și `memory_limit_mb`.
- `backend/Dockerfile`, `frontend/Dockerfile` și profilul `demo` din `docker-compose.yml`.
- Imaginea backend-ului conține LibreOffice (conversia PPTX din Pasul 8), iar docker-compose montează volumul uploads/, ca fișierele să supraviețuiască repornirii.
- `scripts/seed_demo.py`: început în Pasul 7, completat în Pasul 8 cu materialele de demo și acum cu istoricul, cu un profesor, opt studenți, un curs cu trei teme și trimiteri cu data în trecut, pe trei săptămâni, cu profiluri diferite de studenți; graficele arată vii, nu goale.
- `.github/workflows/ci.yml` final, cu cache pentru `pip` și `npm`.
- `scripts/export_openapi.py` și `docs/api.md` generat din schema OpenAPI.
- `README.md`: ce este, cum pornești în cinci comenzi, cum rulezi testele.

**Tehnologii explicate**

- **Variabile de mediu și secrete:** orice valoare care diferă între calculatoare sau e secretă (parola bazei de date, cheia JWT) vine din mediu; un secret ajuns în git trebuie schimbat, nu doar șters.
- **Logging structurat și `request id`:** când o cerere eșuează, filtrezi logurile după același identificator și vezi tot drumul ei.
- **Rate limiting:** limitarea numărului de cereri într-un interval; fereastra fixă e cea mai simplă variantă, cu dezavantajul unor rafale la capetele ferestrelor.
- **Imagini și compose:** o imagine e un șablon de sistem de fișiere, un container e o instanță a ei; compose leagă servicii prin rețea internă, volume și `depends_on` cu `healthcheck`.
- **CI:** joburi pornite la fiecare push, cu servicii auxiliare (PostgreSQL) și cache pentru dependențe.
- **OWASP pe scurt:** injecția (ORM-ul parametrizează interogările), XSS (React escapează textul, iar Markdown-ul nu primește HTML brut), control de acces defectuos (matricea de permisiuni), autentificare slabă (hash Argon2 și rate limit), configurare nesigură (debug oprit, CORS restrâns, secrete în mediu), dependențe vulnerabile (`pip-audit` și `npm audit`).
- **`docker.sock`:** accesul la el echivalează cu drepturi de administrator pe gazdă; o notă despre risc intră în README.

**Teste**

- Flux complet la nivel de API: înregistrare profesor și student, curs, temă, teste, înscriere, trimitere, polling până la `done`, raport; cu `FakeRunner` și o variantă cu `DockerRunner` (marker `docker`).
- Flux complet pentru materiale: profesorul încarcă un PDF și îl asociază unui test, studentul trimite cod greșit și primește, la recomandări, materialul cu pagina corectă (PPTX cu convertorul fals).
- Rate limit: a unsprezecea cerere de login într-un minut primește 429; după fereastră, trece din nou.
- Limite: un cod de peste 64 KB primește 422; `request id` apare în antet.
- Manual, documentat: un coleg sau un calculator curat pornește aplicația urmând doar README-ul.
- Opțional: un singur test Playwright care parcurge autentificarea și o trimitere.

**Gata când**

- [ ] pornești aplicația pe un calculator curat urmând README-ul
- [ ] CI e verde, cu toate joburile
- [ ] fluxul complet trece automat
- [ ] `docs/api.md` corespunde cu `/docs`
- [ ] ai citit lista de securitate din anexă și ai bifat ce se aplică

**Întrebări pentru tine:** D10. În plus: demonstrezi pe laptopul tău sau pe un server al facultății (dacă e server, backend-ul nu se expune public)? Vrei și testul Playwright? Ce limită folosim pentru rate limit (10 cereri pe minut la login, default)?

## Pasul 10 · Predare, documentație și demo (săpt. 13)

**Obiectiv.** Documentația e completă, demo-ul e repetat, iar proiectul e înghețat: de luni din săptămâna 13 nu mai intră nicio funcționalitate nouă, doar corecturi.

**Livrabile**

- `docs/uml/` (PlantUML, cu SVG sau PNG exportat): diagrama de use case, diagrama de clase sau ER, diagrama de componente (arhitectura), diagrama de secvență „trimitere de cod” (browser, router, serviciu, runner, container, bază de date, polling), diagrama de stări pentru Submission și diagrama de secvență pentru popup-ul de recomandări.
- `README.md` final: scopul, capturi de ecran, arhitectura pe scurt, pornirea, rularea testelor, limitele cunoscute.
- `docs/adr/`: câte o notă de decizie (context, decizie, consecințe) pentru `Runner` ca interfață, JWT, polling față de WebSocket, livrarea codului în container, PostgreSQL, stocarea fișierelor în uploads/ și conversia PPTX. Tabelul „Decizii deschise” are toate rândurile închise.
- `docs/demo.md`: scriptul de cinci minute, conturile și datele folosite, plus planul B.
- Înregistrarea video a demo-ului, ca plan de rezervă.
- Raportul de acoperire (`pytest --cov`) și lista „Idei în afara proiectului” din Anexa C.
- Orice livrabil suplimentar cerut de profesor (D18).

**Scriptul de demo (5 minute)**

| Minut | Ce arăți | Ideea de spus |
| --- | --- | --- |
| 0:00 | problema și ecranul de start | corectarea temelor de programare e lentă, iar studentul nu află ce să recapituleze |
| 0:20 | profesorul creează o temă cu teste și concepte și îi asociază materialele încărcate | testele au etichete de concept, unul e ascuns, iar fiecare test indică paginile unde se învață |
| 1:20 | studentul trimite cod greșit, apoi deschide materialul din popup și rubrica Learn | testele se colorează live, cel ascuns nu își arată conținutul, iar popup-ul duce direct la pagina potrivită din curs |
| 2:30 | studentul trimite cod corect | scorul urcă și apare în istoric |
| 3:10 | un program cu buclă infinită sau consum de memorie | sandbox-ul îl oprește și serverul rămâne neatins |
| 3:50 | raportul „unde greșești” și vederea profesorului | verdictele devin concepte de recapitulat |
| 4:40 | diagrama de arhitectură și lista de idei în afara proiectului | interfața `Runner` și legarea materialelor de teste sunt punctele de extindere |

**Tehnologii explicate**

- **PlantUML:** diagrame descrise ca text, deci versionate în git și ușor de modificat.
- **ADR (Architecture Decision Record):** o pagină scurtă per decizie importantă, cu contextul, alternativele și consecințele; arată profesorului că deciziile au fost gândite.
- **Acoperirea testelor:** procentul de linii executate de teste; indică zonele netestate, nu calitatea testelor.

**Verificări**

- Două repetiții complete ale demo-ului pe un mediu curat, cronometrate.
- Un mini-examen oral cu douăsprezece întrebări, la care răspunzi fără să te uiți în cod:
  1. Ce se întâmplă de la apăsarea butonului „Trimite” până apar rezultatele?
  2. De ce este `Runner` o interfață?
  3. Ce limite aplică sandbox-ul și ce atac oprește fiecare?
  4. Ce conține un JWT și cine îl verifică?
  5. Cum garantezi că un student nu vede trimiterile altuia?
  6. De ce task-ul de fundal își deschide propria sesiune de bază de date?
  7. Cum se calculează raportul pe concepte și de ce se ia ultima trimitere?
  8. Ce ar trebui schimbat pentru 200 de studenți simultan?
  9. Cum alege sistemul ce materiale să recomande după un test picat și de ce nu le stochează?
  10. Cum e protejată încărcarea de fișiere împotriva unui fișier fals sau a unei arhive bombă?
  11. Ce ar trebui schimbat pentru a accepta și Java?
  12. Ce nu e încă sigur în proiect și cum ai repara?

**Gata când**

- [ ] toate livrabilele de mai sus există și sunt în git
- [ ] demo-ul a fost repetat de două ori fără ajutor
- [ ] ai răspuns la toate cele douăsprezece întrebări cu vorbele tale
- [ ] lista „Idei în afara proiectului” e scrisă

**Întrebări pentru tine:** D18 (ce cere profesorul): formatul exact al livrabilelor, data evaluării, dacă proiectul e individual sau în echipă.

## Anexe

### A. Checklist de securitate

Se parcurge la sfârșitul Pasului 4, secțiunea „Fișiere încărcate” la sfârșitul Pasului 8, iar tot checklist-ul din nou în Pasul 9. Fiecare punct are un test sau o verificare asociată în pașii de mai sus.

**Sandbox**

- [ ] rețea dezactivată în container
- [ ] memorie și swap limitate la aceeași valoare
- [ ] limită de CPU
- [ ] număr maxim de procese (`pids_limit`)
- [ ] sistemul de fișiere rădăcină doar pentru citire, cu `tmpfs` mic pentru `/tmp`
- [ ] utilizator fără drepturi, `cap_drop=ALL` și `no-new-privileges`
- [ ] limită totală de timp, cu `kill()` la depășire
- [ ] output limitat la `max_output_bytes`
- [ ] container șters în `finally`, cu eticheta `autograder=1` verificabilă
- [ ] niciun mount din gazdă în afara directorului cu codul, doar pentru citire
- [ ] semafor pentru numărul de containere simultane
- [ ] `SubprocessRunner` refuzat când `ENV` nu este `dev`
- [ ] serverul și Docker nu sunt expuse într-o rețea publică
- [ ] riscul `docker.sock` este scris în README

**Aplicație**

- [ ] parole hash-uite cu Argon2, niciun hash în răspunsuri
- [ ] JWT cu expirare, secretul din variabile de mediu
- [ ] matricea de permisiuni acoperă fiecare rută
- [ ] CORS restrâns la originea frontend-ului
- [ ] rate limit pe login, pe trimiteri și pe încărcarea de materiale
- [ ] testele ascunse nu își dezvăluie conținutul
- [ ] Markdown randat fără HTML brut

**Fișiere încărcate**

- [ ] tipul se stabilește după primii octeți, nu după extensie sau Content-Type
- [ ] limită de 20 MB aplicată la citire
- [ ] arhivele PPTX sunt verificate (număr de intrări, dimensiune necomprimată) înainte de conversie
- [ ] conversia LibreOffice are timeout, profil temporar și cel mult o rulare simultană
- [ ] numele de pe disc sunt uuid generate de server, nicio cale nu vine de la client
- [ ] uploads/ nu e servit ca director static; fiecare descărcare verifică calitatea de membru
- [ ] răspunsurile de fișier au Content-Type corect și X-Content-Type-Options: nosniff
- [ ] ștergerea unui material sau a unui curs șterge și fișierele de pe disc
- [ ] testele ascunse apar în recomandări doar ca „Test ascuns #n”
- [ ] titlul materialului se afișează ca text, niciodată ca HTML

### B. Șablonul unui pas nou

Când apare o funcționalitate care nu încape în pașii existenți, o descrii cu acest șablon înainte să scrii cod, ca documentul să rămână sursa adevărului.

```markdown
## Pasul N · Titlu (săpt. X)

**Obiectiv.** Două propoziții: ce funcționează la final.

**Arhitectură și design**
- straturile atinse, interfețe noi, legătura cu „Decizii deschise”

**Cod de scris**
- fișier: ce face, funcții importante cu semnătură

**Tehnologii explicate**
- tehnologie: ce este, ce problemă rezolvă, ce alternative are

**Teste**
- nivel: ce se verifică

**Gata când**
- [ ] criterii verificabile

**Întrebări pentru tine:** ID-uri din „Decizii deschise” și întrebări noi.
```

### C. Idei în afara proiectului

Se completează pe parcurs; orice idee nouă din timpul implementării ajunge aici, nu în cod. Ideile de aici nu fac parte din acest semestru.

- alte limbaje de programare prin noi implementări de `Runner`
- worker separat cu coadă de joburi
- detecția de plagiat între trimiteri
- teste de tip grilă
- căutare în textul materialelor
- versionarea materialelor și publicare programată
- alte formate de material (DOCX, video)
