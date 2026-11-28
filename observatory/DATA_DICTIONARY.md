# Data dictionary

All times are UTC ISO 8601 strings with explicit timezone offsets. Date-only publication values remain date-only. Null denotes an unknown or inapplicable field. Table and key definitions are in [schema.sql](rai/schema.sql).

| Table | Contents |
| --- | --- |
| data_sources | Stable provider key and private configuration metadata |
| source_collection_runs | Provider, start/end, batch or release, outcome, row counts, new listing count and failure reason |
| properties | Canonical properties created through explicit human review |
| property_listings | Stable source ID and external ID, confirmed property link and bounds of dated observation history |
| property_locations | Normalized governorate, wilayat, locally reported area, coordinates and accuracy |
| listing_observations | Observation/version identity, source run, classified listing fields, quoted price, verification and availability |
| price_history | Full valid-price ledger including unchanged quotations at later observations |
| quality_checks and quality_reviews | Detection codes by observation and subsequent review decisions |
| duplicate_candidates and duplicate_reviews | Candidate pairs, corroborating reasons, similarity, active status and manual decision audit |
| official_market_statistics | Publisher, indicator, period, geography, unit, figure, source URL and release fingerprint |
| geospatial_information | Attributed place/feature, type and coordinates |

### Listings

| Field family | Semantics |
| --- | --- |
| Identity | `source_id + external_id` uniquely identify one advertisement. `property_id` is nullable until a pairing is confirmed. |
| Location | Official codes for governorates and wilayats. `area` is source-reported and `area_key` supports spelling normalization. Local areas are populated as coverage becomes available. |
| Coordinates | `confirmed`, `source_reported`, `approximate` or `unknown`. Public coordinates are approximate and omitted when unavailable. |
| Offer | `kind` and `deal` distinguish land classes, homes, apartments, commercial and agricultural property, sale and rent. |
| Price | Decimal text, explicit currency, rental period and basis. Basis is advertised, advertiser-confirmed, independently verified or transaction. Unknown or invalid price may be null. |
| Size | `land_m2`, `built_m2` and bedrooms may be null. Land/farm unit prices use land area. Built assets use built-up area. |
| Dates | `published_at`, `first_observed`, `last_observed`, `last_verified` and observation time express different facts. Undated imported records keep null observation times and a stable snapshot version key. |
| Verification | `unverified`, `source_checked`, `advertiser_confirmed` or `independently_verified`. Claims above unverified require a verification time supplied by the approved source or reviewer. |
| Availability | `unknown`, `available`, `unreachable`, `withdrawn`, `sold_confirmed` or `let_confirmed`. Sold and let require independent verification. |
| Private and public | `public` is an affirmative row-level publication approval. The source-level policy is enforced again at export. Descriptions, exact coordinates and raw source identifiers are private. |
| Flags | Format/consistency flags, missing information, timestamp conflicts, price anomalies and outliers. A quality flag helps prioritize review. |

### Official figures

NCSI records are national monthly aggregates, with geographic annual-book series where available in the release. Each series retains its original publication URL and declared unit. MOHUP `published_dataset_rows` counts validated input rows by month and geography, suppressing cells under 20. These counts describe the downloadable files. They can include multiple source rows for the same event and are unsuitable as counts of transactions. The static snapshot publishes the latest known release of each source/indicator/period/geography series, while SQLite keeps revisions.
