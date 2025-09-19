.PHONY: coverage

build:
	python -m build

install: 
	pipx install dist/zettel-0.0.0.post9002.tar.gz --force

release:
	python -m twine upload dist/*

coverage:
	python -m pytest -s --cov-config=.coveragerc --cov-report html --cov-branch --cov=zettel tests/