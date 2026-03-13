#!/usr/bin/env python3
"""
Linux Service Manager - A practical utility demonstrating Linux-specific features

This script demonstrates:
- Direct Linux system calls via ctypes (fork, exec, kill, etc.)
- File permissions, setuid, and capabilities
- Process management (daemonization, PID files, signal handling)
- Shell integration (environment variables, config files)
- Resource limits and privilege management

Usage:
    python3 linux-service-manager.py <command> [options]

Commands:
    start      Start a service in the background
    stop       Stop a running service
    restart    Restart a service
    status     Check service status
    install    Install as systemd service (optional)
    run        Run service in foreground (for testing)

Example:
    # Start a simple web server as a daemon
    python3 linux-service-manager.py start --name webserver --cmd "python3 -m http.server 8080" --user www-data

    # Check status
    python3 linux-service-manager.py status --name webserver

Author: Linux Service Manager
License: MIT
"""

import os
import sys
import json
import time
import signal
import socket
import logging
import subprocess
import configparser
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Linux-specific imports
try:
    import ctypes
    import ctypes.util
    LIBRARIES_AVAILABLE = True
except ImportError:
    LIBRARIES_AVAILABLE = False
    print("Warning: ctypes not available, some features disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('linux-service-manager')


class LinuxSystemCalls:
    """Wrapper for direct Linux system calls using ctypes"""

    def __init__(self):
        if not LIBRARIES_AVAILABLE:
            raise RuntimeError("ctypes not available")

        # Load standard C library
        self.libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)

        # Define system call signatures
        self._setup_syscalls()

    def _setup_syscalls(self):
        """Define system call function prototypes"""
        # fork() - creates a new process
        self.libc.fork.restype = ctypes.c_int
        self.libc.fork.argtypes = []

        # execvp() - execute program
        self.libc.execvp.restype = ctypes.c_int
        self.libc.execvp.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p)]

        # kill() - send signal to process
        self.libc.kill.restype = ctypes.c_int
        self.libc.kill.argtypes = [ctypes.c_int, ctypes.c_int]

        # getpid() - get process ID
        self.libc.getpid.restype = ctypes.c_int
        self.libc.getpid.argtypes = []

        # getppid() - get parent process ID
        self.libc.getppid.restype = ctypes.c_int
        self.libc.getppid.argtypes = []

        # setsid() - create new session
        self.libc.setsid.restype = ctypes.c_int
        self.libc.setsid.argtypes = []

        # chdir() - change directory
        self.libc.chdir.restype = ctypes.c_int
        self.libc.chdir.argtypes = [ctypes.c_char_p]

        # umask() - set file mode creation mask
        self.libc.umask.restype = ctypes.c_int
        self.libc.umask.argtypes = [ctypes.c_int]

        # getuid() - get real user ID
        self.libc.getuid.restype = ctypes.c_int
        self.libc.getuid.argtypes = []

        # geteuid() - get effective user ID
        self.libc.geteuid.restype = ctypes.c_int
        self.libc.geteuid.argtypes = []

        # setuid() - set user ID (use c_int for uid_t)
        self.libc.setuid.restype = ctypes.c_int
        self.libc.setuid.argtypes = [ctypes.c_int]

    def fork(self) -> int:
        """Wrapper for fork() system call"""
        pid = self.libc.fork()
        if pid == -1:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno))
        return pid

    def execvp(self, file: str, args: List[str]) -> None:
        """Wrapper for execvp() system call"""
        argv = [arg.encode('utf-8') for arg in args]
        argv_array = (ctypes.c_char_p * len(argv))(*argv)
        result = self.libc.execvp(file.encode('utf-8'), argv_array)
        if result == -1:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno))

    def kill(self, pid: int, sig: int) -> None:
        """Wrapper for kill() system call"""
        result = self.libc.kill(pid, sig)
        if result == -1:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno))

    def getpid(self) -> int:
        """Get current process ID"""
        return self.libc.getpid()

    def getppid(self) -> int:
        """Get parent process ID"""
        return self.libc.getppid()

    def setsid(self) -> int:
        """Create new session and set process group ID"""
        result = self.libc.setsid()
        if result == -1:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno))
        return result

    def chdir(self, path: str) -> None:
        """Change working directory"""
        result = self.libc.chdir(path.encode('utf-8'))
        if result == -1:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno))

    def umask(self, mask: int) -> int:
        """Set and get file mode creation mask"""
        return self.libc.umask(mask)

    def getuid(self) -> int:
        """Get real user ID"""
        return self.libc.getuid()

    def geteuid(self) -> int:
        """Get effective user ID"""
        return self.libc.geteuid()

    def setuid(self, uid: int) -> int:
        """Set user ID (requires root)"""
        result = self.libc.setuid(uid)
        if result == -1:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno))
        return result


