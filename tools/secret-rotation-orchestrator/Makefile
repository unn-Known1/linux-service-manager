# Makefile for secret-rotation-orchestrator
.PHONY: all test build install clean help
all: help
help:
	@echo "Secret Rotation Orchestrator - Commands:"
	@echo "  make deps, test, build, install, clean"
deps:
	go mod download
test:
	go test ./...
build:
	go build -o bin/secret-rotation-orchestrator .
install: build
	sudo cp bin/secret-rotation-orchestrator /usr/local/bin/
clean:
	rm -rf bin/
