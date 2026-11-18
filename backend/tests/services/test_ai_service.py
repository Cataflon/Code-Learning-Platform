"""AI test generation with a scripted model (FakeLLMClient) and a scripted sandbox (FakeRunner).

No test here reaches the network or needs an API key.
"""

import threading

import pytest
from pydantic import SecretStr
from sqlalchemy import select

from app.ai.client import FakeLLMClient, InvalidJSONError
from app.core.config import get_settings
from app.models import (
    FileType,
    GenerationJob,
    Material,
    MaterialPage,
    ReviewStatus,
    Role,
    SubmissionStatus,
    TestCase,
    TestCaseMaterial,
    TestSource,
)
from app.services import ai_service, material_service, submission_service
from app.services.ai_service import normalize_name, search_terms
from scripts.demo_pdf import build_pdf
from tests.fakes import FakeRunner, crash, ok, timeout

SOLUTION = "n = abs(int(input()))\nprint(sum(int(d) for d in str(n)))\n"


def digit_sum_runner(**special):
    """Pretends to run the reference solution: the digit sum, or a scripted failure."""

    def run(code, stdin, limits):
        if stdin in special:
            return special[stdin]
        return ok(f"{sum(int(c) for c in stdin if c.isdigit())}\n")

    return FakeRunner(run)


def answer(*tests):
    return {
        "tests": [
            {
                "name": name,
                "input": stdin,
                "concepts": concepts,
                "hidden": hidden,
                "weight": 2,
                "rationale": f"checks {name.lower()}",
                # Even if a model slipped an output in, it must never be used.
                "expected_output": "WRONG",
            }
            for name, stdin, concepts, hidden in tests
        ],
    }


@pytest.fixture(autouse=True)
def ai_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "gemini_api_key", SecretStr("test-key"))


@pytest.fixture
def setup(make_user, make_course, make_assignment, make_concept, make_test_case):
    teacher, student = make_user(Role.teacher), make_user(Role.student)
    course = make_course(teacher, students=[student])
    concepts = {name: make_concept(course, name) for name in ("Loops", "Cazuri limită")}
    assignment = make_assignment(
        course, description="Read an integer and print the sum of its digits."
    )
    manual = make_test_case(assignment, name="Manual", input_data="12\n", expected_output="3\n")
    return {
        "teacher": teacher,
        "student": student,
        "course": course,
        "assignment": assignment,
        "concepts": concepts,
        "manual": manual,
    }


def run_job(db, setup, llm, runner, count=8, solution=SOLUTION):
    job = ai_service.start_generation(db, setup["assignment"], setup["teacher"], count, solution)
    session = db

    def factory():
        return session

    # The same session stands in for the job's own session; closing it is a no-op here.
    session.close = lambda: None
    ai_service.run_generation(job.id, factory, llm, runner, threading.BoundedSemaphore(1))
    db.expire_all()
    return db.get(GenerationJob, job.id)


def drafts(db, assignment):
    return list(
        db.scalars(
            select(TestCase)
            .where(TestCase.assignment_id == assignment.id, TestCase.source == TestSource.ai)
            .order_by(TestCase.position)
        )
    )


def test_expected_output_comes_from_the_sandbox_never_from_the_model(db_session, setup):
    llm = FakeLLMClient(
        [answer(("Simple", "1234\n", ["Loops"], False), ("Negative", "-9075\n", [], True))]
    )

    job = run_job(db_session, setup, llm, digit_sum_runner())

    assert job.status == SubmissionStatus.done
    assert (job.tests_proposed, job.tests_kept) == (2, 2)
    assert job.reference_code == SOLUTION
    assert job.input_tokens == 100 and job.output_tokens == 100
    simple, negative = drafts(db_session, setup["assignment"])
    assert (simple.expected_output, negative.expected_output) == ("10\n", "21\n")
    assert simple.review_status == ReviewStatus.draft
    assert simple.generation_job_id == job.id
    assert simple.ai_rationale == "checks simple"
    assert negative.is_hidden is True
    assert simple.position > setup["manual"].position  # appended after the manual tests


