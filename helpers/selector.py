from typing import List, Dict
from .amazon import search_candidates_for_keyword
from .aliexpress import fetch_aliexpress_candidates
from .keepa_new import enrich_with_keepa  # <-- CAMBIATO: usa il nuovo client
from .redis_store import seen_recently, mark_dedup
from .scoring import compute_brisly_score
from config import KEYWORDS, MIN_DISCOUNT, KEEPA_MAX_ENRICH, AMZ_THROTTLE_MS
import time

DEFAULT_TAGS = {
    "tv": "Hisense SmartTV OLED 144Hz",
    "cuffie": "Cuffie Audio",
    "robot": "RobotAspirapolvere",
    "monitor": "MonitorGaming",
    "ssd": "SSDnvme",
    "gaming": "Gaming",
    "nvme": "SSDnvme", 
    "roborock": "RobotAspirapolvere"
}

def _keyword_tags(kw: str):
    return [t for t in DEFAULT_TAGS.get(kw.split()[0].lower(), "").split() if t]

def gather_candidates() -> List[Dict]:
    all_items: List[Dict] = []
    for kw in KEYWORDS:
        items = search_candidates_for_keyword(kw)
        for it in items:
            it["tags"] = _keyword_tags(kw)
        all_items.extend(items)
        time.sleep(AMZ_THROTTLE_MS / 1000.0)  # pausa anti-TooManyRequests

    # AliExpress (se attivo e quando integrato)
    all_items.extend(fetch_aliexpress_candidates())
    return all_items

def enrich_and_rank(cands: List[Dict]) -> List[Dict]:
    enriched: List[Dict] = []
    keepa_calls = 0
    
    for c in cands:
        if seen_recently(c["asin"]):
            continue

        # Enrichment Keepa (solo Amazon, entro cap per token)
        if c.get("source") == "amazon" and keepa_calls < KEEPA_MAX_ENRICH:
            print(f"[selector] Enriching {c['asin']} with NEW Keepa client...")
            k = enrich_with_keepa(c["asin"])  # Usa il nuovo client
            if k:
                c.update(k)
                # Se manca il "prezzo precedente" ma abbiamo la media 90g,
                # stimiamo lo sconto rispetto ad avg_90
                if not c.get("price_old") and c.get("avg_90"):
                    old = c["avg_90"]
                    if old and c.get("price_now") and old > c["price_now"]:
                        c["price_old"] = old
                        c["discount_pct"] = int(round((old - c["price_now"]) / old * 100))
                print(f"[selector] Keepa enriched {c['asin']} with data: {list(k.keys())}")
            else:
                print(f"[selector] No Keepa data for {c['asin']}")
            keepa_calls += 1

        # Filtro sconto minimo
        if c.get("discount_pct", 0) < MIN_DISCOUNT:
            continue

        # Punteggio BrislyDeals
        score = compute_brisly_score(
            c.get("discount_pct", 0),
            c.get("stars") or c.get("rating") or 4.0,
            c["price_now"],
            c.get("avg_90"),
            rank=c.get("rank") or c.get("sales_rank"),
            total_in_cat=None,
            is_prime=c.get("prime", False),
            buybox_amazon=c.get("buybox_amazon", False),
            n_reviews=c.get("reviews") or c.get("review_count", 0),
        )
        c["score"] = score
        enriched.append(c)

    enriched.sort(key=lambda x: (x["score"], x.get("discount_pct", 0)), reverse=True)
    return enriched

def commit_published(asin: str):
    mark_dedup(asin)
