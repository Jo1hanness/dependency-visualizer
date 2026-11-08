#!/bin/sh
# Запуск: ./run.sh [путь_к_config.csv]
cd "$(dirname "$0")" || exit 1
PYTHONPATH=src exec python3 -m depviz "${1:-config.csv}"
