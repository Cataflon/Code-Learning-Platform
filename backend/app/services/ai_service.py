"""Tests generated with AI and linked automatically to course materials (Step 9).

The main rule (decision D26): the model writes no code and no expected output. The
teacher gives the reference solution, the model proposes test inputs, the solution runs in
the sandbox on every input, and what it prints becomes ``expected_output``. Every generated
test starts as a draft (D28) and counts only after the teacher approves it.
"""

import logging
import re
import threading
import unicodedata
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.client import InvalidJSONError, LLMClient, LLMError
from app.ai.schemas import GenerationResult, MaterialChoice
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
    if not reference_solution.strip():
        raise InvalidDataError("Paste your reference solution: it computes the expected outputs")
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
        model=get_settings().ai_model,
        tests_requested=count,
        reference_code=reference_solution,
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


def _ask[T: BaseModel](
    llm: LLMClient, job: GenerationJob, system: str, user: str, schema: dict, model: type[T]
) -> T:
    """One request, checked with Pydantic; an invalid answer is asked for once more."""
    for attempt in (1, 2):
        try:
            result = llm.complete_json(system, user, schema)
        except InvalidJSONError:
            if attempt == 2:
                raise GenerationError("The model did not return a valid answer twice") from None
            continue
        job.input_tokens += result.input_tokens
        job.output_tokens += result.output_tokens
        try:
            return model.model_validate(result.data)
        except ValidationError:
            if attempt == 2:
                raise GenerationError("The model did not return a valid answer twice") from None
    raise AssertionError("unreachable")


def normalize_name(name: str) -> str:
    """Compare concept names without diacritics, case or extra spaces: "Bucle" == "bucle"."""
    decomposed = unicodedata.normalize("NFKD", name)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(plain.casefold().split())


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

    # 1. The model proposes test inputs for the teacher's solution (no code, no outputs).
    result = _ask(
        llm,
        job,
        prompts.GENERATION_SYSTEM,
        prompts.generation_prompt(
            assignment.description,
            job.reference_code,
            assignment.time_limit_ms,
            assignment.memory_limit_mb,
            [concept.name for concept in concepts],
            job.tests_requested,
        ),
        prompts.GENERATION_SCHEMA,
        GenerationResult,
    )
    job.tests_proposed = len(result.tests)
    db.commit()

    # 2. The sandbox runs the solution on every input; its output is the expected output.
    limits = Limits(
        time_limit_ms=assignment.time_limit_ms, memory_limit_mb=assignment.memory_limit_mb
    )
    kept: list[tuple[int, str]] = []
    with slots:
        for index, test in enumerate(result.tests):
            run = runner.run(job.reference_code, test.input, limits)
            if index == 0:
                again = runner.run(job.reference_code, test.input, limits)
                if again.stdout != run.stdout:
                    raise GenerationError(
                        "The reference solution is not deterministic: two runs on the same "
                        "input printed different outputs"
                    )
            if run.timed_out or run.memory_exceeded or run.exit_code != 0:
                continue  # an input the solution cannot handle is not a test
            kept.append((index, run.stdout))
    job.tests_kept = len(kept)
    if not kept:
        raise GenerationError("The reference solution failed on every generated input")

    # 3. Save the kept tests as drafts, after the existing ones.
    last = db.scalar(
        select(func.max(TestCase.position)).where(TestCase.assignment_id == assignment.id)
    )
    position = -1 if last is None else last
    created = []
    for index, output in kept:
        test = result.tests[index]
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
            concepts=matched,
        )
        db.add(test_case)
        created.append(test_case)
    db.commit()

    # 4. Propose a material and pages for each test (when the course has indexed text).
    for test_case in created:
        link_materials(db, job, test_case, llm)
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


def link_materials(db: Session, job: GenerationJob, test_case: TestCase, llm: LLMClient) -> bool:
    """Ask the model which candidate page explains the test; keep it only if it checks out."""
    assignment = test_case.assignment
    concepts = [concept.name for concept in test_case.concepts]
    terms = search_terms(
        " ".join(concepts), test_case.ai_rationale or "", test_case.name, assignment.description
    )
    candidates = find_candidates(db, assignment.course_id, terms)
    if not candidates:
        return False  # the assignment's materials apply instead (rule from Step 8)
    choice = _ask(
        llm,
        job,
        prompts.LINK_SYSTEM,
        prompts.link_prompt(test_case.name, concepts, test_case.ai_rationale or "", candidates),
        prompts.LINK_SCHEMA,
        MaterialChoice,
    )
    if choice.material_id is None:
        return False
    material = db.get(Material, choice.material_id)
    # Only a material of this course that was among the candidates, with pages that exist.
    if material is None or material.course_id != assignment.course_id:
        return False
    if choice.material_id not in {candidate["material_id"] for candidate in candidates}:
        return False
    try:
        pages = format_pages(parse_pages(choice.pages, material.page_count))
    except PagesError:
        return False
    if db.get(TestCaseMaterial, (test_case.id, material.id)) is None:
        db.add(TestCaseMaterial(test_case_id=test_case.id, material_id=material.id, pages=pages))
    return True


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
