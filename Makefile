.PHONY: run test

run:
	PYTHONPATH=src python3 -m depviz config.csv

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v
