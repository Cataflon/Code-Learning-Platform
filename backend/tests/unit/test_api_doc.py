"""docs/api.md is generated from the code; it must not fall behind the routes."""

from scripts.export_openapi import OUTPUT, render


def test_docs_api_md_matches_the_routes():
    assert OUTPUT.read_text(encoding="utf-8") == render(), (
        "docs/api.md is out of date: run `python -m scripts.export_openapi`"
    )
