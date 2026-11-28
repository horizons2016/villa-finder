"""Publish the reviewed field allowlist and build an isolated static release."""
import json
import os
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit, urlunsplit

from .database import encode
from .geo import GEOGRAPHY, ROOT, distance_km
from .quality import unit_price
from .validation import safe_url, utc

LISTING_FIELDS = ("listing_id", "source_id", "governorate", "wilayat", "area", "area_key", "kind", "deal",
                  "price", "currency", "rental_period", "land_m2", "built_m2", "bedrooms", "published_at",
                  "first_observed", "last_observed", "last_verified", "verification", "availability", "price_basis")
POINT_FIELDS = ("category", "name", "latitude", "longitude")


def make_export(db, sources, built_at=None):
    current = {row["listing_id"]: row for row in db.execute("SELECT * FROM current_listings")
               if row["public"] and sources.get(row["source_id"], {}).get("publish_listings") is True}
    candidates = Counter()
    for row in db.execute("SELECT left_id,right_id FROM duplicate_candidates WHERE active=1 AND decision='pending'"):
        if row["left_id"] in current and row["right_id"] in current:
            candidates.update((row["left_id"], row["right_id"]))
    public_history = defaultdict(list)
    price_changes = defaultdict(list)
    previous_price = {}
    for row in db.execute(
        """SELECT o.*,h.amount FROM listing_observations o LEFT JOIN price_history h ON h.observation_id=o.id
           WHERE o.public=1 AND o.observed_at IS NOT NULL ORDER BY o.observed_at,o.id"""
    ):
        identifier = row["listing_id"]
        if identifier not in current:
            continue
        observation = {key: row[key] for key in ("observed_at", "price", "currency", "rental_period", "price_basis",
                                                  "availability", "kind", "deal", "land_m2", "built_m2")}
        observation["price_per_m2"] = unit_price(observation)
        public_history[identifier].append(observation)
        if row["amount"] is not None:
            dimensions = (row["currency"], row["rental_period"], row["price_basis"])
            previous = previous_price.get((identifier, dimensions))
            if previous != row["amount"]:
                price_changes[identifier].append({**observation, "previous": previous})
            previous_price[identifier, dimensions] = row["amount"]
    quality = defaultdict(list)
    for row in db.execute("SELECT observation_id,code FROM quality_checks ORDER BY code"):
        quality[row["observation_id"]].append(row["code"])
    points = [{key: row[key] for key in POINT_FIELDS} for row in db.execute(
        "SELECT * FROM geospatial_information WHERE source_id='osm' ORDER BY external_id"
    )]
    listings = []
    for identifier, row in current.items():
        source = sources[row["source_id"]]
        link = urlsplit(safe_url(row["url"], source["hosts"]))
        link = urlunsplit((link.scheme, link.netloc, link.path, "", ""))
        # Keep exact/source-reported coordinates and free-text descriptions out of public exports.
        lat = round(row["latitude"], 2) if row["latitude"] is not None else None
        lon = round(row["longitude"], 2) if row["longitude"] is not None else None
        nearby = {}
        if lat is not None:
            for point in points:
                distance = distance_km(lat, lon, point["latitude"], point["longitude"])
                key = point["category"]
                if distance <= 5 and (key not in nearby or distance < nearby[key]["distance_km"]):
                    nearby[key] = {"name": point["name"], "distance_km": round(distance, 2)}
        history = public_history[identifier]
        item = {key: row[key] for key in LISTING_FIELDS}
        item.update(
            url=link, canonical_group=row["property_id"], latitude=lat, longitude=lon, accuracy="approximate" if lat is not None else "unknown",
            duplicate_candidates=candidates[identifier], quality_flags=quality[row["id"]],
            observations=history, price_history=price_changes[identifier], price_per_m2=unit_price(row), nearby=nearby,
            first_observed=history[0]["observed_at"] if history else None,
            last_observed=history[-1]["observed_at"] if history else None,
        )
        listings.append(item)
    statistics = []
    for row in db.execute("""
        WITH ranked AS (
          SELECT s.*,row_number() OVER (
            PARTITION BY source_id,indicator,period,geography
            ORDER BY substr(release_id,1,6) DESC,id DESC
          ) AS rank
          FROM official_market_statistics s
        ) SELECT * FROM ranked WHERE rank=1 ORDER BY period DESC,source_id,indicator,geography
    """):
        source = sources.get(row["source_id"])
        if source and source.get("publish_statistics") is True:
            statistics.append({key: row[key] for key in ("source_id", "indicator", "period", "geography", "value", "unit", "url")})
    relevant = {row["source_id"] for row in (*listings, *statistics)}
    public_sources = {
        identifier: {key: source.get(key) for key in ("name", "url", "coverage", "categories", "terms")}
        for identifier, source in sources.items() if identifier in relevant or identifier == "osm"
    }
    return {
        "schema_version": 1, "built_at": built_at or utc(), "geography": GEOGRAPHY,
        "sources": public_sources, "fresh_days": int(os.environ.get("RAI_FRESH_DAYS", "14")),
        "listings": listings, "official_statistics": statistics, "points": points,
    }


def atomic_json(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", dir=path.parent, encoding="utf-8", delete=False) as temp:
        temp.write(encode(content) + "\n")
    Path(temp.name).replace(path)
    path.chmod(0o644)


def build_site(output, snapshot):
    output = Path(output).resolve()
    if output in (ROOT, ROOT.parent) or not output.name:
        raise ValueError("build into a separate directory")
    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "index.html", output / "index.html")
    for filename in ("app.js", "app.css", "leaflet.js", "leaflet.css", "LEAFLET-LICENSE"):
        source = ROOT / "ui" / filename
        if source.is_file():
            (output / "ui").mkdir(exist_ok=True)
            shutil.copyfile(source, output / "ui" / filename)
    snapshot = Path(snapshot)
    if snapshot.resolve() != output / "public-data.json":
        shutil.copyfile(snapshot, output / "public-data.json")
