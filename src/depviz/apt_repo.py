"""Чтение индекса репозитория Ubuntu (файл Packages) без apt.

Индекс — это текст из блоков (stanza), разделённых пустой строкой.
Каждый блок описывает одну версию пакета полями ``Package``,
``Version``, ``Depends``, ``Pre-Depends``, ``Provides`` и т.д.
Индекс можно скачать по URL или прочитать из локального файла;
поддерживаются сжатые варианты ``.gz`` и ``.xz``.
"""

import gzip
import lzma
import re
import urllib.error
import urllib.request

GZIP_MAGIC = b"\x1f\x8b"
XZ_MAGIC = b"\xfd7zXZ"
URL_PREFIXES = ("http://", "https://")
DEPENDENCY_FIELDS = ("Pre-Depends", "Depends")
TIMEOUT_SECONDS = 60
CONSTRAINT_RE = re.compile(r"\(.*?\)|\[.*?\]|<.*?>")


class RepositoryError(Exception):
    """Ошибка получения или разбора данных репозитория."""


def read_source(source):
    """Прочитать байты индекса по URL или из локального файла."""
    try:
        if source.startswith(URL_PREFIXES):
            with urllib.request.urlopen(source, timeout=TIMEOUT_SECONDS) as r:
                return r.read()
        with open(source, "rb") as file:
            return file.read()
    except (urllib.error.URLError, OSError) as error:
        raise RepositoryError(f"не удалось прочитать {source}: {error}")


def decompress(data):
    """Распаковать gzip/xz, если данные сжаты."""
    try:
        if data.startswith(GZIP_MAGIC):
            return gzip.decompress(data)
        if data.startswith(XZ_MAGIC):
            return lzma.decompress(data)
    except (OSError, lzma.LZMAError) as error:
        raise RepositoryError(f"повреждённый архив индекса: {error}")
    return data


def parse_stanzas(text):
    """Разобрать текст индекса в список словарей поле -> значение."""
    stanzas = []
    current = {}
    last_key = None
    for line in text.splitlines():
        if not line.strip():
            if current:
                stanzas.append(current)
            current, last_key = {}, None
        elif line[0] in " \t" and last_key:
            current[last_key] += " " + line.strip()
        elif ":" in line:
            last_key, value = line.split(":", 1)
            current[last_key] = value.strip()
    if current:
        stanzas.append(current)
    return stanzas


def parse_relation(value):
    """Разобрать поле зависимостей в список имён пакетов.

    Из альтернатив ``a | b`` берётся первая; версии ``(>= 1.0)``,
    архитектуры ``[amd64]``, профили ``<!nocheck>`` и квалификатор
    ``:any`` отбрасываются.
    """
    names = []
    for group in value.split(","):
        first = group.split("|")[0]
        name = CONSTRAINT_RE.sub("", first).strip().split(":")[0]
        if name and name not in names:
            names.append(name)
    return names


class AptRepository:
    """Индекс пакетов с поиском по имени, версии и Provides."""

    def __init__(self, stanzas):
        """Построить индексы по списку блоков описания пакетов."""
        self.packages = {}
        self.providers = {}
        for stanza in stanzas:
            name = stanza.get("Package")
            if not name:
                continue
            self.packages.setdefault(name, []).append(stanza)
            for virtual in parse_relation(stanza.get("Provides", "")):
                self.providers.setdefault(virtual, []).append(name)

    @classmethod
    def load(cls, source):
        """Загрузить индекс по URL или из файла."""
        data = decompress(read_source(source))
        text = data.decode("utf-8", errors="replace")
        repo = cls(parse_stanzas(text))
        if not repo.packages:
            raise RepositoryError(f"в {source} не найдено описаний пакетов")
        return repo

    def versions(self, name):
        """Вернуть список доступных версий пакета."""
        return [s.get("Version", "") for s in self.packages.get(name, [])]

    def resolve(self, name):
        """Вернуть имя реального пакета (с учётом виртуальных)."""
        if name in self.packages:
            return name
        providers = self.providers.get(name)
        return providers[0] if providers else None

    def find(self, name, version=None):
        """Найти блок описания пакета нужной версии."""
        real = self.resolve(name)
        if real is None:
            raise RepositoryError(f"пакет {name} не найден в репозитории")
        stanzas = self.packages[real]
        if not version:
            return stanzas[0]
        for stanza in stanzas:
            if stanza.get("Version") == version:
                return stanza
        available = ", ".join(self.versions(real))
        raise RepositoryError(
            f"версия {version} пакета {name} не найдена "
            f"(доступно: {available})"
        )

    def direct_dependencies(self, name, version=None):
        """Вернуть прямые зависимости пакета (Pre-Depends и Depends)."""
        stanza = self.find(name, version)
        result = []
        for field in DEPENDENCY_FIELDS:
            for dep in parse_relation(stanza.get(field, "")):
                if dep not in result:
                    result.append(dep)
        return result
