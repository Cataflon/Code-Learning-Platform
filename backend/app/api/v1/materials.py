from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse

from app.core.deps import (
    CurrentUser,
    DbSession,
    MemberAssignment,
    MemberCourse,
    MemberMaterial,
    OwnedAssignment,
    OwnedCourse,
    OwnedMaterial,
    OwnedTestCase,
    StudentUser,
    TeacherUser,
    ViewableSubmission,
)
from app.models import MaterialCategory
from app.schemas.material import (
    LearnCourse,
    MaterialLinkIn,
    MaterialLinkRead,
    MaterialRead,
    MaterialUpdate,
    RecommendationsRead,
)
from app.services import material_service
from app.storage.file_store import FileStore, get_file_store
from app.storage.pptx_converter import Converter, get_converter

router = APIRouter(tags=["materials"])

Store = Annotated[FileStore, Depends(get_file_store)]
# Never let a browser guess another type than the one we send.
NOSNIFF = {"X-Content-Type-Options": "nosniff"}
MEDIA_TYPES = {
    "pdf": "application/pdf",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


@router.get("/me/learn", response_model=list[LearnCourse])
def learn(user: StudentUser, db: DbSession):
    """One card per enrolled course, with the number of materials and the latest upload."""
    return material_service.learn_overview(db, user)


@router.get("/courses/{course_id}/materials", response_model=list[MaterialRead])
def list_materials(course: MemberCourse, user: CurrentUser, db: DbSession):
    return material_service.list_materials(db, course, user)


@router.post(
    "/courses/{course_id}/materials",
    response_model=MaterialRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_material(
    course: OwnedCourse,
    user: TeacherUser,
    db: DbSession,
    store: Store,
    converter: Annotated[Converter, Depends(get_converter)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(max_length=200)] = "",
    category: Annotated[MaterialCategory, Form()] = MaterialCategory.lecture,
):
    """A PDF or a PPTX (multipart). A PPTX is converted to PDF before the answer, synchronously."""
    material = material_service.upload_material(
        db, course, user, file.file, file.filename, title, category, store, converter
    )
    return material_service.material_read(db, material, user)


@router.patch("/materials/{material_id}", response_model=MaterialRead)
def update_material(
    data: MaterialUpdate, material: OwnedMaterial, user: CurrentUser, db: DbSession
):
    return material_service.material_read(
        db, material_service.update_material(db, material, data), user
    )


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(material: OwnedMaterial, db: DbSession, store: Store) -> None:
    material_service.delete_material(db, material, store)


@router.get("/materials/{material_id}", response_model=MaterialRead)
def get_material(material: MemberMaterial, user: CurrentUser, db: DbSession):
    return material_service.material_read(db, material, user)


@router.get("/materials/{material_id}/file")
def download_original(material: MemberMaterial, store: Store):
    """The original file, as an attachment, under its cleaned original name."""
    return FileResponse(
        store.path(material.stored_filename),
        media_type=MEDIA_TYPES[material.file_type.value],
        filename=material.original_filename,
        content_disposition_type="attachment",
        headers=NOSNIFF,
    )


@router.get("/materials/{material_id}/preview")
def preview(material: MemberMaterial, store: Store):
    """The PDF shown in the viewer (the original, or the PDF made from a PPTX), inline."""
    return FileResponse(
        store.path(material.preview_name),
        media_type="application/pdf",
        content_disposition_type="inline",
        filename=f"{material.original_filename.rsplit('.', 1)[0]}.pdf",
        headers=NOSNIFF,
    )


@router.get("/assignments/{assignment_id}/materials", response_model=list[MaterialLinkRead])
def assignment_materials(assignment: MemberAssignment, db: DbSession):
    return material_service.assignment_links(db, assignment.id)


@router.put("/assignments/{assignment_id}/materials", response_model=list[MaterialLinkRead])
def set_assignment_materials(
    items: list[MaterialLinkIn], assignment: OwnedAssignment, db: DbSession
):
    """Replace the whole list; materials from another course give 422."""
    return material_service.set_assignment_materials(db, assignment, items)


@router.put("/test-cases/{test_case_id}/materials", response_model=list[MaterialLinkRead])
def set_test_case_materials(items: list[MaterialLinkIn], test_case: OwnedTestCase, db: DbSession):
    return material_service.set_test_case_materials(db, test_case, items)


@router.get("/submissions/{submission_id}/recommendations", response_model=RecommendationsRead)
def recommendations(submission: ViewableSubmission, db: DbSession):
    """What to review for the failed tests of a submission; computed on demand."""
    return material_service.recommendations_for(db, submission)
