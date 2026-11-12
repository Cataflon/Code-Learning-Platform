# Plan de dezvoltare - Platforma de programare cu autograder

Oct 11, 2026 · @Cata

## Ce livrezi până în săptămâna 13

La finalul săptămânii 13 ai o platformă web în care profesorul creează teme cu teste, studentul trimite cod Python rulat izolat în Docker și vede rezultatul pe fiecare test, iar sistemul arată unde greșește studentul, pe concepte. Profesorul poate încărca cursurile și laboratoarele (PDF sau PPTX) și le poate lega de teme și de teste, iar studentul le găsește în rubrica Learn și, când greșește un test, este trimis direct la materialul potrivit.

**Intră în MVP**

- roluri student și profesor, cu autentificare
- cursuri, teme și teste (intrare și ieșire așteptată), fiecare test cu o etichetă de concept
- trimitere de cod Python, rulat în container cu limită de timp și memorie, fără rețea
- rezultate pe test, actualizate live (polling)
- dashboard student (cursuri, teme, scoruri, istoric) și vedere profesor (trimiteri, statistici)
- raportul „unde greșești" pe concepte
- materiale de curs și de laborator (PDF sau PPTX) încărcate de profesor și alese pentru fiecare temă și fiecare test
- rubrica Learn pentru student (un card pe curs, meniu cu materiale) și popup care, după un test greșit, deschide materialul la pagina indicată
- teste automate, CI, documentație și diagrame UML

**Nu intră în proiect**

Căutare în textul materialelor, versionarea materialelor, integrarea cu Moodle, alte limbaje decât Python, cozi de joburi (Celery), detecția de plagiat, teste de tip grilă.

**Presupuneri:** proiect solo, 10-12 ore pe săptămână (circa 100-120 de ore în total), doar Python, un singur backend (monolit), implementat în felii de Fable, pe care tu le revizuiești și le înțelegi, fără integrări externe.

## Ce înveți și cât de adânc

Sunt șase lucruri noi pe care trebuie să le stăpânești bine (Python, FastAPI, SQLAlchemy, autentificarea, Docker, pytest); restul sunt extensii ale frontend-ului pe care îl știi deja. Înveți fiecare piesă în săptămâna în care o folosești, nu în avans.

| Tehnologie | Pentru ce o folosești | Cât de adânc | Săpt. |
| --- | --- | --- | --- |
| Python 3.12 (venv, tipuri, excepții, module) | tot backend-ul | solid | 3 |
| Git și GitHub (branch-uri, pull request) | cod, CI | solid | 3 |
| HTTP și REST (metode, coduri de status, JSON) | designul API-ului | solid | 3-4 |
| FastAPI + Pydantic | rute, validare, documentație Swagger | adânc | 3-5 |
| SQLAlchemy 2 + Alembic | modele, interogări, migrări | adânc | 4 |
| PostgreSQL (SQLite în primele zile) | join-uri, GROUP BY, indexuri | mediu | 4, 9-10 |
| JWT, hash de parole, roluri | autentificare și autorizare | adânc | 5 |
| pytest + TestClient | teste unitare și de integrare | adânc | din săpt. 4 |
| subprocess (Python) | prototipul de rulare a codului | mediu | 6 |
| Docker + docker-compose (+ SDK Python) | sandbox-ul și mediul de rulare | mediu spre adânc | 7-8, 12 |
| React Router + TanStack Query | pagini, cereri către API, polling | mediu (știi deja React) | 5, 8-9 |
| Monaco Editor | editorul de cod din pagină | de bază | 8 |
| Recharts | graficele de progres și raportul | de bază | 10 |
| GitHub Actions | teste automate la fiecare push | de bază | 12 |
| PlantUML sau draw.io | diagramele UML | de bază | 3, 13 |
| Încărcare de fișiere (multipart), LibreOffice headless | materialele PDF/PPTX și conversia lor în PDF | mediu | 11 |
| react-pdf | vizualizatorul de materiale și popup-ul cu pagina indicată | de bază | 11 |

## Calendar pe săptămâni (3-13)

Unsprezece săptămâni, câte o felie care merge de la interfață până la baza de date; sandbox-ul Docker (săpt. 7) este punctul cu cel mai mare risc și are în jurul lui spațiu de rezervă. Fiecare săptămână se încheie cu un test de înțelegere: dacă nu poți explica fluxul cu vorbele tale, nu treci mai departe.

&#91;embedded content: harta fazelor · 6 faze, 6 porți de verificare\]

