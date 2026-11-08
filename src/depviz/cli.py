"""Интерфейс командной строки."""

import sys

from depviz.config import ConfigError, load_config

DEFAULT_CONFIG = "config.csv"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 2


def print_params(config):
    """Вывести все параметры пользователя в формате ключ-значение."""
    for key, value in config.as_items():
        print(f"{key} = {value}")


def main(argv):
    """Запустить приложение с аргументами командной строки."""
    path = argv[0] if argv else DEFAULT_CONFIG
    try:
        config = load_config(path)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    print_params(config)
    return EXIT_OK
