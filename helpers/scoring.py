import math

def clamp01(x): 
    return max(0.0, min(1.0, x))

def normalize_discount(pct):
    return clamp01((pct or 0) / 40.0)

def normalize_rating(stars):
    return clamp01(((stars or 4.0) - 3.5) / 1.0)

def trend_score(current, avg_90):
    if not current or not avg_90 or avg_90 <= 0: 
        return 0.5
    delta = (current - avg_90) / avg_90
    return clamp01(1.0 - (delta / 0.20))

def rank_percentile_score(rank, total_in_cat):
    if not rank or not total_in_cat or total_in_cat <= 0:
        return 0.5
    percentile = rank / total_in_cat
    if percentile <= 0.05: return 1.0
    if percentile >= 0.50: return 0.0
    return clamp01((0.50 - percentile) / 0.45)

def reviews_bonus(n_reviews):
    if not n_reviews or n_reviews <= 0: 
        return 0.0
    return clamp01(math.log10(n_reviews+1) / 3.0)

def compute_brisly_score(discount_pct, stars, current_price, avg_90,
                         rank=None, total_in_cat=None,
                         is_prime=False, buybox_amazon=False,
                         n_reviews=0, weights=None):
    w = weights or {
        "discount":0.35, "rating":0.25, "trend":0.20,
        "rank":0.10, "prime_buybox_bonus":0.10, "reviews_bonus":0.10
    }
    s_discount = normalize_discount(discount_pct or 0)
    s_rating  = normalize_rating(stars or 4.0)
    s_trend   = trend_score(current_price, avg_90)
    s_rank    = rank_percentile_score(rank, total_in_cat)
    bonus = 0.0
    if is_prime and buybox_amazon:
        bonus += w["prime_buybox_bonus"]
    bonus += min(w["reviews_bonus"], reviews_bonus(n_reviews))

    base = (
        w["discount"] * s_discount +
        w["rating"]  * s_rating  +
        w["trend"]   * s_trend   +
        w["rank"]    * s_rank
    )
    score01 = clamp01(base + bonus)
    score05 = round(score01 * 5 * 2) / 2.0
    return score05
