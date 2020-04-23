.PHONY: lint types black clean

lint:
	@python -m flake8 --exclude=.git,venv* simple_fetch_middleware tests

types:
	@mypy --ignore-missing-imports --follow-imports=skip simple_fetch_middleware

black:
	@black --check simple_fetch_middleware tests

clean:
	@find . -name "*.pyc" -delete
	@rm -rf .mypy_cache/ .tox/ build/ dist/ htmlcov/ .coverage coverage.xml
