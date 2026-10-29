"""Shared helpers for the Ecowoods external audit stack. Stdlib only."""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
UA = "EcowoodsExternalAudit/1.0 (+https://ecowoods.ca; black-box QA; dry-run capable)"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def fetch(url: str, method: str = "GET", limit: int = 200_000, timeout: float = 20):
    """HTTP fetch. Returns a dict. Never raises. Body is capped at `limit` bytes."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": UA, "Accept": "*/*"},
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            ttfb = time.perf_counter() - t0
            chunks = []
            got = 0
            while got < limit:
                block = resp.read(min(65536, limit - got))
                if not block:
                    break
                chunks.append(block)
                got += len(block)
            body = b"".join(chunks)
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return {
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "final_url": resp.geturl(),
                "headers": headers,
                "ttfb_ms": round(ttfb * 1000, 1),
                "body": body,
                "bytes_read": len(body),
                "truncated": got >= limit,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = b""
        try:
            body = exc.read(min(limit, 8000))
        except Exception:
            body = b""
        headers = {}
        if exc.headers:
            headers = {k.lower(): v for k, v in exc.headers.items()}
        return {
            "ok": False,
            "status": exc.code,
            "final_url": url,
            "headers": headers,
            "ttfb_ms": round((time.perf_counter() - t0) * 1000, 1),
            "body": body,
            "bytes_read": len(body),
            "truncated": False,
            "error": f"HTTPError {exc.code}",
        }
    except Exception as exc:  # noqa: BLE001 — audit must record, not crash
        return {
            "ok": False,
            "status": 0,
            "final_url": url,
            "headers": {},
            "ttfb_ms": round((time.perf_counter() - t0) * 1000, 1),
            "body": b"",
            "bytes_read": 0,
            "truncated": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def header(res: dict, name: str) -> str:
    return (res.get("headers") or {}).get(name.lower(), "")


def dry_run_requested(argv: list[str]) -> bool:
    return "--dry-run" in argv or os.environ.get("ECOWOODS_AUDIT_DRY_RUN") == "1"


def arg_value(argv: list[str], flag: str, default: str | None = None) -> str | None:
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default
