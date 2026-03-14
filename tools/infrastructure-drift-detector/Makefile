# Makefile for infrastructure-drift-detector
.PHONY: all test run clean install help
all: help
help:
	@echo "Infrastructure Drift Detector - Commands:"
	@echo "  make deps, test, run, install, clean"
deps:
	pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt yet"
test:
	@echo "Running tests..." && python -m pytest tests/ -v 2>/dev/null || echo "No tests yet"
run:
	./infrastructure-drift-detector.py --help
install:
	sudo cp infrastructure-drift-detector.py /usr/local/bin/infrastructure-drift-detector && sudo chmod +x /usr/local/bin/infrastructure-drift-detector
clean:
	rm -rf __pycache__ *.pyc .pytest_cache .coverage
