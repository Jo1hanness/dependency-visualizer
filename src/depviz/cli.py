"""Интерфейс командной строки."""

import sys

from depviz.apt_repo import AptRepository, RepositoryError
from depviz.config import ConfigError, load_config
from depviz.graph import build_graph, find_cycle
from depviz.test_repo import TestRepository

DEFAULT_CONFIG = "config.csv"
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2


def open_repository(config):
    """Открыть тестовый репозиторий или индекс apt."""
    if config.test_mode:
        return TestRepository.load(config.repository)
    return AptRepository.load(config.repository)


def print_graph(graph):
    """Вывести граф списком смежности, отсутствующие пакеты и цикл."""
    print(f"Граф зависимостей {graph.root} (обход BFS):")
    for name in graph.order:
        deps = ", ".join(graph.edges[name]) or "—"
        print(f"  {name} -> {deps}")
    if graph.missing:
        missing = ", ".join(sorted(graph.missing))
        print(f"Нет в репозитории: {missing}")
    cycle = find_cycle(graph.edges, graph.root)
    if cycle:
        print("Обнаружен цикл: " + " -> ".join(cycle))
    else:
        print("Циклических зависимостей нет.")


def run(config):
    """Выполнить анализ по готовой конфигурации."""
    repo = open_repository(config)
    graph = build_graph(repo, config.package_name, config.package_version)
    print_graph(graph)


def main(argv):
    """Запустить приложение с аргументами командной строки."""
    path = argv[0] if argv else DEFAULT_CONFIG
    try:
        config = load_config(path)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    try:
        run(config)
    except RepositoryError as error:
        print(f"Ошибка репозитория: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK
