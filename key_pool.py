"""
TryIT Key Pool — Intelligent key rotation with per-key cooldowns
Handles:
- Per-key rate limit tracking
- Automatic cooldown on 429
- Round-robin selection of healthy keys
- Auto-recovery when cooldown expires
- Pipeline-level wait when all keys exhausted
"""
import time
import threading
from datetime import datetime, timezone, timedelta


class KeyPool:
    """Thread-safe key pool with per-key cooldown tracking."""

    def __init__(self, name, keys, cooldown_seconds=60):
        """
        name: label for logging (e.g. "NVIDIA")
        keys: list of API keys
        cooldown_seconds: default cooldown after a 429
        """
        self.name = name
        self.keys = list(keys)
        self.cooldown_seconds = cooldown_seconds
        # Per-key state: {key_index: cooldown_until (timestamp, UTC)}
        self.cooldown_until = {i: 0 for i in range(len(keys))}
        self.lock = threading.Lock()
        self.counter = 0
        # Stats
        self.stats = {i: {"success": 0, "rate_limit": 0, "error": 0} for i in range(len(keys))}

    def _available_indices(self, now=None):
        now = now or time.time()
        return [i for i in range(len(self.keys)) if self.cooldown_until[i] <= now]

    def get_key(self, wait=True):
        """
        Return (key_index, key) of next available key.
        If none available and wait=True, sleep until earliest cooldown expires.
        """
        while True:
            with self.lock:
                now = time.time()
                available = self._available_indices(now)
                if available:
                    # Round-robin among available
                    idx = available[self.counter % len(available)]
                    self.counter += 1
                    return idx, self.keys[idx]

                # All keys in cooldown
                if not wait:
                    return None, None

                earliest = min(self.cooldown_until.values())
                sleep_for = max(1, earliest - now)
                # Cap at 60s per wait cycle
                sleep_for = min(sleep_for, 60)

            print(f"      ⏳ [{self.name}] all keys in cooldown — waiting {sleep_for:.0f}s", flush=True)
            time.sleep(sleep_for)

    def mark_success(self, idx):
        with self.lock:
            self.stats[idx]["success"] += 1

    def mark_rate_limit(self, idx, cooldown=None):
        """Put key in cooldown. Default uses pool's cooldown_seconds."""
        cd = cooldown or self.cooldown_seconds
        with self.lock:
            self.cooldown_until[idx] = time.time() + cd
            self.stats[idx]["rate_limit"] += 1
        print(f"      ⏳ [{self.name}] key #{idx+1} rate-limited → cooldown {cd}s", flush=True)

    def mark_error(self, idx):
        with self.lock:
            self.stats[idx]["error"] += 1

    def mark_dead(self, idx, reason=""):
        """Permanently disable a key (invalid auth, etc.)."""
        with self.lock:
            self.cooldown_until[idx] = float('inf')
        print(f"      ❌ [{self.name}] key #{idx+1} marked DEAD ({reason})", flush=True)

    def status(self):
        """Return dict summarizing key health."""
        now = time.time()
        with self.lock:
            available = len(self._available_indices(now))
            return {
                "name": self.name,
                "total_keys": len(self.keys),
                "available_now": available,
                "stats": self.stats.copy(),
            }

    def log_status(self):
        s = self.status()
        print(f"   🔐 [{s['name']}] {s['available_now']}/{s['total_keys']} keys available", flush=True)
        for i in range(len(self.keys)):
            st = s['stats'][i]
            cd = self.cooldown_until[i] - time.time()
            if cd == float('inf'):
                state = "DEAD"
            elif cd > 0:
                state = f"cooldown {cd:.0f}s"
            else:
                state = "ready"
            print(f"      key #{i+1}: {state} | ok={st['success']} rl={st['rate_limit']} err={st['error']}", flush=True)


# ── Singleton pools for each provider ──
_pools = {}
_pools_lock = threading.Lock()

def get_pool(name, keys, cooldown_seconds=60):
    """Get or create a KeyPool by name."""
    with _pools_lock:
        if name not in _pools:
            _pools[name] = KeyPool(name, keys, cooldown_seconds)
        return _pools[name]

def all_status():
    with _pools_lock:
        return [p.status() for p in _pools.values()]
