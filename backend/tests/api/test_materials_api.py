import pytest

from app.core.config import get_settings
from app.models import Material, Role
from tests.files import pdf_bytes, pptx_bytes, zip_bytes

API = "/api/v1"
P, F = True, False


def files_on_disk(store):
    """Stored files only (the scratch folder .tmp does not count)."""
    if not store.root.exists():
        return []
    return sorted(path.name for path in store.root.iterdir() if path.is_file())


@pytest.fixture
def course_setup(make_user, make_course):
    teacher, student = make_user(Role.teacher), make_user(Role.student)
    course = make_course(teacher, students=[student])
    return teacher, student, course


def upload(client, headers, course_id, content, filename="lecture.pdf", title="Lecture 4", **form):
    return client.post(
        f"{API}/courses/{course_id}/materials",
        files={"file": (filename, content, "application/octet-stream")},
        data={"title": title, **form},
        headers=headers,
    )


# --- upload ----------------------------------------------------------------------------------


def test_teacher_uploads_a_pdf(client, auth, course_setup, file_store):
    teacher, _, course = course_setup

    response = upload(client, auth(teacher), course.id, pdf_bytes(5), category="lab")

    assert response.status_code == 201
    body = response.json()
    assert (body["title"], body["file_type"], body["page_count"]) == ("Lecture 4", "pdf", 5)
    assert body["category"] == "lab"
    assert body["original_filename"] == "lecture.pdf"
    assert "stored_filename" not in body  # the name on disk is never exposed
    (stored,) = files_on_disk(file_store)
    assert stored.endswith(".pdf") and len(stored) == 36  # uuid4 hex + ".pdf"


def test_a_text_file_named_pdf_is_refused_415(client, auth, course_setup, file_store):
    teacher, _, course = course_setup

    response = upload(client, auth(teacher), course.id, b"just some text", filename="fake.pdf")

    assert response.status_code == 415
    assert files_on_disk(file_store) == []


def test_a_zip_that_is_not_a_presentation_is_refused(client, auth, course_setup):
    teacher, _, course = course_setup
    archive = zip_bytes({"word/document.xml": b"<x/>"})

    response = upload(client, auth(teacher), course.id, archive, filename="slides.pptx")

    assert response.status_code == 415


def test_a_pptx_with_too_many_parts_is_refused_before_conversion(
    client, auth, course_setup, fake_converter
):
    teacher, _, course = course_setup
    entries = {"ppt/presentation.xml": b"<p/>"} | {f"ppt/s{i}.xml": b"" for i in range(2001)}

    response = upload(client, auth(teacher), course.id, zip_bytes(entries), filename="x.pptx")

    assert response.status_code == 415
    assert "too many parts" in response.json()["detail"]
    assert fake_converter.calls == 0


def test_a_zip_bomb_is_refused_before_conversion(client, auth, course_setup, fake_converter):
    teacher, _, course = course_setup
    # 210 MB of zeros compress to a few hundred KB.
    bomb = zip_bytes({"ppt/presentation.xml": b"<p/>", "ppt/big.bin": bytes(210 * 1024 * 1024)})

    response = upload(client, auth(teacher), course.id, bomb, filename="bomb.pptx")

    assert response.status_code == 415
    assert "too large once unpacked" in response.json()["detail"]
    assert fake_converter.calls == 0


def test_files_over_the_limit_get_413(client, auth, course_setup, monkeypatch, file_store):
    teacher, _, course = course_setup
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)

    response = upload(client, auth(teacher), course.id, b"%PDF-" + bytes(2 * 1024 * 1024))

    assert response.status_code == 413
    assert files_on_disk(file_store) == []


def test_a_damaged_or_protected_pdf_gives_422(client, auth, course_setup):
    teacher, _, course = course_setup

    response = upload(client, auth(teacher), course.id, b"%PDF-1.7\nthis is not really a pdf")

    assert response.status_code == 422


def test_a_pptx_is_converted_and_both_files_are_kept(
    client, auth, course_setup, file_store, fake_converter
):
    teacher, _, course = course_setup

    response = upload(client, auth(teacher), course.id, pptx_bytes(), filename="lab-03.pptx")

    assert response.status_code == 201
    body = response.json()
    assert (body["file_type"], body["page_count"]) == ("pptx", fake_converter.pages)
    stored = files_on_disk(file_store)
    assert sorted(name.rsplit(".", 1)[1] for name in stored) == ["pdf", "pptx"]


def test_a_failed_conversion_gives_422_and_leaves_nothing_on_disk(
    client, auth, course_setup, file_store, fake_converter, db_session
):
    teacher, _, course = course_setup
    fake_converter.fail = True

    response = upload(client, auth(teacher), course.id, pptx_bytes(), filename="lab.pptx")

    assert response.status_code == 422
    assert "could not be converted" in response.json()["detail"]
    assert files_on_disk(file_store) == []
    assert db_session.query(Material).count() == 0