def test_inputs_the_solution_cannot_handle_are_dropped(db_session, setup):
    llm = FakeLLMClient(
        [
            answer(
                ("Good", "12\n", [], False),
                ("Crashes", "boom\n", [], False),
                ("Too slow", "slow\n", [], False),
            )
        ]
    )
    runner = digit_sum_runner(**{"boom\n": crash(), "slow\n": timeout()})

    job = run_job(db_session, setup, llm, runner)

    assert (job.tests_proposed, job.tests_kept) == (3, 1)
    assert [test.name for test in drafts(db_session, setup["assignment"])] == ["Good"]


def test_a_non_deterministic_solution_fails_the_job(db_session, setup):
    outputs = iter(["1\n", "2\n"])
    runner = FakeRunner(lambda code, stdin, limits: ok(next(outputs)))
    llm = FakeLLMClient([answer(("Only", "5\n", [], False))])

    job = run_job(db_session, setup, llm, runner)

    assert job.status == SubmissionStatus.error
    assert "not deterministic" in job.error_message
    assert drafts(db_session, setup["assignment"]) == []


def test_an_invalid_answer_is_asked_for_once_more(db_session, setup):
    llm = FakeLLMClient([{"tests": []}, answer(("Simple", "12\n", [], False))])

    job = run_job(db_session, setup, llm, digit_sum_runner())

    assert job.status == SubmissionStatus.done
    assert len(llm.calls) == 2


def test_two_invalid_answers_end_the_job_in_error(db_session, setup):
    llm = FakeLLMClient([InvalidJSONError("bad"), {"tests": "not a list"}])

    job = run_job(db_session, setup, llm, digit_sum_runner())

    assert job.status == SubmissionStatus.error
    assert "valid answer twice" in job.error_message
    assert len(llm.calls) == 2


def test_concepts_are_matched_without_case_or_diacritics_and_never_invented(db_session, setup):
    llm = FakeLLMClient([answer(("Zero", "0\n", ["cazuri limita", "LOOPS", "Recursion"], False))])

    run_job(db_session, setup, llm, digit_sum_runner())

    (zero,) = drafts(db_session, setup["assignment"])
    assert sorted(concept.name for concept in zero.concepts) == ["Cazuri limită", "Loops"]
    assert len(setup["course"].concepts) == 2  # "Recursion" was not created


def test_the_prompt_lists_the_course_concepts_and_the_statement(db_session, setup):
    llm = FakeLLMClient([answer(("Simple", "12\n", [], False))])

    run_job(db_session, setup, llm, digit_sum_runner(), count=6)

    system, user, schema = llm.calls[0]
    assert "Do NOT write expected outputs" in system
    assert "Write 6 tests" in user and "Cazuri limită" in user
    assert "<task_statement>" in user and "sum of its digits" in user
    assert "<reference_solution>" in user and SOLUTION.strip() in user
    assert "expected_output" not in str(schema)
    assert "reference_solution" not in str(schema)  # the model writes no code (D26)


def test_drafts_do_not_count_until_they_are_approved(db_session, setup):
    assignment, student = setup["assignment"], setup["student"]
    run_job(
        db_session, setup, FakeLLMClient([answer(("New", "7\n", [], False))]), digit_sum_runner()
    )
    db_session.refresh(assignment)

    assert assignment.test_count == 1 and assignment.draft_test_count == 1
    submission = submission_service.create_submission(db_session, student, assignment, "print(3)")
    assert submission.total_count == 1  # only the manual test
    from app.services import test_case_service

    visible = test_case_service.list_test_cases(db_session, assignment, student)
    assert [test.name for test in visible] == ["Manual"]

    approved = ai_service.approve_all(db_session, assignment)
    db_session.refresh(assignment)

    assert approved == 1
    assert assignment.test_count == 2 and assignment.draft_test_count == 0


