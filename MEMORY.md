# MEMORY.md - Long-term Project Memory

_This file tracks significant decisions, learnings, and project progress._

---

## GitHub Repository Project (Started 2025-03-14)

### Goal
Create and manage an open-source repository with useful, unique, time-saving tools for developers/system administrators, with automated reporting.

### GitHub Token
- **Status:** Received from user
- **Security:** Must handle carefully, avoid logging in outputs
- **Scope:** Full account access granted
- **Constraint:** Keep private repositories untouched

### Deliverables
1. Public repository creation with:
   - Comprehensive README
   - Full documentation
   - Release notes
   - Installation instructions
   - Usage examples
2. Automation set up:
   - Reporting schedule (every 15 minutes initially)
   - Daily progress summaries
3. Ongoing maintenance plan

---

## Completed Tasks

### 2025-03-14
**Created Linux Service Manager utility:**
- Python script demonstrating Linux system calls, daemonization, process management
- 849 lines, fully functional
- Features: double-fork daemon pattern, setuid privilege dropping, PID management, signal handling, systemd integration
- Files: `linux-service-manager.py`, `README.md`, `QUICKSTART.md`, `demo.sh`, `test-service-manager.sh`, `Makefile`
- Verified working: system calls, daemonization, PID files, status/stop/restart

**Key Learnings:**
- ctypes `c_uid_t` doesn't exist on some systems, use `c_int` for uid_t
- datetime objects need explicit serialization for JSON
- Daemonization requires careful file descriptor handling
- System call wrappers need proper errno handling

---

## Current State

- Linux Service Manager READY for GitHub release
- Need to create repository and push
- Need to set up automated reporting mechanism
- User wants reports every 15 minutes initially
- "agent.py" mentioned - need to clarify what this is

---

## Next Steps

1. **Immediate:**
   - [ ] Create GitHub repository with appropriate name
   - [ ] Push Linux Service Manager code
   - [ ] Set up repository structure (docs/, scripts/, etc.)
   - [ ] Create initial release/tag
   - [ ] Verify repository is public and accessible

2. **Short-term:**
   - [ ] Create automation script for 15-minute reports
   - [ ] Set up cron job or background process
   - [ ] Test reporting mechanism
   - [ ] Create additional useful utilities to populate repo

3. **Medium-term:**
   - [ ] Establish contribution guidelines
   - [ ] Add license (MIT/Apache-2.0)
   - [ ] Create GitHub Actions for CI/testing
   - [ ] Write additional documentation

4. **Long-term:**
   - [ ] Build collection of DevOps/SRE utilities
   - [ ] Consider "agent.py" integration if user clarifies
   - [ ] Community engagement (issues, PRs)

---

## Important Decisions

**Repository Name:** To be determined - should reflect "useful time-saving tools for Linux/DevOps"

**License:** MIT (permissive, common for utilities)

**Initial Content:** Linux Service Manager (complete)

**Reporting Mechanism:**
- Every 15 minutes as requested
- Short format: status of repository, commits, issues, stars, etc.
- Sent via message tool (same channel as current)
- Will need to be turned off/adjusted after initial phase

**Security Protocol:**
- Never log the GitHub token
- Store token in environment variable only
- Use HTTPS for all Git operations
- Rotate token if ever exposed

---

## User Preferences Recorded

- Reports: Every 15 minutes initially, then daily
- Keep private repos private (no modifications)
- Repository should be "useful, unique, effective, time-saver"
- Full documentation required
- User may have existing "agent.py" to consider

---
Updated: 2025-03-14 00:37 GMT+1 - Initial entry