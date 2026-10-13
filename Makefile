VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

.PHONY: install run debug clean lint lint-strict

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) -m src.main $(MAP)

debug:
	$(PYTHON) -m pdb -m src.main $(MAP)

clean:
	find . -type d -name "__pycache__" -not -path "./$(VENV)/*" -exec rm -rf {} +
	rm -rf .mypy_cache

lint:
	$(PYTHON) -m flake8 src
	$(PYTHON) -m mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 src
	$(PYTHON) -m mypy src --strict