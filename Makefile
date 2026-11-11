PYTHON ?= python3

.PHONY: test run run-bg lint clean setup

setup:
	python3 -m venv .venv
	./.venv/bin/pip install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	./run.sh

run-bg:
	./run.sh --background

lint:
	$(PYTHON) -m compileall -q led_sync tests

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete
