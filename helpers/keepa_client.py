from typing import Dict, Optional
import keepa
from config import KEEPA_API_KEY, USE_KEEPA, KEEPA_TTL_HOURS, KEEPA_DOMAIN
from .redis_store import cache_get, cache_set

_client = None

def get_client():
    global _client
    if _client is None:
        _client = keepa.Keepa(KEEPA_API_KEY)
    return _client

def _normalize_price(v):
    """Normalizza i prezzi Keepa che possono essere in centesimi"""
    if v is None:
        return None
    try:
        v = float(v)
        # Se il valore è molto alto (>10000), probabilmente è in centesimi
        return v / 100.0 if v >= 10000 else v
    except (ValueError, TypeError):
        return None

def enrich_with_keepa(asin: str) -> Optional[Dict]:
    """
    Arricchisce un prodotto Amazon con dati Keepa.
    Ritorna un dict con metriche oppure None se non disponibili.
    """
    if not USE_KEEPA or not KEEPA_API_KEY:
        print(f"[keepa] Disabled: USE_KEEPA={USE_KEEPA}, has_key={bool(KEEPA_API_KEY)}")
        return None
    
    # Controlla cache
    cache_key = f"keepa:{asin}"
    cached = cache_get(cache_key)
    if cached:
        print(f"[keepa] Cache hit for {asin}")
        return cached

    # Verifica token disponibili
    try:
        k = get_client()
        # Prova a fare una query di test per verificare i token
        token_check = k.query(asin, domain=KEEPA_DOMAIN, stats=0, history=False, wait=False)
        if not token_check:
            print(f"[keepa] No tokens left or API error for {asin}")
            return None
    except Exception as e:
        print(f"[keepa] Token check error for {asin}: {e}")
        return None

    # Query principale
    try:
        k = get_client()
        products = k.query(
            asin, 
            domain=KEEPA_DOMAIN, 
            stats=90, 
            history=False, 
            rating=True, 
            offers=0,
            wait=True
        )
        
        if not products or not isinstance(products, list) or len(products) == 0:
            print(f"[keepa] No data returned for {asin}")
            return None
            
        item = products[0]
        stats = item.get("stats", {})
        
        print(f"[keepa] Raw stats for {asin}: {stats}")
        
        # Estrai statistiche prezzi con gestione dict/int
        avg_90 = stats.get("avg90") or stats.get("avg")
        if isinstance(avg_90, dict):
            avg_90 = avg_90.get("new") or avg_90.get("buyBox") or avg_90.get("amazon")
            
        min_price = stats.get("min")
        if isinstance(min_price, dict):
            min_price = min_price.get("new") or min_price.get("buyBox") or min_price.get("amazon")
            
        max_price = stats.get("max")
        if isinstance(max_price, dict):
            max_price = max_price.get("new") or max_price.get("buyBox") or max_price.get("amazon")

        # Normalizza i prezzi
        avg_90 = _normalize_price(avg_90)
        min_price = _normalize_price(min_price)
        max_price = _normalize_price(max_price)

        # Rating e recensioni
        current_stats = stats.get("current", {})
        rating = current_stats.get("rating") or item.get("stats", {}).get("rating")
        review_count = current_stats.get("reviewCount") or item.get("stats", {}).get("reviewCount")

        # Informazioni prodotto
        buybox_amazon = item.get("buyBoxIsAmazon", False)
        prime = item.get("isPrimeExclusive", False) or item.get("isPrime", False)
        
        # Categoria
        category_name = None
        category_tree = item.get("categoryTree", [])
        if category_tree:
            category_name = category_tree[-1].get("name")

        # Sales rank
        sales_ranks = current_stats.get("salesRank", {})
        sales_rank = None
        if isinstance(sales_ranks, dict) and sales_ranks:
            try:
                # Prendi il rank più basso (migliore) tra le categorie
                valid_ranks = [v for v in sales_ranks.values() if isinstance(v, int) and v > 0]
                if valid_ranks:
                    sales_rank = min(valid_ranks)
            except (ValueError, TypeError):
                pass

        # Costruisci risultato
        data = {
            "avg_90": avg_90,
            "min_price": min_price,
            "max_price": max_price,
            "buybox_amazon": bool(buybox_amazon),
            "prime": bool(prime),
            "rating": float(rating) if rating is not None else None,
            "review_count": int(review_count) if review_count is not None else None,
            "category_name": category_name,
            "sales_rank": sales_rank
        }
        
        # Salva in cache
        cache_set(cache_key, data, ttl_seconds=KEEPA_TTL_HOURS * 3600)
        
        print(f"[keepa] Success for {asin}: avg90={avg_90}, min={min_price}, max={max_price}, rating={rating}")
        return data
        
    except Exception as e:
        print(f"[keepa] Query error for {asin}: {type(e).__name__}: {e}")
        return None
