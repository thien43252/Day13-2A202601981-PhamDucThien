#!/usr/bin/env python3
"""
Integrated test & trace collector: send test requests to the running app,
then collect traces from Langfuse Cloud.

Usage:
  python scripts/check_langfuse_traces.py

This script will:
1. Load `.env` (if present) 
2. Send test requests to http://127.0.0.1:8000/chat
3. Wait briefly for server to flush events to Langfuse
4. Try to collect and display up to 20 traces from Langfuse Cloud
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None


def load_env_file(path: str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line or line.strip().startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def send_test_requests() -> int:
    """Send test requests to the app. Returns count of successful requests."""
    if httpx is None:
        print("httpx not available, skipping request generation")
        return 0

    queries_file = Path("data/sample_queries.jsonl")
    if not queries_file.exists():
        print(f"Warning: {queries_file} not found, skipping test requests")
        return 0

    queries = [
        json.loads(line)
        for line in queries_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not queries:
        print("No queries found in data/sample_queries.jsonl")
        return 0

    base_url = "http://127.0.0.1:8000"
    print(f"\n[1/3] Generating {len(queries)} test requests...")

    success_count = 0
    try:
        with httpx.Client(timeout=30.0) as client:
            for i, payload in enumerate(queries, 1):
                try:
                    r = client.post(
                        f"{base_url}/chat",
                        json=payload,
                        timeout=30.0,
                    )
                    if r.status_code == 200:
                        resp = r.json()
                        corr_id = resp.get("correlation_id", "?")
                        feature = payload.get("feature", "?")
                        print(f"  [{i}/{len(queries)}] {corr_id} ({feature}) ✓")
                        success_count += 1
                    else:
                        print(f"  [{i}/{len(queries)}] HTTP {r.status_code} ✗")
                except Exception as e:
                    print(f"  [{i}/{len(queries)}] Error: {e} ✗")
    except Exception as e:
        print(f"Failed to send requests: {e}")
        print("  Is the app running? Try: uvicorn app.main:app --reload --env-file .env")
        return 0

    if success_count > 0:
        print(f"\n✓ Sent {success_count}/{len(queries)} requests successfully")
    return success_count


def safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except TypeError as e:
        return e
    except Exception as e:
        return e


def to_list(maybe):
    if maybe is None:
        return []
    if isinstance(maybe, (list, tuple)):
        return list(maybe)
    if isinstance(maybe, dict):
        for key in ("items", "data", "traces", "results"):
            if key in maybe and isinstance(maybe[key], (list, tuple)):
                return list(maybe[key])
        return [maybe]
    try:
        return list(maybe)
    except Exception:
        return [maybe]


def extract_basic(item: Any) -> dict:
    def g(obj, *names):
        for n in names:
            val = None
            if isinstance(obj, dict):
                val = obj.get(n)
            else:
                val = getattr(obj, n, None)
            if val is not None:
                return val
        return None

    return {
        "id": g(item, "id", "trace_id", "traceId"),
        "start_time": g(item, "start_time", "started_at", "timestamp"),
        "tags": g(item, "tags", "metadata", "tags"),
    }


def find_traces(client) -> list:
    """Try multiple methods to fetch traces from Langfuse."""
    attempts = []

    # Debug: print available methods
    public_methods = [m for m in dir(client) if not m.startswith("_")]
    relevant_methods = [m for m in public_methods if any(x in m.lower() for x in ["trace", "list", "get", "query"])]
    
    print(f"[debug] Available client methods containing 'trace/list/get/query': {relevant_methods}")

    # Method 1: Try direct client methods (various SDK versions may have different names)
    trace_methods = [
        "get_traces",
        "list_traces", 
        "get_trace_list",
        "list",
        "all",
        "query",
        "search",
    ]

    for method_name in trace_methods:
        fn = getattr(client, method_name, None)
        if callable(fn):
            try:
                res = fn(limit=20)
                attempts.append((f"client.{method_name}(limit=20)", res))
            except TypeError:
                try:
                    res = fn()
                    attempts.append((f"client.{method_name}()", res))
                except Exception:
                    pass

    # Method 2: Try nested traces object
    traces_obj = getattr(client, "traces", None)
    if traces_obj is None:
        traces_obj = getattr(client, "trace", None)

    if traces_obj is not None:
        print(f"[debug] Found traces object: {type(traces_obj)}")
        for method_name in ["list", "all", "get", "query", "search"]:
            fn = getattr(traces_obj, method_name, None)
            if callable(fn):
                try:
                    res = fn(limit=20)
                    attempts.append((f"client.traces.{method_name}(limit=20)", res))
                except Exception:
                    pass

    # Method 3: Direct REST API call with proper auth
    if httpx is not None:
        try:
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
            secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
            host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")

            print(f"[debug] Attempting REST API calls to {host}")

            if public_key and secret_key:
                # Try various API endpoints
                endpoints = [
                    "/api/public/traces",
                    "/api/traces",
                    "/traces",
                ]

                for endpoint in endpoints:
                    try:
                        with httpx.Client(auth=(public_key, secret_key), timeout=10) as http_client:
                            url = f"{host}{endpoint}?limit=20"
                            print(f"[debug] Trying {url}")
                            resp = http_client.get(url)
                            print(f"[debug]   → Status {resp.status_code}")
                            if resp.status_code == 200:
                                result = resp.json()
                                attempts.append((f"REST GET {host}{endpoint}", result))
                            elif resp.status_code >= 400:
                                print(f"[debug]   → Error: {resp.text[:200]}")
                    except Exception as e:
                        print(f"[debug]   → Exception: {e}")
        except Exception as e:
            print(f"[debug] REST attempt failed: {e}")

    print(f"[debug] Total attempts: {len(attempts)}")

    # Process attempts to find real traces
    for name, result in attempts:
        if isinstance(result, Exception):
            continue

        # Try to extract actual trace data
        traces_data = []

        # Handle dict response with "data" or "traces" key
        if isinstance(result, dict):
            # Check common keys for trace data
            for key in ("data", "traces", "results", "items"):
                if key in result:
                    val = result[key]
                    if isinstance(val, list):
                        traces_data = val
                        break
            # Also check if the dict itself represents a single trace
            if not traces_data and "id" in result:
                traces_data = [result]

        # Handle list response directly
        if isinstance(result, list):
            traces_data = result

        if traces_data:
            print(f"[method] {name} -> found {len(traces_data)} items")
            out = []
            for item in traces_data[:20]:
                basic = extract_basic(item)
                # Include even if some fields are None (partial data is better than nothing)
                out.append(basic)

            # Return if we got any non-null IDs
            if any(t.get("id") for t in out):
                return out
            # Return anyway if we got data (might be valid but field names differ)
            if out:
                return out

    return []


def main():
    load_env_file()

    print("\n" + "=" * 60)
    print("Langfuse Test & Trace Collector")
    print("=" * 60)

    # Step 1: Send test requests
    request_count = send_test_requests()

    # Step 2: Wait for flushing
    print("\n[2/3] Waiting for server to flush events to Langfuse Cloud...")
    time.sleep(2)

    # Step 3: Collect traces from Langfuse Cloud
    print("\n[3/3] Collecting traces from Langfuse Cloud...")

    try:
        from langfuse import get_client
    except Exception as e:
        print(f"\n✗ Langfuse SDK not installed: {e}")
        print("  Install with: pip install -r requirements.txt")
        sys.exit(2)

    try:
        client = get_client()
    except Exception as e:
        print(f"\n✗ Failed to instantiate Langfuse client: {e}")
        sys.exit(2)

    print(f"  Client type: {type(client).__name__}")

    traces = find_traces(client)

    print("\n" + "=" * 60)
    if traces:
        print("✓ SUCCESS: Collected traces from Langfuse Cloud")
        print("=" * 60)
        print(f"\nTraces (showing up to 20):\n")
        print(json.dumps(traces, indent=2, default=str))
        print("\n" + "=" * 60)
        print(f"Total traces collected: {len(traces)}")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Open https://cloud.langfuse.com")
        print("  2. Click 'Traces' in the left sidebar")
        print("  3. Look for traces with tag 'lab'")
        print("  4. Click on any trace to see full details")
        sys.exit(0)
    else:
        print("✗ FAILED: No traces found in Langfuse Cloud")
        print("=" * 60)
        if request_count == 0:
            print("\nPossible issue: No requests were sent to the app")
            print("\nFix:")
            print("  1. Ensure app is running:")
            print("     uvicorn app.main:app --reload --env-file .env")
            print("  2. Check app is responding:")
            print("     curl http://127.0.0.1:8000/health")
        else:
            print("\nPossible issues:")
            print("  1. LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set in .env")
            print("  2. LANGFUSE_HOST not set or incorrect (should be https://cloud.langfuse.com)")
            print("  3. Langfuse credentials are invalid or expired")
            print("  4. Network issue: cannot reach https://cloud.langfuse.com")
            print("\nChecklist:")
            print("  • cat .env | grep LANGFUSE")
            print("  • curl http://127.0.0.1:8000/health")
            print("  • Verify keys in Langfuse dashboard: Settings → API Keys")
            print("  • Restart app: Ctrl+C then uvicorn app.main:app --reload --env-file .env")
        sys.exit(1)


if __name__ == "__main__":
    main()
