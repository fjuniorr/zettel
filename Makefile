.PHONY: install test coverage

install:
	pipx install . --force

test:
	uv run pytest tests/test_notes.py tests/test_notebook.py

coverage:
	uv run pytest -s --cov-config=.coveragerc --cov-report html --cov-branch --cov=zettel tests/