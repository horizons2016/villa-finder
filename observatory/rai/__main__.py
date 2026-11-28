"""Operate the property observatory from the office or CI."""
import argparse
import csv
import json
import logging
import os
from pathlib import Path

from .adapters import authorized_file
from .collector import collect, import_legacy, load_sources, migrate_legacy_database, run_listings
from .database import backup, database, register
from .export import atomic_json, build_site, make_export
from .quality import refresh
from .validation import utc


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=os.environ.get("RAI_DB", "state/observatory.sqlite"))
    parser.add_argument("--config", default=os.environ.get("RAI_SOURCE_CONFIG"))
    commands = parser.add_subparsers(dest="action", required=True)
    collection = commands.add_parser("collect")
    collection.add_argument("--source", action="append")
    collection.add_argument("--refresh", action="store_true")
    collection.add_argument("--poi-file")
    commands.add_parser("legacy")
    migrate = commands.add_parser("migrate-legacy-db")
    migrate.add_argument("file", type=Path)
    manual = commands.add_parser("import")
    manual.add_argument("source")
    manual.add_argument("file", type=Path)
    manual.add_argument("--observed-at", required=True)
    export = commands.add_parser("export")
    export.add_argument("file", type=Path)
    build = commands.add_parser("build")
    build.add_argument("output", type=Path)
    build.add_argument("--snapshot", type=Path, default=Path("public-data.json"))
    backup_cmd = commands.add_parser("backup")
    backup_cmd.add_argument("file", type=Path)
    admin = commands.add_parser("admin")
    admin.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.action == "build":
        build_site(args.output, args.snapshot)
        return 0
    if args.action == "admin":
        from .admin import serve
        serve(args.db, args.port)
        return 0
    sources = load_sources(args.config)
    if args.action in ("collect", "import") and getattr(args, "source", None):
        selected = args.source if isinstance(args.source, list) else [args.source]
        if any(key not in sources for key in selected):
            parser.error("unknown source")
        if args.action == "collect" and any(sources[key]["status"] != "enabled" for key in selected):
            parser.error("one or more sources are disabled")
    with database(args.db) as db:
        if args.action == "legacy":
            register(db, sources)
            print(json.dumps(import_legacy(db, sources), ensure_ascii=False))
        elif args.action == "migrate-legacy-db":
            register(db, sources)
            result = migrate_legacy_database(db, args.file, sources)
            print(json.dumps(result))
            return int(bool(result["unknown_source"] or result["rejected"]))
        elif args.action == "collect":
            statuses = collect(db, sources, args.source, args.refresh, poi_path=args.poi_file)
            print(json.dumps(statuses, ensure_ascii=False))
            return int(any(status != "ok" for status in statuses.values()))
        elif args.action == "import":
            source = sources[args.source]
            if not source.get("permission_reference"):
                parser.error("import requires a locally configured authorization reference")
            if args.file.stat().st_size > 24 * 1024 * 1024:
                parser.error("input exceeds the import size budget")
            register(db, sources)
            try:
                rows = authorized_file(args.file)
            except (ValueError, csv.Error) as error:
                parser.error(f"invalid listing file: {error}")
            result = run_listings(db, source, rows, utc(args.observed_at))
            with db:
                db.execute("BEGIN IMMEDIATE")
                refresh(db)
            print(json.dumps(result))
            return int(result["rejected"] > result["exact_repeats"])
        elif args.action == "export":
            atomic_json(args.file, make_export(db, sources))
        elif args.action == "backup":
            backup(db, args.file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
