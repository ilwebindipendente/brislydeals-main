# helpers/amazon.py
from typing import List, Dict
from config import (
    AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG,
    MIN_STARS, MIN_DISCOUNT, MAX_ITEMS_PER_KEYWORD
)

COUNTRY_CODE = "IT"  # marketplace Italia

def _client():
    # import lazy per avere errori chiari se il pacchetto manca
    try:
        from amazon_paapi import AmazonApi
    except Exception as e:
        raise RuntimeError(f"amazon_paapi import failed: {e}")
    
    if not AMAZON_ACCESS_KEY or not AMAZON_SECRET_KEY:
        raise RuntimeError("Amazon API credentials not configured")
        
    return AmazonApi(
        AMAZON_ACCESS_KEY,
        AMAZON_SECRET_KEY,
        AMAZON_PARTNER_TAG,
        COUNTRY_CODE,
    )

def _safe(getter, default=None):
    try:
        v = getter()
        return v if v is not None else default
    except Exception:
        return default

def search_candidates_for_keyword(keyword: str) -> List[Dict]:
    try:
        api = _client()
        print(f"[amazon] Searching for keyword: {keyword}")
        
        # Search items
        res = api.search_items(
            keywords=keyword,
            item_count=MAX_ITEMS_PER_KEYWORD,
        )

        items = getattr(res, "items", []) or []
        print(f"[amazon] Found {len(items)} items for '{keyword}'")
        
        out: List[Dict] = []

        for it in items:
            asin = _safe(lambda: it.asin)
            title = _safe(lambda: it.item_info.title.display_value, "").strip()
            url = _safe(lambda: it.detail_page_url)
            img = _safe(lambda: it.images.primary.large.url)

            # Prezzi
            price_now = _safe(lambda: it.offers.listings[0].price.amount)
            price_old = _safe(lambda: it.offers.listings[0].saving_basis.amount)

            # Recensioni
            stars = _safe(lambda: it.customer_reviews.star_rating)
            reviews = _safe(lambda: it.customer_reviews.count, 0)

            # Ranking
            rank = _safe(lambda: it.browse_node_info.website_sales_rank.sales_rank.rank)
            category = _safe(lambda: it.browse_node_info.website_sales_rank.sales_rank.product_category_id)

            # Brand & features
            features = _safe(lambda: it.item_info.features.display_values, [])
            brand = _safe(lambda: it.item_info.by_line_info.brand.display_value)

            # Validazione base
            if not asin or not url or not price_now:
                print(f"[amazon] Skipping item - missing basic data: asin={bool(asin)}, url={bool(url)}, price={bool(price_now)}")
                continue
                
            # Filtro stelle
            if stars is not None and float(stars) < MIN_STARS:
                print(f"[amazon] Skipping {asin} - stars {stars} < {MIN_STARS}")
                continue

            # Calcola sconto
            discount_pct = 0
            if price_old and price_old > 0:
                discount_pct = int(round((price_old - price_now) / price_old * 100))
                if discount_pct < MIN_DISCOUNT:
                    print(f"[amazon] Skipping {asin} - discount {discount_pct}% < {MIN_DISCOUNT}%")
                    continue

            product = {
                "source": "amazon",
                "asin": asin,
                "title": title,
                "url": url,
                "image": img,
                "price_now": float(price_now),
                "price_old": float(price_old) if price_old else None,
                "discount_pct": int(discount_pct),
                "stars": float(stars) if stars is not None else None,
                "reviews": int(reviews or 0),
                "category": category,
                "rank": int(rank) if rank else None,
                "brand": brand,
                "features": features if features else [],
            }
            
            print(f"[amazon] Added product {asin}: {title[:50]}... - {discount_pct}% off")
            out.append(product)

        print(f"[amazon] Returning {len(out)} valid products for '{keyword}'")
        return out
        
    except Exception as e:
        print(f"[amazon] Error searching for '{keyword}': {type(e).__name__}: {e}")
        return []
