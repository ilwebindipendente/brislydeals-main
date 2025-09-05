from typing import List, Dict
from config import (AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, AMAZON_PARTNER_TAG,
                    AMAZON_HOST, AMAZON_REGION, MIN_STARS, MIN_DISCOUNT, MAX_ITEMS_PER_KEYWORD)
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.configuration import Configuration
from paapi5_python_sdk.search_items_request import SearchItemsRequest
from paapi5_python_sdk.search_items_resource import SearchItemsResource

def _client():
    cfg = Configuration(
        access_key=AMAZON_ACCESS_KEY,
        secret_key=AMAZON_SECRET_KEY,
        host=AMAZON_HOST,
        region=AMAZON_REGION,
    )
    return DefaultApi(None, cfg)

def search_candidates_for_keyword(keyword: str) -> List[Dict]:
    api = _client()
    req = SearchItemsRequest(
        partner_tag=AMAZON_PARTNER_TAG,
        partner_type="Associates",
        keywords=keyword,
        marketplace="www.amazon.it",
        resources=[
            SearchItemsResource.ITEMINFO_TITLE,
            SearchItemsResource.OFFERS_LISTINGS_PRICE,
            SearchItemsResource.OFFERS_LISTINGS_SAVINGBASIS,
            SearchItemsResource.CUSTOMERREVIEWS_COUNT,
            SearchItemsResource.CUSTOMERREVIEWS_STAR_RATING,
            SearchItemsResource.IMAGES_PRIMARY_LARGE,
            SearchItemsResource.BROWSE_NODE_INFO_WEBSITE_SALES_RANK
        ],
        item_count=MAX_ITEMS_PER_KEYWORD
    )
    res = api.search_items(req)
    items = res.search_result.items if res.search_result else []
    out = []
    for it in items:
        asin = it.asin
        title = (it.item_info.title.display_value if it.item_info and it.item_info.title else "").strip()
        url = it.detail_page_url
        img = it.images.primary.large.url if it.images and it.images.primary and it.images.primary.large else None
        price_now = None; price_old = None

        if it.offers and it.offers.listings:
            lst = it.offers.listings[0]
            if lst.price and lst.price.amount:
                price_now = float(lst.price.amount)
            if lst.saving_basis and lst.saving_basis.amount:
                price_old = float(lst.saving_basis.amount)

        stars = it.customer_reviews.star_rating if it.customer_reviews else None
        reviews = it.customer_reviews.count if it.customer_reviews else 0

        rank = None; category = None
        if it.browse_node_info and it.browse_node_info.website_sales_rank and it.browse_node_info.website_sales_rank.sales_rank:
            sr = it.browse_node_info.website_sales_rank.sales_rank
            rank = sr.rank
            category = sr.product_category_id

        if not asin or not url or not price_now:
            continue
        if stars is not None and stars < MIN_STARS:
            continue
        discount_pct = 0
        if price_old and price_old > 0:
            discount_pct = int(round((price_old - price_now) / price_old * 100))
            if discount_pct < MIN_DISCOUNT:
                continue

        out.append({
            "source": "amazon",
            "asin": asin, "title": title, "url": url, "image": img,
            "price_now": price_now, "price_old": price_old,
            "discount_pct": discount_pct,
            "stars": float(stars) if stars is not None else None,
            "reviews": int(reviews or 0),
            "category": category, "rank": rank,
        })
    return out
