# ADR 0001 · Cum ajunge codul studentului în container

Stare: acceptat (12.11.2026) · Decizia D9

## Context

`DockerRunner` trebuie să pună în container două fișiere, `main.py` și `input.txt`, fără să slăbească
izolarea: sistemul de fișiere rădăcină rămâne doar pentru citire, iar utilizatorul din container nu
are drepturi. Erau două variante:

1. un director temporar de pe gazdă, montat doar pentru citire (bind mount) în `/sandbox`;
2. `put_archive`: containerul se creează, fișierele se copiază în el ca arhivă tar, apoi pornește.

## Spike

Măsurat pe Windows 11 cu Docker Desktop 29.6 (motor Linux prin WSL2), imaginea `autograder-python`,
un program care citește un număr și îl afișează dublat, câte trei rulări:

| Variantă | Rezultat | Timp total pe rulare |
| --- | --- | --- |
| bind mount doar pentru citire, rootfs `read_only` | funcționează | 390–690 ms |
| `put_archive`, rootfs `read_only` | **eșuează**: Docker refuză copierea într-un container cu rădăcina doar pentru citire (400) | n/a |
| `put_archive`, rootfs cu scriere | funcționează | 450–740 ms |

## Decizie

Folosim **directorul temporar montat doar pentru citire**.

- E singura variantă care păstrează `read_only=True`; `put_archive` ar cere un rootfs cu scriere,
  adică exact protecția la care nu vrem să renunțăm.
- Codul și input-ul nu pot fi modificate din container (testul `test_the_submitted_code_cannot_be_modified`).
- Timpul e la fel de bun ca al variantei cu arhivă.

## Consecințe

- Directorul temporar e creat cu `tempfile.TemporaryDirectory` și șters automat după rulare. Pe
  Linux, fișierele primesc drepturi de citire pentru toți (`0644`), pentru că utilizatorul din
  container (uid 10001) nu e utilizatorul gazdei.
- Bind mount-ul folosește o cale de pe gazdă, deci **nu funcționează dacă backend-ul rulează el însuși
  într-un container** fără ca aceeași cale să existe și pe gazdă (D10). De aceea, implicit, backend-ul
  rulează pe gazdă, iar în Docker stau doar baza de date și sandbox-ul.
- Pornirea containerului costă câteva sute de milisecunde pe test. Timpul raportat studentului e
  durata reală a containerului (`StartedAt`–`FinishedAt`), iar limita de așteptare e limita temei
  plus o marjă fixă de pornire (`SANDBOX_STARTUP_MARGIN_MS`, implicit 2000 ms).
- Optimizare posibilă, în afara MVP-ului: un singur container pe trimitere.
