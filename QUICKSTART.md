# Quick Start Guide

## What You Have

A complete Linux service manager utility that demonstrates:

1. **Linux System Calls** - Direct kernel interface via ctypes
2. **Process Management** - Proper daemonization (double-fork)
3. **File Permissions** - PID files, umask, secure defaults
4. **Security** - Privilege dropping (setuid/setgid)
5. **Shell Integration** - Environment variables, config files
6. **Signal Handling** - Graceful shutdown (SIGTERM → SIGKILL)

## Files in This Package

```
├── linux-service-manager.py   # Main script (297KB, 800+ lines)
├── README.md                  # Full documentation
├── QUICKSTART.md             # This file
├── Makefile                  # Build/install shortcuts
├── demo.sh                   # Demonstration script
├── test-service-manager.sh   # Test suite
└── examples/
    └── sample-webserver.conf # Example configuration
```

## 5-Minute Test

```bash
# 1. Run the demo
./demo.sh

# 2. Try starting a service
python3 linux-service-manager.py start --name mytest --cmd "date; sleep 2; date"

# 3. Check status
python3 linux-service-manager.py status --name mytest

# 4. Stop it
python3 linux-service-manager.py stop --name mytest
```

## Key Features to Explore

### 1. System Calls
```bash
python3 linux-service-manager.py sysinfo
```
Shows: PID, PPID, UID, EUID, umask, cwd - all retrieved via direct syscalls.

### 2. Daemonization
The script implements the **double-fork daemon pattern**:
- First fork creates child
- Child calls `setsid()` to become session leader (detach from terminal)
- Second fork ensures daemon can't reacquire controlling terminal
- Result: proper background daemon

See: `ServiceManager.start_service()` lines 238-335

### 3. Privilege Dropping
If started as root, use `--user` to drop privileges:
```bash
sudo python3 linux-service-manager.py start --name web --user www-data --cmd "python3 -m http.server 8080"
```
Demonstrates: `setgid()` then `setuid()` sequence (Linux requirement)

### 4. PID File Management
PID files written with `644` permissions (rw-r--r--). Stored at:
- Default: `/var/run/<name>.pid`
- Custom: `--pidfile /path/to/file`

### 5. Signal Handling
Services receive:
1. `SIGTERM` (15) - Graceful shutdown request
2. Wait up to 5 seconds
3. `SIGKILL` (9) if still running

See: `ServiceManager.stop_service()` lines 382-428

### 6. Environment Control
Pass custom environment variables:
```bash
python3 linux-service-manager.py start \
  --name myservice \
  --cmd "myapp" \
  --env "LOG_LEVEL=debug" \
  --env "CONFIG=/etc/myapp.yaml"
```

The script adds:
- `SERVICE_NAME` - The service name
- `STARTED_AT` - ISO 8601 timestamp

### 7. systemd Integration
Can generate native systemd unit files:
```bash
sudo python3 linux-service-manager.py install --name myservice --desc "My App"
sudo systemctl daemon-reload
sudo systemctl enable --now myservice
```

## Learning Path

If you want to learn from this code:

1. **Start with the CLI** (`main()` function, line 596)
   - See argparse setup
   - Understand the command structure

2. **Service Class** (line 128)
   - Simple data structure
   - Serialization/deserialization
   - Good example of Python data classes

3. **SystemCalls Wrapper** (line 47)
   - ctypes usage
   - Function prototypes
   - Error handling with errno

4. **Daemonization** (`start_service`, line 238)
   - Fork sequence
   - Session management
   - File descriptor handling
   - Privilege dropping

5. **Status & PID Management** (line 356)
   - Reading/writing PID files
   - Process checking via `kill(pid, 0)`
   - JSON serialization

6. **Systemd Integration** (line 468)
   - Unit file generation
   - Integration with init system

## Common Use Cases

### Run a Python script as daemon
```bash
python3 linux-service-manager.py start \
  --name scraper \
  --cmd "python3 /opt/scraper/main.py" \
  --user scraper \
  --restart
```

### Development server
```bash
python3 linux-service-manager.py start \
  --name dev-api \
  --cmd "uvicorn api:app --reload --host 0.0.0.0 --port 8000" \
  --foreground  # See output in real-time
```

### Scheduled task (simplified cron replacement)
```bash
# Create wrapper script
cat > /usr/local/bin/task-wrapper.sh <<'EOF'
#!/bin/bash
/usr/bin/linux-service-manager.py start --name periodic-task --cmd "/opt/tasks/run.sh"
/usr/bin/linux-service-manager.py stop --name periodic-task
EOF
chmod +x /usr/local/bin/task-wrapper.sh

# Add to crontab
# 0 2 * * * /usr/local/bin/task-wrapper.sh
```

## Troubleshooting

### "Permission denied" on PID file
The script tries to write to `/var/run/`, which requires root. Solutions:
1. Run with `sudo`
2. Use `--pidfile /tmp/myservice.pid`
3. Use `~/.local/run/` directory (modify code)

### Service starts but immediately exits
- Check the command is executable: `which <cmd>` or `ls -l <cmd>`
- Run with `--foreground` to see error output
- Check logs: `journalctl -u <name>` if installed as systemd

### Can't drop privileges
- Must be root to drop to another user
- Verify user exists: `id <username>`
- Check `/etc/passwd` for UID/GID

### "Address already in use"
Another process on that port:
```bash
sudo lsof -i :8080
# or
sudo netstat -tulpn | grep 8080
```

Kill or change port. Check for stale PID files.

## Comparing to systemd

| Feature | systemd | This Script |
|---------|---------|-------------|
| Logging | journald (excellent) | stderr only |
| Auto-restart | ✓ (configurable) | Basic |
| Dependencies | ✓ | ✗ |
| Resource control | ✓ (cgroups) | ✗ |
| Socket activation | ✓ | ✗ |
| Timers | ✓ | ✗ |
| Learning value | Low (magic) | High (shows how) |
| Simplicity | Complex | Simple (1 file) |

**Use case for this script:**
- Learning how daemons work
- Simple single-machine services
- When you don't want systemd overhead
- Educational purposes

**Use systemd for:**
- Production servers
- Multi-service dependencies
- Complex configurations
- Standard compliance

## Next Steps

1. Read the full README.md for detailed documentation
2. Run the test suite: `make test` or `./test-service-manager.sh`
3. Try creating your own service configuration
4. Study the code - focus on one section at a time
5. Experiment: Add features (logging to file, config validation, etc.)

## Questions?

The code is heavily commented. Each function explains:
- What it does
- Why it's done this way
- Linux-specific details
- Security considerations

Search for `###` in the code for section headers.

---

**Remember:** This is a learning tool. In production, use systemd. But understanding what's under the hood makes you a better sysadmin and developer.
