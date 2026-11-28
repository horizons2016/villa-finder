"""Tests use synthetic listing rows and offline publication-format fixtures."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from rai.adapters import MONTHS, mohup_rows, ncsi_rows, ncsi_yearbook_rows
from rai.admin import dashboard, review_duplicate, review_quality
from rai.collector import collect, import_legacy, load_sources, migrate_legacy_database, run_listings
from rai.database import backup, database, register
from rai.export import make_export
from rai.geo import GEOGRAPHY, distance_km, place
from rai.quality import outliers, refresh
from rai.validation import normalize_listing, safe_url, utc


FIRST = "2026-01-01T00:00:00+00:00"
SECOND = "2026-02-01T00:00:00+00:00"
THIRD = "2026-03-01T00:00:00+00:00"
SOURCE = {"id": "fixture", "name": "Synthetic", "url": "https://example.com", "hosts": ["example.com"],
          "status": "enabled", "adapter": "feed", "feed_url": "https://example.com/feed",
          "categories": ["listings"], "publish_listings": True}
OTHER = {**SOURCE, "id": "other", "url": "https://example.org", "hosts": ["example.org"]}


def synthetic(**updates):
    return {
        "external_id": "test-house-1", "url": "https://example.com/property/1", "governorate": "مُحافظة مسقط",
        "wilayat": "A'Seeb", "area": "Test area", "type": "house", "deal": "sale", "land_m2": 350,
        "built_m2": 250, "price": 100000, "currency": "OMR", "public": True, "bedrooms": 4,
        "latitude": 23.6301, "longitude": 58.1878, "accuracy": "source_reported",
        "description": "Synthetic listing has quality marble and a large garden",
        **updates,
    }


class GeographyAndValidation(unittest.TestCase):
    def test_official_hierarchy_and_aliases(self):
        governors = GEOGRAPHY["governorates"]
        self.assertEqual(len(governors), 11)
        identifiers = [w[0] for *_, cities in governors for w in cities]
        self.assertEqual(len(set(identifiers)), 63)
        self.assertEqual(place("مسقط", "ولاية السِّيب", "A")[:2], ("muscat", "seeb"))
        self.assertEqual(place(None, "Al Jabal Al Akhdar", None)[:2], ("dakhiliyah", "jabal-akhdar"))
        self.assertEqual(place(None, "سناو", None)[:2], ("north-sharqiyah", "sinaw"))
        self.assertIn("geographic_conflict", place("Dhofar", "Seeb", None)[3])
        self.assertAlmostEqual(distance_km(23, 58, 23, 59), 102.35, delta=.1)

    def test_flags_and_unsubstantiated_status(self):
        row = normalize_listing(synthetic(deal="rent", price=-5, built_m2=-200, published_at="invalid",
                                          availability="sold_confirmed", price_basis="transaction",
                                          latitude=70), SOURCE, utc(FIRST))
        for key in ("missing_rental_period", "invalid_price", "invalid_built_m2", "invalid_coordinates",
                    "invalid_publication_date", "verification_required", "unsubstantiated_status",
                    "unsubstantiated_price_basis"):
            self.assertIn(key, row["flags"])
        self.assertEqual(row["availability"], "unknown")
        self.assertEqual(row["price_basis"], "advertised")
        self.assertIsNone(row["published_at"])
        self.assertIsNone(row["latitude"])

    def test_urls_fail_closed(self):
        for url in ("javascript:alert(1)", "http://example.com/property", "https://example.com@other.org/a",
                    "https://example.com:8000/a", "https://example.com.evil.test/a", "https://example.com/a b",
                    "https://example.com\\@other.org/", "https://127.0.0.1/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                safe_url(url, SOURCE["hosts"])
        self.assertEqual(safe_url("https://example.com/1#fragment", SOURCE["hosts"]), "https://example.com/1")

    def test_robust_outlier_sample_minimum(self):
        self.assertEqual(outliers(list(enumerate([100] * 6 + [500]))), [])
        self.assertEqual(outliers(list(enumerate([100] * 7 + [500]))), [7])
        self.assertEqual(outliers(list(enumerate([98, 99, 100, 100, 100, 101, 102, 900]))), [7])


class Persistence(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "test.sqlite"
        self.manager = database(self.path)
        self.db = self.manager.__enter__()
        self.addCleanup(self.manager.__exit__, None, None, None)
        self.sources = {SOURCE["id"]: SOURCE, OTHER["id"]: OTHER}
        register(self.db, self.sources)

    def query(self, sql):
        return [tuple(row) for row in self.db.execute(sql)]

    def test_ordered_history_idempotency_and_conflict(self):
        self.assertEqual(run_listings(self.db, SOURCE, [synthetic(price=170000)], THIRD)["new"], 1)
        run_listings(self.db, SOURCE, [synthetic()], FIRST)
        run_listings(self.db, SOURCE, [synthetic()], SECOND)
        self.assertEqual(run_listings(self.db, SOURCE, [synthetic()] * 2, SECOND)["exact_repeats"], 1)
        self.assertEqual(run_listings(self.db, SOURCE, [synthetic(price=120000)], SECOND)["rejected"], 1)
        with self.db:
            refresh(self.db)
        self.assertEqual(self.query("SELECT amount FROM price_history ORDER BY observed_at"),
                         [("100000",), ("100000",), ("170000",)])
        self.assertEqual(self.query("SELECT first_observed,last_observed FROM property_listings"), [(utc(FIRST), utc(THIRD))])
        self.assertIn(("conflicting_source_record",), self.query("SELECT code FROM quality_checks"))
        self.assertIn(("large_price_change",), self.query("SELECT code FROM quality_checks"))
        snapshot = make_export(self.db, self.sources, FIRST)
        self.assertEqual(len(snapshot["listings"][0]["price_history"]), 2)
        self.assertEqual(snapshot["listings"][0]["price_history"][1]["previous"], "100000")
        self.assertEqual(self.query("PRAGMA foreign_key_check"), [])

    def test_legacy_sources_stay_private_and_idempotent(self):
        sources = load_sources()
        register(self.db, sources)
        records = import_legacy(self.db, sources)
        self.assertEqual(sum(run["inserted"] for run in records.values()), 247)
        self.assertEqual(sum(run["inserted"] for run in import_legacy(self.db, sources).values()), 0)
        self.assertEqual(self.query("SELECT count(*) FROM listing_observations WHERE observed_at IS NOT NULL"), [(0,)])
        self.assertEqual(make_export(self.db, sources, FIRST)["listings"], [])

    def test_migrate_existing_engine_database_without_altering_it(self):
        from engine import ingest
        old = self.path.with_name("old.sqlite")
        legacy_row = synthetic(source="Oman Real", url="https://omanreal.com/properties/TEST1", type="فيلا", area_m2=350)
        with sqlite3.connect(old) as connection:
            ingest(connection, [legacy_row], FIRST)
        previous = old.read_bytes()
        sources = load_sources()
        register(self.db, sources)
        result = migrate_legacy_database(self.db, old, sources)
        self.assertEqual(result, {"migrated": 1, "rejected": 0, "unknown_source": 0})
        self.assertEqual(migrate_legacy_database(self.db, old, sources)["migrated"], 0)
        self.assertEqual(old.read_bytes(), previous)
        self.assertEqual(self.query("SELECT public,currency FROM listing_observations"), [(0, None)])

    def test_public_export_withholds_private_fields_and_readings(self):
        guarded = synthetic(url="https://example.com/property/1?token=DO_NOT_PUBLISH")
        run_listings(self.db, SOURCE, [{**guarded, "public": False}], FIRST)
        run_listings(self.db, SOURCE, [guarded], SECOND)
        run_listings(self.db, {**OTHER, "publish_listings": False}, [
            synthetic(url="https://example.org/secret", description="private details")
        ], THIRD)
        snapshot = make_export(self.db, self.sources, FIRST)
        self.assertEqual(len(snapshot["listings"]), 1)
        row = snapshot["listings"][0]
        self.assertEqual(row["first_observed"], utc(SECOND))
        self.assertEqual(row["url"], "https://example.com/property/1")
        self.assertEqual(row["latitude"], 23.63)
        self.assertEqual(row["accuracy"], "approximate")
        self.assertNotIn("description", row)
        self.assertNotIn("DO_NOT_PUBLISH", json.dumps(snapshot))

    def test_candidate_cannot_merge_without_review(self):
        run_listings(self.db, SOURCE, [synthetic()], FIRST)
        run_listings(self.db, OTHER, [synthetic(url="https://example.org/2")], FIRST)
        with self.db:
            refresh(self.db)
        self.assertEqual(self.query("SELECT decision FROM duplicate_candidates"), [("pending",)])
        self.assertEqual(self.query("SELECT count(property_id) FROM property_listings"), [(0,)])
        row = self.db.execute("SELECT left_id,right_id FROM duplicate_candidates").fetchone()
        with self.db:
            review_duplicate(self.db, *row, "confirmed", "Synthetic review")
        self.assertEqual(self.query("SELECT count(DISTINCT property_id) FROM property_listings"), [(1,)])
        self.assertEqual(self.query("SELECT decision FROM duplicate_reviews"), [("confirmed",)])
        self.assertEqual(len({x["canonical_group"] for x in make_export(self.db, self.sources)["listings"]}), 1)

    def test_price_and_location_alone_do_not_generate_candidate(self):
        a = synthetic(description=None, latitude=None, longitude=None)
        b = {**a, "url": "https://example.org/2"}
        run_listings(self.db, SOURCE, [a], FIRST)
        run_listings(self.db, OTHER, [b], FIRST)
        with self.db:
            refresh(self.db)
        self.assertEqual(self.query("SELECT count(*) FROM duplicate_candidates"), [(0,)])

    def test_source_failure_isolated_and_recoverable(self):
        ncalls = 0
        def get(url, hosts, bearer):
            nonlocal ncalls
            if url == SOURCE["feed_url"]:
                ncalls += 1
                if ncalls == 1:
                    raise RuntimeError("HTTP 503")
                return json.dumps([synthetic()]).encode()
            return json.dumps([synthetic(url="https://example.org/1")]).encode()
        sources = {**self.sources, "other": {**OTHER, "feed_url": "https://example.org/feed"}}
        self.assertEqual(collect(self.db, sources, get=get), {"fixture": "failed", "other": "ok"})
        self.assertEqual(collect(self.db, sources, get=get), {"fixture": "ok", "other": "ok"})
        self.assertEqual(self.query("SELECT count(*) FROM property_listings"), [(2,)])

    def test_admin_quality_review_and_backup(self):
        run_listings(self.db, SOURCE, [synthetic()], FIRST)
        observation, code = self.db.execute("SELECT observation_id,code FROM quality_checks LIMIT 1").fetchone()
        with self.db:
            review_quality(self.db, observation, code, "acknowledged", "<script>hardcoded test</script>")
        self.assertNotIn("<script>", dashboard(self.db, self.path, "csrf"))
        destination = self.path.with_name("backup.sqlite")
        backup(self.db, destination)
        with sqlite3.connect(destination) as saved:
            self.assertEqual(saved.execute("PRAGMA quick_check").fetchone(), ("ok",))
            self.assertEqual(saved.execute("SELECT count(*) FROM quality_reviews").fetchone(), (1,))


class GovernmentAdapters(unittest.TestCase):
    def test_synthetic_ncsi_layout_uses_monthly_not_ytd(self):
        content = """29 - Real-Estate activity In The Sultanate of Oman
