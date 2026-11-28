CREATE TABLE IF NOT EXISTS data_sources (
    id TEXT PRIMARY KEY, definition TEXT NOT NULL CHECK(json_valid(definition))
);
CREATE TABLE IF NOT EXISTS source_collection_runs (
    id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES data_sources,
    started_at TEXT NOT NULL, ended_at TEXT, status TEXT NOT NULL,
    records INTEGER NOT NULL DEFAULT 0, inserted INTEGER NOT NULL DEFAULT 0,
    rejected INTEGER NOT NULL DEFAULT 0, new_listings INTEGER NOT NULL DEFAULT 0,
    error TEXT, batch_id TEXT
);
CREATE INDEX IF NOT EXISTS runs_by_source ON source_collection_runs(source_id, id DESC);
CREATE TABLE IF NOT EXISTS properties (
    id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, basis TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS property_locations (
    id INTEGER PRIMARY KEY, governorate TEXT, wilayat TEXT, area TEXT, area_key TEXT,
    latitude REAL, longitude REAL, accuracy TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS property_listings (
    id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES data_sources,
    external_id TEXT NOT NULL, property_id INTEGER REFERENCES properties,
    first_observed TEXT, last_observed TEXT,
    UNIQUE(source_id, external_id)
);
CREATE TABLE IF NOT EXISTS listing_observations (
    id INTEGER PRIMARY KEY, listing_id INTEGER NOT NULL REFERENCES property_listings,
    run_id INTEGER NOT NULL REFERENCES source_collection_runs,
    location_id INTEGER NOT NULL REFERENCES property_locations, observed_at TEXT,
    version_key TEXT NOT NULL, url TEXT NOT NULL, kind TEXT, deal TEXT,
    published_at TEXT, price TEXT, currency TEXT, rental_period TEXT,
    land_m2 REAL, built_m2 REAL, bedrooms INTEGER, description TEXT,
    last_verified TEXT, verification TEXT NOT NULL, availability TEXT NOT NULL,
    price_basis TEXT NOT NULL, public INTEGER NOT NULL CHECK(public IN (0, 1)),
    flags TEXT NOT NULL CHECK(json_valid(flags)), payload_hash TEXT NOT NULL,
    UNIQUE(listing_id, version_key)
);
CREATE INDEX IF NOT EXISTS observations_listing_date ON listing_observations(listing_id, observed_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS observations_url ON listing_observations(url);
CREATE TABLE IF NOT EXISTS price_history (
    observation_id INTEGER PRIMARY KEY REFERENCES listing_observations,
    listing_id INTEGER NOT NULL REFERENCES property_listings,
    observed_at TEXT, amount TEXT NOT NULL, currency TEXT, rental_period TEXT, basis TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS quality_checks (
    observation_id INTEGER NOT NULL REFERENCES listing_observations,
    code TEXT NOT NULL,
    PRIMARY KEY (observation_id, code)
);
CREATE TABLE IF NOT EXISTS quality_reviews (
    id INTEGER PRIMARY KEY, observation_id INTEGER NOT NULL REFERENCES listing_observations,
    code TEXT NOT NULL, decision TEXT NOT NULL, note TEXT NOT NULL, reviewed_at TEXT NOT NULL,
    FOREIGN KEY(observation_id, code) REFERENCES quality_checks(observation_id, code)
);
CREATE TABLE IF NOT EXISTS duplicate_candidates (
    left_id INTEGER NOT NULL REFERENCES property_listings,
    right_id INTEGER NOT NULL REFERENCES property_listings,
    reasons TEXT NOT NULL, score REAL NOT NULL, decision TEXT NOT NULL DEFAULT 'pending',
    reviewed_at TEXT, active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY(left_id, right_id), CHECK(left_id < right_id)
);
CREATE TABLE IF NOT EXISTS official_market_statistics (
    id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES data_sources,
    run_id INTEGER NOT NULL REFERENCES source_collection_runs,
    indicator TEXT NOT NULL, period TEXT NOT NULL, geography TEXT NOT NULL,
    value TEXT NOT NULL, unit TEXT NOT NULL, url TEXT NOT NULL, release_id TEXT NOT NULL,
    UNIQUE(source_id, indicator, period, geography, release_id)
);
CREATE TABLE IF NOT EXISTS geospatial_information (
    source_id TEXT NOT NULL REFERENCES data_sources, external_id TEXT NOT NULL,
    category TEXT NOT NULL, name TEXT, latitude REAL NOT NULL, longitude REAL NOT NULL,
    PRIMARY KEY(source_id, external_id)
);
CREATE VIEW IF NOT EXISTS current_listings AS
SELECT o.*, l.source_id, l.external_id, l.property_id, l.first_observed, l.last_observed,
       p.governorate, p.wilayat, p.area, p.area_key, p.latitude, p.longitude, p.accuracy
FROM property_listings AS l
JOIN listing_observations AS o ON o.id = (
    SELECT id FROM listing_observations
    WHERE listing_id = l.id ORDER BY observed_at DESC, id DESC LIMIT 1
)
JOIN property_locations AS p ON p.id = o.location_id;
CREATE TABLE IF NOT EXISTS duplicate_reviews (
    id INTEGER PRIMARY KEY, left_id INTEGER NOT NULL, right_id INTEGER NOT NULL,
    decision TEXT NOT NULL, note TEXT NOT NULL, reviewed_at TEXT NOT NULL,
    FOREIGN KEY(left_id,right_id) REFERENCES duplicate_candidates(left_id,right_id)
);
