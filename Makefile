.PHONY: lint black clean

lint:
	@python -m flake8 --exclude=.git,venv* simple_fetch_middleware tests

black:
	@black --check simple_fetch_middleware tests

clean:
	@find . -name "*.pyc" -delete
	@rm -rf .mypy_cache/ .tox/ build/ dist/ htmlcov/ .coverage coverage.xml
