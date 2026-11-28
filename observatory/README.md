# Property Observatory — implementation contract
Keep main unchanged until reviewed. Build a nationwide directory, not brokerage or financing.
- Preserve source URL, source ID, publication date (nullable), first/last observed UTC, price and area, location and type.
- Append observations; never infer sale from disappearance. Prices are advertised unless independently verified.
- Exact source IDs identify listings; cross-source candidates require review, never auto-merge on price alone.
- Use permitted feeds/API or licensed imports only; no bypass of social platform restrictions. Track source failures and coverage.
- Export only approved public fields; keep raw records and credentials outside public GitHub Pages.
- Acceptance: real source ingestion, repeat-run idempotency, price history, freshness filters, nationwide geography, safe links, tests and review before deployment.
