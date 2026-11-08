"""Тесты разбора индекса репозитория apt."""

import gzip
import os
import tempfile
import unittest

from depviz.apt_repo import (
    AptRepository,
    RepositoryError,
    parse_relation,
    parse_stanzas,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "examples", "Packages_sample")


class ParseTest(unittest.TestCase):
    """Разбор отдельных полей и блоков."""

    def test_relation_strips_versions(self):
        """Версии, архитектуры и :any отбрасываются."""
        value = "libc6 (>= 2.34), python3:any, foo [amd64] <!nocheck>"
        self.assertEqual(parse_relation(value), ["libc6", "python3", "foo"])

    def test_relation_takes_first_alternative(self):
        """Из альтернатив берётся первая."""
        self.assertEqual(parse_relation("debconf | debconf-2.0"),
                         ["debconf"])

    def test_relation_empty(self):
        """Пустое поле — пустой список."""
        self.assertEqual(parse_relation(""), [])

    def test_stanza_continuation_lines(self):
        """Строки-продолжения склеиваются с предыдущим полем."""
        text = "Package: a\nDepends: b,\n c\n\nPackage: d\n"
        stanzas = parse_stanzas(text)
        self.assertEqual(len(stanzas), 2)
        self.assertEqual(parse_relation(stanzas[0]["Depends"]), ["b", "c"])


class RepositoryTest(unittest.TestCase):
    """Поиск пакетов и зависимостей в примере индекса."""

    @classmethod
    def setUpClass(cls):
        """Загрузить пример индекса один раз."""
        cls.repo = AptRepository.load(SAMPLE)

    def test_direct_dependencies_of_version(self):
        """Зависимости берутся для заданной версии."""
        deps = self.repo.direct_dependencies("curl", "8.5.0-2ubuntu10")
        self.assertEqual(deps, ["libc6", "libcurl4t64", "zlib1g"])

    def test_pre_depends_included(self):
        """Pre-Depends входят в прямые зависимости."""
        deps = self.repo.direct_dependencies("perl-base")
        self.assertEqual(deps, ["libc6", "libcrypt1"])

    def test_unknown_version(self):
        """Неизвестная версия — ошибка со списком доступных."""
        with self.assertRaises(RepositoryError) as ctx:
            self.repo.direct_dependencies("curl", "0.0")
        self.assertIn("8.5.0-2ubuntu10", str(ctx.exception))

    def test_unknown_package(self):
        """Неизвестный пакет — ошибка."""
        with self.assertRaises(RepositoryError):
            self.repo.direct_dependencies("no-such-package")

    def test_virtual_package(self):
        """Виртуальный пакет разрешается через Provides."""
        self.assertEqual(self.repo.resolve("debconf-2.0"), "debconf")

    def test_gzip_index(self):
        """Сжатый индекс .gz читается так же."""
        with open(SAMPLE, "rb") as file:
            data = gzip.compress(file.read())
        with tempfile.NamedTemporaryFile(suffix=".gz", delete=False) as tmp:
            tmp.write(data)
        self.addCleanup(os.remove, tmp.name)
        repo = AptRepository.load(tmp.name)
        self.assertIn("curl", repo.packages)

    def test_missing_source(self):
        """Несуществующий источник — ошибка."""
        with self.assertRaises(RepositoryError):
            AptRepository.load("no_such_index")


if __name__ == "__main__":
    unittest.main()