class Service:
    """Represents a managed service"""

    def __init__(self, name: str, command: str, user: str = None,
                 working_dir: str = None, environment: Dict[str, str] = None,
                 auto_restart: bool = False, pidfile: str = None):
        self.name = name
        self.command = command
        self.user = user
        self.working_dir = working_dir or os.getcwd()
        self.environment = environment or {}
        self.auto_restart = auto_restart
        self.pidfile = pidfile or f"/var/run/{name}.pid"
        self.pid = None
        self.start_time = None
        self.process = None

    def to_dict(self) -> Dict:
        """Serialize service configuration to dictionary"""
        return {
            'name': self.name,
            'command': self.command,
            'user': self.user,
            'working_dir': self.working_dir,
            'environment': self.environment,
            'auto_restart': self.auto_restart,
            'pidfile': self.pidfile,
            'pid': self.pid,
            'start_time': self.start_time.isoformat() if self.start_time else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Service':
        """Deserialize service configuration from dictionary"""
        service = cls(
            name=data['name'],
            command=data['command'],
            user=data.get('user'),
            working_dir=data.get('working_dir'),
            environment=data.get('environment', {}),
            auto_restart=data.get('auto_restart', False),
            pidfile=data.get('pidfile')
        )
        service.pid = data.get('pid')
        if data.get('start_time'):
            service.start_time = datetime.fromisoformat(data['start_time'])
        return service


class ServiceManager:
    """Manages Linux services with system call demonstrations"""

    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.path.expanduser('~/.local/share/service-manager'))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.services_file = self.config_dir / 'services.json'
        self.services: Dict[str, Service] = {}
        self.syscalls = None

        # Load services from disk
        self._load_services()

        # Initialize syscalls if available
        if LIBRARIES_AVAILABLE:
            try:
                self.syscalls = LinuxSystemCalls()
                logger.debug("Linux system calls initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize system calls: {e}")

    def _load_services(self):
        """Load service definitions from disk"""
        if self.services_file.exists():
            try:
                with open(self.services_file, 'r') as f:
                    data = json.load(f)
                    for name, service_data in data.items():
                        self.services[name] = Service.from_dict(service_data)
                logger.info(f"Loaded {len(self.services)} services")
            except Exception as e:
                logger.error(f"Failed to load services: {e}")

    def _save_services(self):
        """Save service definitions to disk"""
        try:
            data = {name: service.to_dict() for name, service in self.services.items()}
            with open(self.services_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save services: {e}")

    def _write_pidfile(self, service: Service):
        """Write PID to file with proper permissions (644)"""
        try:
            with open(service.pidfile, 'w') as f:
                f.write(str(service.pid))
            # Set permissions: -rw-r--r--
            os.chmod(service.pidfile, 0o644)
            logger.debug(f"PID file written: {service.pidfile}")
        except Exception as e:
            logger.error(f"Failed to write PID file: {e}")

    def _read_pidfile(self, service: Service) -> Optional[int]:
        """Read PID from file"""
        try:
            if os.path.exists(service.pidfile):
                with open(service.pidfile, 'r') as f:
                    return int(f.read().strip())
        except Exception:
            pass
        return None

    def _remove_pidfile(self, service: Service):
        """Remove PID file"""
        try:
            if os.path.exists(service.pidfile):
                os.remove(service.pidfile)
        except Exception as e:
            logger.error(f"Failed to remove PID file: {e}")

    def _check_pid(self, pid: int) -> bool:
        """Check if a process with given PID exists"""
        try:
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks
            return True
        except OSError:
            return False

    def _set_process_privileges(self, user: str) -> bool:
        """Drop privileges by setting uid/gid (demonstrates setuid)"""
        try:
            import pwd
            # Get user info
            user_info = pwd.getpwnam(user)
            uid = user_info.pw_uid
            gid = user_info.pw_gid

            # Set group first (required before setuid)
            try:
                os.setgid(gid)
            except PermissionError:
                logger.warning(f"Not permitted to set gid to {gid}")

            # Set user ID
            try:
                os.setuid(uid)
            except PermissionError:
                logger.warning(f"Not permitted to set uid to {uid}")
                return False

            # Verify effective ID
            if os.geteuid() == uid and os.getegid() == gid:
                logger.info(f"Dropped privileges to user {user} (uid={uid})")
                return True
            else:
                logger.warning(f"Failed to drop privileges: still uid={os.getuid()}, euid={os.geteuid()}")
                return False
        except KeyError:
            logger.error(f"User '{user}' not found")
            return False
        except Exception as e:
            logger.error(f"Error setting privileges: {e}")
            return False

    def _setup_environment(self, env_vars: Dict[str, str]) -> Dict[str, str]:
        """Setup environment for service process"""
        env = os.environ.copy()
        env.update(env_vars)
        # Add service-specific variables
        env['SERVICE_NAME'] = self.services.get('name', 'unknown')
        env['STARTED_AT'] = datetime.now().isoformat()
        return env

    def _demonstrate_syscalls(self) -> Dict[str, any]:
        """Demonstrate various Linux system calls"""
        if not self.syscalls:
            return {"error": "System calls not available"}

        results = {}

        try:
            # Get process info
            results['pid'] = self.syscalls.getpid()
            results['ppid'] = self.syscalls.getppid()
            results['uid'] = self.syscalls.getuid()
            results['euid'] = self.syscalls.geteuid()

            # Get current umask
            old_umask = self.syscalls.umask(0)
            self.syscalls.umask(old_umask)
            results['umask'] = oct(old_umask)

            # Get current working directory
            cwd_buf = ctypes.create_string_buffer(1024)
            self.syscalls.libc.getcwd(cwd_buf, 1024)
            results['cwd'] = cwd_buf.value.decode('utf-8')

        except Exception as e:
            results['error'] = str(e)

        return results

    def start_service(self, service: Service, foreground: bool = False) -> bool:
        """
        Start a service with full daemonization process

        Demonstrates:
        - fork() to create child process
        - setsid() to create new session
        - Second fork to prevent reacquisition of controlling terminal
        - chdir("/") to avoid blocking mounts
        - umask(0) to set permissions
        - Drop privileges with setuid
        - Write PID file
        - Signal handling
        """
        logger.info(f"Starting service: {service.name}")

        # Check if already running
        existing_pid = self._read_pidfile(service)
        if existing_pid and self._check_pid(existing_pid):
            logger.warning(f"Service {service.name} already running (PID {existing_pid})")
            return False

        try:
            if foreground:
                # Run in foreground (no daemonization)
                logger.info(f"Running {service.name} in foreground")
                env = self._setup_environment(service.environment)

                # Use subprocess for foreground
                process = subprocess.Popen(
                    service.command,
                    shell=True,
                    env=env,
                    cwd=service.working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True  # Creates new session
                )

                service.pid = process.pid
                service.start_time = datetime.now()
                self._write_pidfile(service)
                self._save_services()

                # Monitor process
                try:
                    stdout, stderr = process.communicate()
                    if stdout:
                        print(stdout.decode())
                    if stderr:
                        print(stderr.decode(), file=sys.stderr)
                except KeyboardInterrupt:
                    logger.info("Interrupted, stopping service")
                    process.terminate()
                    process.wait()
                return True

            # DAEMONIZATION PROCESS (the double-fork)

            # First fork
            logger.debug("First fork()")
            pid = os.fork()
            if pid > 0:
                # Parent exits
                logger.debug(f"Parent exiting, child PID: {pid}")
                return True

            # Child continues
            os.setsid()  # Become session leader

            # Second fork - prevents reacquisition of controlling terminal
            logger.debug("Second fork()")
            pid2 = os.fork()
            if pid2 > 0:
                # First child exits
                logger.debug(f"First child exiting, grandchild PID: {pid2}")
                os._exit(0)

            # Grandchild is the daemon
            daemon_pid = os.getpid()
            logger.info(f"Daemon started with PID {daemon_pid}")

            # Change to working directory (or /)
            try:
                os.chdir(service.working_dir)
            except Exception as e:
                logger.warning(f"Cannot change to {service.working_dir}: {e}, using /tmp")
                os.chdir('/tmp')

            # Reset file mode creation mask
            os.umask(0)

            # Close all inherited file descriptors
            sys.stdout.flush()
            sys.stderr.flush()

            # Redirect stdin, stdout, stderr to /dev/null or log file
            devnull = os.open(os.devnull, os.O_RDWR)
            os.dup2(devnull, 0)  # stdin
            os.dup2(devnull, 1)  # stdout
            os.dup2(devnull, 2)  # stderr
            os.close(devnull)

            # Drop privileges if requested (demonstrates setuid)
            if service.user:
                if not self._set_process_privileges(service.user):
                    logger.warning(f"Failed to drop privileges to {service.user}")

            # Prepare environment
            env = self._setup_environment(service.environment)

            # Write PID file
            service.pid = daemon_pid
            service.start_time = datetime.now()
            self._write_pidfile(service)
            self._save_services()

            # Execute the service command
            logger.info(f"Executing: {service.command}")
            try:
                os.execve(
                    '/bin/sh',
                    ['/bin/sh', '-c', service.command],
                    env
                )
            except OSError as e:
                logger.error(f"Failed to exec: {e}")
                self._remove_pidfile(service)
                os._exit(1)

        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            import traceback
            traceback.print_exc()
            return False

        return True

    def stop_service(self, service_name: str) -> bool:
        """Stop a running service"""
        logger.info(f"Stopping service: {service_name}")

        if service_name not in self.services:
            logger.error(f"Service not found: {service_name}")
            return False

        service = self.services[service_name]

        # Get PID from file or memory
        pid = service.pid or self._read_pidfile(service)

        if not pid:
            logger.warning(f"No PID found for service {service_name}")
            self._remove_pidfile(service)
            return True

        if not self._check_pid(pid):
            logger.warning(f"Process {pid} not running")
            self._remove_pidfile(service)
            return True

        try:
            # Send SIGTERM first (graceful shutdown)
            logger.info(f"Sending SIGTERM to PID {pid}")
            if self.syscalls:
                self.syscalls.kill(pid, signal.SIGTERM)
            else:
                os.kill(pid, signal.SIGTERM)

            # Wait for process to exit
            for i in range(10):
                if not self._check_pid(pid):
                    logger.info(f"Service {service_name} stopped")
                    self._remove_pidfile(service)
                    return True
                time.sleep(0.5)

            # If still running, send SIGKILL
            logger.warning(f"Service {service_name} not responding, sending SIGKILL")
            if self.syscalls:
                self.syscalls.kill(pid, signal.SIGKILL)
            else:
                os.kill(pid, signal.SIGKILL)

            time.sleep(0.5)
            if not self._check_pid(pid):
                logger.info(f"Service {service_name} killed")
                self._remove_pidfile(service)
                return True
            else:
                logger.error(f"Failed to stop service {service_name}")
                return False

        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            return False

    def status_service(self, service_name: str) -> Dict:
        """Get status of a service"""
        result = {
            'name': service_name,
            'running': False,
            'pid': None,
            'uptime': None,
            'user': None,
            'start_time': None
        }

        if service_name not in self.services:
            result['status'] = 'not found'
            return result

        service = self.services[service_name]
        pid = service.pid or self._read_pidfile(service)

        if pid and self._check_pid(pid):
            result['running'] = True
            result['pid'] = pid
            result['user'] = service.user
            if service.start_time:
                result['start_time'] = service.start_time.isoformat()
                uptime = datetime.now() - service.start_time
                result['uptime'] = str(uptime).split('.')[0]  # Remove microseconds
        else:
            result['status'] = 'stopped'

        return result

    def install_systemd_service(self, service: Service, description: str = None):
        """
        Install as a systemd service unit

        This demonstrates creating Linux service configuration files
        """
        if not os.access('/etc/systemd/system', os.W_OK):
            logger.error("Cannot write to /etc/systemd/system (need root)")
            return False

        unit_content = f"""[Unit]
Description={description or service.name}
After=network.target

[Service]
Type=forking
PIDFile={service.pidfile}
ExecStart={sys.executable} {os.path.abspath(__file__)} run --name {service.name}
ExecStop={sys.executable} {os.path.abspath(__file__)} stop --name {service.name}
Restart={ 'always' if service.auto_restart else 'no' }
User={service.user if service.user else 'root'}
WorkingDirectory={service.working_dir}
Environment={','.join([f'{k}={v}' for k, v in service.environment.items()])}

[Install]
WantedBy=multi-user.target
"""

        unit_file = Path(f'/etc/systemd/system/{service.name}.service')
        try:
            with open(unit_file, 'w') as f:
                f.write(unit_content)
            logger.info(f"Created systemd unit: {unit_file}")
            logger.info("Run: systemctl daemon-reload && systemctl enable --now " + service.name)
            return True
        except Exception as e:
            logger.error(f"Failed to create systemd unit: {e}")
            return False

    def add_service(self, service: Service) -> bool:
        """Add a service to management"""
        if service.name in self.services:
            logger.error(f"Service {service.name} already exists")
            return False
        self.services[service.name] = service
        self._save_services()
        logger.info(f"Added service: {service.name}")
        return True

    def remove_service(self, service_name: str) -> bool:
        """Remove a service from management"""
        if service_name not in self.services:
            logger.error(f"Service not found: {service_name}")
            return False

        # Stop if running
        self.stop_service(service_name)

        # Remove from configuration
        del self.services[service_name]
        self._save_services()

        # Remove config file
        config_file = self.config_dir / f'{service_name}.conf'
        if config_file.exists():
            config_file.unlink()

        logger.info(f"Removed service: {service_name}")
        return True


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Linux Service Manager - demonstrates system calls and process management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start a service')
    start_parser.add_argument('--name', required=True, help='Service name')
    start_parser.add_argument('--cmd', required=True, help='Command to execute')
    start_parser.add_argument('--user', help='User to run as')
    start_parser.add_argument('--dir', help='Working directory')
    start_parser.add_argument('--env', action='append', help='Environment variable KEY=VALUE')
    start_parser.add_argument('--restart', action='store_true', help='Auto-restart on failure')
    start_parser.add_argument('--pidfile', help='PID file path')
    start_parser.add_argument('--foreground', action='store_true', help='Run in foreground (no daemonize)')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop a service')
    stop_parser.add_argument('--name', required=True, help='Service name')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show service status')
    status_parser.add_argument('--name', required=True, help='Service name')

    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart a service')
    restart_parser.add_argument('--name', required=True, help='Service name')

    # Run command (foreground for testing)
    run_parser = subparsers.add_parser('run', help='Run service in foreground')
    run_parser.add_argument('--name', required=True, help='Service name')

    # Install systemd command
    install_parser = subparsers.add_parser('install', help='Install as systemd service')
    install_parser.add_argument('--name', required=True, help='Service name')
    install_parser.add_argument('--desc', help='Service description')

    # List command
    list_parser = subparsers.add_parser('list', help='List all managed services')

    # Sysinfo command - demonstrate system calls
    info_parser = subparsers.add_parser('sysinfo', help='Show system call information')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    manager = ServiceManager()

    try:
        if args.command == 'start':
            # Parse environment variables
            env_vars = {}
            if args.env:
                for env_str in args.env:
                    key, value = env_str.split('=', 1)
                    env_vars[key] = value

            service = Service(
                name=args.name,
                command=args.cmd,
                user=args.user,
                working_dir=args.dir,
                environment=env_vars,
                auto_restart=args.restart,
                pidfile=args.pidfile
            )

            # Add to manager if not exists
            if args.name not in manager.services:
                manager.add_service(service)
            else:
                service = manager.services[args.name]

            success = manager.start_service(service, foreground=args.foreground)
            return 0 if success else 1

        elif args.command == 'stop':
            success = manager.stop_service(args.name)
            return 0 if success else 1

        elif args.command == 'status':
            status = manager.status_service(args.name)
            print(json.dumps(status, indent=2))
            return 0

        elif args.command == 'restart':
            manager.stop_service(args.name)
            time.sleep(1)
            if args.name in manager.services:
                success = manager.start_service(manager.services[args.name])
                return 0 if success else 1
            return 1

        elif args.command == 'run':
            if args.name not in manager.services:
                logger.error(f"Service {args.name} not found")
                return 1
            service = manager.services[args.name]
            success = manager.start_service(service, foreground=True)
            return 0 if success else 1

        elif args.command == 'install':
            if args.name not in manager.services:
                logger.error(f"Service {args.name} not found. Add it first with 'start'")
                return 1
            success = manager.install_systemd_service(manager.services[args.name], args.desc)
            return 0 if success else 1

        elif args.command == 'list':
            if manager.services:
                print("Managed Services:")
                for name, service in manager.services.items():
                    status = manager.status_service(name)
                    print(f"  {name}:")
                    print(f"    Command: {service.command}")
                    print(f"    User: {service.user or '(current)'}")
                    print(f"    Running: {status.get('running', False)}")
                    if status.get('pid'):
                        print(f"    PID: {status['pid']}")
                        print(f"    Uptime: {status.get('uptime', 'N/A')}")
                    print()
            else:
                print("No services configured")
            return 0

        elif args.command == 'sysinfo':
            if not manager.syscalls:
                print("System calls not available (ctypes missing)")
                return 1

            info = manager._demonstrate_syscalls()
            print("Linux System Call Information:")
            print(json.dumps(info, indent=2))
            return 0

    except KeyboardInterrupt:
        print("\nInterrupted")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
