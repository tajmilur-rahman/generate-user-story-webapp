"""
Brute-force protection for password login.

The demo instance is reachable from the internet, so an unthrottled login form
can be guessed at whatever rate the server accepts. Werkzeug's scrypt hashing
makes each attempt cost real CPU, which slows an attacker down but is not a
limit.

Counters live in this process. That is the right scale for a single-process
deployment (Flask's dev server, or waitress/gunicorn with one worker). Run
several workers and each keeps its own counters, which divides the effective
limit by the worker count rather than removing it. Move to Redis if this ever
runs multi-process.
"""
import threading
import time


class LoginThrottle:
    """
    Sliding-window attempt counter with a lockout.

    Keyed by whatever the caller passes. Callers key on both the client address
    and the submitted email, so one attacker cannot exhaust a victim's budget
    from many addresses, and cannot dodge the limit by rotating emails from one
    address.
    """

    def __init__(self, max_attempts=8, window_seconds=300, lockout_seconds=900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._failures = {}       # key -> [timestamps]
        self._locked_until = {}   # key -> timestamp
        self._lock = threading.Lock()

    def _prune(self, now):
        """Drop expired entries so a long-running process does not grow forever."""
        cutoff = now - self.window_seconds
        for key in list(self._failures):
            kept = [t for t in self._failures[key] if t > cutoff]
            if kept:
                self._failures[key] = kept
            else:
                del self._failures[key]
        for key in list(self._locked_until):
            if self._locked_until[key] <= now:
                del self._locked_until[key]

    def retry_after(self, keys):
        """
        Seconds until these keys may try again, or 0 if they may try now.

        Returns the longest wait across the keys, so being locked on either the
        address or the email is enough to block.
        """
        now = time.time()
        with self._lock:
            self._prune(now)
            waits = [self._locked_until[k] - now for k in keys if k in self._locked_until]
        return int(max(waits)) + 1 if waits else 0

    def record_failure(self, keys):
        """Count a failed attempt against every key, locking any that overflow."""
        now = time.time()
        with self._lock:
            self._prune(now)
            for key in keys:
                attempts = self._failures.setdefault(key, [])
                attempts.append(now)
                if len(attempts) >= self.max_attempts:
                    self._locked_until[key] = now + self.lockout_seconds
                    del self._failures[key]

    def record_success(self, keys):
        """Clear the slate. A correct password proves the client is not guessing."""
        with self._lock:
            for key in keys:
                self._failures.pop(key, None)
                self._locked_until.pop(key, None)


# One shared instance for the app.
login_throttle = LoginThrottle()
