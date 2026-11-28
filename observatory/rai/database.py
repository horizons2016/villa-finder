"""Private SQLite persistence with append-only observations and price history."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import json
import sqlite3

from .geo import normalize
from .validation import normalize_listing, utc

SCHEMA = Path(__file__).with_name("schema.sql")
OBSERVATION_FIELDS = ("url", "kind", "deal", "published_at", "price", "currency", "rental_period",
                      "land_m2", "built_m2", "bedrooms", "description", "last_verified", "verification",
                      "availability", "price_basis", "public")


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"))


def digest(value):
    return sha256(encode(value).encode()).hexdigest()


@contextmanager
def database(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(SCHEMA.read_text(encoding="utf-8"))
        if not db.execute("PRAGMA user_version").fetchone()[0]:
            db.execute("PRAGMA user_version=1")
        yield db
    finally:
        db.close()


def register(db, sources):
    with db:
        db.executemany(
            "INSERT INTO data_sources VALUES (?,?) ON CONFLICT(id) DO UPDATE SET definition=excluded.definition",
            ((key, encode(value)) for key, value in sources.items()),
        )


def start_run(db, source_id, batch=None):
    with db:
        return db.execute(
            "INSERT INTO source_collection_runs(source_id,started_at,status,batch_id) VALUES (?,?,'running',?)",
            (source_id, utc(), batch),
        ).lastrowid


def finish_run(db, run_id, status, records=0, inserted=0, rejected=0, error=None, new_listings=0):
    db.execute(
        """UPDATE source_collection_runs SET ended_at=?,status=?,records=?,inserted=?,rejected=?,error=?,
           new_listings=? WHERE id=?""",
        (utc(), status, records, inserted, rejected, error, new_listings, run_id),
    )


def record_listings(db, source, rows, run_id, observed_at, batch=None):
    observed_at = utc(observed_at) if observed_at else None
    if not observed_at and not batch:
        raise ValueError("undated observations require a stable batch key")
    seen = set()
    inserted = rejected = created = duplicate_rows = 0
    for raw in rows:
        try:
            row = normalize_listing(raw, source, observed_at)
        except (ValueError, TypeError, AttributeError, OverflowError):
            rejected += 1
            continue
        identifier = row["external_id"]
        payload_hash = digest(row)
        if (identifier, payload_hash) in seen:
            duplicate_rows += 1
            continue
        seen.add((identifier, payload_hash))
        existing = db.execute(
            "SELECT id FROM property_listings WHERE source_id=? AND external_id=?", (source["id"], identifier),
        ).fetchone()
        if existing:
            listing_id = existing["id"]
        else:
            listing_id = db.execute(
                "INSERT INTO property_listings(source_id,external_id) VALUES (?,?)", (source["id"], identifier),
            ).lastrowid
            created += 1
        version = observed_at or f"undated:{batch}"
        previous = db.execute(
            "SELECT id,payload_hash FROM listing_observations WHERE listing_id=? AND version_key=?",
            (listing_id, version),
        ).fetchone()
        if previous:
            if previous["payload_hash"] != payload_hash:
                db.execute("INSERT OR IGNORE INTO quality_checks VALUES (?,?)", (previous["id"], "conflicting_source_record"))
                rejected += 1
            continue
        if observed_at:
            db.execute(
                """UPDATE property_listings SET first_observed=min(coalesce(first_observed,?),?),
                   last_observed=max(coalesce(last_observed,?),?) WHERE id=?""",
                (observed_at, observed_at, observed_at, observed_at, listing_id),
            )
        location_id = db.execute(
            "INSERT INTO property_locations VALUES (NULL,?,?,?,?,?,?,?)",
            (row["governorate"], row["wilayat"], row["area"], normalize(row["area"]) or None,
             row["latitude"], row["longitude"], row["accuracy"]),
        ).lastrowid
        placeholders = ",".join("?" for _ in range(len(OBSERVATION_FIELDS) + 7))
        observation_id = db.execute(
            f"""INSERT INTO listing_observations(listing_id,run_id,location_id,observed_at,version_key,
              {','.join(OBSERVATION_FIELDS)},flags,payload_hash) VALUES ({placeholders})""",
            (listing_id, run_id, location_id, observed_at, version,
             *(row[key] for key in OBSERVATION_FIELDS), encode(row["flags"]), payload_hash),
        ).lastrowid
        db.executemany("INSERT INTO quality_checks VALUES (?,?)", ((observation_id, flag) for flag in row["flags"]))
        if row["price"]:
            db.execute(
                "INSERT INTO price_history VALUES (?,?,?,?,?,?,?)",
                (observation_id, listing_id, observed_at, row["price"], row["currency"],
                 row["rental_period"], row["price_basis"]),
            )
        inserted += 1
    rejected += duplicate_rows
    return inserted, rejected, created, duplicate_rows


def backup(db, target):
    target = Path(target)
    if target.exists():
        raise ValueError("backup destination already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as destination:
        db.backup(destination)
        if destination.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("backup failed database integrity check")
