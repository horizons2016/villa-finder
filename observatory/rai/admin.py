"""Loopback-only operational console; access via local browser or an SSH tunnel."""
import base64
import hmac
import html
import os
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .database import database
from .validation import utc


def review_quality(db, observation, code, decision, note):
    if decision not in ("acknowledged", "correction_requested"):
        raise ValueError("invalid quality decision")
    if not db.execute("SELECT 1 FROM quality_checks WHERE observation_id=? AND code=?", (observation, code)).fetchone():
        raise ValueError("quality flag does not exist")
    db.execute("INSERT INTO quality_reviews VALUES (NULL,?,?,?,?,?)", (observation, code, decision, note[:400], utc()))


def review_duplicate(db, left, right, decision, note):
    if decision not in ("confirmed", "different"):
        raise ValueError("invalid duplicate decision")
    pair = db.execute(
        "SELECT decision FROM duplicate_candidates WHERE left_id=? AND right_id=? AND active=1", (left, right),
    ).fetchone()
    if not pair or pair["decision"] != "pending":
        raise ValueError("candidate unavailable for review")
    if decision == "confirmed":
        properties = {row[0] for row in db.execute(
            "SELECT property_id FROM property_listings WHERE id IN (?,?) AND property_id IS NOT NULL", (left, right),
        )}
        if len(properties) > 1:
            raise ValueError("existing confirmed groups overlap; resolve provenance before merging")
        group = next(iter(properties), None)
        if group is None:
            group = db.execute(
                "INSERT INTO properties VALUES (NULL,?,'manual duplicate review')", (utc(),),
            ).lastrowid
        db.execute("UPDATE property_listings SET property_id=? WHERE id IN (?,?)", (group, left, right))
    db.execute(
        "UPDATE duplicate_candidates SET decision=?,reviewed_at=? WHERE left_id=? AND right_id=?",
        (decision, utc(), left, right),
    )
    db.execute("INSERT INTO duplicate_reviews VALUES (NULL,?,?,?,?,?)", (left, right, decision, note[:400], utc()))


def escape(value):
    return html.escape(str(value if value is not None else "—"), quote=True)


def table(headers, rows, actions=None):
    head = "".join(f"<th scope='col'>{escape(label)}</th>" for label in headers)
    body = []
    for row in rows:
        line = "".join(f"<td>{escape(value)}</td>" for value in row)
        if actions:
            line += "<td>" + actions(row) + "</td>"
        body.append("<tr>" + line + "</tr>")
    return "<table><thead><tr>" + head + ("<th scope='col'>Review</th>" if actions else "") + "</tr></thead><tbody>" + "".join(body) + "</tbody></table>"


def review_form(csrf, key, kind, options):
    buttons = "".join(f'<button name="decision" value="{escape(value)}">{escape(label)}</button>' for value, label in options)
    return (f'<form method="post" action="/review/{kind}"><input type="hidden" name="csrf" value="{escape(csrf)}">'
            f'<input type="hidden" name="key" value="{escape(key)}"><label>Review note '
            f'<input name="note" maxlength="400" required></label> {buttons}</form>')


