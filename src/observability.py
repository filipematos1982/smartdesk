"""Bounded process-local metrics and allowlisted JSON request/security events."""
from collections import Counter
from datetime import datetime, timezone
import json
import logging
import sys
import threading
import time
import uuid

from starlette.responses import JSONResponse


class Telemetry:
    def __init__(self):
        self.lock = threading.Lock()
        self.started = time.monotonic()
        self.counts = Counter({"requests": 0, "client_errors": 0, "server_errors": 0, "authentication_failures": 0})
        self.routes = {}
        # A private logger avoids modifying global logging or accumulating handlers.
        self.logger = logging.Logger("smartdesk.events", level=logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def event(self, event, scope, status, duration=0):
        route = getattr(scope.get("route"), "path", "unmatched")
        state = scope.setdefault("state", {})
        role = state.get("actor_role", "anonymous")
        role = role if role in {"employee", "technician", "responsavel"} else "anonymous"
        method = scope.get("method", "OTHER")
        method = method if method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} else "OTHER"
        if event == "authentication_failed":
            with self.lock:
                self.counts["authentication_failures"] += 1
        self.logger.info(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, "request_id": state.get("request_id"),
                                    "method": method, "route": route, "status": status,
                                    "duration_ms": round(duration * 1000, 3), "actor_role": role}, separators=(",", ":")))

    def record(self, scope, status, duration):
        route = getattr(scope.get("route"), "path", "unmatched")
        with self.lock:
            self.counts["requests"] += 1
            self.counts["client_errors"] += int(400 <= status < 500)
            self.counts["server_errors"] += int(status >= 500)
            # Fixed routes plus one overflow bucket avoid user-controlled cardinality.
            label = route if route in self.routes or len(self.routes) < 64 else "other"
            item = self.routes.setdefault(label, {"requests": 0, "errors": 0, "duration_ms_total": 0.0})
            item["requests"] += 1
            item["errors"] += int(status >= 400)
            item["duration_ms_total"] += round(duration * 1000, 3)
        self.event("http_request", scope, status, duration)

    def snapshot(self):
        with self.lock:
            return {"scope": "single-process-local", "uptime_seconds": round(time.monotonic() - self.started, 3),
                    "counts": dict(self.counts), "routes": {key: dict(value) for key, value in self.routes.items()},
                    "limitations": "Resets on restart; no external monitoring, alerts or billing. Instructor acceptance is unconfirmed."}


class ObservabilityMiddleware:
    def __init__(self, app, telemetry):
        self.app, self.telemetry = app, telemetry

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        scope.setdefault("state", {})["request_id"] = uuid.uuid4().hex
        started, status, response_started = time.monotonic(), 500, False

        async def safe_send(message):
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                headers = list(message.get("headers", []))
                policies = {
                    b"cache-control": b"no-store", b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY", b"referrer-policy": b"no-referrer",
                    b"x-request-id": scope["state"]["request_id"].encode(),
                    b"content-security-policy": b"default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
                }
                if scope.get("scheme") == "https":
                    policies[b"strict-transport-security"] = b"max-age=31536000"
                headers = [(key, value) for key, value in headers if key.lower() not in policies]
                message["headers"] = headers + list(policies.items())
            await send(message)

        try:
            await self.app(scope, receive, safe_send)
        except Exception:
            if response_started:
                raise
            await JSONResponse({"detail": "Internal server error"}, status_code=500)(scope, receive, safe_send)
        finally:
            self.telemetry.record(scope, status, time.monotonic() - started)
