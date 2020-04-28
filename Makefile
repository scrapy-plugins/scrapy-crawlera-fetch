.PHONY: lint types black clean

lint:
	@python -m flake8 --exclude=.git,venv* crawlera_fetch tests

types:
	@mypy --ignore-missing-imports --follow-imports=skip crawlera_fetch/*.py tests/*.py

black:
	@black --check crawlera_fetch tests

clean:
	@find . -name "*.pyc" -delete
	@rm -rf .mypy_cache/ .tox/ build/ dist/ htmlcov/ .coverage coverage.xml
