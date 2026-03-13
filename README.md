# Linux Service Manager

A practical Python utility that demonstrates Linux-specific features including system calls, file permissions, process management, and shell integration.

## Features Demonstrated

### 1. Direct Linux System Calls (via ctypes)
- `fork()` - Process creation
- `execvp()` / `execve()` - Program execution
- `kill()` - Signal sending
- `setsid()` - Session management
- `chdir()` - Directory changes
- `umask()` - File permission mask
- `getuid()` / `geteuid()` / `setuid()` - User ID management
- `getpid()` / `getppid()` - Process identification

### 2. File Permissions & Security
- **PID files** with correct permissions (644)
- **Umask management** for file creation
- **Privilege dropping** using `setuid`/`setgid`
- **Capability awareness** (for advanced use)

### 3. Process Management
- **Double-fork daemonization** to prevent zombie processes and terminal re-acquisition
- **PID tracking** and management
- **Signal handling** (SIGTERM, SIGKILL)
- **Auto-restart capability**
- **Process lifecycle management** (start, stop, restart, status)

### 4. Shell Integration
- **Environment variable inheritance** with enhancement
- **Configuration file management** (JSON-based persistence)
- **Command-line interface** using `argparse`
- **Logging to stderr/stdout** with configurable levels
- **Integration with systemd** (optional)

## Installation

The script is self-contained with no external dependencies beyond Python 3.6+.

```bash
# Make executable
chmod +x linux-service-manager.py

# Optional: install system-wide
sudo cp linux-service-manager.py /usr/local/bin/service-manager
sudo chmod 755 /usr/local/bin/service-manager
```

## Quick Start

### Example 1: Simple Web Server

Start a simple HTTP server as a daemon:

```bash
# Start the service
python3 linux-service-manager.py start \
    --name simple-http \
    --cmd "python3 -m http.server 8080" \
    --dir /var/www/html

# Check status
python3 linux-service-manager.py status --name simple-http

# Stop the service
python3 linux-service-manager.py stop --name simple-http
```

### Example 2: Custom User & Environment

Run a service as a non-root user with custom environment:

```bash
python3 linux-service-manager.py start \
    --name myapp \
    --cmd "/opt/myapp/bin/server --config /etc/myapp/config.yaml" \
    --user appuser \
    --env "CONFIG_PATH=/etc/myapp" \
    --env "LOG_LEVEL=info" \
    --restart
```

### Example 3: Foreground Debugging

Run in foreground to see output (useful during development):

```bash
python3 linux-service-manager.py start \
    --name debug-service \
    --cmd "tail -f /var/log/syslog" \
    --foreground
```

Press Ctrl+C to stop.

### Example 4: Install as systemd Service

Once your service is configured, install it as a native systemd unit:

```bash
# First, configure the service normally
python3 linux-service-manager.py start \
    --name myservice \
    --cmd "/usr/bin/myserver" \
    --user www-data

# Install systemd unit
sudo python3 linux-service-manager.py install --name myservice --desc "My Web Server"

# Enable and start with systemd
sudo systemctl daemon-reload
sudo systemctl enable --now myservice
sudo systemctl status myservice
```

After installing as systemd, you can manage it with regular `systemctl` commands, and the service manager's configuration becomes a fallback.

## Command Reference

| Command | Description |
|---------|-------------|
| `start --name NAME --cmd COMMAND` | Start a service as a daemon |
| `start --name NAME --cmd COMMAND --foreground` | Run in foreground (no daemonize) |
| `stop --name NAME` | Stop a running service |
| `restart --name NAME` | Restart a service |
| `status --name NAME` | Show service status (JSON output) |
| `run --name NAME` | Run service in foreground (requires pre-configured service) |
| `install --name NAME [--desc DESCRIPTION]` | Create systemd unit file |
| `list` | List all managed services |
| `sysinfo` | Display Linux system call information |

## Options (for start command)

- `--name NAME` - Service name (required)
- `--cmd COMMAND` - Shell command to execute (required)
- `--user USER` - Run as specified user (requires appropriate privileges)
- `--dir PATH` - Working directory (default: current directory)
- `--env KEY=VALUE` - Environment variable (can be used multiple times)
- `--restart` - Enable auto-restart on failure (requires systemd for full support)
- `--pidfile PATH` - Custom PID file location (default: `/var/run/NAME.pid`)
- `--foreground` - Run in foreground (no daemonization)

## Understanding Daemonization