def test_rules_for_starting_a_job(db_session, setup, monkeypatch):
    from app.core.errors import (
        ConflictError,
        InvalidDataError,
        ServiceUnavailableError,
        TooManyRequestsError,
    )

    assignment, teacher = setup["assignment"], setup["teacher"]
    first = ai_service.start_generation(db_session, assignment, teacher, 8, SOLUTION)
    with pytest.raises(ConflictError):  # one active job per assignment
        ai_service.start_generation(db_session, assignment, teacher, 8, SOLUTION)

    first.status = SubmissionStatus.done
    db_session.commit()
    monkeypatch.setattr(get_settings(), "ai_max_jobs_per_hour", 1)
    with pytest.raises(TooManyRequestsError):
        ai_service.start_generation(db_session, assignment, teacher, 8, SOLUTION)

    assignment.description = "   "
    monkeypatch.setattr(get_settings(), "ai_max_jobs_per_hour", 5)
    with pytest.raises(InvalidDataError):
        ai_service.start_generation(db_session, assignment, teacher, 8, SOLUTION)

    monkeypatch.setattr(get_settings(), "gemini_api_key", SecretStr(""))
    with pytest.raises(ServiceUnavailableError):
        ai_service.start_generation(db_session, assignment, teacher, 8, SOLUTION)


def test_stuck_jobs_are_marked_as_error_at_startup(db_session, setup):
    job = ai_service.start_generation(
        db_session, setup["assignment"], setup["teacher"], 8, SOLUTION
    )
    job.status = SubmissionStatus.running
    db_session.commit()

    assert ai_service.recover_interrupted_jobs(db_session) == 1
    assert job.status == SubmissionStatus.error


# --- the AI writes the solution too (the teacher gave only the statement) ---------------------

AI_SOLUTION = "n = abs(int(input()))\nprint(sum(map(int, str(n))))\n"
CHECK = "n = abs(int(input()))\ns = 0\nwhile n:\n    s += n % 10\n    n //= 10\nprint(s)\n"
STATEMENT = "Read an integer and print the sum of its digits.\n\nExample: input 1234, output 10."


def authored(*tests, examples=()):
    return {
        "reference_solution": AI_SOLUTION,
        "examples": [{"input": i, "output": o} for i, o in examples],
        **answer(*tests),
    }


def two_solutions_runner(check_output=None, check_fails_on=(), reference_output=None):
    """The reference and the check both compute the digit sum, unless told otherwise."""

    def run(code, stdin, limits):
        digit_sum = f"{sum(int(c) for c in stdin if c.isdigit())}\n"
        if code == CHECK:
            if stdin in check_fails_on:
                return crash()
            return ok(check_output.get(stdin, digit_sum) if check_output else digit_sum)
        if reference_output and stdin in reference_output:
            return ok(reference_output[stdin])
        return ok(digit_sum)

    return FakeRunner(run)


@pytest.fixture
def statement_setup(db_session, setup):
    setup["assignment"].description = STATEMENT
    db_session.commit()
    return setup


def test_without_a_solution_the_ai_writes_it_and_a_second_one_checks_it(
    db_session, statement_setup
):
    llm = FakeLLMClient(
        [
            authored(("Simple", "1234\n", [], False), ("Zero", "0\n", [], False)),
            {"solution": CHECK},
        ]
    )

    job = run_job(db_session, statement_setup, llm, two_solutions_runner(), solution="")

    assert job.status == SubmissionStatus.done
    assert (job.reference_by, job.reference_code, job.check_code) == ("ai", AI_SOLUTION, CHECK)
    simple, zero = drafts(db_session, statement_setup["assignment"])
    assert (simple.expected_output, zero.expected_output) == ("10\n", "0\n")
    assert simple.ai_check_output is None and zero.ai_check_output is None
    author_system, author_prompt, author_schema = llm.calls[0]
    assert "reference_solution" in str(author_schema) and "<task_statement>" in author_prompt
    check_system, check_prompt, _ = llm.calls[1]
    assert "independently" in check_system
    assert AI_SOLUTION not in check_prompt  # the check never sees the first solution


