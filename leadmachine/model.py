"""Gemeinsames Datenformat und CSV-Helfer."""
import csv
import re
from pathlib import Path
from urllib.parse import urlparse

FIELDS = [
    "name", "segment", "category", "website", "domain", "phone", "address", "city",
    "postal_code", "rating", "reviews", "hours_raw", "place_id", "source",
    # Ergebnis der Website-Prüfung
    "checked", "has_chatbot", "chatbot_name", "has_booking", "booking_name",
    "has_contact_form", "contact_url", "emergency_text",
    # Bewertung
    "score", "tier", "reasons", "pitch",
]

DATA_DIR = Path("data")
OUT_DIR = Path("out")
LEADS_FILE = DATA_DIR / "leads.csv"


def domain_of(url: str) -> str:
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    host = urlparse(url).netloc.lower()
    return re.sub(r"^www\.", "", host)


def read_csv(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        return list(csv.DictReader(f, dialect=dialect))


def write_csv(path, rows: list[dict], fields: list[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def load_leads() -> list[dict]:
    if not LEADS_FILE.exists():
        raise SystemExit("Noch keine Leads. Zuerst 'search' oder 'import' ausführen.")
    return read_csv(LEADS_FILE)


def save_leads(rows: list[dict]) -> None:
    write_csv(LEADS_FILE, rows, FIELDS)