def test_path_tricks_in_the_file_name_never_reach_the_disk(client, auth, course_setup, file_store):
    teacher, _, course = course_setup

    response = upload(
        client, auth(teacher), course.id, pdf_bytes(), filename="../../etc/passwd.pdf", title=""
    )

    assert response.status_code == 201
    assert response.json()["original_filename"] == "passwd.pdf"
    assert response.json()["title"] == "passwd"  # an empty title comes from the file name
    assert all(".." not in name and "/" not in name for name in files_on_disk(file_store))


def test_students_cannot_upload(client, auth, course_setup):
    _, student, course = course_setup

    response = upload(client, auth(student), course.id, pdf_bytes())

    assert response.status_code == 403


# --- reading and serving ---------------------------------------------------------------------


def test_member_lists_downloads_and_previews(client, auth, course_setup, make_material):
    _, student, course = course_setup
    material = make_material(course, "Lecture 4", pages=6)

    listed = client.get(f"{API}/courses/{course.id}/materials", headers=auth(student))
    original = client.get(f"{API}/materials/{material.id}/file", headers=auth(student))
    preview = client.get(f"{API}/materials/{material.id}/preview", headers=auth(student))

    assert [item["title"] for item in listed.json()] == ["Lecture 4"]
    assert original.status_code == 200
    assert original.headers["x-content-type-options"] == "nosniff"
    assert original.headers["content-disposition"].startswith("attachment")
    assert "lecture-4.pdf" in original.headers["content-disposition"]
    assert original.content.startswith(b"%PDF-")
    assert preview.headers["content-type"] == "application/pdf"
    assert preview.headers["content-disposition"].startswith("inline")
    assert preview.headers["x-content-type-options"] == "nosniff"


def test_rename_and_recategorize(client, auth, course_setup, make_material):
    teacher, _, course = course_setup
    material = make_material(course)

    response = client.patch(
        f"{API}/materials/{material.id}",
        json={"title": "  Lab 3:   Input  ", "category": "lab"},
        headers=auth(teacher),
    )

    assert response.json()["title"] == "Lab 3: Input"
    assert response.json()["category"] == "lab"


def test_deleting_a_material_removes_links_and_files(
    client, auth, course_setup, make_material, make_assignment, file_store
):
    teacher, _, course = course_setup
    material = make_material(course)
    assignment = make_assignment(course)
    client.put(
        f"{API}/assignments/{assignment.id}/materials",
        json=[{"material_id": material.id, "pages": "1-2"}],
        headers=auth(teacher),
    )

    response = client.delete(f"{API}/materials/{material.id}", headers=auth(teacher))

    assert response.status_code == 204
    assert files_on_disk(file_store) == []
    links = client.get(f"{API}/assignments/{assignment.id}/materials", headers=auth(teacher))
    assert links.json() == []


def test_deleting_the_course_removes_every_material_file(
    client, auth, course_setup, make_material, file_store
):
    teacher, _, course = course_setup
    make_material(course, "A")
    make_material(course, "B")
    assert len(files_on_disk(file_store)) == 2

    response = client.delete(f"{API}/courses/{course.id}", headers=auth(teacher))

    assert response.status_code == 204
    assert files_on_disk(file_store) == []


# --- links -----------------------------------------------------------------------------------


def test_assignment_links_are_replaced_and_normalized(
    client, auth, course_setup, make_material, make_assignment
):
    teacher, student, course = course_setup
    lecture, lab = make_material(course, "Lecture 4", pages=28), make_material(course, "Lab 3")
    assignment = make_assignment(course)
    url = f"{API}/assignments/{assignment.id}/materials"

    client.put(url, json=[{"material_id": lab.id}], headers=auth(teacher))
    response = client.put(
        url, json=[{"material_id": lecture.id, "pages": " 18, 12-15 "}], headers=auth(teacher)
    )
    seen = client.get(url, headers=auth(student)).json()

    assert response.status_code == 200
    assert seen == [
        {
            "material_id": lecture.id,
            "title": "Lecture 4",
            "category": "lecture",
            "file_type": "pdf",
            "page_count": 28,
            "pages": "12-15, 18",
            "first_page": 12,
        }
    ]


@pytest.mark.parametrize(
    ("pages", "message"), [("5-3", "backwards"), ("40", "does not exist"), ("x", "not a page")]
)
def test_bad_pages_give_422(
    client, auth, course_setup, make_material, make_assignment, pages, message
):
    teacher, _, course = course_setup
    material = make_material(course, pages=28)
    assignment = make_assignment(course)

    response = client.put(
        f"{API}/assignments/{assignment.id}/materials",
        json=[{"material_id": material.id, "pages": pages}],
        headers=auth(teacher),
    )

    assert response.status_code == 422
    assert message in response.json()["detail"]


def test_material_from_another_course_gives_422(
    client, auth, course_setup, make_material, make_assignment, make_course, make_test_case
):
    teacher, _, course = course_setup
    foreign = make_material(make_course(teacher), "Other course")
    assignment = make_assignment(course)
    test_case = make_test_case(assignment)

    for url in (
        f"{API}/assignments/{assignment.id}/materials",
        f"{API}/test-cases/{test_case.id}/materials",
    ):
        response = client.put(url, json=[{"material_id": foreign.id}], headers=auth(teacher))
        assert response.status_code == 422


