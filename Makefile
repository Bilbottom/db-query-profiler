
test-unit:
	python -m pytest --cov-report term-missing --cov-fail-under=60
	coverage-badge -o coverage.svg -f

test-end-to-end:
	python tests/end-to-end/end_to_end.py
