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
    return AmazonApi(
        AMAZON_ACCESS_KEY,
        AMAZON_SECRET_KEY,
        AMAZON_PARTNER_TAG,
        COUNTRY_CODE,  # niente AmazonLocale, solo 'IT'
    )

def _safe(getter, default=None):
    try:
        v = getter()
        return v if v is not None else default
    except Exception:
        return default

def search_candidates_for_keyword(keyword: str) -> List[Dict]:
    api = _client()

    # Non passiamo 'resources' per evitare il conflitto nella versione attuale
    res = api.search_items(
        keywords=keyword,
        item_count=MAX_ITEMS_PER_KEYWORD,
    )

    items = getattr(res, "items", []) or []
    out: List[Dict] = []

    for it in items:
        asin  = _safe(lambda: it.asin)
        title = _safe(lambda: it.item_info.title.display_value, "").strip()
        url   = _safe(lambda: it.detail_page_url)
        img   = _safe(lambda: it.images.primary.large.url)

        price_now = _safe(lambda: it.offers.listings[0].price.amount)
        price_old = _safe(lambda: it.offers.listings[0].saving_basis.amount)

        stars   = _safe(lambda: it.customer_reviews.star_rating)
        reviews = _safe(lambda: it.customer_reviews.count, 0)

        rank = _safe(lambda: it.browse_node_info.website_sales_rank.sales_rank.rank)
        category = _safe(lambda: it.browse_node_info.website_sales_rank.sales_rank.product_category_id)

        # NUOVO: brand & features (bullet)
        features = _safe(lambda: it.item_info.features.display_values, [])
        brand = _safe(lambda: it.item_info.by_line_info.brand.display_value)


        if not asin or not url or not price_now:
            continue
        if stars is not None and float(stars) < MIN_STARS:
            continue

        discount_pct = 0
        if price_old and price_old > 0:
            discount_pct = int(round((price_old - price_now) / price_old * 100))
            if discount_pct < MIN_DISCOUNT:
                continue

        out.append({
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
        })

    return out
