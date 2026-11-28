"""Collect independently per source and keep operational history in the private database."""
import json
import logging
import os
import re
import sqlite3
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from .adapters import Downloader, STAT_ADAPTERS, authorized_feed, osm_rows
from .database import digest, finish_run, record_listings, register, start_run
from .geo import ROOT
from .quality import refresh
from .validation import safe_url, utc

LOG = logging.getLogger("rai.collector")
NETWORK_ERRORS = (RuntimeError, ValueError, UnicodeError, OSError, subprocess.SubprocessError)


def load_sources(config=None):
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    if config:
        overrides = json.loads(Path(config).read_text(encoding="utf-8"))
        for key, setting in overrides.items():
            if not re.fullmatch(r"[a-z][a-z\d-]{1,39}", key):
                raise ValueError("invalid source key")
            if not setting.get("permission_reference"):
                raise ValueError("local listing sources require a permission reference")
            if key in sources and "listings" not in sources[key]["categories"]:
                raise ValueError("cannot replace a non-listing source")
            source = {**sources.get(key, {"categories": ["listings"]}), **setting}
            source["adapter"] = "feed" if source.get("feed_url") else "manual"
            source["status"] = "enabled" if source["adapter"] == "feed" else "manual"
            safe_url(source["url"], source["hosts"])
            if source.get("feed_url"):
                safe_url(source["feed_url"], source["hosts"])
            sources[key] = source
    return {key: dict(source, id=key) for key, source in sources.items()}


def run_listings(db, source, rows, observed_at=None, batch=None):
    if not isinstance(rows, list):
        raise ValueError("listing import must contain an array")
    run = start_run(db, source["id"], batch)
    try:
        with db:
            db.execute("BEGIN IMMEDIATE")
            inserted, rejected, created, duplicates = record_listings(db, source, rows, run, observed_at, batch)
            finish_run(db, run, "partial" if rejected > duplicates else "ok", len(rows), inserted, rejected,
                       f"{duplicates} repeated rows" if duplicates else None, created)
    except Exception:
        with db:
            finish_run(db, run, "failed", error="listing batch transaction rolled back")
        raise
    return {"rows": len(rows), "inserted": inserted, "rejected": rejected, "new": created, "exact_repeats": duplicates}


def source_listing_id(url):
    path = urlsplit(url).path.rstrip("/")
    match = re.search(r"/(?:search/|properties/|details-)([A-Za-z0-9]+)(?:\.html)?$", path)
    return match[1] if match else url


def import_legacy(db, sources):
    aliases = {"Oman Real": "oman-real", "السوق المفتوح": "opensooq", "Bayut": "bayut"}
    raw = json.loads((ROOT / "legacy.json").read_text(encoding="utf-8"))
    villas = {item["u"]: item for item in json.loads((ROOT.parent / "data/villas.json").read_text(encoding="utf-8"))}
    by_source = {key: [] for key in aliases.values()}
    for row in raw:
        villa = villas.get(row["url"], {})
        by_source[aliases[row["source"]]].append(dict(
            row, external_id=source_listing_id(row["url"]), currency="OMR",
            land_m2=villa.get("la") or row["area_m2"], built_m2=villa.get("bu"), bedrooms=villa.get("b"),
            latitude=villa.get("lat"), longitude=villa.get("lng"),
            accuracy="source_reported" if villa.get("exact") else "approximate",
            public=False, verification="unverified",
        ))
    jaalan_path = ROOT.parent / "data/jaalan.json"
    if jaalan_path.exists():
        for row in json.loads(jaalan_path.read_text(encoding="utf-8")):
            by_source["oman-real"].append(dict(
                external_id=row["id"], url=f"https://omanreal.com/properties/{row['id']}", wilayat="jaalan-ali",
                area=row.get("a"), type=row.get("t"), deal="sale", price=row.get("p"), currency="OMR",
                land_m2=row.get("la"), built_m2=row.get("bu"), bedrooms=row.get("ro"),
                latitude=row.get("lat"), longitude=row.get("lng"), accuracy="source_reported",
                published_at=row.get("d"), public=False, verification="unverified",
            ))
    result = {}
    for identifier, rows in by_source.items():
        result[identifier] = run_listings(db, {**sources[identifier], "publish_listings": False}, rows, batch="repository-legacy-v1")
    with db:
        db.execute("BEGIN IMMEDIATE")
        refresh(db)
    return result



