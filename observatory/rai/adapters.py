"""Independent authorized feed, open publication, and snapshot adapters."""
import calendar
import csv
import html
import io
import json
import re
import subprocess
import time
from collections import Counter
from datetime import date, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .geo import place
from .validation import coordinates, safe_url, text

MAX_DOWNLOAD = 24 * 1024 * 1024
PORTAL_PDF = re.compile(
    r'https://api\.ncsi\.gov\.om/uploads/pdfs/monthly_statistical_bulletin_+([a-z]+)_?(20\d\d)_\d+\.pdf',
    re.I,
)
MOHUP_CSV = re.compile(r"https://cms\.mohup\.gov\.om/uploads/CSV_[A-Za-z0-9_]+\.csv")
YEARBOOK = "https://api.ncsi.gov.om/uploads/pdfs/statistical_year_book_2026___issue_54_1778134524.pdf"
MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
NCSI_SEEDS = {
    "https://api.ncsi.gov.om/uploads/pdfs/monthly_statistical_bulletin___december_2025_ar_1766478007.pdf": (2025, 12),
    "https://api.ncsi.gov.om/uploads/pdfs/monthly_statistical_bulletin___january_2026_1779371510.pdf": (2026, 1),
    "https://api.ncsi.gov.om/uploads/pdfs/monthly_statistical_bulletin__april_2026_1777279015.pdf": (2026, 4),
    "https://api.ncsi.gov.om/uploads/pdfs/monthly_statistical_bulletin__may_2026_1780476675.pdf": (2026, 5),
    "https://api.ncsi.gov.om/uploads/pdfs/monthly_statistical_bulletin___june2026_1782038077.pdf": (2026, 6),
    "https://api.ncsi.gov.om/uploads/pdfs/monthly_statistical_bulletin__november_2026_1795081756.pdf": (2026, 11),
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Downloader:
    def __init__(self, delay=1.0):
        self.delay = delay
        self.last_call = {}
        self.opener = build_opener(NoRedirect)

    def get(self, url, hosts, bearer=None):
        url = safe_url(url, hosts)
        host = urlsplit(url).hostname
        headers = {"User-Agent": "RAI-Property-Intelligence/1.0 (Oman open data and authorized feeds)"}
        if bearer:
            headers["Authorization"] = "Bearer " + bearer
        for index in range(3):
            time.sleep(max(0, self.delay - (time.monotonic() - self.last_call.get(host, 0))))
            self.last_call[host] = time.monotonic()
            try:
                with self.opener.open(Request(url, headers=headers), timeout=25) as response:
                    result = response.read(MAX_DOWNLOAD + 1)
                    if len(result) > MAX_DOWNLOAD:
                        raise ValueError("response exceeded size budget")
                    return result
            except HTTPError as error:
                if error.code not in (408, 429, 500, 502, 503, 504) or index == 2:
                    raise RuntimeError(f"HTTP {error.code}") from None
                retry = error.headers.get("Retry-After", "")
                if retry and not retry.isdigit():
                    raise RuntimeError(f"HTTP {error.code}: deferred by Retry-After") from None
                wait = int(retry) if retry.isdigit() else 0
                if wait > 15:
                    raise RuntimeError(f"HTTP {error.code}: deferred by Retry-After") from None
            except (URLError, TimeoutError, OSError) as error:
                if index == 2:
                    raise RuntimeError(f"download failed ({type(error).__name__})") from None
                wait = 0
            time.sleep(max(wait, 2 ** index))
        raise RuntimeError("download failed")


def ncsi_rows(content, edition, url):
    previous_month = date(*edition, 1) - timedelta(days=1)
    sections = [page for page in content.split("\f") if re.search(r"29\s*-\s*Real.Estate activity In The Sultanate of Oman", page, re.I)
                and "Traded value of sales contracts" in page]
    if len(sections) != 1:
        raise ValueError("NCSI real estate table could not be identified uniquely")
    page = sections[0]
    months = [previous_month]
    for _ in range(2):
        months.append(months[-1].replace(day=1) - timedelta(days=1))
    if not re.search(r"Total\s*\(End\s*-\s*" + previous_month.strftime("%b") + r"\b", page):
        raise ValueError("NCSI table month differs from expected edition")
    indicators = [
        ("traded_property_value", "Traded value of property in the", "million_omr"),
        ("sales_contract_value", "Traded value of sales contracts", "million_omr"),
        ("sales_contract_count", "Sales contracts (No.)", "count"),
        ("properties_issued_count", "Properties issued (No.)", "count"),
    ]
    for indicator, label, unit in indicators:
        line = re.search(r"^\s*" + re.escape(label) + r"\s{2,}([^\n]+)", page, re.M)
        if not line:
            raise ValueError(f"NCSI table label missing: {indicator}")
        match = re.match(r"\s*(" + r"[-+]?\d[\d,.]*\s+" * 7 + r")", line[1])
        if not match:
            raise ValueError(f"NCSI table columns changed: {indicator}")
        values = match[1].split()
        for period, value in zip(months, values[3:6], strict=True):
            if not re.fullmatch(r"\d[\d,]*(?:\.\d+)?", value):
                raise ValueError(f"NCSI value invalid: {indicator}")
            yield (indicator, period.strftime("%Y-%m"), "oman", value.replace(",", ""), unit, url)


def pdf_text(url, hosts, get):
    return subprocess.run(
        ["pdftotext", "-layout", "-", "-"], input=get(url, hosts),
        capture_output=True, check=True, timeout=45,
    ).stdout.decode()


def ncsi_yearbook_rows(content, url):
    title = "Traded Value of Property by Governorates and Month"
    pages = [page for page in content.split("\f") if title in page and "5-3" in page]
    if len(pages) != 1:
        raise ValueError("NCSI yearbook table 5-3 could not be identified uniquely")
    page = pages[0]
    year_line = re.search(re.escape(title) + r"\s+(20\d{2})", page)
    header = next((line for line in page.splitlines() if "Al Wusta" in line and "Muscat" in line), "")
    head = [header.find(name) for name in ("Total", "Al Wusta", "Al Buraymi", "Musandam", "Dhofar", "Muscat")]
    if not year_line or min(head) < 0 or head != sorted(head):
        raise ValueError("NCSI yearbook year or geographic column order changed")
    governorates = (
        "wusta", "dhahirah", "north-sharqiyah", "south-sharqiyah", "south-batinah", "north-batinah",
        "dakhiliyah", "buraimi", "musandam", "dhofar", "muscat",
    )
    for name, month in MONTHS.items():
        monthly = re.search(r"^\s*" + name + r"\s+(.*)$", page, re.I | re.M)
        values = monthly[1].split()[:12] if monthly else []
        if len(values) != 12 or any(not re.fullmatch(r"\d[\d,]*\.\d", v) for v in values):
            raise ValueError(f"NCSI yearbook values missing for {name}")
        totals = [float(value.replace(",", "")) for value in values]
        if abs(sum(totals[1:]) - totals[0]) > 0.7:
            raise ValueError(f"NCSI yearbook geographic totals inconsistent for {name}")
        for geography, value in zip(governorates, values[1:], strict=True):
            yield ("traded_property_value", f"{year_line[1]}-{month:02d}", geography,
                   value.replace(",", ""), "million_omr", url)


def ncsi(source, get):
    warnings = []
    releases = dict(NCSI_SEEDS)
    try:
        catalog = html.unescape(get(source["url"], source["hosts"]).decode())
        for link in PORTAL_PDF.finditer(catalog):
            month = MONTHS.get(link[1].lower())
            if month:
                releases[link[0]] = (int(link[2]), month)
    except (RuntimeError, UnicodeError, ValueError):
        warnings.append("NCSI publication catalog unavailable; tried known editions")
    for url, edition in sorted(releases.items(), key=lambda entry: entry[1]):
        yield url, lambda url=url, edition=edition: (
            ncsi_rows(pdf_text(url, source["hosts"], get), edition, url),
            edition[0] * 100 + edition[1],
        )
    yield YEARBOOK, lambda: (ncsi_yearbook_rows(pdf_text(YEARBOOK, source["hosts"], get), YEARBOOK), 202605)
    for warning in warnings:
        yield None, warning


def mohup_rows(content, url):
    reader = csv.reader(io.StringIO(content.decode("utf-8-sig")), delimiter=";")
    first = next(reader, [])
    required = ("TRANSACTION_DATE", "REGION_AR", "WILAYAT_AR", "SERVICE_SUB_ID")
    if set(required) <= set(first):
        columns = tuple(first.index(key) for key in required)
        width = len(first)
    elif len(first) == 11 and re.fullmatch(r"\d{2}-\d{2}-\d{4}", first[0]) and place(first[2], first[4], None)[1]:
        # The two 2022 files are headerless and use buyer type in column 2.
        from itertools import chain
        reader = chain((first,), reader)
        columns = (0, 2, 4, 1)
        width = 11
    else:
        raise ValueError("MOHUP CSV layout changed")
    totals = Counter()
    valid = 0
    for row in reader:
        if len(row) != width:
            continue
        transaction_date, region, wilaya, type_code = (row[i] for i in columns)
        if not type_code:
            continue
        try:
            period = datetime.strptime(transaction_date, "%d-%m-%Y").strftime("%Y-%m")
        except ValueError:
            continue
        governorate, _, _, flags = place(region, wilaya, None)
        totals[period, "oman"] += 1
        if governorate and "geographic_conflict" not in flags:
            totals[period, governorate] += 1
        valid += 1
    if valid == 0:
        raise ValueError("MOHUP CSV contains no recognized dated rows")
    for (period, geography), count in sorted(totals.items()):
        if count >= 20:
            yield ("published_dataset_rows", period, geography, str(count), "rows", url)


def mohup(source, get):
    catalog = html.unescape(get(source["url"], source["hosts"]).decode())
    urls = set(MOHUP_CSV.findall(catalog))
    if not urls or len(urls) > 36:
        raise ValueError("unexpected number of MOHUP CSV releases")
    for url in sorted(urls):
        yield url, lambda url=url: (mohup_rows(get(url, source["hosts"]), url), None)


def osm_rows(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for category, lat, lon, name in data:
        if category not in {"mosque", "school", "health", "shop", "park", "road", "public"}:
            continue
        point = coordinates({"latitude": lat, "longitude": lon})
        if point[0] is not None:
            identifier = sha256(f"{category}:{point[0]}:{point[1]}".encode()).hexdigest()[:24]
            yield identifier, category, text(name), *point


PARTNER_COLUMNS = (
    "external_id", "url", "governorate", "wilayat", "area", "kind", "deal", "price",
    "currency", "rental_period", "land_m2", "built_m2", "bedrooms", "published_at",
    "availability", "public",
)


def authorized_file(path):
    if path.suffix.lower() != ".csv":
        return json.loads(path.read_text(encoding="utf-8"))
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = stream.readline()
        delimiter = ";" if ";" in header and "," not in header else ","
        stream.seek(0)
        reader = csv.DictReader(stream, delimiter=delimiter, strict=True)
        headings = [column.strip() for column in reader.fieldnames or []]
        if not {"external_id", "url"} <= set(headings):
            raise ValueError("CSV requires external_id and url columns")
        if len(set(headings)) != len(headings) or set(headings) - set(PARTNER_COLUMNS):
            raise ValueError("CSV contains repeated or unsupported column names")
        reader.fieldnames = headings
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV row {reader.line_num} has the wrong number of fields")
            clean = {key: value.strip() or None for key, value in row.items()}
            choice = (clean.get("public") or "").casefold()
            if choice not in ("", "true", "false", "yes", "no", "1", "0", "نعم", "لا"):
                raise ValueError(f"CSV row {reader.line_num} has an invalid public value")
            clean["public"] = choice in ("true", "yes", "1", "نعم")
            rows.append(clean)
        return rows


def authorized_feed(source, get, bearer=None):
    data = json.loads(get(source["feed_url"], source["hosts"], bearer))
    if not isinstance(data, list):
        raise ValueError("listing feed must be a JSON array")
    return data


STAT_ADAPTERS = {"ncsi": ncsi, "mohup": mohup}