Item  Total (End - Oct)
Traded value of property in the  -0.7  2,627.5  2,646.2  296.0  343.0  272.7  3,367.8  label
Traded value of sales contracts  9.8  1,205.9  1,098.1  129.8  124.0  109.0  1,270.3  label
Sales contracts (No.)  -1.6  55,625  56,509  5,556  5,460  4,904  67,074  label
Properties issued (No.)  -15.4  166,725  197,038  18,406  16,375  12,092  233,172  label
"""
        points = list(ncsi_rows(content, (2026, 11), "https://example.com"))
        self.assertEqual(len(points), 12)
        self.assertEqual(points[0][:5], ("traded_property_value", "2026-10", "oman", "296.0", "million_omr"))
        with self.assertRaises(ValueError):
            list(ncsi_rows(content, (2026, 10), "https://example.com"))

    def test_ncsi_yearbook_all_governorates_and_rounding(self):
        header = """5-3
Traded Value of Property by Governorates and Month
2025
Total  Al Wusta  Al Buraymi  Musandam  Dhofar  Muscat
"""
        figures = "11.0" + " 1.0" * 11
        content = header + "\n".join(f"{month}  {figures}" for month in MONTHS)
        records = list(ncsi_yearbook_rows(content, "https://example.com"))
        self.assertEqual(len(records), 132)
        self.assertEqual(len({row[2] for row in records}), 11)
        with self.assertRaises(ValueError):
            list(ncsi_yearbook_rows(content.replace("11.0", "5.0"), "https://example.com"))

    def test_mohup_aggregate_and_suppression(self):
        header = "TRANSACTION_DATE;REGION_AR;WILAYAT_AR;SERVICE_SUB_ID;REDACTED\n"
        line = "01-10-2024;مسقط;السيب;ABC;discard-me\n"
        rare = "01-10-2024;ظفار;صلالة;ABC;discard-me\n"
        records = list(mohup_rows((header + line * 20 + rare).encode(), "https://example.com"))
        self.assertEqual([(x[2], x[3]) for x in records], [("muscat", "20"), ("oman", "21")])
        self.assertNotIn("discard-me", str(records))
        old = "08-12-2022;Individual;جنوب الباطنة;South Batinah;بركاء;Barka;a;b;c;d;1\n"
        records = list(mohup_rows((old * 20 + old[:-4] + "\n").encode(), "https://example.com"))
        self.assertEqual([(x[2], x[3]) for x in records], [("oman", "20"), ("south-batinah", "20")])


if __name__ == "__main__":
    unittest.main()
