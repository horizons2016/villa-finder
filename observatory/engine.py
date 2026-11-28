"""Import authorized normalized JSON listings; retain historical observations."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
 source TEXT NOT NULL, external_id TEXT NOT NULL, first_seen TEXT NOT NULL,
 PRIMARY KEY(source, external_id));
CREATE TABLE IF NOT EXISTS observations (
 source TEXT NOT NULL, external_id TEXT NOT NULL, observed_at TEXT NOT NULL,
 payload TEXT NOT NULL, PRIMARY KEY(source, external_id, observed_at),
 FOREIGN KEY(source, external_id) REFERENCES listings(source, external_id));
"""

def normalize(row):
    fields = ("source", "external_id", "url", "governorate", "wilayat",
              "area", "type", "deal", "published_at", "price", "area_m2")
    result = {k: row.get(k) for k in fields}
    for key in ("source", "external_id", "url"):
        if not isinstance(result[key], str) or not result[key].strip():
            raise ValueError("Missing " + key)
        result[key] = result[key].strip()
    url = urlsplit(result["url"])
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise ValueError("Invalid source URL")
    flags = []
    for key in ("price", "area_m2"):
        try:
            value = Decimal(str(result[key]))
            if not value.is_finite() or value <= 0:
                raise InvalidOperation
            result[key] = str(value.normalize())
        except (InvalidOperation, ValueError):
            result[key] = None
            flags.append("missing_or_invalid_" + key)
    for key in ("governorate", "wilayat", "type", "deal", "published_at"):
        if not result[key]:
            flags.append("missing_" + key)
    result["quality_flags"] = flags
    result["price_status"] = "advertised"
    return result

def ingest(db, rows, observed_at):
    stamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Observation requires timezone")
    stamp = stamp.astimezone(timezone.utc).isoformat()
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    with db:
        for raw in rows:
            row = normalize(raw)
            key = (row["source"], row["external_id"])
            db.execute("INSERT INTO listings VALUES (?,?,?) ON CONFLICT(source,external_id) DO UPDATE SET first_seen=min(first_seen,excluded.first_seen)", (*key, stamp))
            payload = json.dumps(row, ensure_ascii=False, sort_keys=True)
            previous = db.execute("SELECT payload FROM observations WHERE source=? AND external_id=? AND observed_at=?", (*key, stamp)).fetchone()
            if previous and previous[0] != payload:
                raise ValueError("Conflicting observation at identical timestamp")
            db.execute("INSERT OR IGNORE INTO observations VALUES (?,?,?,?)", (*key, stamp, payload))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--db", required=True)
    parser.add_argument("--observed-at", required=True)
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as stream, sqlite3.connect(args.db) as db:
        ingest(db, json.load(stream), args.observed_at)

if __name__ == "__main__":
    main()
