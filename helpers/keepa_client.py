from typing import Dict, Optional
import keepa
from config import KEEPA_API_KEY, USE_KEEPA, KEEPA_TTL_HOURS
from .redis_store import cache_get, cache_set

_client = None
def get_client():
    global _client
    if _client is None:
        _client = keepa.Keepa(KEEPA_API_KEY)
    return _client

def _normalize_price(v):
    if v is None:
        return None
    return float(v/100.0) if v > 10000 else float(v)

def enrich_with_keepa(asin: str) -> Optional[Dict]:
    if not USE_KEEPA or not KEEPA_API_KEY:
        return None
    ck = f"keepa:{asin}"
    cached = cache_get(ck)
    if cached:
        return cached

    k = get_client()
    try:
        p = k.query(asin, stats=90, history=False, rating=True, offers=0)
    except Exception:
        return None
    if not p or not isinstance(p, list):
        return None
    item = p[0]
    stats = item.get("stats", {})

    avg_90 = stats.get("avg90") or stats.get("avg")
    if isinstance(avg_90, dict):
        avg_90 = avg_90.get("new") or avg_90.get("buyBox")
    min_price = stats.get("min");  max_price = stats.get("max")
    if isinstance(min_price, dict): min_price = min_price.get("new")
    if isinstance(max_price, dict): max_price = max_price.get("new")

    avg_90  = _normalize_price(avg_90) if avg_90 else None
    min_p   = _normalize_price(min_price) if min_price else None
    max_p   = _normalize_price(max_price) if max_price else None

    buybox_amazon = bool(item.get("buyBoxIsAmazon", False))
    prime = bool(item.get("isPrimeExclusive", False)) or bool(item.get("isPrime", False))

    rating = item.get("stats", {}).get("current", {}).get("rating") or item.get("stats", {}).get("rating")
    review_count = item.get("stats", {}).get("current", {}).get("reviewCount") or item.get("stats", {}).get("reviewCount")

    category_name = None
    tree = item.get("categoryTree") or []
    if tree:
        category_name = tree[-1].get("name")

    salesRanks = item.get("stats", {}).get("current", {}).get("salesRank")
    sales_rank = None
    if isinstance(salesRanks, dict):
        try:
            sales_rank = min(v for v in salesRanks.values() if isinstance(v, int) and v > 0)
        except ValueError:
            sales_rank = None

    data = {
        "avg_90": avg_90,
        "min_price": min_p,
        "max_price": max_p,
        "buybox_amazon": buybox_amazon,
        "prime": prime,
        "rating": float(rating) if rating else None,
        "review_count": int(review_count) if review_count else None,
        "category_name": category_name,
        "sales_rank": sales_rank
    }
    cache_set(ck, data, ttl_seconds=KEEPA_TTL_HOURS*3600)
    return data
