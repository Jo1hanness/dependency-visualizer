"""Тестовый репозиторий: граф пакетов из текстового файла.

Формат файла — по одной строке на пакет::

    # комментарий
    A: B C
    B: D
    D:

Имена пакетов — большие латинские буквы. Пакет, который упомянут
только справа от двоеточия, считается отсутствующим в репозитории.
"""

import re

from depviz.apt_repo import RepositoryError

NAME_RE = re.compile(r"^[A-Z]+$")
COMMENT = "#"


def parse_line(line, line_no):
    """Разобрать строку ``ИМЯ: ЗАВИСИМОСТИ`` и вернуть пару."""
    if ":" not in line:
        raise RepositoryError(f"строка {line_no}: нет двоеточия")
    name, rest = line.split(":", 1)
    name = name.strip()
    deps = rest.split()
    for item in [name] + deps:
        if not NAME_RE.match(item):
            raise RepositoryError(
                f"строка {line_no}: '{item}' — не большие латинские буквы"
            )
    return name, deps


class TestRepository:
    """Репозиторий из файла описания графа (режим тестирования)."""

    def __init__(self, graph):
        """Сохранить словарь пакет -> список зависимостей."""
        self.graph = graph

    @classmethod
    def load(cls, path):
        """Прочитать файл описания графа."""
        try:
            with open(path, encoding="utf-8") as file:
                lines = file.read().splitlines()
        except OSError as error:
            raise RepositoryError(f"не удалось прочитать {path}: {error}")
        graph = {}
        for line_no, raw in enumerate(lines, start=1):
            line = raw.split(COMMENT, 1)[0].strip()
            if not line:
                continue
            name, deps = parse_line(line, line_no)
            if name in graph:
                raise RepositoryError(f"строка {line_no}: повтор {name}")
            graph[name] = deps
        return cls(graph)

    def resolve(self, name):
        """Вернуть имя пакета, если он есть в репозитории."""
        return name if name in self.graph else None

    def all_packages(self):
        """Вернуть имена всех пакетов репозитория."""
        return list(self.graph)

    def direct_dependencies(self, name, version=None):
        """Вернуть прямые зависимости пакета (версия не учитывается)."""
        if name not in self.graph:
            raise RepositoryError(f"пакет {name} не найден в репозитории")
        return list(self.graph[name])
