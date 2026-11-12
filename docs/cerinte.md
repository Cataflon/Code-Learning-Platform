# Cerințe: platforma de programare cu autograder

Cerințele sunt scrise ca user stories, fiecare cu criterii de acceptare verificabile.
Sursa completă a proiectului este [masterprompt.md](masterprompt.md).

## Student

**US-01 · Cont și autentificare.** Ca student, vreau să îmi creez un cont și să mă autentific, ca să am acces la cursurile mele.
- înregistrarea cere nume, email și parolă de minimum 8 caractere
- un email deja folosit este refuzat (409)
- după un refresh al paginii rămân autentificat

**US-02 · Înscriere la curs.** Ca student, vreau să mă înscriu la un curs cu un cod primit de la profesor.
- un cod valid mă adaugă la curs; unul greșit dă un mesaj clar
- a doua înscriere la același curs este refuzată (409)
- pot părăsi cursul din profil

**US-03 · Vizualizarea temei.** Ca student, vreau să văd enunțul, limitele și testele publice ale unei teme.
- văd doar temele publicate
- testele ascunse nu își arată input-ul și outputul așteptat

**US-04 · Trimiterea codului.** Ca student, vreau să trimit cod Python din browser și să văd verdictul pe fiecare test.
- trimiterea răspunde imediat, iar testele se colorează pe măsură ce rulează
- văd scorul, timpul pe test și conceptul verificat de fiecare test
- la un test picat văd indiciul profesorului, dacă există

**US-05 · Istoricul încercărilor.** Ca student, vreau să văd încercările mele anterioare și câte mai am.
- fiecare încercare apare cu pătrățelele de verdict și scorul
- după numărul maxim de încercări nu mai pot trimite

**US-06 · Dashboard.** Ca student, vreau un panou cu temele, termenele, scorurile și ultimele trimiteri.
- temele sunt ordonate după termen
- văd cel mai bun scor și conceptele de recapitulat

**US-07 · Raportul „unde greșești”.** Ca student, vreau să văd pe concepte ce stăpânesc și ce am de recapitulat.
- raportul folosește cea mai recentă trimitere terminată a fiecărei teme
- fiecare concept are procent și nivel (review, in progress, mastered)

**US-08 · Learn.** Ca student, vreau să găsesc materialele cursurilor mele într-un singur loc.
- văd un card pe curs, cu numărul de materiale
- pot deschide un material în pagină și îl pot descărca

**US-09 · Recomandări după un test picat.** Ca student, vreau să fiu trimis la materialul și pagina potrivită când greșesc un test.
- după o trimitere cu teste picate apare un popup cu materialele asociate
- linkul deschide materialul direct la pagina indicată
- la o trimitere perfectă popup-ul nu apare

## Profesor

**US-10 · Cursuri.** Ca profesor, vreau să creez cursuri și să dau studenților un cod de înscriere.
- contul de profesor cere un cod de invitație
- pot regenera codul de înscriere; cel vechi nu mai funcționează

**US-11 · Teme și teste.** Ca profesor, vreau să creez teme cu teste, greutăți, teste ascunse și etichete de concept.
- o temă nepublicată nu e vizibilă studenților
- fiecare test are input, output așteptat, greutate și concepte

**US-12 · Trimiteri și statistici.** Ca profesor, vreau să văd trimiterile clasei și unde se greșește.
- văd rata de trecere pe test și distribuția scorurilor
- pot filtra și căuta trimiterile și pot vedea codul trimis

**US-13 · Materiale.** Ca profesor, vreau să încarc cursuri și laboratoare ca PDF sau PPTX.
- fișierele care nu sunt PDF sau PPTX reale sunt refuzate, la fel cele peste 20 MB
- PPTX-ul se convertește în PDF pentru previzualizare

**US-14 · Legarea materialelor.** Ca profesor, vreau să leg materialele, cu pagini, de teme și de teste.
- pot indica pagini ca „12-15, 18”; formatul greșit este refuzat
- materialele din alt curs nu pot fi asociate

## Cerințe nefuncționale

**US-15 · Izolarea codului.** Ca administrator al platformei, vreau ca niciun cod trimis de studenți să nu poată afecta serverul.
- codul rulează în container fără rețea, cu limite de timp, memorie și procese
- o buclă infinită sau un consum mare de memorie este oprit, iar containerul este șters
