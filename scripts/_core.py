# -*- coding: utf-8 -*-
"""
Сборка PDF-шпаргалки "Python: работа с Excel, CSV и Parquet".

Скрипт генерирует тело документа через ReportLab, обложку через
HTML/Playwright, а затем объединяет их в один PDF через pypdf.

Использование:
    python3 build_pdf.py

Результат:
    ../../Python_Excel_CSV_Parquet_Cheatsheet.pdf
"""
from __future__ import annotations

import hashlib
import os
import platform
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

# ─────────────────────────────────────────────────────────────────────────────
# Подключение утилиты install_font_fallback из PDF-skill
# ─────────────────────────────────────────────────────────────────────────────
SKILL_SCRIPTS = "/home/z/my-project/skills/pdf/scripts"
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

from pdf import install_font_fallback  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Пути к шрифтам
# ─────────────────────────────────────────────────────────────────────────────
_IS_MAC = platform.system() == "Darwin"
FONT_DIR = os.path.expanduser("~/.openclaw/workspace/fonts") if _IS_MAC else "/usr/share/fonts"

# ─────────────────────────────────────────────────────────────────────────────
# Регистрация шрифтов
# ─────────────────────────────────────────────────────────────────────────────
import os as _os


def _register_font(name: str, path: str) -> bool:
    """Безопасная регистрация шрифта: если файла нет — пропускаем."""
    if _os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[font] Не удалось зарегистрировать {name}: {exc}", file=sys.stderr)
            return False
    else:
        print(f"[font] Файл не найден: {path}", file=sys.stderr)
        return False


# Китайские шрифты (нужны для fallback в редких случаях)
_register_font("NotoSerifSC", f"{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf")
_register_font("NotoSerifSC-Bold", f"{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf")

# Noto Sans SC может быть в виде variable font с [wght] в имени — пробуем оба варианта
_nsc_path = f"{FONT_DIR}/truetype/chinese/NotoSansSC-Regular.ttf"
if not _os.path.exists(_nsc_path):
    _nsc_var = f"{FONT_DIR}/truetype/chinese/NotoSansSC[wght].ttf"
    if _os.path.exists(_nsc_var):
        _nsc_path = _nsc_var
_register_font("Noto Sans SC", _nsc_path)
_register_font("Noto Sans SC Bold", f"{FONT_DIR}/truetype/chinese/NotoSansSC-Bold.ttf")

_register_font("SarasaMonoSC", f"{FONT_DIR}/truetype/chinese/SarasaMonoSC-Regular.ttf")

# Английский шрифт с поддержкой кириллицы — основной для русского текста
_register_font("FreeSerif", f"{FONT_DIR}/truetype/freefont/FreeSerif.ttf")
_register_font("FreeSerif-Bold", f"{FONT_DIR}/truetype/freefont/FreeSerifBold.ttf")
_register_font("FreeSerif-Italic", f"{FONT_DIR}/truetype/freefont/FreeSerifItalic.ttf")
_register_font("FreeSerif-BoldItalic", f"{FONT_DIR}/truetype/freefont/FreeSerifBoldItalic.ttf")

# Моноширинный шрифт для блоков кода
_register_font("DejaVuSans", f"{FONT_DIR}/truetype/dejavu/DejaVuSansMono.ttf")
_register_font("DejaVuSans-Bold", f"{FONT_DIR}/truetype/dejavu/DejaVuSansMono-Bold.ttf")

# Регистрация семейств шрифтов
try:
    registerFontFamily("NotoSerifSC", normal="NotoSerifSC", bold="NotoSerifSC-Bold")
except Exception:
    pass
try:
    registerFontFamily("Noto Sans SC", normal="Noto Sans SC", bold="Noto Sans SC Bold")
except Exception:
    pass
registerFontFamily(
    "FreeSerif",
    normal="FreeSerif",
    bold="FreeSerif-Bold",
    italic="FreeSerif-Italic",
    boldItalic="FreeSerif-BoldItalic",
)
registerFontFamily("DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold")

# Включаем автоматический fallback для глифов, отсутствующих в FreeSerif.
# Это критично для корректного отображения кириллицы и смешанных шрифтов.
install_font_fallback()

# ─────────────────────────────────────────────────────────────────────────────
# Палитра (согласованная техническая гамма)
# ─────────────────────────────────────────────────────────────────────────────
PAGE_BG = colors.HexColor("#FFFFFF")
SECTION_BG = colors.HexColor("#F5F7FA")
CARD_BG = colors.HexColor("#F4F6F8")
CODE_BG = colors.HexColor("#F4F6F8")
CODE_BORDER = colors.HexColor("#D0D7DE")
TABLE_STRIPE = colors.HexColor("#EEF2F7")

