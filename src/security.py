"""Session-bound CSRF checks and bounded, process-local login throttling."""
import hmac
import math
import secrets
import time
from collections import OrderedDict
from threading import Lock

from fastapi import HTTPException, Request


def csrf_token(request):
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def require_csrf(request: Request):
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    # Preserve unauthenticated API responses; no mutation is possible without a user.
    if request.url.path.startswith("/api/") and not request.session.get("uid"):
        return
    expected = request.session.get("csrf_token")
    supplied = request.headers.get("X-CSRF-Token")
    if supplied is None:
        form = await request.form()
        supplied = form.get("csrf_token")
    if (not isinstance(expected, str) or not isinstance(supplied, str)
            or len(supplied) > 256
            or not hmac.compare_digest(expected.encode(), supplied.encode())):
        raise HTTPException(403, "Invalid or missing CSRF token. Reload the page and try again.")


class LoginLimiter:
    """Five failed attempts per minute per socket IP, not forwarded headers.

    This deliberately bounded limiter is for one-process training deployments.
    Multiple workers require a shared limiter at an approved trusted ingress.
    """
    def __init__(self, limit=5, window=60, capacity=10_000, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.capacity = capacity
        self.clock = clock
        self.entries = OrderedDict()
        self.lock = Lock()

    def check(self, address):
        now = self.clock()
        with self.lock:
            # Entries remain ordered by fixed-window start time.
            while self.entries and next(iter(self.entries.values()))[0] + self.window <= now:
                self.entries.popitem(last=False)
            started, count = self.entries.get(address, (now, 0))
            if count >= self.limit:
                retry = max(1, math.ceil(started + self.window - now))
                raise HTTPException(429, "Too many login attempts. Try again later.",
                                    headers={"Retry-After": str(retry)})
            if address not in self.entries and len(self.entries) >= self.capacity:
                self.entries.popitem(last=False)
            self.entries[address] = (started, count + 1)

    def reset(self, address):
        with self.lock:
            self.entries.pop(address, None)
