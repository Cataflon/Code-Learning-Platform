# Designul 8-bit al platformei Autograder

Specificatia noului design pentru frontend-ul React + Vite + Tailwind. Inlocuieste stilul variantei D (machetele din `docs/machete/`) peste tot unde se suprapun. Comportamentul paginilor ramane cel din plan (masterprompt), se schimba doar aspectul.

Sursa de adevar vizuala, in ordinea importantei:
1. `reference/prototip-autograder-8bit.html` - prototip functional; se deschide in browser (Dashboard, pagina temei, Learn, pagina cursului, lectia). Toate valorile exacte sunt in el.
2. `screenshots/` - capturi desktop (1360 px) si telefon (390 px) pentru fiecare ecran.
3. Acest document - regulile si deciziile.

## 1. Directia

- Tema intunecata (fundal negru), stil pixel art / 8-bit, inspirat de jocurile retro.
- Fundal animat discret: "maree" de caractere ASCII (vezi sectiunea 7).
- Carduri cu chenar pixelat, fara colturi rotunjite, cu umbra neagra decalata.
- Titlurile si butoanele sunt pixelate; informatiile importante (teste, explicatii, cod) raman intr-un font normal, ca sa fie usor de citit.
- Interfata ramane in engleza, ca in machete.

## 2. Culori (tokens)

| Token | Valoare | Folosire |
| --- | --- | --- |
| `--bg` | `#000000` | fundalul paginii |
| `--card` | `#0a0d22` | fundalul cardurilor (peste el se pune 9% din culoarea cardului) |
| `--edge` | `#2b3366` | chenare neutre |
| `--ink` | `#f5f2ff` | text principal |
| `--ink-2` | `#c9c5e6` | text secundar |
| `--ink-3` | `#8d89b3` | text slab (meta, etichete) |
| `--accent` | `#8b7bff` | violet, actiuni principale |
| `--accent-strong` | `#b3a8ff` | linkuri, focus |
| `--ok` | `#5ee08c` | test trecut |
| `--bad` | `#ff6684` | test picat, concepte de repetat |
| `--warn` | `#ffbe4f` | termene, materiale recomandate |
| `--blue` | `#5cc6ff` | trimiteri recente |
| `--pink` | `#ff92d4` | accent decorativ |
| `--idle` | `#262c55` | patratele/segmente goale |

Butonul principal are fundal `#7a64ff`, cel secundar (galben) `#ffbe4f` cu text `#2a1700`.

Fiecare card primeste o culoare (`--tint`) dupa ce contine: violet = lucru curent, verde = scor, rosu = de repetat, albastru = trimiteri, galben = recomandari/materiale, iar fiecare curs are culoarea lui (violet `#b1a6ff`, albastru `#a3cdff`, lila `#efbaff`). Chenarul cardului = 62% tint + negru; fundalul = 9% tint peste `--card`.

In Tailwind: culorile se pun in `tailwind.config.js` la `theme.extend.colors`, cu aceleasi nume.

## 3. Fonturi

Din Google Fonts (sau @fontsource):

| Rol | Font | Unde |
| --- | --- | --- |
| Titluri, butoane, logo, cifre mari | **Press Start 2P** | h1 (22-38 px), h2 de card (12 px), butoane (11 px), statistici (24 px) |
| Text de interfata | **Pixelify Sans** 500 | meniu (17 px), etichete, meta, liste, chips (14 px) |
| Cronometru, numere de pagina, etichete PDF/PPTX | **VT323** | 16-22 px |
| Informatii importante | **Inter** | textul temei, Input/Expected output, numele testelor si conceptul, mesajul de sub testul picat, mesajul de sub editor, textul paginilor din cititor (15 px, line-height 1.6) |
| Cod | **JetBrains Mono** | editorul de cod si fragmentele de cod (14 px, line-height 1.75) |

Regula: tot ce citeste studentul ca sa inteleaga ce are de facut sau de ce a picat (enunt, teste, explicatii, cod) foloseste Inter / JetBrains Mono. Restul foloseste fonturile pixelate.

## 4. Componente

**Chenar pixelat (comun pentru card, buton, chip, avatar, pagini din cititor):** fara `border` si fara `border-radius`; chenarul se deseneaza cu patru umbre de 4 px pe laturi, astfel colturile raman "taiate" ca la pixel art:

```css
box-shadow:
  0 -4px 0 0 var(--b), 0 4px 0 0 var(--b), -4px 0 0 0 var(--b), 4px 0 0 0 var(--b),
  8px 8px 0 0 rgba(0,0,0,.65);   /* umbra decalata */
```

Elementul are `margin: 4px`, ca chenarul sa nu se lipeasca de vecini. Componentele se fac o singura data (`PixelCard`, `PixelButton`, `Chip`, `ProgressBar`, `VerdictSquares`) si se refolosesc.

