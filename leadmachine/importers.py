"""CSV (Outscraper oder eigene Liste) in das gemeinsame Format bringen."""
from .model import FIELDS, domain_of, read_csv

ALIASES = {
    "name": ["name", "title", "firma", "company"],
    "website": ["site", "website", "websiteuri", "web", "url"],
    "phone": ["phone", "phone_1", "telefon", "nationalphonenumber"],
    "address": ["full_address", "address", "adresse"],
    "city": ["city", "stadt", "ort"],
    "postal_code": ["postal_code", "zip", "plz"],
    "category": ["category", "type", "subtypes", "kategorie"],
    "rating": ["rating", "bewertung"],
    "reviews": ["reviews", "reviews_count", "userratingcount", "rezensionen"],
    "hours_raw": ["working_hours", "working_hours_old_format", "opening_hours", "oeffnungszeiten"],
    "place_id": ["place_id", "google_id", "id"],
}

SEGMENTS = {
    "handwerk": [
        "elektr", "sanitär", "sanitaer", "heizung", "klempner", "dachdeck", "maler",
        "schreiner", "tischler", "installat", "handwerk", "fliesen", "zimmer", "gartenbau",
        "schlosser", "glaser", "klima", "bauunternehmen", "metallbau", "trockenbau",
    ],
    "praxis": [
        "zahn", "arzt", "ärzt", "praxis", "physio", "kieferorth", "orthop", "heilprakt",
        "tierarzt", "dermatolog", "hno", "augenarzt", "gynäkolog", "kinderarzt", "psycho",
    ],
}


def segment_of(name: str, category: str) -> str:
    text = f"{name} {category}".lower()
    for segment, words in SEGMENTS.items():
        if any(w in text for w in words):
            return segment
    return "sonstige"


def normalize(row: dict, source: str) -> dict | None:
    low = {str(k).strip().lower(): (v or "").strip() for k, v in row.items() if k}
    out = {f: "" for f in FIELDS}
    for field, names in ALIASES.items():
        for n in names:
            if low.get(n):
                out[field] = low[n]
                break
    if not out["name"]:
        return None
    if out["website"] and "://" not in out["website"]:
        out["website"] = "https://" + out["website"]
    out["domain"] = domain_of(out["website"])
    out["segment"] = segment_of(out["name"], out["category"])
    out["source"] = source
    return out


def merge(existing: list[dict], new: list[dict]) -> tuple[list[dict], int]:
    """Doppelte (gleiche Domain, sonst gleicher Name+Stadt) überspringen."""
    def key(r):
        return r["domain"] or f'{r["name"].lower()}|{r["city"].lower()}'

    seen = {key(r) for r in existing}
    added = 0
    for r in new:
        if key(r) not in seen:
            existing.append(r)
            seen.add(key(r))
            added += 1
    return existing, added


def import_file(path: str, source: str = "import") -> list[dict]:
    rows = [normalize(r, source) for r in read_csv(path)]
    return [r for r in rows if r]
