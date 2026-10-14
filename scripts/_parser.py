# -*- coding: utf-8 -*-
"""Парсер упрощённой разметки в flowables ReportLab с последующей группировкой
в KeepTogether-блоки для предотвращения разрывов между связанными элементами.

Поддерживаемые конструкции:

    # Заголовок H1
    ## Подзаголовок H2
    ### Подзаголовок H3

    Обычный абзац текста.

    - Маркированный пункт
    1. Нумерованный пункт

    >TIP: Заголовок совета
    Текст совета.

    >WARN: Заголовок предупреждения
    Текст предупреждения.

    >NOTE: Заголовок примечания
    Текст примечания.

    ```env=Jupyter Notebook
    df.head()
    ```

    ---
    Горизонтальная линия.

    [[CHECKLIST]]
    - пункт 1
    [[END]]

    [[IMAGE:путь:ширина]]
    Вставка мини-иллюстрации в текст.

После разбора выполняется постпроцессинг:
- перед H1/H2/H3 добавляется CondPageBreak для защиты от orphan headings;
- callout-плашки (TIP/WARN/NOTE) оборачиваются в KeepTogether со своим заголовком
  и вводным абзацем;
- блоки кода группируются с предшествующим вводным абзацем;
- между подряд идущими callout-плашками добавляется явный Spacer для визуального
  отделения.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    CondPageBreak,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Preformatted,
    Spacer,
)

from _core import (
    AVAILABLE_WIDTH,
    bullet,
    checklist,
    code as code_block,
    h1,
    h2,
    h3,
    hr,
    numbered,
    p,
    p_noindent,
    safe_keep_together,
    spacer,
    tip,
    warning,
    note,
)


# Пороги CondPageBreak перед заголовками (доля высоты страницы, которая
# должна оставаться, чтобы заголовок не ушел в orphan).
# Если на странице осталось меньше указанной доли, происходит переход на
# следующую страницу.
H1_MIN_SPACE = A4[1] * 0.22   # ~185pt — H1: нужен существенный блок под раздел
H2_MIN_SPACE = A4[1] * 0.13   # ~109pt — H2: 13% страницы
H3_MIN_SPACE = A4[1] * 0.08   # ~67pt — H3: достаточно 2-3 строк контента

# Корень проекта — для разрешения относительных путей к изображениям
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_markdown(text: str) -> list:
    """Преобразует markdown-подобный текст в список flowables ReportLab
    с постпроцессингом для улучшения разбиения на страницы.
    """
    raw_flowables = _parse_raw(text)
    return _post_process(raw_flowables)


# ─────────────────────────────────────────────────────────────────────────────
# Стадия 1: разбор разметки в плоский список flowables
# ─────────────────────────────────────────────────────────────────────────────
def _parse_raw(text: str) -> list:
    flowables: list = []
    lines = text.split("\n")
    i = 0
    n = len(lines)

    def _flush_paragraph(buf: list[str]):
        if not buf:
            return
        joined = " ".join(line.strip() for line in buf if line.strip())
        if joined:
            flowables.append(p(joined))

    def _flush_bullets(buf: list[str]):
        if not buf:
            return
        for item in buf:
            flowables.append(bullet(item.strip()))

    def _flush_numbered(buf: list[str]):
        if not buf:
            return
        for idx, item in enumerate(buf, start=1):
            flowables.append(numbered(idx, item.strip()))

    para_buf: list[str] = []
    bullet_buf: list[str] = []
    num_buf: list[str] = []

    while i < n:
        raw = lines[i]
        line = raw.rstrip("\n")

        # Пропускаем пустые строки — flush накопленных буферов
        if not line.strip():
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []
            i += 1
            continue

        # H1, H2, H3
        if line.startswith("### "):
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []
            flowables.append(h3(line[4:].strip()))
            i += 1
            continue
        if line.startswith("## "):
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []
            flowables.append(h2(line[3:].strip()))
            i += 1
            continue
        if line.startswith("# "):
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []
            flowables.append(h1(line[2:].strip()))
            i += 1
            continue

        # Вставка изображения: [[IMAGE:path:width_pt]]
        if line.strip().startswith("[[IMAGE:"):
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []
            # Формат: [[IMAGE:path:width]]
            inner = line.strip()[2:-2]  # снимаем [[ ... ]]
            parts = inner.split(":")
            if len(parts) >= 3:
                img_path = parts[1]
                try:
                    img_w = float(parts[2])
                except ValueError:
                    img_w = AVAILABLE_WIDTH * 0.55
                # Разрешаем путь относительно корня проекта
                if not os.path.isabs(img_path):
                    img_path = str(PROJECT_ROOT / img_path)
                if os.path.exists(img_path):
                    # Получаем реальные размеры изображения
                    from PIL import Image as PILImage
                    pil_img = PILImage.open(img_path)
                    orig_w, orig_h = pil_img.size
                    aspect = orig_h / orig_w
                    # Если заданная ширина приводит к слишком большой высоте
                    # (больше 380pt — оставляем минимум 20pt под код и подписи),
                    # ограничиваем по высоте
                    max_height = 420
                    target_w = img_w
                    target_h = img_w * aspect
                    if target_h > max_height:
                        target_h = max_height
                        target_w = target_h / aspect
                    img = Image(img_path, width=target_w, height=target_h)
                    img.hAlign = "CENTER"
                    img._is_image = True
                    flowables.append(img)
                else:
                    print(f"[parser] Изображение не найдено: {img_path}", file=sys.stderr)
            i += 1
            continue

        # Callout
        if line.startswith(">TIP:") or line.startswith(">WARN:") or line.startswith(">NOTE:"):
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []

            if line.startswith(">TIP:"):
                kind = "TIP"
                title = line[5:].strip()
            elif line.startswith(">WARN:"):
                kind = "WARN"
                title = line[6:].strip()
            else:
                kind = "NOTE"
                title = line[6:].strip()

            # Читаем тело до следующей пустой строки
            body_lines = []
            i += 1
            while i < n and lines[i].strip():
                body_lines.append(lines[i].strip())
                i += 1
            body = " ".join(body_lines)
            if kind == "TIP":
                flowables.append(tip(title, body))
            elif kind == "WARN":
                flowables.append(warning(title, body))
            else:
                flowables.append(note(title, body))
            continue

        # Code block
        if line.startswith("```"):
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []

            env = None
            header = line[3:].strip()
            if header.startswith("env="):
                env = header[4:].strip()

            code_lines = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            # Пропускаем закрывающие ```
            if i < n and lines[i].startswith("```"):
                i += 1
            flowables.append(code_block("\n".join(code_lines), env=env))
            continue

        # Horizontal rule
        if line.strip() == "---":
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []
            flowables.append(hr())
            i += 1
            continue

        # Checklist
        if line.strip() == "[[CHECKLIST]]":
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            _flush_numbered(num_buf)
            num_buf = []
            i += 1
            items = []
            while i < n and lines[i].strip() != "[[END]]":
                if lines[i].strip().startswith("- "):
                    items.append(lines[i].strip()[2:].strip())
                i += 1
            # Пропускаем [[END]]
            if i < n and lines[i].strip() == "[[END]]":
                i += 1
            cl_items = checklist(items)
            for cl in cl_items:
                cl._is_checklist = True
            flowables.extend(cl_items)
            continue

        # Bullet
        if line.startswith("- "):
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_numbered(num_buf)
            num_buf = []
            bullet_buf.append(line[2:].strip())
            i += 1
            continue

        # Numbered
        if line and line[0].isdigit() and "." in line[:4]:
            _flush_paragraph(para_buf)
            para_buf = []
            _flush_bullets(bullet_buf)
            bullet_buf = []
            # Отделяем текст после "N. "
            dot_idx = line.find(".")
            item_text = line[dot_idx + 1:].strip()
            num_buf.append(item_text)
            i += 1
            continue

        # Обычный абзац
        para_buf.append(line.strip())
        i += 1

    # Финальный flush
    _flush_paragraph(para_buf)
    _flush_bullets(bullet_buf)
    _flush_numbered(num_buf)

    return flowables


# ─────────────────────────────────────────────────────────────────────────────
# Стадия 2: постпроцессинг — группировка, CondPageBreak, отступы
# ─────────────────────────────────────────────────────────────────────────────
def _is_heading(f) -> bool:
    return getattr(f, "_is_heading", False)


def _heading_level(f) -> int:
    return getattr(f, "_heading_level", 0)


def _is_block(f) -> bool:
    """Code block или callout — помечены атрибутом _is_block=True."""
    return getattr(f, "_is_block", False)


def _is_callout(f) -> bool:
    return getattr(f, "_is_block", False) and getattr(f, "_block_kind", "") in {
        "tip", "warning", "note"
    }


def _is_code(f) -> bool:
    return getattr(f, "_is_block", False) and getattr(f, "_block_kind", "") == "code"


def _is_image(f) -> bool:
    return getattr(f, "_is_image", False)


def _is_checklist_item(f) -> bool:
    return getattr(f, "_is_checklist", False)


def _is_bullet(f) -> bool:
    return getattr(f, "_is_bullet", False)


def _post_process(flowables: list) -> list:
    """Группировка flowables в блоки KeepTogether с CondPageBreak перед
    заголовками и явными отступами между callout-плашками.

    Логика группировки (мелкогранулярная, чтобы избежать больших пустот):
    1. Заголовок H1/H2/H3 начинает новый блок. Перед H1/H2/H3 добавляется
       CondPageBreak, чтобы заголовок не остался один в конце страницы.
    2. Каждый code-блок, callout-плашка и изображение закрывают текущий блок
       и начинают собственный. Это означает:
       - заголовок + вводный абзац → один KeepTogether (защита от отрыва
         заголовка от описания)
       - код → отдельный KeepTogether (можно перенести, если не помещается)
       - плашка → отдельный KeepTogether
       - изображение → отдельный KeepTogether
    3. Между подряд идущими callout-плашками добавляется Spacer(1, 6).
    4. Между кодом и последующей плашкой — Spacer(1, 6).
    5. Каждая группа оборачивается в safe_keep_together.
    """
    result: list = []
    current_unit: list = []
    prev_was_callout = False
    prev_was_code = False

    def _flush_unit():
        nonlocal current_unit
        if not current_unit:
            return
        # Удаляем хвостовые Spacer из блока, чтобы не было лишних пустот
        while current_unit and isinstance(current_unit[-1], Spacer):
            current_unit.pop()
        if current_unit:
            result.extend(safe_keep_together(current_unit))
        current_unit = []

    for f in flowables:
        # Заголовок — начинает новый блок
        if _is_heading(f):
            _flush_unit()
            level = _heading_level(f)
            if level == 0:
                result.append(CondPageBreak(H1_MIN_SPACE))
            elif level == 1:
                result.append(CondPageBreak(H2_MIN_SPACE))
            elif level == 2:
                result.append(CondPageBreak(H3_MIN_SPACE))
            current_unit.append(f)
            prev_was_callout = False
            prev_was_code = False
            continue

        # Code-блок — закрывает текущий блок (H3 + описание), сам становится
        # отдельным KeepTogether. Это позволяет коду перенестись на следующую
        # страницу, не унося с собой заголовок и описание.
        if _is_code(f):
            _flush_unit()
            if prev_was_callout:
                # Между плашкой и следующим кодом — отступ
                result.append(Spacer(1, 6))
            current_unit.append(f)
            current_unit.append(Spacer(1, 4))
            _flush_unit()
            prev_was_callout = False
            prev_was_code = True
            continue

        # Callout-плашка — отдельный KeepTogether
        if _is_callout(f):
            _flush_unit()
            if prev_was_callout:
                # Между подряд идущими плашками — отступ для визуального отделения
                result.append(Spacer(1, 6))
            elif prev_was_code:
                # Между кодом и плашкой — отступ
                result.append(Spacer(1, 6))
            current_unit.append(f)
            current_unit.append(Spacer(1, 18))
            _flush_unit()
            prev_was_callout = True
            prev_was_code = False
            continue

        # Изображение — добавляем в текущий блок (связка «заголовок + описание + изображение»).
        # Это связывает изображение с его описанием, чтобы они были на одной странице.
        # Если в текущем блоке уже есть код — flush'им его, потом начинаем новый блок
        # с изображением (изображение не должно быть связано с предыдущим кодом).
        if _is_image(f):
            # Если в текущем блоке есть код — это блок «код + плашка», flush'им
            has_code_in_unit = any(_is_code(el) for el in current_unit)
            if has_code_in_unit:
                _flush_unit()
            # Добавляем изображение в текущий блок (связка с описанием выше)
            if prev_was_callout and not current_unit:
                result.append(Spacer(1, 6))
            current_unit.append(f)
            _flush_unit()
            # Явный отступ после изображения (16pt) — добавляем в result после flush
            # как самостоятельный flowable, чтобы он не был удалён trailing cleanup
            result.append(Spacer(1, 16))
            prev_was_callout = False
            prev_was_code = False
            continue

        # Чек-лист пункты — добавляем в текущий блок
        if _is_checklist_item(f):
            current_unit.append(f)
            continue

        # Горизонтальная линия — начинает новый блок
        if isinstance(f, HRFlowable):
            _flush_unit()
            result.append(f)
            prev_was_callout = False
            prev_was_code = False
            continue

        # Обычный flowable (абзац, буллет и т.д.) — добавляем в текущий блок
        current_unit.append(f)
        prev_was_callout = False
        prev_was_code = False

    _flush_unit()
    return result