- **Card:** chenar 4 px in culoarea cardului, umbra 8 px, o dunga de 4 px mai deschisa sus (`rgba(255,255,255,.07)`), separatoare interne punctate de 2 px (`dashed`). Cardurile pe care se poate da click se ridica 4 px la hover (in trepte, fara tranzitie lina) si chenarul ia culoarea plina.
- **Buton:** bloc plat cu relief: dunga deschisa sus (inset 4 px alb 14%), dunga inchisa jos (inset 4 px negru 28%), umbra neagra 8 px. Hover: se ridica 2 px. Click: coboara 3 px si umbra scade (efect de buton apasat).
- **Chip / eticheta:** chenar pixelat de 2 px, fundal 18% din culoare, text Pixelify 14 px.
- **Patratele pentru teste:** patrate fara rotunjire, cu relief (umbra interioara deschisa sus-stanga, inchisa jos-dreapta). Verde = trecut, rosu = picat, gol = `--idle`, violet care clipeste = ruleaza.
- **Bare de progres:** 12 px inaltime, desenate din segmente de 8 px cu pauze de 2 px.
- **Header:** fara chenar in jurul elementelor de meniu. Elementul activ e subliniat cu o linie de 4 px si are o lumina violet discreta care urca de jos ("headlight"). Sublinierea aluneca spre elementul peste care treci cu mouse-ul si revine la cel activ. Logo-ul (4 patratele) se roteste si isi schimba culorile la hover.
- **Stelute pixelate:** cateva stelute care clipesc in cardul principal de pe Dashboard (detaliu decorativ, doar acolo).

## 5. Ecrane

| Ecran | Captura | Ce contine |
| --- | --- | --- |
| Dashboard student | `dashboard-*.png` | card mare cu termenul urmator (titlu, chips, cronometru, patratelele ultimei incercari, doua butoane), 3 statistici, tabelul temelor, "To review", "Recent submissions" |
| Pagina temei | `assignment-*.png` | enunt + Input/Expected output, materiale de studiu, editor de cod, butonul Run tests, lista testelor; pe telefon: file Task / Code / Tests |
| Learn | `learn-*.png` | banda cu recomandarea dupa ultima incercare + carduri de curs cu imagine sus si titlu dedesubt, profesor, procent citit |
| Pagina cursului | `course-*.png` | antet cu imaginea cursului si progres, apoi cate un card pe lectie: numar, tip fisier, titlu, pagini, progres, sageata; lectia recomandata e galbena |
| Lectia (cititor PDF) | `lesson-*.png` | in stanga PDF-ul cu navigare pe pagini (si sagetile tastaturii) si lista paginilor; in dreapta: despre fisier, progresul pe capitole, vizitele anterioare |

Fluxul Learn: Learn (carduri de curs) -> click pe curs -> pagina cursului (lista de lectii) -> click pe lectie -> cititorul PDF. Imaginea de pe cardul cursului: daca profesorul nu incarca una, se genereaza din culoarea cursului (gradient + patratele + o linie de cod), ca in prototip (functia `cover()`).

Ecranele care nu sunt in prototip (Concept report, Courses, profilul, ecranele profesorului, login, erori, stari goale) se construiesc din aceleasi componente, in acelasi stil. Nu se inventeaza alt stil.

## 6. Miscare

- Animatiile sunt scurte si in trepte (`steps()`), ca in jocuri: intrarea paginii 0,16 s, hover 0,05-0,1 s, sublinierea din header 0,16 s, barele de progres 0,4 s.
- Rularea testelor: testele se completeaza pe rand, cate unul la ~0,3 s, cu o bara de progres sub editor.
- Fara glow care urmareste mouse-ul.
- `prefers-reduced-motion: reduce` opreste toate animatiile (fundalul se deseneaza o singura data, static).

## 7. Fundalul animat

- Componenta: `code/GlyphTideBackground.jsx` (recreare proprie a efectului React Bits "Glyph Tide"; detaliile sunt in comentariul din fisier).
- Pus o singura data in layout, `position: fixed`, `z-index: 0`, opacitate 0,34; continutul aplicatiei sta deasupra (`position: relative; z-index: 1`).
- Lent: o urcare si coborare a apei dureaza 60 s; fara interactiune cu mouse-ul.
- Header-ul e semi-transparent cu blur, ca fundalul sa se vada discret prin el.

## 8. Responsive

- Coloana de continut: maxim 1120 px, centrata, margini laterale de minim 16 px.
- Sub 960 px: grilele devin o coloana, meniul pastreaza doar iconitele.
- Sub 640 px: meniul de sus dispare si apare o bara de navigare jos (Dashboard, Courses, Learn, Report); pagina temei are file (Task / Code / Tests); butoanele ocupa toata latimea.
- Nimic nu face scroll orizontal pe pagina; doar codul si lista paginilor din cititor au scroll propriu.

## 9. Accesibilitate

- Focus vizibil: contur de 3 px `--accent-strong` pe orice element interactiv.
- Culoarea nu e singurul semnal: testele au si text ("Passed", "Wrong answer").
- Contrastul textului pe carduri trebuie sa ramana cel din prototip.
