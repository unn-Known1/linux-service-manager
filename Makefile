# Makefile for Linux Service Manager
# Convenience commands for building, testing, and installation

.PHONY: all test install clean install-systemd uninstall help

# Default target
all: help

# Show help
help:
	@echo "Linux Service Manager - Makefile"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  test          - Run the test suite"
	@echo "  install       - Install script to /usr/local/bin"
	@echo "  uninstall     - Remove installed script"
	@echo "  install-systemd NAME=<name> DESC=<desc> - Create systemd unit"
	@echo "  clean         - Remove temporary files"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "Examples:"
	@echo "  make test"
	@echo "  sudo make install"
	@echo "  sudo make install-systemd NAME=myapp DESC='My Application'"

# Run tests
test:
	@echo "Running test suite..."
	@./test-service-manager.sh

# Install to /usr/local/bin
install:
	@echo "Installing linux-service-manager to /usr/local/bin/..."
	@sudo cp linux-service-manager.py /usr/local/bin/service-manager
	@sudo chmod 755 /usr/local/bin/service-manager
	@echo "Installed successfully. Run with: service-manager <command>"

# Uninstall
uninstall:
	@echo "Removing service-manager..."
	@sudo rm -f /usr/local/bin/service-manager
	@echo "Uninstalled"

# Install as systemd service
install-systemd:
	@if [ -z "$(NAME)" ]; then \
		echo "ERROR: NAME parameter required"; \
		echo "Usage: make install-systemd NAME=<service-name> DESC='<description>'"; \
		exit 1; \
	fi
	@echo "Installing systemd service for $(NAME)..."
	@./linux-service-manager.py install --name $(NAME) --desc "$(DESC)"
	@echo ""
	@echo "To enable and start:"
	@echo "  sudo systemctl daemon-reload"
	@echo "  sudo systemctl enable --now $(NAME)"
	@echo "  sudo systemctl status $(NAME)"

# Clean temporary files
clean:
	@echo "Cleaning..."
	@rm -f /var/run/test-service-*.pid
	@rm -rf ~/.local/share/service-manager/test-*
	@echo "Clean complete"

# Quick start example
example-http:
	@echo "Starting example HTTP server..."
	@./linux-service-manager.py start --name example-http --cmd "python3 -m http.server 8080" --dir ./public || true
	@echo "Server starting... Check status with: ./linux-service-manager.py status --name example-http"
	@echo "Stop with: ./linux-service-manager.py stop --name example-http"
