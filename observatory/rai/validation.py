"""Validate incoming facts while retaining interpretable quality signals."""
import ipaddress
import math
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit

from .geo import normalize, place

KINDS = {
    "residential-land": ("أرض سكنية", "residential land"),
    "commercial-land": ("أرض تجارية", "commercial land"),
    "villa": ("فيلا", "villa"),
    "mixed-land": ("أرض سكنية تجارية", "mixed-use land"),
    "industrial-land": ("أرض صناعية", "industrial land"),
    "chalet": ("شاليه", "chalet"),
    "house": ("منزل", "house", "بيت", "بيت / فيلا"),
    "apartment": ("شقة", "apartment", "flat"),
    "commercial": ("عقار تجاري", "commercial property", "office", "shop"),
    "farm": ("مزرعة", "farm", "أرض زراعية", "agricultural land"),
}
DEALS = {"sale": ("بيع", "for sale"), "rent": ("إيجار", "for rent")}
VERIFICATION = ("unverified", "source_checked", "advertiser_confirmed", "independently_verified")
AVAILABILITY = ("unknown", "available", "unreachable", "withdrawn", "sold_confirmed", "let_confirmed")
PRICE_BASES = ("advertised", "advertiser_confirmed", "independently_verified", "transaction")
PERIODS = ("day", "week", "month", "year")
ACCURACIES = ("approximate", "source_reported", "confirmed")
CURRENCIES = ("OMR", "AED", "USD", "EUR", "GBP", "SAR", "QAR", "KWD", "BHD")


def utc(value=None):
    stamp = datetime.now(timezone.utc) if value is None else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("timestamps require an explicit time zone")
    return stamp.astimezone(timezone.utc).isoformat(timespec="microseconds")


def safe_url(value, hosts):
    if not isinstance(value, str) or len(value) > 2048 or any(c.isspace() or ord(c) < 32 for c in value) or "\\" in value:
        raise ValueError("invalid URL")
    parts = urlsplit(value)
    host = parts.hostname
    if parts.scheme != "https" or host not in hosts or parts.username is not None or parts.password is not None or parts.port not in (None, 443):
        raise ValueError("URL outside the source allowlist")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("literal IP addresses are disallowed")
    return urlunsplit(("https", host, parts.path or "/", parts.query, ""))


def text(value, limit=200):
    return value.strip()[:limit] if isinstance(value, str) and value.strip() else None


def positive(value, cap):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
        return number if number.is_finite() and Decimal("0.000001") <= number <= cap else None
    except (InvalidOperation, ValueError):
        return None


def category(value, options):
    return next((k for k, aliases in options.items() if normalize(value) in {normalize(v) for v in (k, *aliases)}), None) if value else None


def publication(value):
    if isinstance(value, str):
        try:
            if len(value) == 10:
                return date.fromisoformat(value).isoformat()
            return utc(value)
        except ValueError:
            pass
    return None


def coordinates(row):
    try:
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if 16 <= lat <= 27 and 51 <= lon <= 61 and math.isfinite(lat + lon):
            return lat, lon
    except (KeyError, ValueError, TypeError):
        pass
    return None, None


def normalize_listing(row, source, observed_at):
    if not isinstance(row, dict):
        raise ValueError("listing must be an object")
    external_id = text(row.get("external_id"), 500)
    if not external_id:
        raise ValueError("missing external identifier")
    url = safe_url(row.get("url"), source["hosts"])
    governorate, wilayat, area, flags = place(row.get("governorate"), row.get("wilayat"), text(row.get("area")))
    if not area:
        flags.append("missing_area")
    result = {"external_id": external_id, "url": url, "governorate": governorate, "wilayat": wilayat, "area": area}
    for key, options in (("kind", KINDS), ("deal", DEALS)):
        raw = row.get(key)
        if key == "kind" and not raw:
            raw = row.get("type")
        result[key] = category(raw, options)
        if not result[key]:
            flags.append(("invalid_" if raw else "missing_") + key)
    for key, cap in (("price", 10**10), ("land_m2", 10**8), ("built_m2", 10**8), ("bedrooms", 100)):
        raw = row.get(key)
        number = positive(raw, cap)
        if key == "bedrooms" and str(raw) == "0":
            number = Decimal(0)
        if key == "bedrooms" and number is not None and number != int(number):
            number = None
        if number is None and (raw is not None or key == "price"):
            flags.append(("invalid_" if raw is not None else "missing_") + key)
        if number is None:
            result[key] = None
        elif key == "price":
            result[key] = format(number.normalize(), "f")
        elif key == "bedrooms":
            result[key] = int(number)
        else:
            result[key] = float(number)
    if result["land_m2"] is None and result["built_m2"] is None:
        flags.append("missing_dimensions")
    currency = text(row.get("currency"), 8)
    result["currency"] = currency.upper() if currency else None
    if result["price"] and result["currency"] not in CURRENCIES:
        flags.append("missing_currency" if not currency else "invalid_currency")
        result["currency"] = None
    period = row.get("rental_period")
    result["rental_period"] = period if result["deal"] == "rent" and period in PERIODS else None
    if result["deal"] == "rent" and not period:
        flags.append("missing_rental_period")
    elif period and result["rental_period"] is None:
        flags.append("invalid_rental_period")
    result["published_at"] = publication(row.get("published_at"))
    if result["published_at"] and observed_at and result["published_at"][:10] > observed_at[:10]:
        result["published_at"] = None
    if not result["published_at"]:
        flags.append("invalid_publication_date" if row.get("published_at") else "unknown_publication_date")
    lat, lon = coordinates(row)
    result.update(latitude=lat, longitude=lon, accuracy="unknown")
    if lat is not None:
        accuracy = row.get("accuracy")
        result["accuracy"] = accuracy if accuracy in ACCURACIES else "source_reported"
    elif row.get("latitude") is not None or row.get("longitude") is not None:
        flags.append("invalid_coordinates")
    result["verification"] = row.get("verification") if row.get("verification") in VERIFICATION else "unverified"
    result["availability"] = row.get("availability") if row.get("availability") in AVAILABILITY else "unknown"
    result["price_basis"] = row.get("price_basis") if row.get("price_basis") in PRICE_BASES else "advertised"
    try:
        verified = utc(row["last_verified"]) if row.get("last_verified") else None
    except (AttributeError, ValueError):
        verified = None
    if verified and observed_at and verified > observed_at:
        verified = None
    if result["verification"] == "unverified" or not verified:
        result["verification"] = "unverified"
        verified = None
    if not verified and row.get("last_verified"):
        flags.append("invalid_verification_date")
    result["last_verified"] = verified
    if result["availability"] in ("sold_confirmed", "let_confirmed") and (
        not verified or result["verification"] != "independently_verified"
    ):
        flags.append("unsubstantiated_status")
        result["availability"] = "unknown"
    required = {"advertiser_confirmed": ("advertiser_confirmed", "independently_verified"),
                "independently_verified": ("independently_verified",), "transaction": ("independently_verified",)}
    if result["price_basis"] in required and result["verification"] not in required[result["price_basis"]]:
        result["price_basis"] = "advertised"
        flags.append("unsubstantiated_price_basis")
    result["description"] = text(row.get("description"), 4000)
    result["public"] = int(source.get("publish_listings") is True and row.get("public") is True)
    if not result["last_verified"]:
        flags.append("verification_required")
    result["flags"] = sorted(flags)
    return result
