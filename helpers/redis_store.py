import json, time
from typing import Optional, List, Dict
try:
    from upstash_redis import Redis
except Exception:
    Redis = None
from config import UPSTASH_REDIS_URL, UPSTASH_REDIS_TOKEN, DEDUP_DAYS

_memory = {"dedup": set(), "cache": {}, "metrics": []}

def get_client() -> Optional["Redis"]:
    if UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN and Redis:
        return Redis(url=UPSTASH_REDIS_URL, token=UPSTASH_REDIS_TOKEN)
    return None

# ----- DEDUP -----
def mark_dedup(asin: str):
    r = get_client()
    key = f"dedup:{asin}"
    ttl = DEDUP_DAYS*24*3600
    if r:
        r.set(key, "1", ex=ttl)
    else:
        _memory["dedup"].add((asin, time.time()+ttl))

def seen_recently(asin: str) -> bool:
    r = get_client()
    key = f"dedup:{asin}"
    if r:
        return r.get(key) is not None
    now = time.time()
    _memory["dedup"] = {(a,exp) for (a,exp) in _memory["dedup"] if exp > now}
    return any(a == asin for a,_ in _memory["dedup"])

# ----- CACHE (generic) -----
def cache_get(key: str):
    r = get_client()
    if r:
        val = r.get(key)
        return json.loads(val) if val else None
    return _memory["cache"].get(key)

def cache_set(key: str, value, ttl_seconds: int):
    r = get_client()
    if r:
        r.set(key, json.dumps(value), ex=ttl_seconds)
    else:
        _memory["cache"][key] = value  # no TTL in-memory

# ----- METRICS (weekly) -----
def metrics_add(week_key: str, item: Dict, score: float):
    r = get_client()
    disc = int(item.get("discount_pct", 0))
    data = {
        "asin": item["asin"], "title": item["title"], "channel": item.get("channel"),
        "price_now": item.get("price_now"), "price_old": item.get("price_old"),
        "discount_pct": disc, "score": score, "source": item.get("source"),
        "ts": int(time.time())
    }
    if r:
        r.zadd(f"wk:{week_key}:score", {json.dumps(data): score})
        r.zadd(f"wk:{week_key}:discount", {json.dumps(data): disc})
    else:
        _memory["metrics"].append(data)

def metrics_top(week_key: str, kind: str, topn: int = 5):
    r = get_client()
    if r:
        key = f"wk:{week_key}:{kind}"
        vals = r.zrevrange(key, 0, topn-1)
        return [json.loads(v) for v in (vals or [])]
    arr = sorted(_memory["metrics"], key=lambda x: x.get(kind,0), reverse=True)
    return arr[:topn]
