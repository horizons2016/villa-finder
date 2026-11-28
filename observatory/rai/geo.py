"""Bilingual official administrative boundaries as names, without inferred coordinates."""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEOGRAPHY = json.loads((ROOT / "geography.json").read_text(encoding="utf-8"))


def normalize(value):
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.translate({**str.maketrans("أإآٱىة", "اااايه"), ord("ـ"): None})
    return " ".join(re.findall(r"[^\W_]+", text)).strip()


def keys(names):
    return {normalize(name) for name in names}


GOVERNORS = {}
WILAYATS = {}
for governorate, ar, en, wilayats in GEOGRAPHY["governorates"]:
    for key in keys([governorate, ar, en, f"محافظة {ar}", f"{en} Governorate"]):
        GOVERNORS[key] = governorate
    for wilaya, *names in wilayats:
        for key in keys([wilaya, *names, f"ولاية {names[0]}"]):
            WILAYATS[key] = (governorate, wilaya)

for alias, identifier in {
    "Al Batinah North": "north-batinah", "Al Batinah South": "south-batinah",
    "Ash Sharqiyah North": "north-sharqiyah", "Ash Sharqiyah South": "south-sharqiyah",
    "Al Buraymi": "buraimi", "Al Dakhiliyah": "dakhiliyah",
}.items():
    GOVERNORS[normalize(alias)] = identifier


def place(governorate, wilayat, area):
    governor = GOVERNORS.get(normalize(governorate))
    matched = WILAYATS.get(normalize(wilayat))
    flags = []
    if governorate and not governor:
        flags.append("unknown_governorate")
    if not matched:
        flags.append("unknown_wilayat" if wilayat else "missing_wilayat")
    if matched:
        if governor and governor != matched[0]:
            flags.append("geographic_conflict")
            return governor, None, area, flags
        governor = matched[0]
    if not governor:
        flags.append("missing_governorate")
    return governor, matched[1] if matched else None, area, flags


def distance_km(a_lat, a_lon, b_lat, b_lon):
    from math import asin, cos, radians, sin, sqrt
    a_lat, a_lon, b_lat, b_lon = map(radians, (a_lat, a_lon, b_lat, b_lon))
    h = sin((b_lat - a_lat) / 2) ** 2
    h += cos(a_lat) * cos(b_lat) * sin((b_lon - a_lon) / 2) ** 2
    return 6371.0088 * 2 * asin(min(1, sqrt(h)))
