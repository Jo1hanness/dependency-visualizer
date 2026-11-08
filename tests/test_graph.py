"""Тесты построения графа зависимостей."""

import os
import tempfile
import unittest

from depviz.apt_repo import AptRepository, RepositoryError
from depviz.graph import build_graph, find_cycle, reverse_dependencies
from depviz.test_repo import TestRepository

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES = os.path.join(ROOT, "examples")


def repo_from_text(text):
    """Создать тестовый репозиторий из строки."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as file:
        file.write(text)
    try:
        return TestRepository.load(file.name)
    finally:
        os.remove(file.name)


class GraphTest(unittest.TestCase):
    """BFS по тестовому репозиторию."""

    def test_bfs_order(self):
        """Вершины перечисляются по уровням (BFS)."""
        repo = TestRepository.load(
            os.path.join(EXAMPLES, "repo_simple.txt"))
        graph = build_graph(repo, "A")
        self.assertEqual(graph.order, ["A", "B", "C", "D", "E", "F"])
        self.assertEqual(graph.edges["C"], ["D", "E"])

    def test_cycle_terminates(self):
        """Цикл A -> B -> C -> A обрабатывается без зацикливания."""
        repo = repo_from_text("A: B\nB: C\nC: A\n")
        graph = build_graph(repo, "A")
        self.assertEqual(graph.order, ["A", "B", "C"])
        self.assertEqual(find_cycle(graph.edges, "A"), ["A", "B", "C", "A"])

    def test_self_dependency(self):
        """Пакет, зависящий сам от себя, — цикл длины 1."""
        graph = build_graph(repo_from_text("A: A\n"), "A")
        self.assertEqual(find_cycle(graph.edges, "A"), ["A", "A"])

    def test_no_cycle(self):
        """Ромбовидный граф — не цикл."""
        graph = build_graph(repo_from_text("A: B C\nB: D\nC: D\nD:\n"), "A")
        self.assertEqual(find_cycle(graph.edges, "A"), [])
        self.assertEqual(graph.order.count("D"), 1)

    def test_missing_package(self):
        """Неописанный пакет попадает в missing и становится листом."""
        graph = build_graph(repo_from_text("A: B X\nB:\n"), "A")
        self.assertEqual(graph.missing, {"X"})
        self.assertNotIn("X", graph.edges)

    def test_unknown_root(self):
        """Неизвестный корневой пакет — ошибка."""
        with self.assertRaises(RepositoryError):
            build_graph(repo_from_text("A:\n"), "Z")

    def test_bad_file(self):
        """Строчные буквы в тестовом репозитории — ошибка."""
        with self.assertRaises(RepositoryError):
            repo_from_text("A: b\n")

    def test_apt_transitive(self):
        """Транзитивные зависимости в индексе apt с циклом libc6."""
        repo = AptRepository.load(os.path.join(EXAMPLES, "Packages_sample"))
        graph = build_graph(repo, "curl", "8.5.0-2ubuntu10")
        self.assertIn("libgcc-s1", graph.order)
        self.assertIn("perl-base", graph.order)
        cycle = find_cycle(graph.edges, "curl")
        self.assertEqual(cycle, ["libc6", "libgcc-s1", "libc6"])


class ReverseTest(unittest.TestCase):
    """Обратные зависимости."""

    def test_reverse_simple(self):
        """От D зависят B и C напрямую и A транзитивно."""
        repo = TestRepository.load(
            os.path.join(EXAMPLES, "repo_simple.txt"))
        graph = reverse_dependencies(repo, "D")
        self.assertEqual(graph.order, ["D", "B", "C", "A"])

    def test_reverse_cycle(self):
        """В цикле от A зависят все участники цикла."""
        graph = reverse_dependencies(repo_from_text("A: B\nB: C\nC: A\n"),
                                     "A")
        self.assertEqual(sorted(graph.order), ["A", "B", "C"])

    def test_reverse_leaf_root(self):
        """От корневого пакета никто не зависит."""
        graph = reverse_dependencies(repo_from_text("A: B\nB:\n"), "A")
        self.assertEqual(graph.order, ["A"])

    def test_reverse_unknown(self):
        """Пакет, которого нет нигде, — ошибка."""
        with self.assertRaises(RepositoryError):
            reverse_dependencies(repo_from_text("A:\n"), "Z")

    def test_reverse_apt(self):
        """От libkrb5support0 зависят библиотеки Kerberos и curl."""
        repo = AptRepository.load(os.path.join(EXAMPLES, "Packages_sample"))
        graph = reverse_dependencies(repo, "libkrb5support0")
        self.assertIn("libgssapi-krb5-2", graph.order)
        self.assertIn("curl", graph.order)


if __name__ == "__main__":
    unittest.main()