def migrate_legacy_database(db, old_file, sources):
    """Read a v0 engine database without modifying it. Import facts as private."""
    aliases = {"Oman Real": "oman-real", "السوق المفتوح": "opensooq", "Bayut": "bayut"}
    path = Path(old_file).resolve()
    if not path.is_file():
        raise ValueError("legacy database file does not exist")
    destination = Path(db.execute("PRAGMA database_list").fetchone()[2]).resolve()
    if path == destination:
        raise ValueError("use a separate database for migration")
    old = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    batches = {}
    unmapped = 0
    try:
        for name, observed_at, payload in old.execute(
            "SELECT source,observed_at,payload FROM observations ORDER BY observed_at,source,external_id"
        ):
            source_id = aliases.get(name, name)
            if source_id not in sources:
                unmapped += 1
                continue
            row = json.loads(payload)
            category = row.get("type")
            if category in ("فيلا", "villa", "أرض سكنية", "أرض تجارية"):
                row["land_m2"] = row.get("area_m2")
            row.update(external_id=source_listing_id(row["url"]), public=False, verification="unverified")
            batches.setdefault((source_id, observed_at), []).append(row)
    finally:
        old.close()
    result = {"migrated": 0, "rejected": 0, "unknown_source": unmapped}
    for (source_id, observed_at), rows in batches.items():
        snapshot_source = {**sources[source_id], "publish_listings": False}
        totals = run_listings(db, snapshot_source, rows, observed_at, "previous-engine-db")
        result["migrated"] += totals["inserted"]
        result["rejected"] += totals["rejected"]
    with db:
        db.execute("BEGIN IMMEDIATE")
        refresh(db)
    return result

def update_osm(db, source, poi_path=None):
    path = Path(poi_path) if poi_path else ROOT.parent / "data/poi.json"
    run = start_run(db, source["id"], path.name)
    try:
        points = list(osm_rows(path))
        if not points:
            raise ValueError("GIS snapshot contains no supported points")
        with db:
            db.execute("DELETE FROM geospatial_information WHERE source_id=?", (source["id"],))
            db.executemany("INSERT OR IGNORE INTO geospatial_information VALUES (?,?,?,?,?,?)",
                           ((source["id"], *point) for point in points))
            count = db.execute("SELECT count(*) FROM geospatial_information WHERE source_id=?", (source["id"],)).fetchone()[0]
            finish_run(db, run, "ok", len(points), count)
        return "ok"
    except NETWORK_ERRORS as error:
        with db:
            finish_run(db, run, "failed", error=f"GIS snapshot failed ({type(error).__name__})")
        return "failed"


def update_statistics(db, source, get, refresh_known=False):
    run = start_run(db, source["id"])
    errors = []
    rows = inserted = completed = 0
    try:
        for url, loader in STAT_ADAPTERS[source["adapter"]](source, get):
            if url is None:
                errors.append(loader)
                continue
            if not refresh_known and db.execute(
                "SELECT 1 FROM source_collection_runs WHERE source_id=? AND batch_id=? AND status='ok' LIMIT 1",
                (source["id"], url),
            ).fetchone():
                completed += 1
                continue
            release = start_run(db, source["id"], url)
            try:
                records, edition = loader()
                records = list(records)
                if not records:
                    raise ValueError("official release yielded no supported records")
                fingerprint = f"{edition or 0:06d}:{digest(records)}"
                with db:
                    count = 0
                    for record in records:
                        count += db.execute(
                            """INSERT OR IGNORE INTO official_market_statistics(source_id,run_id,
                            indicator,period,geography,value,unit,url,release_id) VALUES (?,?,?,?,?,?,?,?,?)""",
                            (source["id"], release, *record, fingerprint),
                        ).rowcount
                    finish_run(db, release, "ok", len(records), count)
                rows += len(records)
                inserted += count
                completed += 1
            except NETWORK_ERRORS as error:
                message = str(error) if isinstance(error, (ValueError, RuntimeError)) else type(error).__name__
                errors.append(f"{urlsplit(url).path.rsplit('/', 1)[-1]}: {message[:160]}")
                with db:
                    finish_run(db, release, "failed", error=errors[-1])
    except NETWORK_ERRORS as error:
        message = str(error) if isinstance(error, (ValueError, RuntimeError)) else type(error).__name__
        errors.append(f"catalog: {message[:160]}")
    status = ("partial" if completed else "failed") if errors else ("ok" if completed else "failed")
    with db:
        finish_run(db, run, status, rows, inserted, error="; ".join(errors)[:1500] or None)
    return status


def collect(db, sources, selected=None, refresh_known=False, get=None, poi_path=None):
    register(db, sources)
    get = get or Downloader().get
    result = {}
    for identifier, source in sources.items():
        if source["status"] != "enabled" or (selected and identifier not in selected):
            continue
        adapter = source.get("adapter")
        try:
            if adapter in STAT_ADAPTERS:
                status = update_statistics(db, source, get, refresh_known)
            elif adapter == "osm":
                status = update_osm(db, source, poi_path)
            elif adapter == "feed":
                token_key = source.get("bearer_env")
                token = os.environ.get(token_key) if token_key else None
                if token_key and not token:
                    raise RuntimeError("authorized feed credential is missing")
                rows = authorized_feed(source, get, token)
                result[identifier] = run_listings(db, source, rows, utc())
                status = "partial" if result[identifier]["rejected"] > result[identifier]["exact_repeats"] else "ok"
            else:
                raise ValueError("unknown source adapter")
        except NETWORK_ERRORS as error:
            with db:
                run = start_run(db, identifier)
                message = str(error) if isinstance(error, RuntimeError) else type(error).__name__
                finish_run(db, run, "failed", error=message[:180])
            status = "failed"
        result[identifier] = status
        LOG.info("%s %s", identifier, status)
    with db:
        db.execute("BEGIN IMMEDIATE")
        refresh(db)
    return result