HEADER_FILL = colors.HexColor("#1F3A5F")        # тёмно-синий, по выбору пользователя
COVER_BLOCK = colors.HexColor("#1F3A5F")

BORDER = colors.HexColor("#B0BEC5")
ICON = colors.HexColor("#1F3A5F")

ACCENT = colors.HexColor("#2F5A8F")
ACCENT_2 = colors.HexColor("#B25435")

TEXT_PRIMARY = colors.HexColor("#1A1A1A")
TEXT_MUTED = colors.HexColor("#5C6470")

# Семантические цвета для блоков "Совет"/"Внимание"/"Важно"
TIP_BG = colors.HexColor("#EAF5EC")
TIP_BORDER = colors.HexColor("#1A7F37")
TIP_TEXT = colors.HexColor("#0F5132")

WARN_BG = colors.HexColor("#FFF4E5")
WARN_BORDER = colors.HexColor("#B85C00")
WARN_TEXT = colors.HexColor("#7A3D00")

NOTE_BG = colors.HexColor("#EAF2FA")
NOTE_BORDER = colors.HexColor("#1F3A5F")
NOTE_TEXT = colors.HexColor("#1F3A5F")

# ─────────────────────────────────────────────────────────────────────────────
# Стили абзацев
# ─────────────────────────────────────────────────────────────────────────────
BASE = getSampleStyleSheet()

H1_STYLE = ParagraphStyle(
    name="H1",
    fontName="FreeSerif-Bold",
    fontSize=20,
    leading=26,
    textColor=HEADER_FILL,
    spaceBefore=18,
    spaceAfter=12,
    alignment=TA_LEFT,
)

H2_STYLE = ParagraphStyle(
    name="H2",
    fontName="FreeSerif-Bold",
    fontSize=15,
    leading=20,
    textColor=HEADER_FILL,
    spaceBefore=14,
    spaceAfter=8,
    alignment=TA_LEFT,
)

H3_STYLE = ParagraphStyle(
    name="H3",
    fontName="FreeSerif-Bold",
    fontSize=12.5,
    leading=17,
    textColor=ACCENT,
    spaceBefore=10,
    spaceAfter=6,
    alignment=TA_LEFT,
)

BODY_STYLE = ParagraphStyle(
    name="Body",
    fontName="FreeSerif",
    fontSize=10.5,
    leading=15.5,
    textColor=TEXT_PRIMARY,
    alignment=TA_JUSTIFY,
    spaceAfter=6,
    firstLineIndent=0,
)

BODY_NOINDENT = ParagraphStyle(
    name="BodyNoIndent",
    parent=BODY_STYLE,
    firstLineIndent=0,
    spaceAfter=4,
)

BULLET_STYLE = ParagraphStyle(
    name="Bullet",
    fontName="FreeSerif",
    fontSize=10.5,
    leading=15,
    textColor=TEXT_PRIMARY,
    leftIndent=18,
    bulletIndent=4,
    spaceAfter=3,
    alignment=TA_LEFT,
)

CAPTION_STYLE = ParagraphStyle(
    name="Caption",
    fontName="FreeSerif-Italic",
    fontSize=9,
    leading=12,
    textColor=TEXT_MUTED,
    alignment=TA_CENTER,
    spaceBefore=3,
    spaceAfter=8,
)

CODE_STYLE = ParagraphStyle(
    name="Code",
    fontName="DejaVuSans",
    fontSize=8.5,
    leading=11.5,
    textColor=TEXT_PRIMARY,
    leftIndent=0,
    rightIndent=0,
    alignment=TA_LEFT,
)

CODE_LABEL_STYLE = ParagraphStyle(
    name="CodeLabel",
    fontName="FreeSerif-Bold",
    fontSize=8.5,
    leading=11,
    textColor=TEXT_MUTED,
    alignment=TA_LEFT,
    spaceAfter=2,
)

CALLOUT_BODY = ParagraphStyle(
    name="CalloutBody",
    fontName="FreeSerif",
    fontSize=10,
    leading=14,
    textColor=TEXT_PRIMARY,
    alignment=TA_LEFT,
    leftIndent=0,
    rightIndent=0,
)

CALLOUT_TITLE = ParagraphStyle(
    name="CalloutTitle",
    fontName="FreeSerif-Bold",
    fontSize=10,
    leading=13,
    textColor=TEXT_PRIMARY,
    alignment=TA_LEFT,
    spaceAfter=2,
)

TOC_LEVEL0 = ParagraphStyle(
    name="TOCLevel0",
    fontName="FreeSerif-Bold",
    fontSize=12,
    leading=17,
    textColor=TEXT_PRIMARY,
    leftIndent=0,
    spaceBefore=6,
    spaceAfter=2,
)

