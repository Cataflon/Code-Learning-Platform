"""A tiny PDF writer for demo lecture slides: text pages only, built-in fonts, no dependency.

Each page is a list of lines; a line starting with "$ " is drawn in Courier (code), a line
starting with "# " is a title. Coordinates are in points on a 4:3 landscape page.
"""

WIDTH, HEIGHT = 720, 540


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _page_stream(header: str, lines: list[str], number: int, total: int) -> bytes:
    out = [
        "BT",
        "/F1 11 Tf",
        "0.45 0.45 0.6 rg",
        f"60 {HEIGHT - 50} Td",
        f"({_escape(header)}) Tj",
        "ET",
    ]
    y = HEIGHT - 110
    for line in lines:
        if line.startswith("# "):
            out += [
                "BT",
                "/F2 24 Tf",
                "0.12 0.11 0.3 rg",
                f"60 {y} Td",
                f"({_escape(line[2:])}) Tj",
                "ET",
            ]
            y -= 46
        elif line.startswith("$ "):
            out += [
                "BT",
                "/F3 14 Tf",
                "0.1 0.1 0.25 rg",
                f"80 {y} Td",
                f"({_escape(line[2:])}) Tj",
                "ET",
            ]
            y -= 22
        else:
            out += [
                "BT",
                "/F1 16 Tf",
                "0.15 0.15 0.25 rg",
                f"60 {y} Td",
                f"({_escape(line)}) Tj",
                "ET",
            ]
            y -= 28
    out += [
        "BT",
        "/F1 10 Tf",
        "0.5 0.5 0.6 rg",
        f"{WIDTH - 90} 30 Td",
        f"({number} / {total}) Tj",
        "ET",
    ]
    return "\n".join(out).encode("latin-1", errors="replace")


def build_pdf(header: str, pages: list[list[str]]) -> bytes:
    """Return the bytes of a PDF with one page per entry of ``pages``."""
    objects: list[bytes] = []

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    catalog = add(b"")  # filled in at the end
    pages_ref = add(b"")
    fonts = [
        add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
        add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"),
        add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"),
    ]
    resources = (
        f"<< /Font << /F1 {fonts[0]} 0 R /F2 {fonts[1]} 0 R /F3 {fonts[2]} 0 R >> >>".encode()
    )
    kids = []
    for number, lines in enumerate(pages, start=1):
        stream = _page_stream(header, lines, number, len(pages))
        content = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        kids.append(
            add(
                b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] /Contents %d 0 R /Resources "
                % (pages_ref, WIDTH, HEIGHT, content)
                + resources
                + b" >>"
            )
        )
    objects[catalog - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages_ref
    objects[pages_ref - 1] = (
        b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % kid for kid in kids) + b"] /Count %d >>"
    ) % len(kids)

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % index + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        catalog,
        xref,
    )
    return bytes(out)
