# Checklist de securitate (Pasul 10)

Lista din Anexa A a planului, parcursă pe 19.11.2026, cu dovada fiecărui punct: un test automat
(numele lui) sau locul din cod ori din configurare. Testele marcate `docker` rulează cu Docker
pornit și în CI.

## Sandbox

| | Punct | Dovadă |
| --- | --- | --- |
| ✓ | rețea dezactivată în container | `network_disabled=True` în `app/runner/docker_runner.py`; `test_network_is_unreachable`, `test_dns_does_not_resolve` |
| ✓ | memorie și swap limitate la aceeași valoare | `mem_limit = memswap_limit`; `test_huge_allocation_gives_memory_limit`, `test_growing_list_gives_memory_limit` |
| ✓ | limită de CPU | `nano_cpus` din `SANDBOX_CPUS` (implicit 0,5) |
| ✓ | număr maxim de procese | `pids_limit` (64); `test_fork_bomb_is_contained_by_pids_limit` |
| ✓ | rădăcina doar pentru citire, `tmpfs` mic pe `/tmp` | `read_only=True`, `/tmp` 16 MB `noexec`; `test_writing_outside_tmp_fails`, `test_tmp_is_writable_but_small` |
| ✓ | utilizator fără drepturi, `cap_drop=ALL`, `no-new-privileges` | uid 10001; `test_runs_as_unprivileged_user_without_capabilities` |
| ✓ | limită totală de timp, cu `kill()` | `test_infinite_loop_is_killed_within_the_limit_plus_margin`, `test_sleeping_forever_is_killed_too` |
| ✓ | output limitat | `truncate_output`; `test_huge_output_is_truncated` |
| ✓ | container șters în `finally`, etichetă `autograder=1` | `test_no_containers_are_left_behind`, `test_leftover_containers_from_a_killed_server_are_removed` |
| ✓ | niciun mount în afara directorului cu codul, doar citire | un singur volum, `/sandbox` `ro`; `test_the_submitted_code_cannot_be_modified` |
| ✓ | semafor pentru containere simultane | `get_run_slots()` (`MAX_CONCURRENT_RUNS`, implicit 2), folosit de trimiteri și de generarea AI |
| ✓ | `SubprocessRunner` refuzat în afara `ENV=dev` | validatorul din `Settings` și `build_runner` |
| ✓ | serverul și Docker nu sunt expuse public | implicit backend-ul ascultă pe `127.0.0.1`; profilul `demo` publică doar portul 8080 al nginx; baza de date pe 5433 doar pentru dezvoltare locală |
| ✓ | riscul `docker.sock` scris în README | secțiunea „Demo într-o singură comandă” din README și comentariul din `docker-compose.yml` |

## Aplicație

| | Punct | Dovadă |
| --- | --- | --- |
| ✓ | parole Argon2, niciun hash în răspunsuri | `test_same_password_gives_different_hashes`, `test_register_creates_student_and_never_returns_password` |
| ✓ | JWT cu expirare, secretul din mediu | `JWT_SECRET`, `ACCESS_TOKEN_MINUTES`; `test_expired_token_is_rejected`, `test_tampered_token_is_rejected` |
| ✓ | matricea de permisiuni acoperă fiecare rută | `tests/api/test_permissions.py` (inclusiv rutele de admin și scoaterea unui student) |
| ✓ | CORS restrâns la originea frontend-ului | `CORS_ORIGINS` (implicit `http://localhost:5173`); în profilul demo nu e nevoie de CORS (nginx servește totul de pe o origine) |
| ✓ | rate limit pe login, trimiteri, încărcări | `app/core/rate_limit.py`; `test_the_eleventh_sign_in_in_a_minute_gets_429`, `test_submissions_are_limited_per_student` |
| ✓ | testele ascunse nu își dezvăluie conținutul | `test_hidden_test_content_is_missing_from_the_student_response` |
| ✓ | Markdown randat fără HTML brut | `react-markdown` fără `rehype-raw` (`AssignmentPage.jsx`) |
| ✓ | conturi dezactivate și roluri (D30) | `test_a_disabled_account_cannot_sign_in_and_its_token_stops_working`, `test_rules_that_keep_an_admin_in_charge`; adminul nu vede conținutul cursurilor (matricea de permisiuni) |
| ✓ | coduri de invitație folosite o singură dată, fără curse | rând blocat cu `FOR UPDATE`; `test_an_invite_code_lets_one_teacher_register_then_is_used`, `test_expired_and_revoked_codes_do_not_work` |
| ✓ | identificator pe fiecare cerere, pentru urmărire | `X-Request-ID` în răspunsuri și în loguri; `test_every_answer_carries_a_request_id` |

