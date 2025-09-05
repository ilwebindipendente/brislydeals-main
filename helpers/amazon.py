from typing import List, Dict
from config import (
    AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG,
    MIN_STARS, MIN_DISCOUNT, MAX_ITEMS_PER_KEYWORD
)

# Lib PAAPI 5 “python-amazon-paapi”
# Docs: https://pypi.org/project/python-amazon-paapi/
try:
    from amazon_paapi import AmazonApi, AmazonLocale, Resources
except ImportError:
    # Render installerà, ma questa guard evita crash locali
    AmazonApi = None

def _client():
    if AmazonApi is None:
        raise RuntimeError("amazon_paapi non installato")
    # IT marketplace
    return AmazonApi(AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG, AmazonLocale.Italy)

def _safe_get(fn, default=None):
    try:
        v = fn()
        return v if v is not None else default
    except Exception:
        return default

def search_candidates_for_keyword(keyword: str) -> List[Dict]:
    api = _client()
    res = api.search_items(
        keywords=keyword,
        item_count=MAX_ITEMS_PER_KEYWORD,
        resources=[
            Resources.ITEM_INFO_TITLE,
            Resources.OFFERS_LISTINGS_PRICE,
            Resources.OFFERS_LISTINGS_SAVING_BASIS,
            Resources.CUSTOMER_REVIEWS_COUNT,
            Resources.CUSTOMER_REVIEWS_STAR_RATING,
            Resources.IMAGES_PRIMARY_LARGE,
            Resources.BROWSE_NODE_INFO_WEBSITE_SALES_RANK,
            Resources.DETAILS_PAGE_URL,
        ],
    )

    items = res.items or []
    out: List[Dict] = []

    for it in items:
        asin  = _safe_get(lambda: it.asin)
        title = _safe_get(lambda: it.item_info.title.display_value, "").strip()
        url   = _safe_get(lambda: it.detail_page_url)
        img   = _safe_get(lambda: it.images.primary.large.url)

        price_now = _safe_get(lambda: it.offers.listings[0].price.amount)
        price_old = _safe_get(lambda: it.offers.listings[0].saving_basis.amount)

        stars   = _safe_get(lambda: it.customer_reviews.star_rating)
        reviews = _safe_get(lambda: it.customer_reviews.count, 0)

        rank = _safe_get(lambda: it.browse_node_info.website_sales_rank.sales_rank.rank)
        category = _safe_get(lambda: it.browse_node_info.website_sales_rank.sales_rank.product_category_id)

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
        })

    return out


