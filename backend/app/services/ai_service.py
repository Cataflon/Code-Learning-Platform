"""Tests generated with AI and linked automatically to course materials (Step 9).

The main rule (decision D26): the model never writes an expected output. A reference solution
runs in the sandbox on every input, and what it prints becomes ``expected_output``.

* When the teacher pastes the solution, the model only proposes the inputs.
* When the teacher writes only the statement, the model writes the solution and the inputs,
  then, in a separate request, a second independent solution. The first solution must pass
  the examples of the statement; on every input both solutions run, and a test where they
  disagree keeps the second output (``ai_check_output``) so the teacher sees it.

Every generated test starts as a draft (D28) and counts only after the teacher approves it.
"""

import logging
import re
import threading
import unicodedata
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import InvalidJSONError, LLMClient, LLMError, LLMResult
from app.ai.schemas import (
    AuthoredResult,
    CheckSolution,
    GenerationResult,
    LinkChoices,
    StatementExample,
)
from app.core.config import get_settings
from app.core.errors import (
    ConflictError,
    InvalidDataError,
    NotFoundError,
    ServiceUnavailableError,
    TooManyRequestsError,
)
from app.models import (
    Assignment,
    Concept,
    GenerationJob,
    Material,
    ReviewStatus,
    SubmissionStatus,
    TestCase,
    TestCaseMaterial,
    TestSource,
    User,
)
from app.runner.base import Limits, Runner
from app.runner.compare import outputs_match
from app.services.pages import PagesError, format_pages, parse_pages

logger = logging.getLogger(__name__)

ACTIVE = (SubmissionStatus.queued, SubmissionStatus.running)
MAX_CANDIDATES = 12
INTERRUPTED = "The server restarted while the tests were being generated. Start again."


class GenerationError(Exception):
    """A reason to stop the job with a message the teacher can act on."""


# --- availability, starting and reading jobs -------------------------------------------------


def ensure_available() -> None:
    """Without an API key the feature does not exist (decision D29)."""
    if not get_settings().ai_available:
        raise ServiceUnavailableError("AI test generation is not configured on this server")


