"""The popup rule (build_recommendations), on hand-written links."""

from app.models import FileType, MaterialCategory
from app.schemas.material import MaterialLinkRead
from app.services.material_service import build_recommendations


def link(material_id, pages="", title=None, page_count=30):
    return MaterialLinkRead(
        material_id=material_id,
        title=title or f"Material {material_id}",
        category=MaterialCategory.lecture,
        file_type=FileType.pdf,
        page_count=page_count,
        pages=pages,
        first_page=1,
    )


def test_a_failed_test_with_its_own_materials_uses_only_those():
    result = build_recommendations(
        [(1, "Zero")], {1: [link(10, "12-15")]}, assignment_materials=[link(20)]
    )

    assert [(r.material_id, r.pages, r.first_page) for r in result] == [(10, "12-15", 12)]
    assert result[0].from_assignment is False
    assert result[0].tests == ["Zero"]


def test_a_test_without_materials_falls_back_to_the_assignment():
    result = build_recommendations([(1, "Zero")], {}, assignment_materials=[link(20, "3-4")])

    assert [(r.material_id, r.pages) for r in result] == [(20, "3-4")]
    assert result[0].from_assignment is True


def test_duplicates_are_merged_with_their_pages_and_sorted_by_need():
    result = build_recommendations(
        [(1, "A"), (2, "B"), (3, "Hidden test #1")],
        {
            1: [link(10, "12-15"), link(11, "2")],
            2: [link(10, "14-18")],
            3: [link(10, "22")],
        },
        assignment_materials=[],
    )

    first, second = result
    assert (first.material_id, first.pages, first.test_count) == (10, "12-18, 22", 3)
    assert first.tests == ["A", "B", "Hidden test #1"]
    assert (second.material_id, second.test_count) == (11, 1)


def test_whole_material_wins_over_pages():
    result = build_recommendations(
        [(1, "A"), (2, "B")], {1: [link(10, "4")], 2: [link(10, "")]}, assignment_materials=[]
    )

    assert result[0].pages == ""
    assert result[0].first_page == 1


def test_no_failed_tests_give_no_recommendations():
    assert build_recommendations([], {1: [link(10)]}, assignment_materials=[link(20)]) == []


def test_failed_tests_without_any_material_give_nothing():
    assert build_recommendations([(1, "A")], {}, assignment_materials=[]) == []
