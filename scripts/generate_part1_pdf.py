#!/usr/bin/env python3
from __future__ import annotations

import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "part-1-banking-poc-lifecycle.md"
TARGET = ROOT / "docs" / "part-1-banking-poc-lifecycle.pdf"

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT = 54
TOP = 742
BOTTOM = 54
LINE_HEIGHT = 14


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def markdown_to_layout_lines(markdown: str) -> list[tuple[str, int, str]]:
    lines: list[tuple[str, int, str]] = []
    in_code = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            in_code = not in_code
            lines.append(("", 10, "normal"))
            continue

        if not line:
            lines.append(("", 10, "normal"))
            continue

        if in_code:
            wrapped = textwrap.wrap(
                line,
                width=86,
                replace_whitespace=False,
                drop_whitespace=False,
            ) or [""]
            for item in wrapped:
                lines.append((item, 9, "code"))
            continue

        if line.startswith("# "):
            lines.append((line[2:], 18, "bold"))
            lines.append(("", 10, "normal"))
            continue

        if line.startswith("## "):
            lines.append((line[3:], 14, "bold"))
            lines.append(("", 10, "normal"))
            continue

        if line.startswith("### "):
            lines.append((line[4:], 12, "bold"))
            continue

        wrapped = textwrap.wrap(line, width=92) or [""]
        for item in wrapped:
            lines.append((item, 10, "normal"))

    return lines


def build_pages(layout_lines: list[tuple[str, int, str]]) -> list[str]:
    pages: list[list[tuple[str, int, str]]] = [[]]
    y = TOP

    for text, size, font in layout_lines:
        if y < BOTTOM:
            pages.append([])
            y = TOP
        pages[-1].append((text, size, font))
        y -= LINE_HEIGHT if size <= 10 else LINE_HEIGHT + 4

    rendered_pages: list[str] = []
    for page_lines in pages:
        commands = ["BT"]
        y = TOP
        for text, size, font in page_lines:
            font_name = {"normal": "F1", "bold": "F2", "code": "F3"}[font]
            safe_text = escape_pdf_text(text)
            commands.append(f"/{font_name} {size} Tf")
            commands.append(f"1 0 0 1 {LEFT} {y} Tm")
            commands.append(f"({safe_text}) Tj")
            y -= LINE_HEIGHT if size <= 10 else LINE_HEIGHT + 4
        commands.append("ET")
        rendered_pages.append("\n".join(commands))

    return rendered_pages


def pdf_object(object_id: int, body: str) -> bytes:
    return f"{object_id} 0 obj\n{body}\nendobj\n".encode("latin-1")


def write_pdf(page_streams: list[str]) -> None:
    objects: list[bytes] = []

    objects.append(pdf_object(1, "<< /Type /Catalog /Pages 2 0 R >>"))

    font_objects = [
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    ]
    objects.extend(pdf_object(index, body) for index, body in enumerate(font_objects, start=3))

    page_ids: list[int] = []
    next_id = 6
    for stream in page_streams:
        stream_bytes = stream.encode("latin-1", errors="replace")
        content_id = next_id
        page_id = next_id + 1
        next_id += 2

        objects.append(
            pdf_object(
                content_id,
                f"<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream",
            )
        )
        objects.append(
            pdf_object(
                page_id,
                (
                    "<< /Type /Page /Parent 2 0 R "
                    f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                    "/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> "
                    f"/Contents {content_id} 0 R >>"
                ),
            )
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    pages_object = pdf_object(2, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>")
    objects.insert(1, pages_object)

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )

    TARGET.write_bytes(output)


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    layout_lines = markdown_to_layout_lines(markdown)
    page_streams = build_pages(layout_lines)
    write_pdf(page_streams)
    print(f"Wrote {TARGET}")


if __name__ == "__main__":
    main()
