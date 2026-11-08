"""Загрузка и проверка настроек из конфигурационного файла CSV.

Файл состоит из строк вида ``параметр,значение``. Первая строка
может быть заголовком ``parameter,value``.
"""

import csv
import os
import re
from dataclasses import dataclass

HEADER = ("parameter", "value")
REQUIRED_KEYS = (
    "package_name",
    "repository",
    "test_mode",
    "package_version",
    "ascii_tree",
)
OPTIONAL_KEYS = ("reverse_mode",)
ROW_LENGTH = 2
TRUE_WORDS = ("true", "yes", "1", "да")
FALSE_WORDS = ("false", "no", "0", "нет")
APT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9+.\-]+$")
TEST_NAME_RE = re.compile(r"^[A-Z]+$")
VERSION_RE = re.compile(r"^[0-9A-Za-z.+~:\-]+$")
URL_PREFIXES = ("http://", "https://")


class ConfigError(Exception):
    """Ошибка в конфигурационном файле."""


@dataclass
class Config:
    """Настройки, заданные пользователем."""

    package_name: str
    repository: str
    test_mode: bool
    package_version: str
    ascii_tree: bool
    reverse_mode: bool = False

    def as_items(self):
        """Вернуть список пар (параметр, значение) для вывода."""
        return [(key, getattr(self, key)) for key in REQUIRED_KEYS]


def read_csv(path):
    """Прочитать CSV-файл и вернуть словарь параметр -> значение."""
    if not os.path.isfile(path):
        raise ConfigError(f"конфигурационный файл не найден: {path}")
    params = {}
    with open(path, encoding="utf-8", newline="") as file:
        for line_no, row in enumerate(csv.reader(file), start=1):
            if not row or not "".join(row).strip():
                continue
            if len(row) != ROW_LENGTH:
                raise ConfigError(
                    f"строка {line_no}: ожидалось 2 столбца, "
                    f"получено {len(row)}"
                )
            key, value = row[0].strip(), row[1].strip()
            if (key, value) == HEADER:
                continue
            if key in params:
                raise ConfigError(f"строка {line_no}: повтор параметра {key}")
            params[key] = value
    return params


def parse_bool(key, value):
    """Преобразовать строку в логическое значение."""
    word = value.lower()
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    raise ConfigError(f"{key}: ожидалось true/false, получено '{value}'")


def check_keys(params):
    """Проверить, что заданы все параметры и нет лишних."""
    missing = [key for key in REQUIRED_KEYS if key not in params]
    if missing:
        raise ConfigError("не заданы параметры: " + ", ".join(missing))
    known = REQUIRED_KEYS + OPTIONAL_KEYS
    unknown = [key for key in params if key not in known]
    if unknown:
        raise ConfigError("неизвестные параметры: " + ", ".join(unknown))


def check_package_name(name, test_mode):
    """Проверить имя пакета с учётом режима работы."""
    if not name:
        raise ConfigError("package_name: имя пакета не задано")
    pattern = TEST_NAME_RE if test_mode else APT_NAME_RE
    if not pattern.match(name):
        rule = "большие латинские буквы" if test_mode else "имя пакета apt"
        raise ConfigError(f"package_name: '{name}' не подходит ({rule})")


def check_repository(repository, test_mode):
    """Проверить URL или путь к файлу репозитория."""
    if not repository:
        raise ConfigError("repository: не задан URL или путь к файлу")
    if repository.startswith(URL_PREFIXES):
        if test_mode:
            raise ConfigError(
                "repository: в тестовом режиме нужен путь к файлу, а не URL"
            )
        return
    if not os.path.isfile(repository):
        raise ConfigError(f"repository: файл не найден: {repository}")


def check_version(version, test_mode):
    """Проверить версию пакета (в тестовом режиме не обязательна)."""
    if not version:
        if test_mode:
            return
        raise ConfigError("package_version: версия пакета не задана")
    if not VERSION_RE.match(version):
        raise ConfigError(f"package_version: недопустимая версия '{version}'")


def load_config(path):
    """Прочитать и проверить конфигурацию, вернуть объект Config."""
    params = read_csv(path)
    check_keys(params)
    test_mode = parse_bool("test_mode", params["test_mode"])
    ascii_tree = parse_bool("ascii_tree", params["ascii_tree"])
    reverse_mode = parse_bool(
        "reverse_mode", params.get("reverse_mode", "false")
    )
    check_package_name(params["package_name"], test_mode)
    check_repository(params["repository"], test_mode)
    check_version(params["package_version"], test_mode)
    return Config(
        package_name=params["package_name"],
        repository=params["repository"],
        test_mode=test_mode,
        package_version=params["package_version"],
        ascii_tree=ascii_tree,
        reverse_mode=reverse_mode,
    )
