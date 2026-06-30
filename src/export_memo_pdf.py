"""Convert outputs/executive_memo.md to outputs/executive_memo.pdf using reportlab."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "outputs" / "executive_memo.md"
PDF_PATH = ROOT / "outputs" / "executive_memo.pdf"

BRAND_BLUE = colors.HexColor("#1a3c6e")
BRAND_RED = colors.HexColor("#c0392b")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
MID_GRAY = colors.HexColor("#888888")


def build_styles():
    base = getSampleStyleSheet()

    title = ParagraphStyle(
        "DocTitle",
        parent=base["Title"],
        fontSize=22,
        textColor=BRAND_BLUE,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=base["Normal"],
        fontSize=11,
        textColor=MID_GRAY,
        spaceAfter=16,
        fontName="Helvetica",
    )
    h1 = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontSize=13,
        textColor=BRAND_BLUE,
        spaceBefore=14,
        spaceAfter=4,
        fontName="Helvetica-Bold",
        borderPad=2,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontSize=11,
        textColor=BRAND_RED,
        spaceBefore=10,
        spaceAfter=2,
        fontName="Helvetica-Bold",
    )
    body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=10,
        leading=15,
        spaceAfter=6,
        fontName="Helvetica",
    )
    bullet = ParagraphStyle(
        "Bullet",
        parent=body,
        leftIndent=16,
        spaceAfter=3,
        bulletIndent=4,
    )
    sub_bullet = ParagraphStyle(
        "SubBullet",
        parent=body,
        leftIndent=32,
        spaceAfter=2,
        bulletIndent=20,
        fontSize=9,
    )
    code = ParagraphStyle(
        "Code",
        parent=base["Code"],
        fontSize=9,
        backColor=LIGHT_GRAY,
        leftIndent=12,
        rightIndent=12,
        spaceAfter=6,
        fontName="Courier",
    )
    return dict(title=title, subtitle=subtitle, h1=h1, h2=h2,
                body=body, bullet=bullet, sub_bullet=sub_bullet, code=code)


def md_inline(text: str) -> str:
    """Convert basic markdown inline to ReportLab XML."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # Code ticks
    text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)
    # Strip markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text


def parse_table(lines: list[str], styles: dict) -> Table:
    """Parse a markdown table into a ReportLab Table."""
    rows = []
    for line in lines:
        if re.match(r'^\|[-| :]+\|$', line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        rows.append(cells)

    if not rows:
        return None

    header = rows[0]
    data_rows = rows[1:]

    table_data = []
    header_cells = [Paragraph(f"<b>{md_inline(c)}</b>", styles["body"]) for c in header]
    table_data.append(header_cells)
    for row in data_rows:
        table_data.append([Paragraph(md_inline(c), styles["body"]) for c in row])

    col_count = len(header)
    available = 6.5 * inch
    col_width = available / col_count

    t = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def md_to_flowables(md_text: str, styles: dict) -> list:
    flowables = []
    lines = md_text.splitlines()
    i = 0
    in_table = False
    table_lines = []

    while i < len(lines):
        line = lines[i]

        # Detect table
        if line.startswith('|'):
            table_lines.append(line)
            i += 1
            continue
        elif table_lines:
            t = parse_table(table_lines, styles)
            if t:
                flowables.append(Spacer(1, 6))
                flowables.append(t)
                flowables.append(Spacer(1, 8))
            table_lines = []

        raw = line.rstrip()

        if not raw:
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # H1
        if raw.startswith("# "):
            text = raw[2:].strip()
            flowables.append(Paragraph(md_inline(text), styles["title"]))
            flowables.append(Paragraph("Customer Churn Analysis — Executive Memo", styles["subtitle"]))
            flowables.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=10))
            i += 1
            continue

        # H2
        if raw.startswith("## "):
            text = raw[3:].strip()
            flowables.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#dddddd"), spaceBefore=8))
            flowables.append(Paragraph(md_inline(text), styles["h1"]))
            i += 1
            continue

        # H3
        if raw.startswith("### "):
            text = raw[4:].strip()
            flowables.append(Paragraph(md_inline(text), styles["h2"]))
            i += 1
            continue

        # Sub-bullet (starts with spaces + -)
        if re.match(r'^\s{2,}-\s', raw):
            text = re.sub(r'^\s+-\s*', '', raw)
            flowables.append(Paragraph(f"&#8226; {md_inline(text)}", styles["sub_bullet"]))
            i += 1
            continue

        # Numbered list
        m = re.match(r'^(\d+)\.\s+(.*)', raw)
        if m:
            text = m.group(2)
            flowables.append(Paragraph(f"<b>{m.group(1)}.</b> {md_inline(text)}", styles["bullet"]))
            i += 1
            continue

        # Bullet
        if raw.startswith("- "):
            text = raw[2:]
            flowables.append(Paragraph(f"&#8226; {md_inline(text)}", styles["bullet"]))
            i += 1
            continue

        # Normal paragraph
        flowables.append(Paragraph(md_inline(raw), styles["body"]))
        i += 1

    # flush trailing table
    if table_lines:
        t = parse_table(table_lines, styles)
        if t:
            flowables.append(t)

    return flowables


def main():
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Memo not found: {MD_PATH}")

    print(f"[memo_pdf] reading {MD_PATH}")
    md_text = MD_PATH.read_text(encoding="utf-8")

    styles = build_styles()

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=0.85 * inch,
        title="Customer Churn — Executive Memo",
        author="Data Science Team",
    )

    flowables = md_to_flowables(md_text, styles)
    doc.build(flowables)
    print(f"[memo_pdf] written -> {PDF_PATH}")


if __name__ == "__main__":
    main()
