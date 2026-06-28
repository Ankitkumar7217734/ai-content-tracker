"""Markdown to PDF conversion."""

from fpdf import FPDF


def markdown_to_pdf_bytes(markdown: str, title: str = "Report") -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, _strip_markdown(markdown))
    return bytes(pdf.output())


def _strip_markdown(text: str) -> str:
    """Lightweight markdown stripping for fpdf2 plain-text output."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            line = line.lstrip("#").strip()
        line = line.replace("**", "").replace("*", "").replace("`", "")
        lines.append(line)
    return "\n".join(lines) or title
