"""Comparable groups, explainable anomaly flags, and review-only duplicate links."""
from collections import defaultdict
from itertools import combinations
from statistics import median, quantiles

from .database import encode
from .geo import distance_km, normalize


def comparable(row):
    if row["price_basis"] != "advertised" or not all(row[key] for key in ("price", "currency", "deal", "kind", "wilayat")):
        return None
    if row["deal"] == "rent" and not row["rental_period"]:
        return None
    return tuple(row[key] for key in ("wilayat", "kind", "deal", "currency", "rental_period"))


def unit_price(row):
    if not row["kind"] or row["price"] is None:
        return None
    size = row["land_m2"] if row["kind"].endswith("-land") or row["kind"] == "farm" else row["built_m2"]
    return float(row["price"]) / size if size else None


def outliers(values):
    if len(values) < 8:
        return []
    sample = [value for _, value in values]
    typical = median(sample)
    mad = median(abs(value - typical) for value in sample)
    q1, _, q3 = quantiles(sample, n=4, method="inclusive")
    iqr = q3 - q1
    if mad == 0 and iqr == 0:
        return [identifier for identifier, value in values if typical > 0 and abs(value / typical - 1) > 0.25]
    return [
        identifier for identifier, value in values
        if (mad > 0 and abs(value - typical) * 0.67448975 / mad > 3.5)
        or (iqr > 0 and (value < q1 - 3 * iqr or value > q3 + 3 * iqr))
    ]


def similar_area(a, b):
    return a and b and abs(a - b) / max(a, b) <= 0.05


def duplicate_reasons(left, right):
    if left["url"] == right["url"]:
        return ["identical_url"], 1.0
    if not left["kind"] or not left["deal"] or not left["wilayat"]:
        return [], 0
    if any(left[key] != right[key] for key in ("kind", "deal", "wilayat")):
        return [], 0
    if left["accuracy"] == right["accuracy"] == "confirmed" and distance_km(
        left["latitude"], left["longitude"], right["latitude"], right["longitude"],
    ) > 0.15:
        return [], 0
    reasons = []
    score = 0.0
    if left["area_key"] and left["area_key"] == right["area_key"]:
        reasons.append("same_local_area")
        score += 0.15
    for key in ("land_m2", "built_m2"):
        if similar_area(left[key], right[key]):
            reasons.append(f"similar_{key}")
            score += 0.15
    if left["bedrooms"] is not None and left["bedrooms"] == right["bedrooms"]:
        reasons.append("same_bedrooms")
        score += 0.1
    a = set(normalize(left["description"]).split())
    b = set(normalize(right["description"]).split())
    if len(a & b) >= 5 and len(a & b) / len(a | b) >= 0.7:
        reasons.append("similar_description")
        score += 0.4
    if left["accuracy"] in ("confirmed", "source_reported") and right["accuracy"] in ("confirmed", "source_reported"):
        if distance_km(left["latitude"], left["longitude"], right["latitude"], right["longitude"]) <= 0.035:
            reasons.append("nearby_reported_coordinates")
            score += 0.35
    if score >= 0.65 and ("similar_description" in reasons or "nearby_reported_coordinates" in reasons):
        reasons.append("cross_source_match" if left["source_id"] != right["source_id"] else "possible_repost")
        if left["price"] and right["price"] and all(left[key] == right[key] for key in ("currency", "rental_period", "price_basis")):
            if abs(float(left["price"]) / float(right["price"]) - 1) >= 0.2:
                reasons.append("different_advertised_prices")
        return reasons, min(score, 0.99)
    return [], 0


def candidate_pairs(current):
    urls = defaultdict(list)
    blocks = defaultdict(list)
    for row in current:
        urls[row["url"]].append(row)
        if row["wilayat"] and row["kind"] and row["deal"]:
            blocks[row["wilayat"], row["kind"], row["deal"]].append(row)
    seen = set()
    for group in (*urls.values(), *blocks.values()):
        for left, right in combinations(group, 2):
            pair = tuple(sorted((left["listing_id"], right["listing_id"])))
            if pair not in seen:
                seen.add(pair)
                yield pair, left, right


def refresh(db):
    current = list(db.execute("SELECT * FROM current_listings"))
    groups = defaultdict(list)
    sqm_groups = defaultdict(list)
    flags = []
    for row in current:
        key = comparable(row)
        if key:
            groups[key].append((row["id"], float(row["price"])))
            sqm = unit_price(row)
            if sqm is not None:
                sqm_groups[key].append((row["id"], sqm))
    for grouped, code in ((groups, "comparable_price_outlier"), (sqm_groups, "comparable_sqm_outlier")):
        for sample in grouped.values():
            flags.extend((identifier, code) for identifier in outliers(sample))
    prior = {}
    for row in db.execute(
        """SELECT observation_id,listing_id,amount,currency,rental_period,basis
           FROM price_history WHERE observed_at IS NOT NULL
           ORDER BY listing_id, observed_at, observation_id"""
    ):
        prev = prior.get(row["listing_id"])
        if prev and all(row[key] == prev[key] for key in ("currency", "rental_period", "basis")) and row["currency"]:
            if max(float(row["amount"]), float(prev["amount"])) / min(float(row["amount"]), float(prev["amount"])) >= 1.5:
                flags.append((row["observation_id"], "large_price_change"))
        elif prev and (row["currency"] != prev["currency"] or row["rental_period"] != prev["rental_period"]):
            flags.append((row["observation_id"], "changed_currency_or_period"))
        prior[row["listing_id"]] = row
    db.executemany("INSERT OR IGNORE INTO quality_checks VALUES (?,?)", flags)
    db.execute("UPDATE duplicate_candidates SET active=0")
    for pair, left, right in candidate_pairs(current):
        reasons, score = duplicate_reasons(left, right)
        if reasons:
            db.execute(
                """INSERT INTO duplicate_candidates(left_id,right_id,reasons,score) VALUES (?,?,?,?)
                   ON CONFLICT(left_id,right_id) DO UPDATE SET reasons=excluded.reasons,score=excluded.score,active=1""",
                (*pair, encode(reasons), score),
            )
