"""Представление графа на языке диаграмм Mermaid и вывод картинки.

Картинка PNG строится утилитой ``mmdc`` (Mermaid CLI), если она
установлена. Иначе создаётся HTML-страница, которая рисует граф
библиотекой mermaid.js прямо в браузере. Результат открывается
программой просмотра по умолчанию.
"""

import html
import os
import shutil
import subprocess
import tempfile
import webbrowser

MERMAID_JS = (
    "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"
)
HTML_TEMPLATE = """<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title></head>
<body><pre class="mermaid">
{diagram}</pre>
<script src="{script}"></script>
<script>mermaid.initialize({{startOnLoad: true}});</script>
</body></html>
"""
TIMEOUT_SECONDS = 60
MISSING_STYLE = "classDef missing stroke-dasharray: 5 5,fill:#fee"
ROOT_STYLE = "classDef root fill:#cde,stroke:#036,stroke-width:2px"


class RenderError(Exception):
    """Не удалось получить изображение графа."""


def node_ids(graph):
    """Сопоставить каждой вершине короткий идентификатор n0, n1, ..."""
    names = list(graph.order)
    for deps in graph.edges.values():
        names.extend(dep for dep in deps if dep not in names)
    return {name: f"n{index}" for index, name in enumerate(names)}


def to_mermaid(graph):
    """Сформировать текст диаграммы Mermaid (flowchart сверху вниз)."""
    ids = node_ids(graph)
    lines = ["graph TD"]
    for name, node in ids.items():
        lines.append(f'    {node}["{name}"]')
    for name in graph.order:
        for dep in graph.edges[name]:
            lines.append(f"    {ids[name]} --> {ids[dep]}")
    lines.append(f"    {ROOT_STYLE}")
    lines.append(f"    class {ids[graph.root]} root")
    if graph.missing:
        lines.append(f"    {MISSING_STYLE}")
        missing = ",".join(ids[name] for name in sorted(graph.missing))
        lines.append(f"    class {missing} missing")
    return "\n".join(lines) + "\n"


def render_with_mmdc(text, png_path):
    """Построить PNG локальной утилитой mmdc."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".mmd", delete=False, encoding="utf-8"
    ) as file:
        file.write(text)
    try:
        subprocess.run(
            ["mmdc", "-i", file.name, "-o", png_path, "-b", "white"],
            check=True, capture_output=True, timeout=TIMEOUT_SECONDS,
        )
    except (subprocess.SubprocessError, OSError) as error:
        raise RenderError(f"mmdc завершился с ошибкой: {error}")
    finally:
        os.remove(file.name)


def render_html(text, html_path, title):
    """Сохранить HTML-страницу, рисующую граф через mermaid.js."""
    page = HTML_TEMPLATE.format(
        title=html.escape(title), diagram=html.escape(text),
        script=MERMAID_JS,
    )
    with open(html_path, "w", encoding="utf-8") as file:
        file.write(page)


def render_image(text, base_path, title):
    """Построить изображение графа и вернуть путь к файлу.

    Если установлен mmdc — PNG, иначе HTML-страница с диаграммой.
    """
    if shutil.which("mmdc"):
        png_path = base_path + ".png"
        render_with_mmdc(text, png_path)
        return png_path
    html_path = base_path + ".html"
    render_html(text, html_path, title)
    return html_path


def show_image(path):
    """Открыть файл в программе просмотра по умолчанию."""
    return webbrowser.open("file://" + os.path.abspath(path))
