# Project status · 28 November 2026

**Release state** — Review release with a functional bilingual browse shell, official real estate statistics, licensed map points, a private historical store and an authenticated local operations console. The production listing service requires authorized data.

| Area | State and evidence |
| --- | --- |
| Real integrations | Three source integrations exercised: NCSI and MOHUP from their official websites, and OpenStreetMap from the existing licensed repository extract. Fourteen entries in the discovery registry. |
| Listing inventory | 247 existing records imported privately: 211 Oman Real, 33 OpenSooq and 3 Bayut. Locations are Seeb and Jalan Bani Bu Ali. Zero new live listings and zero public listings. |
| Historical observations | 247 baseline observations and associated advertised prices imported with an undated observation marker. Zero dated live observations or observed live price changes. Publication fields, where known, are separate. |
| Official dataset | 239 release-level observation rows in SQLite. 215 latest values in the review snapshot, of which 180 are NCSI and 35 are MOHUP published-file row counts. NCSI has 132 governorate figures for 2025 plus national figures for 12 observed months between September 2025 and October 2026. June and July 2026 remain gaps in the national series. |
| Geographic directory | 11 governorates and 63 wilayats. Local areas are linked to the input records. Official governorate-level traded values cover all 11 in the 2025 annual-book series. The 215-service snapshot has limited coverage in Muscat. |
| Quality | All 247 inventory records remain unverified. 74 lack publication dates, 7 lack usable dimensions, 8 advertised prices and 6 unit prices were flagged as statistical outliers. Zero candidate pairs met the conservative rule on the legacy dataset. The number of unique underlying properties is unknown. |
| Hosting | The separately hosted, owner-only static preview is deployed and the deployment provider confirmed readiness. An unauthenticated request was denied. The existing GitHub Pages root returned HTTP 200. The office refresh script completed a manual run for all three enabled sources. Unattended operation requires a persistent RAI-controlled host. |
| Cost | Standard library, SQLite and Leaflet. Open government datasets and OSM tiles for policy-compliant preview traffic. Zero paid purchases. Office storage, backups and production tile service depend on the hosting arrangement. |

## Reproducible continuation

1. Validate an existing or new partner feed agreement against the provider's collection, retention and public-use scope. Configure it in a private file and keep credentials in the environment.
2. Run an actual feed collection, a second timed reading and an explicit availability-status update. Check data coverage, price history and public-field exports.
3. Enable collection scheduling, monitoring and backups on the persistent office host. For authorized production use, deploy the export and front end to the approved production path.
4. Expand GIS using a licensed extract and review high-volume map hosting. Add load tests using an appropriately licensed data volume. Retain the SQLite-to-PostGIS cutover criteria in [architecture](ARCHITECTURE.md).

GitHub review: [draft pull request #1](https://github.com/horizons2016/villa-finder/pull/1). The published Villa Finder remains on its existing branch.

See [test report](TEST_REPORT.md) and [deployment](DEPLOYMENT.md) for exact commands and verification limits.
