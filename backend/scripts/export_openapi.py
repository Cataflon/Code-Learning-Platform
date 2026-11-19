"""Write docs/api.md from the OpenAPI schema of the app (Step 10).

Usage: ``python -m scripts.export_openapi`` (from backend/). A test checks that the committed
file matches the code, so a route changed without running this fails CI.
"""

from pathlib import Path

from app.main import create_app

OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "api.md"
METHODS = ("get", "post", "put", "patch", "delete")


def _schema_name(schema: dict | None) -> str:
    if not schema:
        return ""
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if schema.get("type") == "array":
        return f"list[{_schema_name(schema.get('items'))}]"
    if "anyOf" in schema:
        return " | ".join(
            _schema_name(option) or option.get("type", "") for option in schema["anyOf"]
        )
    return schema.get("type", "")


def _body(operation: dict) -> str:
    content = operation.get("requestBody", {}).get("content", {})
    for media, spec in content.items():
        name = _schema_name(spec.get("schema"))
        kind = "form" if "form" in media else "JSON"
        return f"{kind} `{name}`" if name else kind
    return "–"


def _answers(operation: dict) -> str:
    parts = []
    for code, spec in sorted(operation.get("responses", {}).items()):
        if code == "422":
            continue  # every route with input can answer 422; listed once in the intro
        schema = spec.get("content", {}).get("application/json", {}).get("schema")
        name = _schema_name(schema)
        parts.append(f"{code} `{name}`" if name else code)
    return ", ".join(parts)


def _params(operation: dict) -> str:
    query = [p["name"] for p in operation.get("parameters", []) if p["in"] == "query"]
    return ", ".join(f"`{name}`" for name in query) or "–"


def render() -> str:
    schema = create_app().openapi()
    by_tag: dict[str, list[str]] = {}
    for path, item in schema["paths"].items():
        for method in METHODS:
            operation = item.get(method)
            if operation is None:
                continue
            tag = (operation.get("tags") or ["other"])[0]
            text = operation.get("description") or operation.get("summary") or ""
            summary = text.split("\n")[0]
            by_tag.setdefault(tag, []).append(
                f"| `{method.upper()} {path}` | {summary} | {_params(operation)} | "
                f"{_body(operation)} | {_answers(operation)} |"
            )

    lines = [
        "# API",
        "",
        "Generated from the OpenAPI schema by `python -m scripts.export_openapi`; do not edit by",
        "hand. The interactive version is at `/docs` while the backend runs.",
        "",
        "- Every route except `/health`, `/api/v1/config`, sign-in and registration needs",
        "  `Authorization: Bearer <token>` (from `POST /api/v1/auth/login`).",
        '- Errors have one shape: `{"detail": "...", "code": "..."}`. Invalid input answers',
        "  422; another course's resources answer 404, a wrong role 403.",
        "- Every answer carries `X-Request-ID`; a 429 also carries `Retry-After`.",
        "",
    ]
    for tag in sorted(by_tag):
        lines += [
            f"## {tag}",
            "",
            "| Route | What it does | Query | Body | Answers |",
            "| --- | --- | --- | --- | --- |",
            *by_tag[tag],
            "",
        ]
    names = sorted(schema.get("components", {}).get("schemas", {}))
    lines += ["## Schemas", "", ", ".join(f"`{name}`" for name in names), ""]
    return "\n".join(lines)


def main() -> None:
    OUTPUT.write_text(render(), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