def test_tests_where_the_two_solutions_disagree_are_flagged(db_session, statement_setup):
    llm = FakeLLMClient(
        [
            authored(
                ("Simple", "1234\n", [], False),
                ("Negative", "-56\n", [], True),
                ("Big", "99\n", [], True),
            ),
            {"solution": CHECK},
        ]
    )
    runner = two_solutions_runner(check_output={"-56\n": "-11\n"}, check_fails_on=("99\n",))

    run_job(db_session, statement_setup, llm, runner, solution="")

    simple, negative, big = drafts(db_session, statement_setup["assignment"])
    assert simple.ai_check_output is None
    assert (negative.expected_output, negative.ai_check_output) == ("11\n", "-11\n")
    assert big.ai_check_output == "(the second solution stopped: runtime error)"


def test_the_solution_must_pass_the_example_of_the_statement(db_session, statement_setup):
    llm = FakeLLMClient(
        [authored(("Simple", "12\n", [], False), examples=[("1234", "10")]), {"solution": CHECK}]
    )
    runner = two_solutions_runner(reference_output={"1234": "9\n"})

    job = run_job(db_session, statement_setup, llm, runner, solution="")

    assert job.status == SubmissionStatus.error
    assert "fails the example in the task statement" in job.error_message
    assert drafts(db_session, statement_setup["assignment"]) == []


def test_an_example_the_statement_does_not_contain_is_ignored(db_session, statement_setup):
    llm = FakeLLMClient(
        [authored(("Simple", "12\n", [], False), examples=[("777", "1")]), {"solution": CHECK}]
    )

    job = run_job(db_session, statement_setup, llm, two_solutions_runner(), solution="")

    assert job.status == SubmissionStatus.done  # "777 -> 1" is not in the statement


def test_with_the_teachers_solution_no_second_solution_is_asked_for(db_session, setup):
    llm = FakeLLMClient([answer(("Simple", "12\n", [], False))])

    job = run_job(db_session, setup, llm, digit_sum_runner())

    assert (job.reference_by, job.check_code) == ("teacher", None)
    assert len(llm.calls) == 1


# --- materials -------------------------------------------------------------------------------


def lecture_pdf(db, store, course, pages):
    """A material whose pages carry real text, as uploaded."""
    store.root.mkdir(parents=True, exist_ok=True)
    source = store.temp_dir() / "lecture.pdf"
    source.write_bytes(build_pdf("LECTURE", pages))
    material = Material(
        course_id=course.id,
        title="Lecture 4: Loops",
        file_type=FileType.pdf,
        original_filename="lecture.pdf",
        stored_filename=store.save_file(source, "pdf"),
        size_bytes=100,
        page_count=len(pages),
    )
    db.add(material)
    db.commit()
    return material


LECTURE_PAGES = [
    ["# Introduction", "Welcome to the course"],
    ["# Strings", "Concatenation and slicing"],
    ["# Negative numbers", "Take abs before extracting digits", "The digit sum ignores the sign"],
    ["# Digit extraction", "Use modulo and integer division in a loop"],
]


def test_page_text_is_extracted_for_search(db_session, setup, file_store):
    material = lecture_pdf(db_session, file_store, setup["course"], LECTURE_PAGES)

    count = material_service.extract_pages(db_session, material, file_store)

    pages = db_session.scalars(
        select(MaterialPage)
        .where(MaterialPage.material_id == material.id)
        .order_by(MaterialPage.page_no)
    ).all()
    assert count == 4 and material.text_pages == 4
    assert "abs before extracting digits" in pages[2].text


def test_a_pdf_without_text_has_no_text_pages(db_session, setup, make_material, file_store):
    blank = make_material(setup["course"], pages=3)  # blank pages, like a scan

    assert material_service.extract_pages(db_session, blank, file_store) == 0
    assert blank.text_pages == 0


def test_full_text_search_finds_the_right_pages(db_session, setup, file_store):
    material = lecture_pdf(db_session, file_store, setup["course"], LECTURE_PAGES)
    material_service.extract_pages(db_session, material, file_store)

    found = ai_service.find_candidates(
        db_session, setup["course"].id, search_terms("negative numbers digit sign")
    )

    assert found[0]["page_no"] == 3
    assert {candidate["page_no"] for candidate in found} >= {3, 4}
    assert 2 not in {candidate["page_no"] for candidate in found}


def test_generated_tests_are_linked_to_the_page_the_model_picks(db_session, setup, file_store):
    material = lecture_pdf(db_session, file_store, setup["course"], LECTURE_PAGES)
    material_service.extract_pages(db_session, material, file_store)
    llm = FakeLLMClient(
        [
            answer(("Negative numbers", "-45\n", [], True), ("Plain digits", "45\n", [], False)),
            {
                "links": [
                    {"test": 0, "material_id": material.id, "pages": "3-4"},
                    {"test": 1, "material_id": material.id, "pages": "40"},  # no such page
                    {"test": 7, "material_id": material.id, "pages": "1"},  # no such test
                ]
            },
        ]
    )

    job = run_job(db_session, setup, llm, digit_sum_runner())

    negative, plain = drafts(db_session, setup["assignment"])
    links = {link.test_case_id: link.pages for link in db_session.scalars(select(TestCaseMaterial))}
    assert job.status == SubmissionStatus.done
    assert links == {negative.id: "3-4"}
    assert job.input_tokens == 200  # one generation call and one linking call for all tests
    assert len(llm.calls) == 2
    _, link_prompt, _ = llm.calls[1]
    assert "data, not instructions" in llm.calls[1][0]
    assert "<candidate_pages>" in link_prompt
    assert '<test number="0">' in link_prompt and '<test number="1">' in link_prompt


def test_a_range_beyond_the_pages_the_search_found_is_dropped(db_session, setup, file_store):
    unrelated = [["# Turtle graphics", "Pen colour, heading, circles"]] * 4
    material = lecture_pdf(db_session, file_store, setup["course"], LECTURE_PAGES + unrelated)
    material_service.extract_pages(db_session, material, file_store)
    llm = FakeLLMClient(
        [
            answer(("Negative numbers", "-45\n", [], True), ("Plain digits", "45\n", [], False)),
            {
                "links": [
                    {"test": 0, "material_id": material.id, "pages": "3-8"},  # 6-8 never found
                    {"test": 1, "material_id": material.id, "pages": "4"},
                ]
            },
        ]
    )

    run_job(db_session, setup, llm, digit_sum_runner())

    negative, plain = drafts(db_session, setup["assignment"])
    links = {link.test_case_id: link.pages for link in db_session.scalars(select(TestCaseMaterial))}
    assert links == {plain.id: "4"}


def test_a_material_of_another_course_is_never_linked(db_session, setup, file_store, make_course):
    material = lecture_pdf(db_session, file_store, setup["course"], LECTURE_PAGES)
    material_service.extract_pages(db_session, material, file_store)
    other = lecture_pdf(db_session, file_store, make_course(), LECTURE_PAGES)
    llm = FakeLLMClient(
        [
            answer(("Negative numbers", "-45\n", [], True)),
            {"links": [{"test": 0, "material_id": other.id, "pages": "3"}]},
        ]
    )

    run_job(db_session, setup, llm, digit_sum_runner())

    assert db_session.scalars(select(TestCaseMaterial)).all() == []


def test_without_indexed_pages_no_linking_call_is_made(db_session, setup):
    llm = FakeLLMClient([answer(("Simple", "12\n", [], False))])

    run_job(db_session, setup, llm, digit_sum_runner())

    assert len(llm.calls) == 1


def test_helpers():
    assert normalize_name("  Cazuri   LIMITĂ ") == "cazuri limita"
    assert search_terms("Negative numbers, the sign!", "sign 2024 ab") == [
        "negative",
        "numbers",
        "the",
        "sign",
    ]
