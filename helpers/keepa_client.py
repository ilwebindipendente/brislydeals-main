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
    Utilizza la sintassi corretta dell'API Keepa.
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

    try:
        k = get_client()
        
        # CORREZIONE PRINCIPALE: Domain code stringa per Italia
        domain_code = "IT"  # Client Python usa stringhe, non numeri!
        
        print(f"[keepa] Querying {asin} on domain {domain_code} (Italia)...")
        
        # Query ottimizzata basata sulla documentazione ufficiale
        # Costo: ~4 token (1 base + 1 rating + 2 buybox)
        products = k.query(
            asin, 
            domain=domain_code,
            stats=90,           # Statistiche ultimi 90 giorni (no token)
            days=90,            # Limita storici a 90 giorni (no token) 
            history=False,      # Esclude dati storici pesanti (no token)
            rating=True,        # Include rating/reviews (+1 token se < 14gg)
            buybox=True,        # Include Buy Box data (+2 token)
            update=2,           # Refresh solo se dati > 2 ore (risparmia)
            wait=True
        )
        
        if not products or not isinstance(products, list) or len(products) == 0:
            print(f"[keepa] No data returned for {asin}")
            return None
            
        item = products[0]
        
        # Controllo validità prodotto
        if not item or item.get('asin') != asin:
            print(f"[keepa] ASIN mismatch or empty item for {asin}")
            return None
            
        print(f"[keepa] Successfully retrieved data for {asin}")
        
        # Estrai statistiche (dalla documentazione: stats field)
        stats = item.get("stats", {})
        
        # Prezzi dalle statistiche (ultimi 90 giorni)
        avg_90 = stats.get("avg")
        min_price = stats.get("min") 
        max_price = stats.get("max")
        
        # Le stats possono avere sottocampi per tipo di prezzo
        # Prova prima il prezzo Amazon (indice 0), poi new, poi qualsiasi
        if isinstance(avg_90, dict):
            avg_90 = avg_90.get(0) or avg_90.get("amazon") or avg_90.get("new")
        if isinstance(min_price, dict):
            min_price = min_price.get(0) or min_price.get("amazon") or min_price.get("new")
        if isinstance(max_price, dict):
            max_price = max_price.get(0) or max_price.get("amazon") or max_price.get("new")

        # Normalizza prezzi
        avg_90 = _normalize_price(avg_90)
        min_price = _normalize_price(min_price)
        max_price = _normalize_price(max_price)

        # Rating e recensioni - accesso come attributi
        try:
            current_rating = None
            current_reviews = None
            
            # Prova diversi modi per accedere ai dati
            if hasattr(item, 'stats') and item.stats:
                current_stats = getattr(item.stats, 'current', None)
                if current_stats:
                    current_rating = getattr(current_stats, 'rating', None)
                    current_reviews = getattr(current_stats, 'reviewCount', None)
            
            # Fallback: cerca direttamente nell'item
            if current_rating is None:
                current_rating = getattr(item, 'rating', None)
            if current_reviews is None:
                current_reviews = getattr(item, 'reviewCount', None)
                
        except Exception as e:
            print(f"[keepa] Could not extract rating/reviews: {e}")
            current_rating = None
            current_reviews = None

        # Buy Box info
        try:
            buybox_amazon = getattr(item, 'buyBoxIsAmazon', False)
        except Exception:
            buybox_amazon = False
        
        # Info Prime/prodotto base
        try:
            prime = getattr(item, 'isPrimeExclusive', False) or getattr(item, 'isPrime', False)
        except Exception:
            prime = False
        
        # Categoria
        category_name = None
        try:
            category_tree = getattr(item, 'categoryTree', None)
            if category_tree and len(category_tree) > 0:
                category_name = category_tree[-1].get('name') if hasattr(category_tree[-1], 'get') else getattr(category_tree[-1], 'name', None)
        except Exception:
            pass

        # Sales rank
        sales_rank = None
        try:
            if hasattr(item, 'stats') and item.stats:
                current_stats = getattr(item.stats, 'current', None)
                if current_stats and hasattr(current_stats, 'salesRanks'):
                    ranks = getattr(current_stats, 'salesRanks', None)
                    if ranks:
                        if hasattr(ranks, 'values'):  # dict-like
                            valid_ranks = [v for v in ranks.values() if isinstance(v, int) and v > 0]
                        elif hasattr(ranks, '__iter__'):  # list-like
                            valid_ranks = [v for v in ranks if isinstance(v, int) and v > 0]
                        else:
                            valid_ranks = []
                        
                        if valid_ranks:
                            sales_rank = min(valid_ranks)
        except Exception:
            pass

        # Costruisci risultato
        data = {
            "avg_90": avg_90,
            "min_price": min_price,
            "max_price": max_price,
            "buybox_amazon": bool(buybox_amazon),
            "prime": bool(prime),
            "rating": float(current_rating) if current_rating is not None else None,
            "review_count": int(current_reviews) if current_reviews is not None else None,
            "category_name": category_name,
            "sales_rank": sales_rank
        }
        
        # Cache solo se abbiamo dati utili
        if any(v is not None for v in [avg_90, min_price, max_price, current_rating]):
            cache_set(cache_key, data, ttl_seconds=KEEPA_TTL_HOURS * 3600)
            print(f"[keepa] ✅ SUCCESS {asin}: avg90={avg_90}€, rating={current_rating}, buybox_amazon={buybox_amazon}")
            return data
        else:
            print(f"[keepa] ⚠️ No useful data for {asin}")
            return None
        
    except Exception as e:
        error_msg = str(e)
        print(f"[keepa] ❌ Error for {asin}: {type(e).__name__}: {error_msg}")
        
        # Gestione specifica errori
        if "REQUEST_REJECTED" in error_msg:
            print(f"[keepa] 🔄 Rate limited, sleeping 3 seconds...")
            time.sleep(3)
        elif "402" in error_msg or "Payment Required" in error_msg:
            print(f"[keepa] 💳 API key issue or plan expired")
        elif "429" in error_msg or "Too Many Requests" in error_msg:
            print(f"[keepa] 🚫 Out of tokens")
        
        return None
