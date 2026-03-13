#!/bin/bash
#
# Demonstration script for Linux Service Manager
# Shows off various Linux-specific features
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/linux-service-manager.py"

echo "=========================================="
echo "Linux Service Manager Demonstration"
echo "=========================================="
echo ""

echo "1. Demonstrating direct system calls..."
echo "----------------------------------------"
python3 "$PYTHON" sysinfo
echo ""

echo "2. Listing available commands..."
echo "----------------------------------------"
python3 "$PYTHON" --help
echo ""

echo "3. Starting a simple foreground service..."
echo "----------------------------------------"
echo "   (This will run for 3 seconds, showing real-time output)"
timeout 5s python3 "$PYTHON" start --name demo-foreground --cmd "echo 'Hello from daemon!'; sleep 1; echo 'Still running...'; sleep 1; echo 'Done!'" --foreground 2>&1 || true
echo ""

echo "4. Demonstrating daemonization (background service)..."
echo "----------------------------------------"
echo "   Starting service..."
python3 "$PYTHON" start --name demo-daemon --cmd "sleep 10" 2>&1
sleep 1

echo "   Checking PID file..."
if [ -f "/var/run/demo-daemon.pid" ]; then
    echo "   ✓ PID file exists at /var/run/demo-daemon.pid"
    echo "   Contents: $(cat /var/run/demo-daemon.pid)"
    echo "   Permissions: $(ls -l /var/run/demo-daemon.pid | awk '{print $1}')"
else
    echo "   ✗ PID file not found (maybe permission issue?)"
fi

echo ""
echo "   Checking process..."
PID=$(cat /var/run/demo-daemon.pid 2>/dev/null || echo "")
if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
    echo "   ✓ Process $PID is running"
    echo "   Process details:"
    ps -p "$PID" -o pid,ppid,user,cmd
else
    echo "   ✗ Process not found"
fi

echo ""
echo "   Checking status..."
python3 "$PYTHON" status --name demo-daemon
echo ""

echo "   Stopping service..."
python3 "$PYTHON" stop --name demo-daemon
echo ""

echo "5. Demonstrating privilege dropping (requires root)..."
echo "----------------------------------------"
if [ "$(id -u)" -eq 0 ]; then
    echo "   Running as root - privilege dropping is available"
    echo "   (Use --user option to drop to non-root user)"
    echo "   Example: python3 $PYTHON start --name service --user nobody --cmd '...'"
else
    echo "   Not running as root - privilege dropping limited"
    echo "   (Run this script with sudo to test)"
fi
echo ""

echo "6. Demonstrating environment variable handling..."
echo "----------------------------------------"
echo "   Starting service with custom environment..."
python3 "$PYTHON" start --name demo-env --cmd "env | grep -E '^(SERVICE_NAME|STARTED_AT|CUSTOM_VAR)='" \
    --env "CUSTOM_VAR=HelloWorld" \
    --foreground 2>&1 || true
echo ""

echo "7. Listing all services..."
echo "----------------------------------------"
python3 "$PYTHON" list
echo ""

echo "=========================================="
echo "Demonstration Complete!"
echo "=========================================="
echo ""
echo "Key Linux features demonstrated:"
echo "  ✓ System calls (fork, exec, getpid, kill, setsid, etc.)"
echo "  ✓ Double-fork daemonization pattern"
echo "  ✓ PID file management with proper permissions (644)"
echo "  ✓ Signal handling (SIGTERM, SIGKILL)"
echo "  ✓ Privilege dropping (setuid/setgid)"
echo "  ✓ Process lifecycle management"
echo "  ✓ Environment variable control"
echo "  ✓ Configuration persistence (JSON)"
echo ""
echo "Try these commands:"
echo "  python3 linux-service-manager.py start --name myservice --cmd 'your-command'"
echo "  python3 linux-service-manager.py status --name myservice"
echo "  python3 linux-service-manager.py stop --name myservice"
echo "  python3 linux-service-manager.py install --name myservice   # for systemd"
echo ""
echo "See README.md for detailed documentation"
