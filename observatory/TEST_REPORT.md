# Test report · 28 November 2026

## Passed

| Check | Result |
| --- | --- |
| Automated Python suite | 15/15 passed on Python 3.12. Includes exact repeats, idempotency, old-engine migration, out-of-order price history, candidate matching and review, source failure and recovery, privacy gating, open-data parser layouts and statistical validation. |
| Actual official data collection | Six NCSI monthly PDF editions and one Statistical Year Book downloaded and parsed. Three MOHUP CSV files downloaded and parsed. Initial MOHUP failures on two legacy CSV layouts reproduced and corrected. |
| Real geospatial snapshot | 215 OSM points imported from the existing repository. Browser enabled the schools layer and rendered 51 markers with attribution. |
| Database consistency | SQLite integrity check returned `ok` and foreign key check returned zero violations. SQLite backup restored a test database with the expected review row. |
| Browser desktop | Arabic RTL and English LTR, governorate-dependent wilayat selectors, national and governorate figures, map controls, source links and empty directory rendered. |
| Browser narrow viewport | 375 CSS-pixel document with no page overflow. Fixture listings tested list view, listing detail, dated price history, links and comparison. Test data excluded from the release directory. |
| Defensive verification | Invalid URLs rejected, private fields excluded, query strings stripped, unconfirmed sale treated as unknown and markup rendered as text. Local admin verified status codes for authentication, host, Origin, CSRF and an approved review write. |
| Build and product separation | JavaScript syntax check and Python compilation passed. The isolated release contains approved UI and a static snapshot. Existing Villa Finder returned HTTP 200. |

## Gaps

- Production live listing collection, end-to-end removal detection and time-series verification await an authorized live feed. Browser listing interactions used clearly identified test fixtures.
- POI coverage beyond the existing Muscat extract, road geometry, travel distances, environmental datasets, nationwide load benchmarks and PostgreSQL/PostGIS migration were outside the tested runtime.
- Office cron deployment and uptime are unverified. The scheduled job script can be run manually using the same commands. GitHub push and PR runs validate only the branch build and tests.
