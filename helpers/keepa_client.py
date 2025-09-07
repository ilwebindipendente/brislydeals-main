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

    # Query con gestione migliorata degli errori
    try:
        k = get_client()
        
        # CORREZIONE 1: Usa dominio numerico invece di stringa
        # IT = 5, US = 1, UK = 2, DE = 3, FR = 4, etc.
        domain_id = 5  # Italia
        
        print(f"[keepa] Querying {asin} on domain {domain_id}...")
        
        # CORREZIONE 2: Parametri più conservativi
        products = k.query(
            asin, 
            domain=domain_id,  # Usa numero invece di "IT"
            stats=90,
            history=False,
            rating=True,
            offers=0,
            wait=True,
            days=90  # Limita il range di giorni
        )
        
        if not products or not isinstance(products, list) or len(products) == 0:
            print(f"[keepa] No data returned for {asin}")
            return None
            
        item = products[0]
        
        # CORREZIONE 3: Controllo se il prodotto esiste davvero
        if not item or item.get('asin') != asin:
            print(f"[keepa] ASIN mismatch or empty item for {asin}")
            return None
            
        stats = item.get("stats", {})
        
        print(f"[keepa] Raw stats for {asin}: {list(stats.keys())}")
        
        # Estrai statistiche prezzi con gestione dict/int
        avg_90 = stats.get("avg") or stats.get("avg90")
        if isinstance(avg_90, dict):
            avg_90 = avg_90.get(0) or avg_90.get("amazon") or avg_90.get("new")
            
        min_price = stats.get("min")
        if isinstance(min_price, dict):
            min_price = min_price.get(0) or min_price.get("amazon") or min_price.get("new")
            
        max_price = stats.get("max")
        if isinstance(max_price, dict):
            max_price = max_price.get(0) or max_price.get("amazon") or max_price.get("new")

        # Normalizza i prezzi
        avg_90 = _normalize_price(avg_90)
        min_price = _normalize_price(min_price)
        max_price = _normalize_price(max_price)

        # Rating e recensioni - gestione migliorata
        current_stats = stats.get("current", {})
        rating = None
        review_count = None
        
        # Prova diverse chiavi per rating
        if "rating" in current_stats:
            rating = current_stats["rating"]
        elif "rating" in item:
            rating = item["rating"]
        
        # Prova diverse chiavi per review count
        if "reviewCount" in current_stats:
            review_count = current_stats["reviewCount"]
        elif "reviewCount" in item:
            review_count = item["reviewCount"]

        # Informazioni prodotto
        buybox_amazon = item.get("buyBoxIsAmazon", False)
        prime = item.get("isPrimeExclusive", False) or item.get("isPrime", False)
        
        # Categoria - gestione migliorata
        category_name = None
        if "categoryTree" in item and item["categoryTree"]:
            try:
                category_name = item["categoryTree"][-1]["name"]
            except (KeyError, IndexError, TypeError):
                pass

        # Sales rank - gestione migliorata
        sales_rank = None
        if "salesRanks" in current_stats and current_stats["salesRanks"]:
            try:
                ranks = current_stats["salesRanks"]
                if isinstance(ranks, dict):
                    valid_ranks = [v for v in ranks.values() if isinstance(v, int) and v > 0]
                    if valid_ranks:
                        sales_rank = min(valid_ranks)
                elif isinstance(ranks, list) and ranks:
                    sales_rank = ranks[0]
            except (ValueError, TypeError, KeyError):
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
        
        # Salva in cache solo se abbiamo almeno qualche dato utile
        if any(v is not None for v in [avg_90, min_price, max_price, rating]):
            cache_set(cache_key, data, ttl_seconds=KEEPA_TTL_HOURS * 3600)
            print(f"[keepa] Success for {asin}: avg90={avg_90}, min={min_price}, max={max_price}, rating={rating}")
        else:
            print(f"[keepa] No useful data for {asin}, not caching")
        
        return data
        
    except Exception as e:
        print(f"[keepa] Query error for {asin}: {type(e).__name__}: {e}")
        
        # CORREZIONE 4: Se è REQUEST_REJECTED, aspetta un po'
        if "REQUEST_REJECTED" in str(e):
            print(f"[keepa] Rate limited, sleeping 2 seconds...")
            time.sleep(2)
        
        return None
