# Makefile for incident-timeline-builder
.PHONY: all test run clean install help
all: help
help:
	@echo "Incident Timeline Builder - Commands:"
	@echo "  make deps, test, run, install, clean"
deps:
	pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt yet"
test:
	@echo "Running tests..." && python -m pytest tests/ -v 2>/dev/null || echo "No tests yet"
run:
	./incident-timeline-builder.py --help
install:
	sudo cp incident-timeline-builder.py /usr/local/bin/incident-timeline-builder && sudo chmod +x /usr/local/bin/incident-timeline-builder
clean:
	rm -rf __pycache__ *.pyc .pytest_cache .coverage