def start_generation(
    db: Session, assignment: Assignment, teacher: User, count: int, reference_solution: str
) -> GenerationJob:
    ensure_available()
    if not assignment.description.strip():
        raise InvalidDataError("Write the task statement before generating tests")
    by_teacher = bool(reference_solution.strip())
    active = db.scalar(
        select(GenerationJob.id).where(
            GenerationJob.assignment_id == assignment.id, GenerationJob.status.in_(ACTIVE)
        )
    )
    if active is not None:
        raise ConflictError("Tests are already being generated for this assignment")
    limit = get_settings().ai_max_jobs_per_hour
    recent = db.scalar(
        select(func.count())
        .select_from(GenerationJob)
        .where(
            GenerationJob.requested_by == teacher.id,
            GenerationJob.created_at >= datetime.now(UTC) - timedelta(hours=1),
        )
    )
    if recent >= limit:
        raise TooManyRequestsError(
            f"At most {limit} generations per hour; try again later",
            headers={"Retry-After": "600"},
        )
    job = GenerationJob(
        assignment_id=assignment.id,
        requested_by=teacher.id,
        model=get_settings().ai_models[0][:64],
        tests_requested=count,
        reference_code=reference_solution if by_teacher else None,
        reference_by="teacher" if by_teacher else "ai",
        created_at=datetime.now(UTC),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> GenerationJob:
    job = db.get(GenerationJob, job_id)
    if job is None:
        raise NotFoundError("Generation job not found")
    return job


def phase_of(job: GenerationJob) -> str:
    """What the page says while the job runs, derived from what is already filled in."""
    if job.status != SubmissionStatus.running:
        return job.status.value
    if job.tests_proposed is None:
        return "writing"  # waiting for the model to propose test inputs
    if job.tests_kept is None:
        return "sandbox"  # running the reference solution
    return "linking"  # choosing materials


# --- the background job ----------------------------------------------------------------------


def run_generation(
    job_id: int,
    session_factory: Callable[[], Session],
    llm: LLMClient,
    runner: Runner,
    slots: threading.BoundedSemaphore,
) -> None:
    """Runs after the 202 answer, with its own database session (like run_submission)."""
    db = session_factory()
    try:
        job = db.get(GenerationJob, job_id)
        if job is None or job.status != SubmissionStatus.queued:
            return
        job.status = SubmissionStatus.running
        job.started_at = datetime.now(UTC)
        db.commit()
        generate_tests(db, job, llm, runner, slots)
        job.status = SubmissionStatus.done
        job.finished_at = datetime.now(UTC)
        db.commit()
    except Exception as exc:
        # Drafts saved before the failure stay; the job explains what went wrong.
        db.rollback()
        message = str(exc) if isinstance(exc, GenerationError | LLMError) else None
        if message is None:
            logger.exception("Generation job %s crashed", job_id)
            message = "The tests could not be generated."
        job = db.get(GenerationJob, job_id)
        if job is not None:
            job.status = SubmissionStatus.error
            job.error_message = message[:500]
            job.finished_at = datetime.now(UTC)
            db.commit()
    finally:
        db.close()


def recover_interrupted_jobs(db: Session) -> int:
    stuck = list(db.scalars(select(GenerationJob).where(GenerationJob.status.in_(ACTIVE))))
    for job in stuck:
        job.status = SubmissionStatus.error
        job.error_message = INTERRUPTED
        job.finished_at = datetime.now(UTC)
    db.commit()
    return len(stuck)


def _request[T: BaseModel](
    llm: LLMClient, system: str, user: str, schema: dict, model: type[T]
) -> tuple[T, list[LLMResult]]:
    """One request, checked with Pydantic; an invalid answer is asked for once more.

    Touches no database object, so it can run in another thread; the answers are returned
    with the result so the caller can count their tokens on the job.
    """
    answers: list[LLMResult] = []
    for attempt in (1, 2):
        try:
            result = llm.complete_json(system, user, schema)
        except InvalidJSONError:
            if attempt == 2:
                raise GenerationError("The model did not return a valid answer twice") from None
            continue
        answers.append(result)
        try:
            return model.model_validate(result.data), answers
        except ValidationError:
            if attempt == 2:
                raise GenerationError("The model did not return a valid answer twice") from None
    raise AssertionError("unreachable")


def _count(job: GenerationJob, answers: list[LLMResult]) -> None:
    for result in answers:
        job.input_tokens += result.input_tokens
        job.output_tokens += result.output_tokens
        if result.model:
            job.model = result.model[:64]  # a fallback model may have answered


def _ask[T: BaseModel](
    llm: LLMClient, job: GenerationJob, system: str, user: str, schema: dict, model: type[T]
) -> T:
    value, answers = _request(llm, system, user, schema, model)
    _count(job, answers)
    return value


def normalize_name(name: str) -> str:
    """Compare concept names without diacritics, case or extra spaces: "Bucle" == "bucle"."""
    decomposed = unicodedata.normalize("NFKD", name)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(plain.casefold().split())


def _flat(value: str) -> str:
    return " ".join(value.split())


def _clean(run) -> bool:
    return not (run.timed_out or run.memory_exceeded or run.exit_code != 0)


def _verdict_of(run) -> str:
    if run.timed_out:
        return "time limit exceeded"
    if run.memory_exceeded:
        return "memory limit exceeded"
    return "runtime error"


def generate_tests(
    db: Session,
    job: GenerationJob,
    llm: LLMClient,
    runner: Runner,
    slots: threading.BoundedSemaphore,
) -> list[TestCase]:
    assignment = job.assignment
    concepts = list(db.scalars(select(Concept).where(Concept.course_id == assignment.course_id)))
    by_name = {normalize_name(concept.name): concept for concept in concepts}
    concept_names = [concept.name for concept in concepts]
    limits_args = (assignment.time_limit_ms, assignment.memory_limit_mb)

    # 1. The model proposes the inputs; it writes the solution too when the teacher gave none.
    examples: list[StatementExample] = []
    if job.reference_by == "ai":
        # The second solution is written without seeing the first, so both requests are
        # independent and run at the same time (the slower one sets the wait).
        with ThreadPoolExecutor(max_workers=1) as pool:
            check_request = pool.submit(
                _request,
                llm,
                prompts.CHECK_SYSTEM,
                prompts.check_prompt(assignment.description, *limits_args),
                prompts.CHECK_SCHEMA,
                CheckSolution,
            )
            authored = _ask(
                llm,
                job,
                prompts.AUTHOR_SYSTEM,
                prompts.author_prompt(
                    assignment.description, *limits_args, concept_names, job.tests_requested
                ),
                prompts.AUTHOR_SCHEMA,
                AuthoredResult,
            )
            check, check_answers = check_request.result()
        _count(job, check_answers)
        job.reference_code = authored.reference_solution
        tests = authored.tests
        # Only examples really written in the statement count (the model may not invent one).
        statement = _flat(assignment.description)
        examples = [
            example
            for example in authored.examples
            if _flat(example.input) in statement and _flat(example.output) in statement
        ]
        job.check_code = check.solution
    else:
        result = _ask(
            llm,
            job,
            prompts.GENERATION_SYSTEM,
            prompts.generation_prompt(
                assignment.description,
                job.reference_code,
                *limits_args,
                concept_names,
                job.tests_requested,
            ),
            prompts.GENERATION_SCHEMA,
            GenerationResult,
        )
        tests = result.tests
    job.tests_proposed = len(tests)
    db.commit()

    # 2. The sandbox runs the solution on every input; its output is the expected output.
    limits = Limits(time_limit_ms=limits_args[0], memory_limit_mb=limits_args[1])
    solution = job.reference_code
    kept: list[tuple[int, str, str | None]] = []
    with slots:
        for example in examples:
            run = runner.run(solution, example.input, limits)
            if not _clean(run) or not outputs_match(run.stdout, example.output):
                shown = _flat(example.input)[:60]
                raise GenerationError(
                    "The solution written by the AI fails the example in the task statement "
                    f"(input “{shown}”). Make the statement clearer or paste your own solution."
                )
        for index, test in enumerate(tests):
            run = runner.run(solution, test.input, limits)
            if index == 0:
                again = runner.run(solution, test.input, limits)
                if again.stdout != run.stdout:
                    raise GenerationError(
                        "The reference solution is not deterministic: two runs on the same "
                        "input printed different outputs"
                    )
            if not _clean(run):
                continue  # an input the solution cannot handle is not a test
            disagreement = None
            if job.check_code:
                other = runner.run(job.check_code, test.input, limits)
                if not _clean(other):
                    disagreement = f"(the second solution stopped: {_verdict_of(other)})"
                elif not outputs_match(other.stdout, run.stdout):
                    disagreement = other.stdout
            kept.append((index, run.stdout, disagreement))
    job.tests_kept = len(kept)
    if not kept:
        raise GenerationError("The reference solution failed on every generated input")

    # 3. Save the kept tests as drafts, after the existing ones.
    last = db.scalar(
        select(func.max(TestCase.position)).where(TestCase.assignment_id == assignment.id)
    )
    position = -1 if last is None else last
    created = []
    for index, output, disagreement in kept:
        test = tests[index]
        position += 1
        matched = []
        for name in test.concepts:
            concept = by_name.get(normalize_name(name))
            if concept is not None and concept not in matched:
                matched.append(concept)  # unknown names are ignored, never created
        test_case = TestCase(
            assignment_id=assignment.id,
            name=test.name,
            input_data=test.input,
            expected_output=output,
            is_hidden=test.hidden,
            weight=test.weight,
            position=position,
            source=TestSource.ai,
            review_status=ReviewStatus.draft,
            generation_job_id=job.id,
            ai_rationale=test.rationale or None,
            ai_check_output=disagreement,
            concepts=matched,
        )
        db.add(test_case)
        created.append(test_case)
    db.commit()

    # 4. Propose a material and pages for every test, in one request.
    link_materials(db, job, created, llm)
    db.commit()
    return created


# --- linking tests to materials --------------------------------------------------------------

_WORD = re.compile(r"\w{3,}", re.UNICODE)


def search_terms(*texts: str, limit: int = 30) -> list[str]:
    """Distinct words of 3+ letters, in order of appearance (the full-text query)."""
    words: list[str] = []
    for value in texts:
        for word in _WORD.findall((value or "").lower()):
            if word not in words and not word.isdigit():
                words.append(word)
    return words[:limit]


def find_candidates(db: Session, course_id: int, terms: list[str]) -> list[dict]:
    """Best pages of the course for these words (decision D27): ts_rank over tsvector.

    The words are joined with OR, so a page matches when it contains any of them and pages
    that contain more of them rank higher.
    """
    if not terms:
        return []
    query = " | ".join(terms)
    rows = db.execute(
        text(
            """
            SELECT p.material_id, p.page_no, p.text, m.title,
                   ts_rank(p.tsv, to_tsquery('simple', :query)) AS rank
            FROM material_pages p JOIN materials m ON m.id = p.material_id
            WHERE m.course_id = :course_id AND p.tsv @@ to_tsquery('simple', :query)
            ORDER BY rank DESC, p.material_id, p.page_no
            LIMIT :limit
            """
        ),
        {"query": query, "course_id": course_id, "limit": MAX_CANDIDATES},
    )
    return [
        {
            "material_id": row.material_id,
            "page_no": row.page_no,
            "text": row.text,
            "title": row.title,
        }
        for row in rows
        if row.rank > 0
    ]


def _merge_candidates(per_test: list[list[dict]], limit: int) -> list[dict]:
    """The best pages of every test, taken in turns, so each test keeps its top pages."""
    merged: dict[tuple[int, int], dict] = {}
    depth = max((len(pages) for pages in per_test), default=0)
    for rank in range(depth):
        for pages in per_test:
            if rank < len(pages) and len(merged) < limit:
                page = pages[rank]
                merged.setdefault((page["material_id"], page["page_no"]), page)
    return list(merged.values())


def link_materials(
    db: Session, job: GenerationJob, test_cases: list[TestCase], llm: LLMClient
) -> int:
    """Ask once which candidate pages explain each test; keep only proposals that check out."""
    if not test_cases:
        return 0
    assignment = test_cases[0].assignment
    per_test = []
    for test_case in test_cases:
        concepts = [concept.name for concept in test_case.concepts]
        terms = search_terms(
            " ".join(concepts), test_case.ai_rationale or "", test_case.name, assignment.description
        )
        per_test.append(find_candidates(db, assignment.course_id, terms))
    candidates = _merge_candidates(per_test, prompts.MAX_LINK_PAGES)
    if not candidates:
        return 0  # the materials of the assignment apply instead (rule from Step 8)
    described = [
        {
            "name": test_case.name,
            "concepts": [concept.name for concept in test_case.concepts],
            "rationale": test_case.ai_rationale or "",
        }
        for test_case in test_cases
    ]
    choices = _ask(
        llm,
        job,
        prompts.LINK_SYSTEM,
        prompts.link_prompt(described, candidates),
        prompts.LINK_SCHEMA,
        LinkChoices,
    )
    # Pages the search found, plus their neighbours: a proposal may not go beyond them.
    near: dict[int, set[int]] = {}
    for candidate in candidates:
        page = candidate["page_no"]
        near.setdefault(candidate["material_id"], set()).update((page - 1, page, page + 1))
    linked: set[int] = set()
    for choice in choices.links:
        if not 0 <= choice.test < len(test_cases) or choice.test in linked:
            continue
        if choice.material_id is None or choice.material_id not in near:
            continue
        material = db.get(Material, choice.material_id)
        # Only a material of this course that was among the candidates, with pages that exist.
        if material is None or material.course_id != assignment.course_id:
            continue
        try:
            ranges = parse_pages(choice.pages, material.page_count)
        except PagesError:
            continue
        chosen = {page for start, end in ranges for page in range(start, end + 1)}
        if not chosen or not chosen <= near[material.id]:
            continue  # the whole material, or pages the search never found
        pages = format_pages(ranges)
        test_case = test_cases[choice.test]
        if db.get(TestCaseMaterial, (test_case.id, material.id)) is None:
            db.add(
                TestCaseMaterial(test_case_id=test_case.id, material_id=material.id, pages=pages)
            )
        linked.add(choice.test)
    return len(linked)


# --- review ----------------------------------------------------------------------------------


def approve(db: Session, test_case: TestCase) -> TestCase:
    if test_case.expected_output is None:
        raise InvalidDataError("A test without an expected output cannot be approved")
    test_case.review_status = ReviewStatus.approved
    db.commit()
    db.refresh(test_case)
    return test_case


def approve_all(db: Session, assignment: Assignment) -> int:
    drafts = [test for test in assignment.test_cases if test.review_status == ReviewStatus.draft]
    for test in drafts:
        if test.expected_output is None:
            raise InvalidDataError(f"“{test.name}” has no expected output")
        test.review_status = ReviewStatus.approved
    db.commit()
    return len(drafts)