## Fișiere încărcate

| | Punct | Dovadă |
| --- | --- | --- |
| ✓ | tipul după primii octeți | `test_a_text_file_named_pdf_is_refused_415`, `test_a_zip_that_is_not_a_presentation_is_refused` |
| ✓ | 20 MB aplicat la citire | `test_files_over_the_limit_get_413`; în demo, nginx are `client_max_body_size 25m` |
| ✓ | PPTX verificat înainte de conversie | `test_a_pptx_with_too_many_parts_is_refused_before_conversion`, `test_a_zip_bomb_is_refused_before_conversion` |
| ✓ | conversie cu timeout, profil temporar, una singură odată | `app/storage/pptx_converter.py` (`PPTX_CONVERT_TIMEOUT_S`, profil temporar, lacăt); `test_a_failed_conversion_gives_422_and_leaves_nothing_on_disk` |
| ✓ | nume uuid generate de server | `test_path_tricks_in_the_file_name_never_reach_the_disk` |
| ✓ | `uploads/` nu e servit static; descărcările verifică membrii | `test_member_lists_downloads_and_previews`, matricea de permisiuni |
| ✓ | Content-Type corect și `nosniff` | `test_member_lists_downloads_and_previews`; nginx adaugă și el `nosniff` |
| ✓ | ștergerea materialului sau a cursului șterge fișierele | `test_deleting_a_material_removes_links_and_files`, `test_deleting_the_course_removes_every_material_file` |
| ✓ | testele ascunse apar în recomandări doar ca „Hidden test #n” | `test_recommendations_follow_test_links_then_assignment_links` |
| ✓ | titlul materialului afișat ca text | React escapează textul; niciun `dangerouslySetInnerHTML` în `src/` |

## Generare cu AI (Pasul 9)

| | Punct | Dovadă |
| --- | --- | --- |
| ✓ | cheile (`GEMINI_API_KEY`, `NVIDIA_API_KEY`, `ANTHROPIC_API_KEY`) doar în `.env` | `SecretStr`; fixture-ul `no_real_ai_key` le golește în teste; `test_the_api_key_never_appears_in_answers`; `.env` în `.gitignore` |
| ✓ | codul studenților nu ajunge la model; enunțul tăiat la 8 000 de caractere | `app/ai/prompts.py` (`MAX_STATEMENT_CHARS`); singurele texte trimise sunt enunțul, soluția profesorului și paginile materialelor |
| ✓ | soluția de referință rulează doar în sandbox, cu semaforul global | `ai_service.generate_tests` folosește `Runner` și `get_run_slots()` |
| ✓ | ieșirile vin doar din rulare; conceptele și paginile se validează | `test_expected_output_comes_from_the_sandbox_never_from_the_model`, `test_a_range_beyond_the_pages_the_search_found_is_dropped`, `test_a_material_of_another_course_is_never_linked` |
| ✓ | soluția scrisă de AI e verificată | exemplul din enunț și a doua soluție: `test_the_solution_must_pass_the_example_of_the_statement`, `test_tests_where_the_two_solutions_disagree_are_flagged` |
| ✓ | textul materialelor e marcat ca dată | `LINK_SYSTEM` și etichetele `<candidate_pages>`; `test_generated_tests_are_linked_to_the_page_the_model_picks` |
| ✓ | ciornele nu sunt vizibile studenților și nu contează | `test_drafts_do_not_count_until_they_are_approved` |
| ✓ | un job activ pe temă, limită pe oră | `test_rules_for_starting_a_job` (409 și 429) |

## Limite cunoscute

- Limita de cereri ține contoarele în memoria procesului: e corectă pentru un singur proces (cum
  rulează aplicația), dar mai multe procese ar avea nevoie de un depozit comun (de exemplu Redis).
- Profilul `demo` dă backend-ului acces la `docker.sock`, adică drepturi de administrator pe
  gazdă: e făcut pentru un calculator personal, nu pentru un server.
- Pe varianta gratuită a Gemini, enunțurile și soluțiile trimise pot fi folosite de Google.
