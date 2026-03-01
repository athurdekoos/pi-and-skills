# System Health Check Reference

## Emergency Checks (🔴) — every 5 minutes

### RAM_CRITICAL — Available memory < 500 MB
- **Why:** 4 pi sessions + node server can spike. Below 500 MB the OOM killer may fire.
- **Fix:** Kill idle pi sessions, restart node server, check for memory leaks.

### DISK_CRITICAL — Root filesystem > 90% full
- **Why:** Full disk breaks logging, git, package installs, everything.
- **Fix:** `docker system prune`, clear /tmp, remove old node_modules, check log sizes.

### OOM_KILLED — OOM killer event detected
- **Why:** Kernel killed a process to free memory. Something important may be dead.
- **Fix:** Check `dmesg | grep -i oom`, identify what was killed, restart it, add swap or reduce load.

### SWAP_HEAVY — Swap usage > 50% (1.35 GB)
- **Why:** Heavy swap on a VM = extreme slowness. RAM is overcommitted.
- **Fix:** Reduce concurrent pi sessions, restart memory-hungry processes.

### NODE_SERVER_DOWN — Ports 7777/7778 not responding
- **Why:** Your dev server crashed or was killed.
- **Fix:** `cd ~/dev/commuication_with_ai/server && node src/server.js &`

## Warning Checks (🟡) — daily digest + immediate if severe

### RAM_ELEVATED — Available memory < 1.5 GB
- **Why:** Getting close to danger zone. Time to pay attention.
- **Fix:** Monitor, close unused sessions.

### DISK_FILLING — Root filesystem > 75% full
- **Why:** Trending toward critical. Docker images and node_modules grow fast.
- **Fix:** Audit large directories: `du -sh /home/mia/* | sort -rh | head -10`

### LOAD_HIGH — 5-min load average > 5.0
- **Why:** 6 cores, so load > 5 means near saturation.
- **Fix:** Check `top`, kill runaway processes.

### SERVICE_FAILED — systemd service in failed state
- **Why:** Something crashed and didn't restart.
- **Fix:** `systemctl status <unit>`, then `systemctl restart <unit>`

### SSH_BRUTE_FORCE — > 50 failed SSH auth attempts in last hour
- **Why:** Someone is trying to break in.
- **Fix:** Consider fail2ban, key-only auth, or changing SSH port.

### ZOMBIES — More than 5 zombie processes
- **Why:** Parent processes not cleaning up children. Can accumulate.
- **Fix:** `ps aux | grep Z`, kill parent processes.

### INODE_HIGH — Inode usage > 70%
- **Why:** node_modules creates millions of tiny files.
- **Fix:** Remove unused node_modules dirs.

## Info Checks (ℹ️) — daily digest only

### UPTIME — System uptime
- Just informational. Long uptime may mean missing kernel updates.

### DOCKER_DISK — Docker disk usage
- Report docker image/volume sizes if docker is installed.

### STALE_TESTS — Test processes running > 2 hours
- Integration tests may be stuck.
- **Fix:** Kill them: `pkill -f "integration.test"`
