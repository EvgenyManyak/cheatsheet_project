# -*- coding: utf-8 -*-
"""Оркестратор: собирает тело PDF, рендерит обложку, объединяет в один файл."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Убедимся, что модули из текущего каталога импортируются
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, "/home/z/my-project/skills/pdf/scripts")

from _core import (  # noqa: E402
    AVAILABLE_WIDTH,
    BODY_STYLE,
    BORDER,
    BOTTOM_MARGIN,
    HEADER_FILL,
    H1_STYLE,
    H2_STYLE,
    H3_STYLE,
    LEFT_MARGIN,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    RIGHT_MARGIN,
    SECTION_BG,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TOP_MARGIN,
    TOC_LEVEL0,
    TOC_LEVEL1,
    TocDocTemplate,
    _draw_header_footer,
    add_heading,
    hr,
    p,
    spacer,
)
from _parser import parse_markdown  # noqa: E402
from _content1 import INTRO_CONTENT, DATA_INSPECT_CONTENT  # noqa: E402
from _content2 import TRANSFORM_CONTENT, SAFETY_CONTENT  # noqa: E402
from _content3 import VIZ_CONTENT, SAVE_CONTENT, ENV_CONTENT, CHECKLIST_CONTENT  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm, mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Сборка оглавления
# ─────────────────────────────────────────────────────────────────────────────
def build_toc() -> list:
    flowables: list = []

    # Заголовок "Содержание"
    toc_title_style = ParagraphStyle(
        name="TOCTitle",
        fontName="FreeSerif-Bold",
        fontSize=22,
        leading=28,
        textColor=HEADER_FILL,
        alignment=TA_LEFT,
        spaceAfter=18,
    )
    flowables.append(Paragraph("Содержание", toc_title_style))
    flowables.append(
        HRFlowable(width="100%", thickness=1, color=HEADER_FILL, spaceBefore=2, spaceAfter=18)
    )

    toc = TableOfContents()
    toc.levelStyles = [TOC_LEVEL0, TOC_LEVEL1]
    flowables.append(toc)
    flowables.append(PageBreak())
    return flowables


# ─────────────────────────────────────────────────────────────────────────────
# Сборка тела документа
# ─────────────────────────────────────────────────────────────────────────────
def build_body(output_path: str) -> None:
    doc = TocDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="Python · Excel, CSV, Parquet — учебная шпаргалка",
        author="Z.ai",
        creator="Z.ai",
        subject="Учебная шпаргалка по работе с Excel, CSV и Parquet в Python",
    )

    story: list = []

    # Оглавление
    story.extend(build_toc())

    # Контентные разделы
    for content in (
        INTRO_CONTENT,
        DATA_INSPECT_CONTENT,
        TRANSFORM_CONTENT,
        SAFETY_CONTENT,
        VIZ_CONTENT,
        SAVE_CONTENT,
        ENV_CONTENT,
        CHECKLIST_CONTENT,
    ):
        flowables = parse_markdown(content)
        story.extend(flowables)
        # Небольшой разделитель между разделами
        story.append(spacer(8))

    doc.multiBuild(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)
    print(f"Body PDF создан: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Рендер обложки через html2poster.js
# ─────────────────────────────────────────────────────────────────────────────
def render_cover(html_path: str, pdf_path: str) -> None:
    """Рендер HTML-обложки в PDF через html2poster.js (Playwright)."""
    script = "/home/z/my-project/skills/pdf/scripts/html2poster.js"
    cmd = ["node", script, html_path, "--output", pdf_path, "--width", "794px"]
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        raise RuntimeError("Не удалось сгенерировать обложку")
    print(f"Cover PDF создан: {pdf_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Объединение обложки и тела в один PDF
# ─────────────────────────────────────────────────────────────────────────────
def merge_cover_body(cover_pdf: str, body_pdf: str, output_pdf: str) -> None:
    from pypdf import PdfReader, PdfWriter

    A4_W, A4_H = 595.28, 841.89

    def normalize(page):
        box = page.mediabox
        w, h = float(box.width), float(box.height)
        # Всегда масштабируем к A4 (595.28 x 841.89 pt) — даже маленькие расхождения
        # в доли точки приводят к ошибке "Inconsistent page sizes" в pdf_qa.py.
        if abs(w - A4_W) > 0.1 or abs(h - A4_H) > 0.1:
            page.scale_to(A4_W, A4_H)
        return page

    writer = PdfWriter()
    cover_page = PdfReader(cover_pdf).pages[0]
    writer.add_page(normalize(cover_page))
    for page in PdfReader(body_pdf).pages:
        writer.add_page(normalize(page))
    writer.add_metadata(
        {
            "/Title": "Python · Excel, CSV, Parquet — учебная шпаргалка",
            "/Author": "Z.ai",
            "/Creator": "Z.ai",
            "/Subject": "Учебная шпаргалка по работе с Excel, CSV и Parquet в Python",
        }
    )
    with open(output_pdf, "wb") as f:
        writer.write(f)
    print(f"Final PDF создан: {output_pdf}")


# ─────────────────────────────────────────────────────────────────────────────
# Главная точка входа
# ─────────────────────────────────────────────────────────────────────────────
def main():
    build_dir = SCRIPT_DIR.parent / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    body_pdf = build_dir / "_body.pdf"
    cover_pdf = build_dir / "_cover.pdf"
    final_pdf = SCRIPT_DIR.parent / "Python_Excel_CSV_Parquet_Cheatsheet.pdf"

    # 1. Сборка тела
    build_body(str(body_pdf))

    # 2. Рендер обложки
    cover_html = SCRIPT_DIR / "cover.html"
    render_cover(str(cover_html), str(cover_pdf))

    # 3. Объединение
    merge_cover_body(str(cover_pdf), str(body_pdf), str(final_pdf))

    # 4. Очистка промежуточных файлов (по желанию можно оставить)
    # body_pdf.unlink()
    # cover_pdf.unlink()

    print("\n=== Готово ===")
    print(f"Финальный PDF: {final_pdf}")
    print(f"Размер: {os.path.getsize(final_pdf) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