def dashboard(db, path, csrf):
    summary = db.execute("""
      SELECT (SELECT count(*) FROM property_listings),
             (SELECT count(*) FROM listing_observations),
             (SELECT count(*) FROM listing_observations WHERE observed_at IS NOT NULL),
             (SELECT count(*) FROM official_market_statistics),
             (SELECT count(*) FROM geospatial_information),
             (SELECT count(*) FROM duplicate_candidates WHERE decision='pending' AND active=1),
             (SELECT count(*) FROM quality_checks)
    """).fetchone()
    source_rows = db.execute("""
        SELECT d.id,json_extract(d.definition,'$.status'),json_extract(d.definition,'$.coverage'),
        (SELECT count(*) FROM property_listings l WHERE l.source_id=d.id),
        (SELECT coalesce(sum(r.new_listings),0) FROM source_collection_runs r WHERE r.source_id=d.id),
        (SELECT MAX(r.ended_at) FROM source_collection_runs r WHERE r.source_id=d.id AND r.status='ok'
          AND (r.batch_id IS NULL OR d.id='osm')),
        (SELECT r.status FROM source_collection_runs r WHERE r.source_id=d.id ORDER BY r.id DESC LIMIT 1),
        (SELECT count(*) FROM source_collection_runs r WHERE r.source_id=d.id AND r.status IN ('failed','partial'))
        FROM data_sources d ORDER BY d.id
    """)
    runs = db.execute("""
        SELECT id,source_id,status,started_at,round((julianday(ended_at)-julianday(started_at))*86400,2),
        records,inserted,new_listings,rejected,error FROM source_collection_runs ORDER BY id DESC LIMIT 60
    """)
    flags = db.execute("""
        SELECT c.code,count(*) FROM quality_checks c JOIN current_listings o ON o.id=c.observation_id
        GROUP BY c.code ORDER BY count(*) DESC LIMIT 50
    """)
    queue = db.execute("""
        SELECT c.observation_id,c.code,o.source_id,o.wilayat,o.kind,o.price
        FROM quality_checks c JOIN current_listings o ON o.id=c.observation_id
        WHERE NOT EXISTS(SELECT 1 FROM quality_reviews r WHERE r.observation_id=c.observation_id AND r.code=c.code)
        ORDER BY o.id DESC,c.code LIMIT 50
    """)
    duplicates = db.execute("""
        SELECT d.left_id,d.right_id,d.score,d.reasons,a.source_id,b.source_id,a.wilayat,a.kind,a.price,b.price
        FROM duplicate_candidates d JOIN current_listings a ON a.listing_id=d.left_id
        JOIN current_listings b ON b.listing_id=d.right_id
        WHERE d.decision='pending' AND d.active=1 ORDER BY d.score DESC,d.left_id,d.right_id LIMIT 50
    """)
    headings = ("Listings", "Observations", "Dated observations", "Official release records", "GIS features",
                "Pending duplicates", "Historical quality flags", "Database + WAL bytes")
    size = sum(p.stat().st_size for p in (Path(path), Path(str(path) + "-wal")) if p.exists())
    parts = [
        table(headings, [[*summary, size]]),
        "<h2>Source coverage and health</h2>",
        table(("Source", "Configuration", "Coverage", "Listings", "First seen records", "Last successful collection UTC",
               "Latest run", "Failed or partial runs"), source_rows),
        "<h2>Recent collection runs</h2>",
        table(("Run", "Source", "Status", "Started UTC", "Seconds", "Rows", "Inserted", "New listings", "Rejected", "Error"), runs),
        "<h2>Current quality flags</h2>", table(("Issue", "Records"), flags),
        "<h2>Quality review queue</h2>",
        table(("Observation", "Issue", "Source", "Wilayat", "Property type", "Price"), queue,
              lambda row: review_form(csrf, f"{row[0]}:{row[1]}", "quality",
                                      [("acknowledged", "Acknowledge"), ("correction_requested", "Request correction")])),
        "<h2>Duplicate candidates</h2>",
        table(("Listing A", "Listing B", "Score", "Reasons", "Source A", "Source B", "Wilayat", "Type", "Price A", "Price B"),
              duplicates, lambda row: review_form(csrf, f"{row[0]}:{row[1]}", "duplicate",
                                                  [("confirmed", "Confirm same property"), ("different", "Mark different")])),
    ]
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
    <title>RAI Property Intelligence Operations</title><style>
    body{font:16px system-ui;color:#102641;background:#f2f7fa;margin:1rem}
    h1,h2{line-height:1.2}table{display:block;overflow:auto;background:white;border-collapse:collapse;margin-bottom:1rem}
    th,td{text-align:left;padding:.45rem;border-bottom:1px solid #c9d8e2;white-space:nowrap}
    button,input{font:inherit}button{margin:.15rem}</style>
    <h1>RAI Property Intelligence Operations</h1>
    <p>Collection times are UTC. Corrections create a later observation through an authorized import.</p>""" + "".join(parts) + "</html>"


def serve(path, port):
    password = os.environ.get("RAI_ADMIN_PASSWORD", "")
    if len(password) < 20:
        raise SystemExit("Set RAI_ADMIN_PASSWORD with a strong secret of at least 20 characters.")
    credentials = "Basic " + base64.b64encode(("rai:" + password).encode()).decode()
    csrf = secrets.token_urlsafe(32)
    allowed_host = f"127.0.0.1:{port}"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, content="", location=None):
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
            if status == 401:
                self.send_header("WWW-Authenticate", 'Basic realm="RAI Operations", charset="UTF-8"')
            if location:
                self.send_header("Location", location)
            payload = content.encode()
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def authorized(self):
            if self.headers.get("Host") != allowed_host:
                self.reply(400, "Invalid host")
                return False
            provided = self.headers.get("Authorization", "")
            if not hmac.compare_digest(provided.encode(), credentials.encode()):
                self.reply(401, "Authentication required")
                return False
            return True

        def do_GET(self):
            if not self.authorized():
                return
            if self.path != "/":
                self.reply(404, "Page unavailable")
                return
            with database(path) as db:
                self.reply(200, dashboard(db, path, csrf))

        def do_POST(self):
            if not self.authorized():
                return
            action = urlsplit(self.path).path
            if action not in ("/review/quality", "/review/duplicate"):
                self.reply(404, "Page unavailable")
                return
            if self.headers.get("Origin") != f"http://{allowed_host}":
                self.reply(403, "Invalid origin")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length < 8192:
                    raise ValueError("Invalid review form length")
                form = parse_qs(self.rfile.read(length).decode(), max_num_fields=4, strict_parsing=True)
                if not hmac.compare_digest(form["csrf"][0].encode(), csrf.encode()):
                    self.reply(403, "Invalid review token")
                    return
                identifier, extra = form["key"][0].split(":", 1)
                decision, note = form["decision"][0], form["note"][0].strip()
                if not note:
                    raise ValueError("Review note is required")
                with database(path) as db, db:
                    db.execute("BEGIN IMMEDIATE")
                    if action == "/review/quality":
                        review_quality(db, int(identifier), extra, decision, note)
                    else:
                        review_duplicate(db, int(identifier), int(extra), decision, note)
            except (KeyError, ValueError, UnicodeError):
                self.reply(400, "Review could not be saved. Reload the console and check the review fields.")
                return
            self.reply(303, location="/")

    with database(path):
        pass
    server = HTTPServer(("127.0.0.1", port), Handler)
    print(f"RAI Operations http://{allowed_host}/", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