This script implements the **double-fork daemon pattern**, which is the proper way to create daemons in Unix/Linux:

```
Parent Process
    |
    | fork() - First fork
    v
Child 1 - becomes session leader (setsid)
    |
    | fork() - Second fork
    v
Grandchild - The actual daemon (looses session leadership)
```

Why double-fork?
- First fork allows parent to exit, preventing zombie
- `setsid()` creates new session, detaches from terminal
- Second fork ensures daemon can't reacquire a controlling terminal

This is the standard pattern used by many daemons (Apache, SSH daemon, etc.).

## Linux Permissions & Security

### PID Files
PID files are created with mode `644` (`-rw-r--r--`), allowing all users to read but only the owner to write. This is standard practice for PID files in `/var/run`.

### Umask
The daemon sets `umask(0)` to ensure files are created with explicit permissions only. After forking, files will be created with `0666 & ~umask`, i.e., `0666` (rw-rw-rw-) meaning the programmer explicitly sets permissions on files created.

### Privilege Dropping
Services started with `--user` will drop privileges after forking using `setuid()` and `setgid()`. The sequence is important:
1. Set GID first (required by Linux)
2. Set UID
3. Verify effective IDs match desired user

**Note:** The script must be run as root to successfully drop privileges to another user. If not root, privilege dropping will fail but the service will still run.

## Signal Handling

Services receive signals in this order on graceful shutdown:
- `SIGTERM` (15) - Graceful termination request, process can clean up
- `SIGKILL` (9) - Force kill if process doesn't exit after 5 seconds

## Files & Directories

```
~/.local/share/service-manager/
├── services.json              # Service definitions
└── <service-name>.conf        # Individual service configs

/var/run/<service-name>.pid    # PID files (created at runtime)
```

## Troubleshooting

### "Permission denied" when starting service
- Check if PID file directory is writable (`/var/run/` usually requires root)
- Use custom `--pidfile` to write to user-writable location

### Service starts but immediately exits
- Check logs using `journalctl` if running as systemd
- For manual mode, run with `--foreground` to see output
- Ensure command is executable and paths are correct

### Cannot drop privileges
- Must run as root to drop to another user
- Check that the specified user exists (`id <user>`)

### "Address already in use"
- Another process using the same port
- Check PID file if stale: `cat /var/run/<name>.pid` and `ps -p <pid>`
- Stop the other service or change ports

## Advanced: Using System Calls Directly

The `sysinfo` command shows information gathered via direct system calls:

```bash
$ python3 linux-service-manager.py sysinfo
{
  "pid": 12345,
  "ppid": 6789,
  "uid": 1000,
  "euid": 1000,
  "umask": "0o22",
  "cwd": "/home/user"
}
```

This demonstrates reading process state directly from the kernel via syscalls.

## Learning Resources

The code is heavily commented. Key functions to study:

- `ServiceManager.start_service()` - Full daemonization process
- `ServiceManager._set_process_privileges()` - Privilege dropping
- `LinuxSystemCalls` class - Syscall wrappers using ctypes
- `ServiceManager._demonstrate_syscalls()` - Reading system state

## License

MIT - Feel free to modify and use for learning.

## Security Considerations

- This utility can run arbitrary commands as root if started with sudo
- PID files are owned by the user who started the service
- Environment variables are passed to child processes (security risk if they contain secrets)
- Always validate and sanitize service configurations from untrusted sources

## Testing

You can test the daemonization with a simple sleep command:

```bash
# Start a test service
python3 linux-service-manager.py start \
    --name test-daemon \
    --cmd "sleep 300" \
    --foreground  # Remove --foreground to daemonize

# In another terminal, check it's running
ps aux | grep test-daemon

# Check PID file
cat /var/run/test-daemon.pid

# Stop it
python3 linux-service-manager.py stop --name test-daemon
```

## Comparison to systemd

While this script demonstrates how daemons work, in production you should use `systemd`:
- Better logging with journald
- Automatic restart policies
- Dependency management
- Resource control (cgroups)
- Security features (Capabilities, PrivateTmp, etc.)

However, understanding daemonization is crucial for debugging, writing portable code, and understanding what systemd does under the hood.

## Contributing

This is a learning tool. Feel free to enhance it with:
- Socket activation (like systemd)
- More syscalls (getrlimit, prlimit, etc.)
- Capability management (libcap)
- Namespace isolation (unshare)
- Resource limits and control groups
