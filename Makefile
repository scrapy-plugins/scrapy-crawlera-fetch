.PHONY: lint black clean

lint:
	@python -m flake8 --exclude=.git,venv* crawlera_fetch_middleware tests

black:
	@black --check crawlera_fetch_middleware tests

clean:
	@find . -name "*.pyc" -delete
	@rm -rf .mypy_cache/ .tox/ build/ dist/ htmlcov/ .coverage coverage.xml
