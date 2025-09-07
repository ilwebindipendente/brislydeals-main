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
    """Normalizza i prezzi Keepa che sono sempre in centesimi"""
    if v is None or v == -1 or v == -2:
        return None
    try:
        return float(v) / 100.0
    except (ValueError, TypeError):
        return None

def enrich_with_keepa(asin: str) -> Optional[Dict]:
    """
    Arricchisce un prodotto Amazon con dati Keepa.
    Utilizza la struttura dict corretta restituita dall'API.
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
        
        print(f"[keepa] Querying {asin} on domain IT (Italia)...")
        
        # Query ottimizzata
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
            print(f"[keepa] No data returned for {asin}")
            return None
            
        item = products[0]
        
        # Controllo che sia un dict valido
        if not isinstance(item, dict):
            print(f"[keepa] Invalid item type: {type(item)}")
            return None
            
        print(f"[keepa] Successfully retrieved data for {asin}")
        
        # Estrai statistiche dal dict "stats"
        stats = item.get("stats", {})
        
        # Prezzi dalle statistiche - gestione liste con indici specifici
        # Indici Keepa: 0=Amazon, 1=New, 2=Used, 3=Sales Rank, 4=List Price, etc.
        current_prices = stats.get("current", [])
        
        # Prezzi attuali (in centesimi)
        amazon_price = current_prices[0] if len(current_prices) > 0 else None
        new_price = current_prices[1] if len(current_prices) > 1 else None
        list_price = current_prices[4] if len(current_prices) > 4 else None
        
        # Usa il new price come prezzo corrente, fallback su amazon price
        current_price = new_price if new_price and new_price > 0 else amazon_price
        current_price = _normalize_price(current_price)
        
        # Prezzo di listino (per calcolare sconto)
        list_price = _normalize_price(list_price)
        
        # Prezzi min/max storici dalle statistiche
        min_data = stats.get("min", [])
        max_data = stats.get("max", [])
        
        # Estrai prezzi da liste [timestamp, price] - prendi il prezzo dell'indice corretto
        min_price = None
        max_price = None
        
        if isinstance(min_data, list) and len(min_data) > 1:
            # min_data[1] = New price min, min_data[0] = Amazon price min
            min_new = min_data[1] if len(min_data) > 1 and min_data[1] else None
            min_amazon = min_data[0] if len(min_data) > 0 and min_data[0] else None
            
            if isinstance(min_new, list) and len(min_new) > 1:
                min_price = _normalize_price(min_new[1])
            elif isinstance(min_amazon, list) and len(min_amazon) > 1:
                min_price = _normalize_price(min_amazon[1])
                
        if isinstance(max_data, list) and len(max_data) > 1:
            max_new = max_data[1] if len(max_data) > 1 and max_data[1] else None
            max_amazon = max_data[0] if len(max_data) > 0 and max_data[0] else None
            
            if isinstance(max_new, list) and len(max_new) > 1:
                max_price = _normalize_price(max_new[1])
            elif isinstance(max_amazon, list) and len(max_amazon) > 1:
                max_price = _normalize_price(max_amazon[1])

        # Calcola media 90 giorni (approssimazione da min/max se non disponibile altrimenti)
        avg_90 = None
        if min_price and max_price:
            avg_90 = (min_price + max_price) / 2
        elif current_price:
            avg_90 = current_price

        # Rating e recensioni - potrebbero essere in posizioni specifiche del current array
        rating = None
        review_count = None
        
        # Spesso rating è all'indice 16, review count all'indice 17 (varia per marketplace)
        if len(current_prices) > 16:
            rating_raw = current_prices[16]
            if rating_raw and rating_raw > 0:
                rating = float(rating_raw) / 10.0  # Keepa rating è in decimi
                
        if len(current_prices) > 17:
            review_count_raw = current_prices[17]
            if review_count_raw and review_count_raw > 0:
                review_count = int(review_count_raw)

        # Buy Box info
        buybox_amazon = None
        buy_box_price = stats.get("buyBoxPrice")
        if buy_box_price and buy_box_price > 0:
            buybox_amazon = True  # Se c'è un prezzo buy box, probabilmente è Amazon
            
        # Prime info (spesso nei campi buyBox)
        prime = stats.get("buyBoxIsPrimeEligible") or stats.get("buyBoxIsPrimeExclusive")
        if prime is None:
            prime = False
        
        # Categoria dal dict principale
        category_name = None
        category_tree = item.get("categoryTree")
        if category_tree and len(category_tree) > 0:
            try:
                category_name = category_tree[-1].get("name")
            except (AttributeError, IndexError):
                pass

        # Sales rank - spesso all'indice 3 del current array
        sales_rank = None
        if len(current_prices) > 3:
            rank_raw = current_prices[3]
            if rank_raw and rank_raw > 0:
                sales_rank = int(rank_raw)

        # Costruisci risultato
        data = {
            "avg_90": avg_90,
            "min_price": min_price,
            "max_price": max_price,
            "buybox_amazon": bool(buybox_amazon) if buybox_amazon is not None else None,
            "prime": bool(prime),
            "rating": rating,
            "review_count": review_count,
            "category_name": category_name,
            "sales_rank": sales_rank,
            # Aggiungi anche il prezzo corrente per debug
            "current_price_keepa": current_price,
            "list_price_keepa": list_price
        }
        
        # Cache solo se abbiamo almeno qualche dato utile
        useful_data = [avg_90, min_price, max_price, rating, current_price]
        if any(v is not None for v in useful_data):
            cache_set(cache_key, data, ttl_seconds=KEEPA_TTL_HOURS * 3600)
            print(f"[keepa] ✅ SUCCESS {asin}: current={current_price}€, avg90={avg_90}€, min={min_price}€, max={max_price}€, rating={rating}")
            return data
        else:
            print(f"[keepa] ⚠️ No useful data extracted for {asin}")
            return None
        
    except Exception as e:
        print(f"[keepa] ❌ Error for {asin}: {type(e).__name__}: {e}")
        
        if "REQUEST_REJECTED" in str(e):
            print(f"[keepa] 🔄 Rate limited, sleeping 3 seconds...")
            time.sleep(3)
        
        return None