def test_teacher_sees_test_links_and_usage(
    client, auth, course_setup, make_material, make_assignment, make_test_case
):
    teacher, student, course = course_setup
    material = make_material(course)
    assignment = make_assignment(course, title="Digit sum")
    draft = make_assignment(course, title="Draft", is_published=False)
    first, second = make_test_case(assignment), make_test_case(assignment)
    draft_test = make_test_case(draft)
    for test_case in (first, second, draft_test):
        client.put(
            f"{API}/test-cases/{test_case.id}/materials",
            json=[{"material_id": material.id, "pages": "2"}],
            headers=auth(teacher),
        )

    tests = client.get(f"{API}/assignments/{assignment.id}/test-cases", headers=auth(teacher))
    as_teacher = client.get(f"{API}/courses/{course.id}/materials", headers=auth(teacher)).json()
    as_student = client.get(f"{API}/courses/{course.id}/materials", headers=auth(student)).json()

    assert tests.json()[0]["materials"][0]["pages"] == "2"
    assert {u["assignment_title"]: u["test_count"] for u in as_teacher[0]["used_in"]} == {
        "Digit sum": 2,
        "Draft": 1,
    }
    assert [u["assignment_title"] for u in as_student[0]["used_in"]] == ["Digit sum"]


# --- recommendations and Learn ---------------------------------------------------------------


@pytest.fixture
def failed_submission(
    course_setup, make_material, make_assignment, make_test_case, make_concept, make_submission
):
    teacher, student, course = course_setup
    lecture = make_material(course, "Lecture 4", pages=28)
    lab = make_material(course, "Lab 3", pages=16)
    assignment = make_assignment(course)
    negative = make_concept(course, "Negative numbers")
    passed = make_test_case(assignment, name="Simple")
    hidden = make_test_case(assignment, name="Secret", is_hidden=True, concepts=[negative])
    zero = make_test_case(assignment, name="Zero")
    submission = make_submission(student, assignment, [P, F, F])
    return {
        "teacher": teacher,
        "student": student,
        "course": course,
        "assignment": assignment,
        "lecture": lecture,
        "lab": lab,
        "tests": (passed, hidden, zero),
        "submission": submission,
    }


def test_recommendations_follow_test_links_then_assignment_links(client, auth, failed_submission):
    s = failed_submission
    teacher = auth(s["teacher"])
    _, hidden, _ = s["tests"]
    client.put(
        f"{API}/test-cases/{hidden.id}/materials",
        json=[{"material_id": s["lecture"].id, "pages": "12-15"}],
        headers=teacher,
    )
    client.put(
        f"{API}/assignments/{s['assignment'].id}/materials",
        json=[{"material_id": s["lab"].id}],
        headers=teacher,
    )

    body = client.get(
        f"{API}/submissions/{s['submission'].id}/recommendations", headers=auth(s["student"])
    ).json()

    assert [t["name"] for t in body["failed_tests"]] == ["Hidden test #1", "Zero"]
    assert body["failed_tests"][0]["concepts"] == ["Negative numbers"]
    # one failed test each, so the tie is broken by title
    lab, lecture = body["materials"]
    assert (lecture["title"], lecture["pages"], lecture["first_page"]) == ("Lecture 4", "12-15", 12)
    assert lecture["tests"] == ["Hidden test #1"] and lecture["from_assignment"] is False
    assert (lab["title"], lab["pages"], lab["from_assignment"]) == ("Lab 3", "", True)
    assert "Secret" not in str(body)


def test_recommendations_are_private_to_the_author_and_the_teacher(
    client, auth, failed_submission, make_user, db_session
):
    from app.models import Enrollment

    s = failed_submission
    classmate = make_user(Role.student)
    db_session.add(Enrollment(user_id=classmate.id, course_id=s["course"].id))
    db_session.commit()
    url = f"{API}/submissions/{s['submission'].id}/recommendations"

    assert client.get(url, headers=auth(classmate)).status_code == 404
    assert client.get(url, headers=auth(s["teacher"])).status_code == 200


def test_a_perfect_submission_has_no_recommendations(
    client, auth, failed_submission, make_submission
):
    s = failed_submission
    perfect = make_submission(s["student"], s["assignment"], [P, P, P])

    body = client.get(
        f"{API}/submissions/{perfect.id}/recommendations", headers=auth(s["student"])
    ).json()

    assert body["failed_tests"] == [] and body["materials"] == []


def test_learn_shows_every_enrolled_course(client, auth, make_user, make_course, make_material):
    student = make_user(Role.student)
    with_files = make_course(students=[student], title="Procedural Programming")
    make_course(students=[student], title="Data Structures")
    make_material(with_files, "A")
    make_material(with_files, "B")

    body = client.get(f"{API}/me/learn", headers=auth(student)).json()

    assert [(c["title"], c["material_count"]) for c in body] == [
        ("Data Structures", 0),
        ("Procedural Programming", 2),
    ]
    assert body[0]["last_material_at"] is None
    assert body[1]["teacher_name"]