Sandbox-ul (faza „Rulare cod") e singura fază marcată ca riscantă; dacă alunecă, se mută pagina live cu o săptămână mai târziu.

### Săpt. 3 · Fundații și cerințe (săptămâna curentă)

- **Înveți:** Python de bază (venv, funcții, clase, tipuri, excepții), Git cu branch-uri, drumul unei cereri HTTP.
- **Construiești:** repo cu `backend/` și `frontend/`, o rută FastAPI, docker-compose cu Postgres, primul test pytest. Scrii 12-15 user stories, diagrama use case și schema bazei de date v1.
- **Gata când:** poți explica drumul unei cereri de la browser la baza de date și înapoi.

### Săpt. 4 · API REST și date

- **Înveți:** rute FastAPI, modele Pydantic, SQLAlchemy 2, migrări Alembic, coduri de status.
- **Construiești:** modelele User, Course, Assignment și TestCase; CRUD pentru cursuri, teme și teste; câte un test pytest pe fiecare rută.
- **Gata când:** Swagger arată CRUD-ul funcțional și poți explica diferența dintre un model Pydantic și unul SQLAlchemy.

### Săpt. 5 · Autentificare și roluri

- **Înveți:** hash de parole, JWT, dependențe FastAPI, autorizare pe roluri; în frontend, React Router și păstrarea token-ului.
- **Construiești:** register și login, rute protejate, înrolarea studentului la curs, paginile de autentificare în React.
- **Gata când:** un student primește 403 la crearea unei teme, iar profesorul o creează; poți explica ce conține token-ul și cine îl verifică.

### Săpt. 6 · Trimiteri și evaluare (prototip fără Docker)

- **Înveți:** `subprocess` cu timeout, stdin și stdout, compararea ieșirii cu cea așteptată.
- **Construiești:** modelele Submission și TestResult, endpoint-ul de trimitere și un evaluator în spatele unei interfețe `Runner`, cu teste unitare.
- **Gata când:** o trimitere întoarce rezultatul pe fiecare test. Acest runner e doar pentru dezvoltare locală, cu cod scris de tine; nu îl expune public.

### Săpt. 7 · Sandbox Docker (cea mai riscantă)

- **Înveți:** imagini și containere, limite de memorie și CPU, rețea dezactivată, utilizator fără drepturi, sistem de fișiere doar pentru citire, timeout și oprirea containerelor.
- **Construiești:** un al doilea `Runner` care rulează codul într-un container dintr-o imagine mică de Python, cu curățare după fiecare rulare.
- **Gata când:** ai teste care trec pe cod corect și opresc curat o buclă infinită, un consum mare de memorie și o încercare de acces la rețea sau la fișiere.

### Săpt. 8 · Rezultate live și pagina unei teme

- **Înveți:** `BackgroundTasks`, statusuri (în coadă, rulează, terminat), polling cu TanStack Query, Monaco Editor.
- **Construiești:** trimiterea devine asincronă; pagina temei are editor, buton de trimitere și lista de teste care se completează pe rând.
- **Gata când:** trimiți cod din browser și vezi testele trecând în timp real.

### Săpt. 9 · Dashboard student și vedere profesor

- **Înveți:** interogări de agregare (`GROUP BY`, `JOIN`) și paginare.
- **Construiești:** dashboard-ul studentului (cursuri, teme, scoruri, istoric); pentru profesor, crearea temelor și a testelor din interfață și tabelul cu trimiteri.
- **Gata când:** ambele roluri parcurg fluxul complet doar din UI.

### Săpt. 10 · Concepte și raportul „unde greșești"

- **Înveți:** relația many-to-many (teste și concepte), agregarea pe concept, Recharts.
- **Construiești:** etichete pe teste, rata de eșec pe concept pentru fiecare student, un grafic și lista „ce să recapitulezi", cu date de test realiste.
- **Gata când:** raportul arată concepte diferite pentru doi studenți diferiți și poți explica interogarea din spatele lui.

### Săpt. 11 · Materiale, Learn și recomandări

- **Înveți:** încărcarea de fișiere în FastAPI (multipart) și validarea după conținut, conversia PPTX în PDF cu LibreOffice, afișarea PDF-urilor cu react-pdf.
- **Construiești:** tabelele Material, AssignmentMaterial și TestCaseMaterial; încărcarea și lista materialelor pentru profesor; selectorul de materiale, cu pagini, la teme și la teste; rubrica Learn cu un card pe curs și meniul materialelor; popup-ul care, după un test greșit, deschide materialul la pagina indicată.
- **Gata când:** profesorul încarcă un PDF și un PPTX și le leagă de un test, iar studentul care greșește testul ajunge din popup la pagina potrivită; poți explica cum se alege recomandarea și cum e protejată încărcarea.

### Săpt. 12 · Calitate și pregătire de demo

- **Înveți:** GitHub Actions, logging, validarea intrărilor (dimensiunea codului, limită simplă de cereri).
- **Construiești:** teste de integrare pentru fluxul principal, inclusiv materialele, CI care le rulează, mesaje de eroare clare, un cont demo cu istoric pe trei săptămâni și `docker compose up` care pornește totul.
- **Gata când:** un coleg clonează repo-ul și pornește aplicația cu o singură comandă.

### Săpt. 13 · Predare

- **Construiești:** nicio funcționalitate nouă. Diagramele UML finale (use case, ER, arhitectură, secvență pentru trimitere și pentru popup-ul de recomandări), README, scriptul demo de 5 minute și o înregistrare video de rezervă.
- **Gata când:** ai repetat demo-ul de două ori fără ajutor și poți răspunde la „de ce ai ales X" pentru fiecare decizie importantă.

## Săptămâna 14 și criteriul „gata"

Săptămâna 14 este rezervă: corectezi bug-uri, repeți prezentarea și îți pregătești răspunsurile la întrebări, fără funcționalități noi. Proiectul e gata pentru demo când toate punctele de mai jos sunt bifate.

- [ ] Profesorul se autentifică, creează un curs, o temă și 4-5 teste cu etichete de concept
- [ ] Studentul se înrolează, trimite cod și vede testele trecând live
- [ ] Codul rău (buclă infinită, memorie, rețea) este oprit fără să afecteze serverul
- [ ] Raportul „unde greșești" arată concepte diferite pentru doi studenți
- [ ] Profesorul încarcă un PDF și un PPTX și le asociază unui test; studentul care greșește testul vede popup-ul și ajunge la pagina indicată
- [ ] Studentul găsește aceleeași materiale în rubrica Learn, pe cardul cursului
- [ ] `docker compose up` pornește aplicația de la zero
- [ ] Testele automate trec în CI
- [ ] Ai diagramele UML, README-ul și un script de demo de 5 minute
- [ ] Poți explica fiecare strat (UI, API, bază de date, runner) fără să te uiți în cod

## Riscuri, tăieri și reguli de lucru

Dacă rămâi în urmă, tai în ordinea de mai jos și nu atingi sandbox-ul, autentificarea cu roluri sau testele pe evaluator.

**Ce tai, în ordine**

1. vederea pe clasă pentru profesor; rămâne doar raportul studentului
2. recomandările pe test din popup; rămân doar materialele asociate temei
3. conversia PPTX în PDF; se acceptă doar PDF (D20)
4. graficele din Recharts, înlocuite cu un tabel sortat
5. Monaco Editor, înlocuit cu un câmp de text simplu
6. PostgreSQL, înlocuit cu SQLite (schimbi doar conexiunea, SQLAlchemy ascunde diferența)
7. CI în GitHub Actions; rulezi testele local

**Riscuri**

| Risc | Semnal | Răspuns |
| --- | --- | --- |
| Sandbox-ul Docker durează mai mult | la finalul săpt. 7 nu rulează încă cod izolat | folosești săpt. 8 pentru el, muți pagina live în săpt. 9 și tai punctele 1 și 2 |
| Scope creep (grile, alte limbaje, Moodle) | apare o idee nouă în timpul semestrului | o treci în Anexa C din masterprompt, „Idei în afara proiectului”, și mergi mai departe |
| Înveți mai lent decât planul | un test de înțelegere picat de două ori | tai din listă, nu comprima învățatul |
| Cod nesigur rulat pe un server public | cineva altcineva are acces la aplicație | demo-ul rulează local; runner-ul din săpt. 6 nu se expune niciodată |
| Conversia PPTX în PDF nu merge sau e lentă | LibreOffice eșuează pe primele prezentări de test sau trece de 60 s | accepți doar PDF (D20) și păstrezi PPTX-ul doar ca descărcare, fără previzualizare |
| Încărcarea de fișiere deschide o breșă | un fișier care nu e PDF sau PPTX trece de validare, sau o arhivă bombă blochează serverul | validare după conținut, limită de 20 MB, nume generate de server și secțiunea „Fișiere încărcate” din checklist-ul de securitate |

**Reguli ca să înțelegi tot proiectul**

- Fable implementează în felii mici, iar tu înțelegi fiecare felie: citești pull request-ul, rulezi testele și răspunzi la cele trei întrebări de verificare de la finalul pasului.
- Codul de securitate (sandbox, autentificare, încărcarea de fișiere), Docker și configurările le citești linie cu linie înainte să le păstrezi.
- La finalul fiecărei săptămâni scrii 5-10 rânduri în `docs/decizii.md`: ce ai construit și de ce.
- Duminica, 20 de minute: explici cu voce tare fluxul săptămânii și notezi ce nu e clar.
- Un commit sau pull request pe felie, cu mesaj clar.
- Blocat mai mult de 45 de minute pe aceeași problemă: ceri ajutor, nu mai insiști.
