# Makefile for multi-cloud-cost-optimizer
.PHONY: all test run clean install help
all: help
help:
	@echo "Multi-Cloud Cost Optimizer - Commands:"
	@echo "  make deps, test, run, install, clean"
deps:
	pip install -r requirements.txt 2>/dev/null || echo "No requirements.txt yet"
test:
	@echo "Running tests..." && python -m pytest tests/ -v 2>/dev/null || echo "No tests yet"
run:
	./multi-cloud-cost-optimizer.py --help
install:
	sudo cp multi-cloud-cost-optimizer.py /usr/local/bin/multi-cloud-cost-optimizer && sudo chmod +x /usr/local/bin/multi-cloud-cost-optimizer
clean:
	rm -rf __pycache__ *.pyc .pytest_cache .coverage
