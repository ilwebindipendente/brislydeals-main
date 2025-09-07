from typing import Dict, Optional
import keepa
import time
from config import KEEPA_API_KEY, USE_KEEPA, KEEPA_TTL_HOURS, KEEPA_DOMAIN
from .redis_store import cache_get, cache_set

_client = None

def get_client():
    global _client
    if _client is None:
        _client = keepa.Keepa(KEEPA_API_KEY)
    return _client

def enrich_with_keepa(asin: str) -> Optional[Dict]:
    """
    Nuovo parser Keepa che usa stats_parsed.
    Bypassa il problema di cache del vecchio file.
    """
    if not USE_KEEPA or not KEEPA_API_KEY:
        print(f"[keepa_new] Disabled: USE_KEEPA={USE_KEEPA}, has_key={bool(KEEPA_API_KEY)}")
        return None
    
    # Controlla cache
    cache_key = f"keepa_new:{asin}"
    cached = cache_get(cache_key)
    if cached:
        print(f"[keepa_new] Cache hit for {asin}")
        return cached

    try:
        k = get_client()
        
        print(f"[keepa_new] Querying {asin} on domain IT...")
        
        # Query Keepa
        products = k.query(
            asin, 
            domain="IT",
            stats=90,
            days=90,
            history=False,
            rating=True,
            buybox=True,
            update=2,
            wait=True
        )
        
        if not products or not isinstance(products, list) or len(products) == 0:
            print(f"[keepa_new] No data returned for {asin}")
            return None
            
        item = products[0]
        
        if not isinstance(item, dict):
            print(f"[keepa_new] Invalid item type: {type(item)}")
            return None
            
        # USA IL NUOVO PARSING CON stats_parsed
        stats_parsed = item.get("stats_parsed", {})
        
        if not stats_parsed:
            print(f"[keepa_new] No stats_parsed field for {asin}")
            return None
        
        print(f"[keepa_new] Found stats_parsed with keys: {list(stats_parsed.keys())}")
        
        # Estrai dati dai campi parsed (già in euro)
        current_data = stats_parsed.get("current", {})
        avg_data = stats_parsed.get("avg", {})  # Media generale
        avg90_data = stats_parsed.get("avg90", avg_data)  # Media 90 giorni se disponibile
        min_data = stats_parsed.get("min", {})
        max_data = stats_parsed.get("max", {})
        
        # Prezzi correnti
        current_price = current_data.get("NEW") or current_data.get("AMAZON")
        list_price = current_data.get("LISTPRICE")
        
        # Prezzi storici (media 90 giorni)
        avg_90 = avg90_data.get("NEW") or avg90_data.get("AMAZON")
        
        # Prezzi min/max
        min_price = min_data.get("NEW") or min_data.get("AMAZON")
        max_price = max_data.get("NEW") or max_data.get("AMAZON")
        
        # Sales rank
        sales_rank = current_data.get("SALES")
        
        # Rating/Reviews - potrebbero essere in altri campi
        rating = None
        review_count = None
        
        # Buy Box e Prime info dai dati raw
        stats_raw = item.get("stats", {})
        buybox_amazon = stats_raw.get("buyBoxIsAmazon")
        prime = stats_raw.get("buyBoxIsPrimeEligible") or stats_raw.get("buyBoxIsPrimeExclusive")
        
        # Categoria
        category_name = None
        category_tree = item.get("categoryTree", [])
        if category_tree:
            try:
                category_name = category_tree[-1].get("name")
            except (AttributeError, IndexError):
                pass

        # Costruisci risultato
        data = {
            "avg_90": avg_90,
            "min_price": min_price,
            "max_price": max_price,
            "buybox_amazon": bool(buybox_amazon) if buybox_amazon is not None else None,
            "prime": bool(prime) if prime else False,
            "rating": rating,
            "review_count": review_count,
            "category_name": category_name,
            "sales_rank": int(sales_rank) if sales_rank else None,
            "current_price_keepa": current_price,
            "list_price_keepa": list_price
        }
        
        # Cache solo se abbiamo dati utili
        useful_data = [avg_90, min_price, max_price, current_price, sales_rank]
        if any(v is not None for v in useful_data):
            cache_set(cache_key, data, ttl_seconds=KEEPA_TTL_HOURS * 3600)
            print(f"[keepa_new] SUCCESS {asin}: current={current_price}€, avg90={avg_90}€, min={min_price}€, max={max_price}€, rank={sales_rank}")
            return data
        else:
            print(f"[keepa_new] No useful data extracted for {asin}")
            return None
        
    except Exception as e:
        print(f"[keepa_new] Error for {asin}: {type(e).__name__}: {e}")
        return None
