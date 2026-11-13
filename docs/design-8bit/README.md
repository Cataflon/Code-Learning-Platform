# Pachet de design 8-bit pentru Autograder

Pachetul contine tot ce trebuie ca sa schimbi designul frontend-ului in tema 8-bit.

## Continut

| Fisier | Ce este |
| --- | --- |
| `DESIGN.md` | specificatia completa: culori, fonturi, componente, ecrane, animatii, responsive |
| `reference/prototip-autograder-8bit.html` | prototipul functional; se deschide direct in browser |
| `screenshots/` | capturi pentru 5 ecrane, pe desktop si pe telefon |
| `code/theme-8bit.css` | toate stilurile prototipului, de folosit ca referinta pentru valori exacte |
| `code/GlyphTideBackground.jsx` | componenta React pentru fundalul animat, gata de folosit |

## Cum il folosesti cu Claude Code

1. Dezarhiveaza folderul `design-8bit/` in repository, la `docs/design-8bit/`.
2. Deschide Claude Code in repository si lipeste mesajul de mai jos.

```text
Vreau sa schimbi designul frontend-ului dupa pachetul din docs/design-8bit/.

Inainte sa scrii cod:
1. Citeste docs/design-8bit/DESIGN.md complet.
2. Deschide docs/design-8bit/reference/prototip-autograder-8bit.html si uita-te la capturile din docs/design-8bit/screenshots/.
3. Uita-te la structura actuala din frontend/ (pagini, componente, tailwind.config.js) si spune-mi pe scurt planul: ce fisiere schimbi, ce componente noi creezi, in ce ordine.

Apoi implementeaza, in pasi mici:
1. Tokens si fonturi: culorile din DESIGN.md in tailwind.config.js, fonturile (Press Start 2P, Pixelify Sans, VT323, Inter, JetBrains Mono).
2. Componente comune: PixelCard, PixelButton, Chip, ProgressBar, VerdictSquares, header-ul cu sublinierea si lumina de jos, bara de navigare pentru telefon.
3. Fundalul: copiaza docs/design-8bit/code/GlyphTideBackground.jsx in frontend/src/components/ si pune-l o singura data in layout.
4. Ecranele, in ordinea: Dashboard, pagina temei, Learn, pagina cursului, cititorul de lectii. Apoi restul ecranelor in acelasi stil.

Reguli:
- Schimbi doar aspectul. Rutele, apelurile catre API si logica raman cum sunt.
- Valorile exacte (culori, marimi, umbre, durate) le iei din prototip si din code/theme-8bit.css, nu le aproximezi.
- Textul temei, testele, explicatiile si codul raman in Inter / JetBrains Mono, nu in fonturile pixelate.
- Respecta prefers-reduced-motion si pastreaza focusul vizibil.
- Dupa fiecare ecran ruleaza aplicatia, compara cu captura lui si corecteaza diferentele.
- Fa commit dupa fiecare pas pe o ramura design/8bit, cu mesaje clare. Nu adauga linii Co-Authored-By, "Generated with" sau alte mentiuni despre un asistent AI in commit-uri sau in pull request si nu schimba user.name / user.email din git. Nu da push; il dau eu.
```

## Observatii

- Fundalul este o recreare a efectului React Bits "Glyph Tide". Componenta originala este in React Bits Pro si cere licenta; daca o ai, comanda de instalare si setarile sunt in comentariul din `GlyphTideBackground.jsx`.
- Prototipul are date de exemplu. In aplicatie datele vin din API.
- Pentru commit-uri fara Claude la colaboratori, pune si `.claude/settings.json` cu `{"attribution":{"commit":"","pr":""}}` in repository.
