import time

def sleep_from_headers(headers: dict, default_interval: int = 5) -> int:
    remaining = headers.get("X-Ratelimit-Remaining") or headers.get("X-RateLimit-Remaining")
    reset = headers.get("X-Ratelimit-Reset") or headers.get("X-RateLimit-Reset")
    if remaining is not None and str(remaining).isdigit() and int(remaining) == 0:
        try:
            s = int(reset)
            time.sleep(max(s, default_interval))
            return max(s, default_interval)
        except Exception:
            pass
    time.sleep(default_interval)
    return default_interval
