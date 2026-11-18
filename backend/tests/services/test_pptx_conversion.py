"""The real LibreOffice conversion. Slow, and only where LibreOffice is installed."""

import pytest

from app.services.material_service import count_pdf_pages
from app.storage.pptx_converter import convert_pptx_to_pdf, find_soffice
from tests.files import pptx_bytes

pytestmark = pytest.mark.libreoffice


@pytest.fixture(autouse=True)
def needs_libreoffice():
    if find_soffice() is None:
        pytest.skip("LibreOffice (soffice) is not installed")


def test_a_small_presentation_becomes_a_pdf_with_one_page_per_slide(tmp_path):
    source = tmp_path / "lab.pptx"
    source.write_bytes(pptx_bytes(slides=3))

    result = convert_pptx_to_pdf(source, tmp_path)

    assert result.suffix == ".pdf"
    assert count_pdf_pages(result) == 3
