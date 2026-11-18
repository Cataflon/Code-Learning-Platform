"""Course materials: upload checks, links to assignments and tests, recommendations, Learn.

Uploaded files are untrusted data. The type is decided by the first bytes, never by the
extension or the Content-Type; the size limit is enforced while reading; PPTX archives are
checked for zip bombs before LibreOffice sees them; names on disk come from FileStore.
"""

import contextlib
import re
import shutil
import tempfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import (
    InvalidDataError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
)
from app.models import (
    Assignment,
    AssignmentMaterial,
    Course,
    Enrollment,
    FileType,
    Material,
    MaterialCategory,
    Role,
    Submission,
    SubmissionStatus,
    TestCase,
    TestCaseMaterial,
    User,
    Verdict,
)
from app.schemas.material import (
    FailedTest,
    LearnCourse,
    MaterialLinkIn,
    MaterialLinkRead,
    MaterialRead,
    MaterialUpdate,
    MaterialUsage,
    Recommendation,
    RecommendationsRead,
)
from app.services import submission_service
from app.services.pages import PagesError, first_page, format_pages, merge_ranges, parse_pages
from app.storage.file_store import FileStore
from app.storage.pptx_converter import ConversionError, Converter

CHUNK = 1024 * 1024
MAX_ZIP_ENTRIES = 2000
MAX_UNZIPPED_BYTES = 200 * 1024 * 1024
TITLE_MAX = 120


# --- reading and checking an upload ----------------------------------------------------------


def read_limited(stream: BinaryIO, target: Path, max_bytes: int) -> int:
    """Copy the upload to ``target`` in chunks, stopping as soon as it passes ``max_bytes``.

    The limit applies to what is actually read, not to a Content-Length header a client
    could lie about.
    """
    written = 0
    with target.open("wb") as out:
        while chunk := stream.read(CHUNK):
            written += len(chunk)
            if written > max_bytes:
                raise PayloadTooLargeError(
                    f"The file is larger than {max_bytes // (1024 * 1024)} MB"
                )
            out.write(chunk)
    if written == 0:
        raise InvalidDataError("The file is empty")
    return written


def detect_type(path: Path) -> FileType:
    """PDF starts with %PDF-; a PPTX is a ZIP archive that contains ppt/presentation.xml."""
    with path.open("rb") as handle:
        head = handle.read(5)
    if head == b"%PDF-":
        return FileType.pdf
    if zipfile.is_zipfile(path):
        check_pptx_archive(path)
        return FileType.pptx
    raise UnsupportedMediaTypeError("Only PDF and PPTX files are accepted")


def check_pptx_archive(path: Path) -> None:
    """Refuse archives that are not presentations, and archives built to explode (zip bombs)."""
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ZIP_ENTRIES:
                raise UnsupportedMediaTypeError("The presentation has too many parts")
            if sum(entry.file_size for entry in entries) > MAX_UNZIPPED_BYTES:
                raise UnsupportedMediaTypeError("The presentation is too large once unpacked")
            if "ppt/presentation.xml" not in {entry.filename for entry in entries}:
                raise UnsupportedMediaTypeError("Only PDF and PPTX files are accepted")
    except zipfile.BadZipFile as exc:
        raise UnsupportedMediaTypeError("Only PDF and PPTX files are accepted") from exc


def count_pdf_pages(path: Path) -> int:
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            raise InvalidDataError("The PDF is protected with a password")
        pages = len(reader.pages)
    except InvalidDataError:
        raise
    except Exception as exc:  # pypdf raises many kinds of errors on damaged files
        raise InvalidDataError("The PDF is damaged and could not be read") from exc
    if pages == 0:
        raise InvalidDataError("The PDF has no pages")
    return pages


_UNSAFE = re.compile(r"[\x00-\x1f\x7f/\\:*?\"<>|]+")


def clean_filename(name: str | None, file_type: FileType) -> str:
    """Only the last path component, without control or path characters, right extension.

    Used for display and for the download name; never to build a path on disk.
    """
    base = re.split(r"[/\\]", name or "")[-1]
    stem = _UNSAFE.sub("_", Path(base).stem).strip(" ._") or "material"
    return f"{stem[:200]}.{file_type.value}"


def clean_title(title: str | None, filename: str) -> str:
    title = " ".join((title or "").split())
    if not title:
        title = Path(filename).stem.replace("_", " ").replace("-", " ").strip() or "Material"
    return title[:TITLE_MAX]


# --- upload, rename, delete ------------------------------------------------------------------


