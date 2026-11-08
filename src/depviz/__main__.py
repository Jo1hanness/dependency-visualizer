"""Точка входа: ``python -m depviz config.csv``."""

import sys

from depviz.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
