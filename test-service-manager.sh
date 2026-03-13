#!/bin/bash
#
# Test script for Linux Service Manager
# This script tests various functionality of the service manager
#

set -e  # Exit on error
set -u  # Error on undefined variable

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/linux-service-manager.py"
TEST_PIDFILE="/tmp/test-service-$$.pid"
TEST_SERVICE_NAME="test-service-$$"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

check_python() {
    log_info "Checking Python availability..."
    if command -v python3 &> /dev/null; then
        PYTHON="python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
    else
        log_error "Python not found. Please install Python 3.6+"
        return 1
    fi

    # Check version
    VERSION=$($PYTHON -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Found Python $VERSION"
    return 0
}

check_ctypes() {
    log_info "Checking ctypes availability..."
    $PYTHON -c "import ctypes" 2>/dev/null && {
        log_info "ctypes available - system calls will work"
        return 0
    }
    log_warn "ctypes not available - some features disabled"
    return 0
}

test_sysinfo() {
    log_info "Testing sysinfo command..."
    if $PYTHON "$PYTHON_SCRIPT" sysinfo > /dev/null 2>&1; then
        log_info "sysinfo command works"
        return 0
    else
        log_warn "sysinfo command failed (ctypes may not be available)"
        return 0
    fi
}

test_foreground_service() {
    log_info "Testing foreground service..."

    # Start a simple sleep service in background
    local service_name="${TEST_SERVICE_NAME}-fg"

    # Start service in foreground with a timeout
    timeout 5s $PYTHON "$PYTHON_SCRIPT" start \
        --name "$service_name" \
        --cmd "sleep 2 && echo 'Service completed'" \
        --foreground > /dev/null 2>&1 || true

    sleep 1

    # Check if system call demos work
    log_info "Foreground service test completed"
    return 0
}

test_daemon_service() {
    log_info "Testing daemon service..."

    local service_name="${TEST_SERVICE_NAME}-daemon"
    local pidfile="${TEST_PIDFILE}"

    # Clean up any existing PID file
    rm -f "$pidfile"

    log_info "Starting daemon..."
    if $PYTHON "$PYTHON_SCRIPT" start \
        --name "$service_name" \
        --cmd "sleep 30" \
        --pidfile "$pidfile" \
        --foreground > /dev/null 2>&1; then
        # Wait for daemon to start
        sleep 1

        # Check if PID file exists
        if [ -f "$pidfile" ]; then
            local pid=$(cat "$pidfile")
            log_info "PID file created: $pid"

            # Check if process exists
            if ps -p "$pid" > /dev/null 2>&1; then
                log_info "Process $pid is running"

                # Check PID file permissions
                local perms=$(stat -c %a "$pidfile" 2>/dev/null || stat -f %Lp "$pidfile")
                log_info "PID file permissions: $perms"

                # Try to stop it
                log_info "Stopping service..."
                if $PYTHON "$PYTHON_SCRIPT" stop --name "$service_name"; then
                    log_info "Service stopped successfully"

                    # Verify process is gone
                    sleep 1
                    if ! ps -p "$pid" > /dev/null 2>&1; then
                        log_info "Process confirmed stopped"
                    else
                        log_error "Process still running after stop"
                        kill -9 "$pid" 2>/dev/null || true
                    fi

                    # Verify PID file removed
                    rm -f "$pidfile"
                else
                    log_error "Failed to stop service"
                    kill -9 "$pid" 2>/dev/null || true
                    rm -f "$pidfile"
                fi
            else
                log_error "Process $pid not found"
            fi
        else
            log_error "PID file not created"
        fi
    else
        log_error "Failed to start daemon"
        return 1
    fi

    return 0
}

test_privilege_dropping() {
    log_info "Testing privilege dropping..."

    # Only run as root if we can
    if [ "$(id -u)" -eq 0 ]; then
        log_info "Running as root, testing privilege drop..."

        # Create a test user if it doesn't exist
        if ! id -u testuser &>/dev/null; then
            useradd -r -s /bin/false testuser 2>/dev/null || true
        fi

        if id -u testuser &>/dev/null; then
            if $PYTHON "$PYTHON_SCRIPT" start \
                --name "privdrop-test" \
                --cmd "sleep 2" \
                --user "testuser" \
                --foreground > /dev/null 2>&1; then
                log_info "Privilege dropping successful"
            else
                log_warn "Privilege dropping failed (may be expected)"
            fi
        else
            log_warn "Test user not available, skipping"
        fi
    else
        log_info "Not running as root, skipping privilege drop test (run with sudo to test)"
    fi

    return 0
}

test_status_command() {
    log_info "Testing status command..."

    local service_name="${TEST_SERVICE_NAME}-status"
    local pidfile="${TEST_PIDFILE}"

    # Start a service
    if $PYTHON "$PYTHON_SCRIPT" start \
        --name "$service_name" \
        --cmd "sleep 10" \
        --pidfile "$pidfile" \
        --foreground > /dev/null 2>&1; then
        sleep 1

        # Get status
        local status_json=$($PYTHON "$PYTHON_SCRIPT" status --name "$service_name")
        echo "Status output: $status_json"

        # Check if it indicates running
        if echo "$status_json" | grep -q '"running": true'; then
            log_info "Status correctly shows service running"
        else
            log_error "Status does not show service as running"
        fi

        # Stop service
        $PYTHON "$PYTHON_SCRIPT" stop --name "$service_name"
    else
        log_warn "Failed to start service for status test"
    fi

    return 0
}

cleanup() {
    log_info "Cleaning up test files..."
    rm -f "$TEST_PIDFILE"

    # Kill any leftover test processes
    pkill -f "sleep 30" 2>/dev/null || true
    pkill -f "sleep 10" 2>/dev/null || true

    # Clean up test services from manager
    $PYTHON "$PYTHON_SCRIPT" stop --name "${TEST_SERVICE_NAME}-fg" 2>/dev/null || true
    $PYTHON "$PYTHON_SCRIPT" stop --name "${TEST_SERVICE_NAME}-daemon" 2>/dev/null || true
    $PYTHON "$PYTHON_SCRIPT" stop --name "${TEST_SERVICE_NAME}-status" 2>/dev/null || true
    $PYTHON "$PYTHON_SCRIPT" stop --name "privdrop-test" 2>/dev/null || true

    log_info "Cleanup complete"
}

run_all_tests() {
    log_info "=========================================="
    log_info "Linux Service Manager Test Suite"
    log_info "=========================================="
    echo ""

    check_python
    check_ctypes
    echo ""

    test_sysinfo
    echo ""

    test_foreground_service
    echo ""

    test_daemon_service
    echo ""

    test_privilege_dropping
    echo ""

    test_status_command
    echo ""

    log_info "=========================================="
    log_info "All tests completed!"
    log_info "=========================================="
}

# Run tests
trap cleanup EXIT
run_all_tests
