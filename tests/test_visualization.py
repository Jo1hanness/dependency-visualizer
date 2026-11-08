"""Тесты вывода графа: Mermaid и ASCII-дерево."""

import os
import tempfile
import unittest

from depviz.ascii_tree import render_tree
from depviz.graph import build_graph
from depviz.mermaid import render_html, to_mermaid
from depviz.test_repo import TestRepository


def graph_from_text(text, root="A"):
    """Построить граф из описания тестового репозитория."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as file:
        file.write(text)
    try:
        return build_graph(TestRepository.load(file.name), root)
    finally:
        os.remove(file.name)


class MermaidTest(unittest.TestCase):
    """Текст диаграммы Mermaid."""

    def test_edges_and_header(self):
        """Диаграмма содержит заголовок, вершины и рёбра."""
        text = to_mermaid(graph_from_text("A: B\nB:\n"))
        self.assertTrue(text.startswith("graph TD"))
        self.assertIn('n0["A"]', text)
        self.assertIn("n0 --> n1", text)

    def test_missing_styled(self):
        """Отсутствующие пакеты выделяются отдельным стилем."""
        text = to_mermaid(graph_from_text("A: X\n"))
        self.assertIn("class n1 missing", text)

    def test_special_names(self):
        """Имена apt с символами + и . попадают только в подписи."""
        graph = graph_from_text("A: B\nB:\n")
        graph.order[1] = "libstdc++6"
        graph.edges = {"A": ["libstdc++6"], "libstdc++6": []}
        text = to_mermaid(graph)
        self.assertIn('n1["libstdc++6"]', text)
        self.assertIn("n0 --> n1", text)

    def test_html_page(self):
        """HTML-страница содержит экранированную диаграмму."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "g.html")
            render_html("graph TD\n    n0 --> n1\n", path, "Граф")
            with open(path, encoding="utf-8") as file:
                page = file.read()
        self.assertIn("n0 --&gt; n1", page)
        self.assertIn("mermaid.initialize", page)


class AsciiTreeTest(unittest.TestCase):
    """ASCII-дерево зависимостей."""

    def test_simple_tree(self):
        """Ветки и последние элементы рисуются разными символами."""
        lines = render_tree(graph_from_text("A: B C\nB:\nC:\n"))
        self.assertEqual(lines, ["A", "├── B", "└── C"])

    def test_repeated_node_marked(self):
        """Повторно встреченный пакет помечается (*)."""
        lines = render_tree(graph_from_text("A: B C\nB: D\nC: D\nD:\n"))
        self.assertIn("    └── D (*)", lines)

    def test_cycle_is_finite(self):
        """Цикл не приводит к бесконечному дереву."""
        lines = render_tree(graph_from_text("A: B\nB: A\n"))
        self.assertEqual(lines, ["A", "└── B", "    └── A (*)"])

    def test_missing_marked(self):
        """Отсутствующий пакет помечается в дереве."""
        lines = render_tree(graph_from_text("A: X\n"))
        self.assertEqual(lines[1], "└── X (нет в репозитории)")


if __name__ == "__main__":
    unittest.main()