TOC_LEVEL1 = ParagraphStyle(
    name="TOCLevel1",
    fontName="FreeSerif",
    fontSize=11,
    leading=15,
    textColor=TEXT_PRIMARY,
    leftIndent=20,
    spaceBefore=0,
    spaceAfter=0,
)


# ─────────────────────────────────────────────────────────────────────────────
# Утилиты для сборки контента
# ─────────────────────────────────────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 2.0 * cm
RIGHT_MARGIN = 2.0 * cm
TOP_MARGIN = 2.0 * cm
BOTTOM_MARGIN = 2.0 * cm
AVAILABLE_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


# Максимальная высота блока KeepTogether — 60% от высоты страницы.
# Большие блоки ReportLab не сможет перенести целиком и оставит пустоту.
MAX_KEEP_HEIGHT = A4[1] * 0.60  # ~505pt ≈ 17.8 см


def safe_keep_together(elements):
    """Объединяет flowables в KeepTogether только если их общая высота разумна.

    Если блок превышает MAX_KEEP_HEIGHT — сохраняем связку «заголовок + первый
    элемент», чтобы избежать отрыва заголовка от содержимого, остальное
    pagination обрабатывает самостоятельно.
    """
    if not elements:
        return []
    total_h = 0
    for el in elements:
        try:
            _, h = el.wrap(AVAILABLE_WIDTH, A4[1])
            total_h += h
        except Exception:
            total_h += 20  # грубая оценка при ошибке
    if total_h <= MAX_KEEP_HEIGHT:
        return [KeepTogether(elements)]
    # Блок слишком большой — сохраняем только первые 2 элемента вместе,
    # остальное переносится естественно.
    if len(elements) >= 2:
        head = list(elements[:2])
        tail = list(elements[2:])
        return [KeepTogether(head)] + tail
    return list(elements)


def add_heading(text: str, style: ParagraphStyle, level: int = 0) -> Paragraph:
    """Заголовок с поддержкой автоматического оглавления.

    В оглавление попадают только H1 (level=0) и H2 (level=1).
    H3 (level=2) в оглавление не включается для компактности, но помечается
    как заголовок для целей CondPageBreak и KeepTogether.
    """
    key = "h_" + hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    p = Paragraph(f'<a name="{key}"/>{text}', style)
    # Помечаем как заголовок (для парсера)
    p._is_heading = True
    p._heading_level = level
    if level < 2:
        # H1 и H2 — попадают в TOC
        p.bookmark_name = key
        p.bookmark_level = level
        p.bookmark_text = text
        p.bookmark_key = key
    # H3 — bookmark_name не устанавливаем, в TOC не попадает
    return p


def h1(text: str) -> Paragraph:
    return add_heading(text, H1_STYLE, level=0)


def h2(text: str) -> Paragraph:
    return add_heading(text, H2_STYLE, level=1)


def h3(text: str) -> Paragraph:
    return add_heading(text, H3_STYLE, level=2)


def p(text: str) -> Paragraph:
    return Paragraph(text, BODY_STYLE)


def p_noindent(text: str) -> Paragraph:
    return Paragraph(text, BODY_NOINDENT)


def bullet(text: str) -> Paragraph:
    p_item = Paragraph(text, BULLET_STYLE, bulletText="•")
    p_item._is_bullet = True
    return p_item


def numbered(n: int, text: str) -> Paragraph:
    p_item = Paragraph(text, BULLET_STYLE, bulletText=f"{n}.")
    p_item._is_bullet = True
    return p_item


def _make_code_table(code_text: str, env_label: str | None) -> Table:
    """Создаёт блок кода с серой подложкой, моноширинным шрифтом и меткой среды."""
    # Экранируем спецсимволы, безопасные для Paragraph
    escaped = code_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Сохраняем переносы строк через <br/>
    lines = escaped.split("\n")
    html = "<br/>".join(lines)
    code_paragraph = Paragraph(html, CODE_STYLE)

    rows = []
    if env_label:
        rows.append([Paragraph(f"<b>{env_label}</b>", CODE_LABEL_STYLE)])
    rows.append([code_paragraph])

    col_width = AVAILABLE_WIDTH - 4  # оставляем 4pt на внутренние отступы
    table = Table(rows, colWidths=[col_width], hAlign="CENTER")
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, CODE_BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if env_label:
        # Метка среды — отдельный блок сверху
        style_cmds.append(("LINEBELOW", (0, 0), (-1, 0), 0.3, CODE_BORDER))
        style_cmds.append(("BOTTOMPADDING", (0, 0), (-1, 0), 4))
        style_cmds.append(("TOPPADDING", (0, 0), (-1, 0), 4))
    table.setStyle(TableStyle(style_cmds))
    return table


