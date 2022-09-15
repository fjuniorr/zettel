.PHONY: coverage

build:
	python -m build

release:
	python -m twine upload --repository pypi dist/*

coverage:
	python -m pytest -s --cov-config=.coveragerc --cov-report html --cov-branch --cov=zettel tests/