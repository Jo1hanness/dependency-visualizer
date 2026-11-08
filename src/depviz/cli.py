"""Интерфейс командной строки."""

import sys

from depviz.apt_repo import AptRepository, RepositoryError
from depviz.config import ConfigError, load_config

DEFAULT_CONFIG = "config.csv"
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2


def print_direct_dependencies(config):
    """Вывести прямые зависимости пакета из репозитория apt."""
    repo = AptRepository.load(config.repository)
    deps = repo.direct_dependencies(
        config.package_name, config.package_version
    )
    title = f"{config.package_name} {config.package_version}"
    print(f"Прямые зависимости {title}:")
    for dep in deps:
        print(f"  {dep}")
    if not deps:
        print("  (нет зависимостей)")


def main(argv):
    """Запустить приложение с аргументами командной строки."""
    path = argv[0] if argv else DEFAULT_CONFIG
    try:
        config = load_config(path)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    if config.test_mode:
        print("Тестовый режим поддерживается начиная с этапа 3.")
        return EXIT_OK
    try:
        print_direct_dependencies(config)
    except RepositoryError as error:
        print(f"Ошибка репозитория: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