def code(code_text: str, env: str | None = None) -> Table:
    """Блок кода с меткой среды выполнения.

    Параметр env может принимать значения:
        'Jupyter Notebook' — ячейка Jupyter
        'Google Colab' — ячейка Colab
        'PowerShell' — терминал Windows
        'Linux' — терминал Linux/macOS
        'Python' — инвариантный Python-код (любая среда)
        None — без метки
    """
    block = _make_code_table(code_text, env)
    # Метка для постпроцессора — этот блок должен оставаться цельным
    block._is_block = True
    block._block_kind = "code"
    return block


def callout(title: str, body_text: str, kind: str = "note") -> Table:
    """Унифицированный блок-плашка: note/tip/warning.

    Заголовок вынесен в шапку блока, цветовая гамма согласована.
    """
    if kind == "tip":
        bg, border, text_color = TIP_BG, TIP_BORDER, TIP_TEXT
        title_prefix = "СОВЕТ"
    elif kind == "warning":
        bg, border, text_color = WARN_BG, WARN_BORDER, WARN_TEXT
        title_prefix = "ВНИМАНИЕ"
    elif kind == "note":
        bg, border, text_color = NOTE_BG, NOTE_BORDER, NOTE_TEXT
        title_prefix = "ПРИМЕЧАНИЕ"
    else:
        raise ValueError(f"Неизвестный тип callout: {kind}")

    title_para = Paragraph(
        f"<b>{title_prefix}. {title}</b>",
        ParagraphStyle(
            name="CalloutHeader",
            fontName="FreeSerif-Bold",
            fontSize=10.5,
            leading=14,
            textColor=text_color,
            alignment=TA_LEFT,
        ),
    )
    body_para = Paragraph(body_text, CALLOUT_BODY)

    col_width = AVAILABLE_WIDTH - 4
    table = Table([[title_para], [body_para]], colWidths=[col_width], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 3, border),
                ("BOX", (0, 0), (-1, -1), 0.4, border),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (0, 0), 6),
                ("BOTTOMPADDING", (0, 0), (0, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    # Метки для постпроцессора
    table._is_block = True
    table._block_kind = kind
    return table


def tip(title: str, body_text: str) -> Table:
    return callout(title, body_text, kind="tip")


def warning(title: str, body_text: str) -> Table:
    return callout(title, body_text, kind="warning")


def note(title: str, body_text: str) -> Table:
    return callout(title, body_text, kind="note")


def spacer(h: float = 6) -> Spacer:
    return Spacer(1, h)


def hr() -> HRFlowable:
    return HRFlowable(
        width="100%",
        thickness=0.4,
        color=BORDER,
        spaceBefore=4,
        spaceAfter=8,
    )


def checklist(items: list[str]) -> list[Paragraph]:
    """Список с символом □ для чек-листов."""
    style = ParagraphStyle(
        name="Checklist",
        fontName="FreeSerif",
        fontSize=10.5,
        leading=15,
        textColor=TEXT_PRIMARY,
        leftIndent=20,
        bulletIndent=2,
        spaceAfter=3,
        alignment=TA_LEFT,
    )
    return [Paragraph(item, style, bulletText="□") for item in items]


# ─────────────────────────────────────────────────────────────────────────────
# Шаблон документа с поддержкой TOC
# ─────────────────────────────────────────────────────────────────────────────
class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        # Используем _is_heading (помечаем все заголовки), но в TOC
        # попадают только H1 и H2 (для которых установлен bookmark_level)
        if hasattr(flowable, "bookmark_name") and hasattr(flowable, "bookmark_level"):
            level = getattr(flowable, "bookmark_level", 0)
            text = getattr(flowable, "bookmark_text", "")
            key = getattr(flowable, "bookmark_key", "")
            self.notify("TOCEntry", (level, text, self.page, key))


# ─────────────────────────────────────────────────────────────────────────────
# Колонтитулы
# ─────────────────────────────────────────────────────────────────────────────
def _draw_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("FreeSerif", 8)
    canvas.setFillColor(TEXT_MUTED)

    # Шапка
    header_text = "Python · Excel, CSV, Parquet — учебная шпаргалка"
    canvas.drawString(LEFT_MARGIN, PAGE_HEIGHT - TOP_MARGIN + 12, header_text)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(
        LEFT_MARGIN,
        PAGE_HEIGHT - TOP_MARGIN + 8,
        PAGE_WIDTH - RIGHT_MARGIN,
        PAGE_HEIGHT - TOP_MARGIN + 8,
    )

    # Подвал: страница X из Y не рисуется здесь (Y появится после multiBuild)
    canvas.drawString(LEFT_MARGIN, BOTTOM_MARGIN - 14, "Z.ai · учебный материал")
    page_num_text = f"Стр. {canvas.getPageNumber()}"
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, BOTTOM_MARGIN - 14, page_num_text)

    canvas.restoreState()