def upload_material(
    db: Session,
    course: Course,
    teacher: User,
    stream: BinaryIO,
    filename: str | None,
    title: str | None,
    category: MaterialCategory,
    store: FileStore,
    converter: Converter,
) -> Material:
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    work = Path(tempfile.mkdtemp(prefix="upload-", dir=store.temp_dir()))
    saved: list[str] = []
    try:
        upload = work / "upload.bin"
        size = read_limited(stream, upload, max_bytes)
        file_type = detect_type(upload)
        original = work / f"original.{file_type.value}"
        upload.rename(original)

        if file_type == FileType.pdf:
            preview = None
            page_count = count_pdf_pages(original)
        else:
            try:
                preview = converter(original, work)
            except ConversionError as exc:
                raise InvalidDataError(f"The presentation could not be converted: {exc}") from exc
            page_count = count_pdf_pages(preview)

        stored = store.save_file(original, file_type.value)
        saved.append(stored)
        preview_name = store.save_file(preview, "pdf") if preview else None
        if preview_name:
            saved.append(preview_name)

        material = Material(
            course_id=course.id,
            title=clean_title(title, clean_filename(filename, file_type)),
            category=category,
            file_type=file_type,
            original_filename=clean_filename(filename, file_type),
            stored_filename=stored,
            preview_filename=preview_name,
            size_bytes=size,
            page_count=page_count,
            uploaded_by=teacher.id,
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        return material
    except BaseException:
        # Nothing may stay on disk when the upload is refused or the database fails.
        db.rollback()
        for name in saved:
            store.delete(name)
        raise
    finally:
        shutil.rmtree(work, ignore_errors=True)


def get_material(db: Session, material_id: int) -> Material:
    material = db.get(Material, material_id)
    if material is None:
        raise NotFoundError("Material not found")
    return material


def update_material(db: Session, material: Material, data: MaterialUpdate) -> Material:
    if data.title is not None:
        material.title = data.title
    if data.category is not None:
        material.category = data.category
    db.commit()
    db.refresh(material)
    return material


def delete_material(db: Session, material: Material, store: FileStore) -> None:
    """Rows go first (links follow through ON DELETE CASCADE); files only after the commit,
    so a disk error can never undo a database change that already happened."""
    names = material.stored_names
    db.delete(material)
    db.commit()
    for name in names:
        store.delete(name)


def stored_names_of_course(db: Session, course_id: int) -> list[str]:
    rows = db.execute(
        select(Material.stored_filename, Material.preview_filename).where(
            Material.course_id == course_id
        )
    )
    return [name for row in rows for name in row if name]


def delete_files(store: FileStore, names: list[str]) -> None:
    for name in names:
        with contextlib.suppress(OSError):
            store.delete(name)


# --- listing ---------------------------------------------------------------------------------


def list_materials(db: Session, course: Course, viewer: User) -> list[MaterialRead]:
    """Newest first, each with the assignments that use it (students: published ones only)."""
    materials = list(
        db.scalars(
            select(Material)
            .where(Material.course_id == course.id)
            .order_by(Material.created_at.desc(), Material.id.desc())
        )
    )
    usage = _usage(db, course.id, published_only=viewer.role == Role.student)
    return [
        MaterialRead.model_validate(
            {**_material_fields(material), "used_in": usage.get(material.id, [])}
        )
        for material in materials
    ]


def material_read(db: Session, material: Material, viewer: User) -> MaterialRead:
    usage = _usage(db, material.course_id, published_only=viewer.role == Role.student)
    return MaterialRead.model_validate(
        {**_material_fields(material), "used_in": usage.get(material.id, [])}
    )


def _material_fields(material: Material) -> dict:
    return {
        "id": material.id,
        "course_id": material.course_id,
        "title": material.title,
        "category": material.category,
        "file_type": material.file_type,
        "original_filename": material.original_filename,
        "size_bytes": material.size_bytes,
        "page_count": material.page_count,
        "text_pages": material.text_pages,
        "created_at": material.created_at,
    }


def _usage(db: Session, course_id: int, published_only: bool) -> dict[int, list[MaterialUsage]]:
    whole = select(AssignmentMaterial.material_id, Assignment.id, Assignment.title).join(
        Assignment, Assignment.id == AssignmentMaterial.assignment_id
    )
    per_test = (
        select(TestCaseMaterial.material_id, Assignment.id, Assignment.title)
        .join(TestCase, TestCase.id == TestCaseMaterial.test_case_id)
        .join(Assignment, Assignment.id == TestCase.assignment_id)
    )
    whole = whole.where(Assignment.course_id == course_id)
    per_test = per_test.where(Assignment.course_id == course_id)
    if published_only:
        whole = whole.where(Assignment.is_published.is_(True))
        per_test = per_test.where(Assignment.is_published.is_(True))

    found: dict[int, dict[int, dict]] = defaultdict(dict)
    for material_id, assignment_id, title in db.execute(whole):
        entry = found[material_id].setdefault(
            assignment_id, {"title": title, "whole": False, "tests": 0}
        )
        entry["whole"] = True
    for material_id, assignment_id, title in db.execute(per_test):
        entry = found[material_id].setdefault(
            assignment_id, {"title": title, "whole": False, "tests": 0}
        )
        entry["tests"] += 1
    return {
        material_id: [
            MaterialUsage(
                assignment_id=assignment_id,
                assignment_title=entry["title"],
                for_assignment=entry["whole"],
                test_count=entry["tests"],
            )
            for assignment_id, entry in sorted(by_assignment.items())
        ]
        for material_id, by_assignment in found.items()
    }


def learn_overview(db: Session, student: User) -> list[LearnCourse]:
    """One card per enrolled course, with or without materials."""
    rows = db.execute(
        select(
            Course,
            func.count(Material.id).label("count"),
            func.max(Material.created_at).label("last"),
        )
        .join(Enrollment, Enrollment.course_id == Course.id)
        .outerjoin(Material, Material.course_id == Course.id)
        .where(Enrollment.user_id == student.id)
        .group_by(Course.id)
        .order_by(Course.title)
    )
    return [
        LearnCourse(
            id=course.id,
            title=course.title,
            color=course.color,
            teacher_name=course.teacher_name,
            material_count=count,
            last_material_at=last,
        )
        for course, count, last in rows
    ]


# --- links to assignments and tests ----------------------------------------------------------


def _link_read(material: Material, pages: str) -> MaterialLinkRead:
    return MaterialLinkRead(
        material_id=material.id,
        title=material.title,
        category=material.category,
        file_type=material.file_type,
        page_count=material.page_count,
        pages=pages,
        first_page=first_page(pages),
    )


def _validated_links(
    db: Session, course_id: int, items: list[MaterialLinkIn]
) -> list[tuple[Material, str]]:
    """Every material must be from the course, at most once, with pages that exist."""
    ids = [item.material_id for item in items]
    if len(ids) != len(set(ids)):
        raise InvalidDataError("A material appears more than once")
    materials = {
        material.id: material
        for material in db.scalars(
            select(Material).where(Material.id.in_(ids), Material.course_id == course_id)
        )
    }
    if len(materials) != len(ids):
        raise InvalidDataError("Every material must belong to the same course as the assignment")
    links = []
    for item in items:
        material = materials[item.material_id]
        try:
            pages = format_pages(parse_pages(item.pages, material.page_count))
        except PagesError as exc:
            raise InvalidDataError(f"{material.title}: {exc}") from exc
        links.append((material, pages))
    return links


def assignment_links(db: Session, assignment_id: int) -> list[MaterialLinkRead]:
    links = db.scalars(
        select(AssignmentMaterial).where(AssignmentMaterial.assignment_id == assignment_id)
    )
    return sorted(
        (_link_read(link.material, link.pages) for link in links), key=lambda link: link.title
    )


def test_case_links(db: Session, test_case_ids: list[int]) -> dict[int, list[MaterialLinkRead]]:
    result: dict[int, list[MaterialLinkRead]] = defaultdict(list)
    if not test_case_ids:
        return result
    links = db.scalars(
        select(TestCaseMaterial).where(TestCaseMaterial.test_case_id.in_(test_case_ids))
    )
    for link in links:
        result[link.test_case_id].append(_link_read(link.material, link.pages))
    for value in result.values():
        value.sort(key=lambda link: link.title)
    return result


def set_assignment_materials(
    db: Session, assignment: Assignment, items: list[MaterialLinkIn]
) -> list[MaterialLinkRead]:
    """Replace the whole list in one transaction: no half-saved state is ever visible."""
    links = _validated_links(db, assignment.course_id, items)
    for old in db.scalars(
        select(AssignmentMaterial).where(AssignmentMaterial.assignment_id == assignment.id)
    ):
        db.delete(old)
    db.flush()
    for material, pages in links:
        db.add(
            AssignmentMaterial(assignment_id=assignment.id, material_id=material.id, pages=pages)
        )
    db.commit()
    return assignment_links(db, assignment.id)


def set_test_case_materials(
    db: Session, test_case: TestCase, items: list[MaterialLinkIn]
) -> list[MaterialLinkRead]:
    links = _validated_links(db, test_case.assignment.course_id, items)
    for old in db.scalars(
        select(TestCaseMaterial).where(TestCaseMaterial.test_case_id == test_case.id)
    ):
        db.delete(old)
    db.flush()
    for material, pages in links:
        db.add(TestCaseMaterial(test_case_id=test_case.id, material_id=material.id, pages=pages))
    db.commit()
    return test_case_links(db, [test_case.id])[test_case.id]


# --- recommendations -------------------------------------------------------------------------


@dataclass
class _Pick:
    material: MaterialLinkRead
    whole: bool = False
    ranges: list[tuple[int, int]] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    from_assignment: bool = False


def build_recommendations(
    failed_tests: list[tuple[int, str]],
    test_materials: dict[int, list[MaterialLinkRead]],
    assignment_materials: list[MaterialLinkRead],
) -> list[Recommendation]:
    """Pure rule of the popup.

    For every failed test, take the test's own materials; when it has none, the materials of
    the assignment. Then one entry per material: pages merged (empty = the whole material),
    the failed tests that led to it, and the most needed material first.
    """
    picks: dict[int, _Pick] = {}
    for test_id, test_name in failed_tests:
        own = test_materials.get(test_id, [])
        links = own or assignment_materials
        for link in links:
            pick = picks.setdefault(link.material_id, _Pick(material=link))
            if not own:
                pick.from_assignment = True
            if test_name not in pick.tests:
                pick.tests.append(test_name)
            if link.pages:
                pick.ranges.extend(parse_pages(link.pages, link.page_count))
            else:
                pick.whole = True
    result = []
    for pick in picks.values():
        pages = "" if pick.whole else format_pages(merge_ranges(pick.ranges))
        result.append(
            Recommendation(
                material_id=pick.material.material_id,
                title=pick.material.title,
                category=pick.material.category,
                file_type=pick.material.file_type,
                page_count=pick.material.page_count,
                pages=pages,
                first_page=first_page(pages),
                test_count=len(pick.tests),
                tests=pick.tests,
                from_assignment=pick.from_assignment,
            )
        )
    result.sort(key=lambda r: (-r.test_count, r.title.lower()))
    return result


def recommendations_for(db: Session, submission: Submission) -> RecommendationsRead:
    """Computed on demand, never stored, so it always follows the current links."""
    assignment = submission.assignment
    test_cases = assignment.approved_tests
    labels = submission_service.hidden_labels(test_cases)
    by_id = {test.id: test for test in test_cases}
    failed = []
    if submission.status == SubmissionStatus.done:
        for result in sorted(submission.results, key=lambda r: by_id[r.test_case_id].position):
            if result.verdict != Verdict.passed:
                test = by_id[result.test_case_id]
                failed.append(
                    FailedTest(
                        test_case_id=test.id,
                        name=labels.get(test.id, test.name),
                        is_hidden=test.is_hidden,
                        concepts=[concept.name for concept in test.concepts],
                    )
                )
    materials = build_recommendations(
        [(test.test_case_id, test.name) for test in failed],
        test_case_links(db, [test.test_case_id for test in failed]),
        assignment_links(db, assignment.id),
    )
    return RecommendationsRead(
        submission_id=submission.id,
        assignment_id=assignment.id,
        failed_tests=failed,
        materials=materials,
    )


# --- page text for the AI linker (Step 9) ----------------------------------------------------

MAX_PAGE_TEXT = 20_000


def extract_pages(db: Session, material: Material, store: FileStore) -> int:
    """Store the text of every page of the viewer PDF in material_pages (decision D27).

    Replaces what was there before. A scanned PDF has no text layer: it ends with
    text_pages = 0 and the linker leaves it alone.
    """
    from app.models import MaterialPage

    for old in db.scalars(select(MaterialPage).where(MaterialPage.material_id == material.id)):
        db.delete(old)
    db.flush()
    count = 0
    try:
        reader = PdfReader(str(store.path(material.preview_name)))
        for number, page in enumerate(reader.pages, start=1):
            try:
                raw = page.extract_text() or ""
            except Exception:  # one unreadable page must not stop the others
                raw = ""
            text = " ".join(raw.split())[:MAX_PAGE_TEXT]
            if text:
                db.add(MaterialPage(material_id=material.id, page_no=number, text=text))
                count += 1
    except Exception:
        count = 0
    material.text_pages = count
    db.commit()
    return count


def extract_pages_in_background(material_id: int, session_factory, store: FileStore) -> None:
    """After an upload, outside the request, so uploading answers as fast as before."""
    db = session_factory()
    try:
        material = db.get(Material, material_id)
        if material is not None:
            extract_pages(db, material, store)
    finally:
        db.close()
