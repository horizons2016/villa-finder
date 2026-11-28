# Deployment

## Static preview

Build only the approved site payload. Preview and public hosting must serve the resulting directory, with `index.html`, `ui/` and `public-data.json`. Keep the operations console and SQLite on a trusted private host.

```sh
cd observatory
python -m rai build dist
```

The checked-in snapshot is reproducible from the collection commands. To build a refreshed state, use `python -m rai build dist --snapshot state/public-data.json`. Deploy the dist contents to a separate review host or path. For GitHub Pages, use a separately approved path/branch or domain, leaving the existing root deployment in place. The included branch workflow runs tests and builds an artifact. GitHub schedules read their workflow from the default branch, so this feature branch does not start a scheduled job. GitHub-hosted jobs also need a private durable store for operational SQLite and approved feed secrets. A public Actions artifact is suitable for the approved static bundle.

## Always-on office host

On a Linux host with Python, SQLite and Poppler installed, clone the reviewed branch to an account controlled by RAI. Reserve private storage for state and backups. Supply environment variables from an owner-readable service environment file. Configure cron under the service account using local Muscat time, or translate 04:15 Oman time to 00:15 UTC on a UTC host. Replace the placeholder absolute paths and keep the logs private.

```cron
15 4 * * * /usr/bin/flock -n /srv/rai-property/observatory/state/refresh.lock /srv/rai-property/observatory/ops/refresh.sh >> /srv/rai-property/observatory/state/collection.log 2>&1
```

Create the state directory first with mode 0700. Load any nondefault environment variables via your service supervisor or an owner-readable wrapper. The job collection and export proceed independently of searches. A partial source run produces a nonzero exit status and exports the last persisted valid data. Rotate logs. Review failures in the admin console. Tune cadence to provider authorization terms.

## Authorized feeds and imports

Provide `RAI_SOURCE_CONFIG` as the path to a private JSON mapping whose keys are stable provider IDs. A source needs a recorded permission reference. One example shape follows. The example host is a placeholder.

```json
{
  "example-agency": {
    "name": "Example Agency",
    "url": "https://example.com/",
    "hosts": ["example.com"],
    "feed_url": "https://example.com/rai-approved-feed.json",
    "bearer_env": "RAI_PARTNER_TOKEN",
    "permission_reference": "private agreement ID and retention/publication terms",
    "publish_listings": false,
    "coverage": "Contract scope"
  }
}
```

The scheduled adapter reads a JSON array from the approved feed. Omit feed_url for manual-only access and use `python -m rai import example-agency approved.json --observed-at 2026-11-28T00:00:00Z` with the actual UTC collection timestamp. The row format uses `external_id`, `url`, `governorate`, `wilayat`, `area`, `kind`, `deal`, `price`, `currency`, `rental_period`, `land_m2`, `built_m2`, `bedrooms`, `latitude`, `longitude`, `accuracy`, `published_at`, `last_verified`, `verification`, `availability`, `price_basis`, `description` and `public`. Use public flags only within the provider's scope. Keep credentials in the process environment or an approved secret store.

### Start with a direct agency or developer export

Download the [partner CSV template](partner-listings-template.csv), fill it using the partner's own inventory and save it as UTF-8 CSV. Excel can open and export that format. Start with a partner able to share stable listing IDs and individual listing URLs on an approved domain. Record authorization for ingestion and separate permission for publishing the selected fields. The importer defaults each row to private unless the partner's approved file explicitly marks it public. Keep the filled file and permission reference outside the repository.

For a manual provider, configure the approved source without `feed_url` and use the same import command with a `.csv` file. CSV values for `public` include `true`, `yes` or `نعم`. Use the same `external_id` and a fresh observation timestamp for later exports. Send explicit availability changes to distinguish withdrawals or unreachability from an omitted row. The existing export command generates the vetted publishable snapshot.

## Operations and recovery

- Start `python -m rai admin` with an environment-provided high-entropy `RAI_ADMIN_PASSWORD`. Sign in at `http://127.0.0.1:8766/` as `rai`. Use an SSH tunnel if remote. Serve the console only on loopback, with authentication and CSRF checks.
- Run `python -m rai backup /private/backups/observatory-YYYY-MM-DD.sqlite` regularly and keep a copy on controlled storage. SQLite's backup API includes committed WAL contents. Encrypt backups at rest and apply institutional retention.
- Stop writers for restoration, move the failed SQLite and WAL files to a quarantine path, restore a verified backup, and run SQLite integrity and foreign-key checks. Restart with a permitted collector run, rebuild the approved export and compare the results with the previous release.
- For a pre-existing v0 SQLite file from `engine.py`, run `python -m rai --db state/observatory.sqlite migrate-legacy-db /private/old.sqlite`. Use a different destination. This keeps the source file intact and migrates matched observations as private, recording unresolved sources and rejected rows.

The application has no paid API requirement. Computation, storage, backup, and availability depend on the chosen host. The standard OSM tile service is best effort and suited to policy-compliant preview traffic. Higher load requires a reviewed tile provider or self-hosting.
