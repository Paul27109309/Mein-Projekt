"""Öffnungszeiten lesen (Outscraper und Google Places, deutsch/englisch)."""
import ast
import json
import re

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_DAY_PREFIX = {
    "mo": 0, "mon": 0, "di": 1, "tue": 1, "mi": 2, "wed": 2, "do": 3, "thu": 3,
    "fr": 4, "fri": 4, "sa": 5, "sat": 5, "so": 6, "sun": 6,
}
_RANGE = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:uhr)?\s*[–—\-]+\s*"
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:uhr)?",
    re.I,
)
_CLOSED = re.compile(r"geschlossen|closed|ruhetag", re.I)


def _day_index(label: str):
    label = label.strip().lower()
    for prefix in sorted(_DAY_PREFIX, key=len, reverse=True):
        if label.startswith(prefix):
            return _DAY_PREFIX[prefix]
    return None


def _to_mapping(raw) -> dict[int, str]:
    """Rohtext in {Tag: Text} umwandeln."""
    if not raw:
        return {}
    data = raw
    if isinstance(raw, str):
        text = raw.strip()
        data = None
        for loader in (json.loads, ast.literal_eval):
            try:
                data = loader(text)
                break
            except (ValueError, SyntaxError):
                continue
        if data is None:
            data = [p for p in re.split(r"\s*\|\s*|\n", text) if p]
    out: dict[int, str] = {}
    if isinstance(data, dict):
        items = [(k, v) for k, v in data.items()]
    elif isinstance(data, list):
        items = []
        for entry in data:
            if isinstance(entry, dict):
                items.extend(entry.items())
            elif isinstance(entry, str) and ":" in entry:
                k, v = entry.split(":", 1)
                items.append((k, v))
    else:
        return {}
    for k, v in items:
        idx = _day_index(str(k))
        if idx is not None:
            out[idx] = str(v)
    return out


def _hour24(h: int, m: str | None, marker: str | None) -> float:
    h = h % 12 + (12 if marker and marker.lower() == "pm" else 0) if marker else h
    return h + (int(m) / 60 if m else 0)


def parse_day(text: str):
    """Liefert (öffnet, schließt) als Dezimalstunden, 'closed' oder None."""
    if _CLOSED.search(text):
        return "closed"
    m = _RANGE.search(text)
    if not m:
        return None
    oh, om, oam, ch, cm, cam = m.groups()
    close = _hour24(int(ch), cm, cam)
    if oam:
        open_ = _hour24(int(oh), om, oam)
    else:
        open_ = int(oh) + (int(om) / 60 if om else 0)
        if cam and open_ >= close:  # "8–5 PM": Öffnung am Vormittag
            open_ = int(oh) % 12 + (int(om) / 60 if om else 0)
    if close <= open_ and close < 12:
        close += 12
    return open_, close


def analyse(raw) -> dict:
    """Kennzahlen: Schließzeit unter der Woche, Wochenende zu."""
    days = {i: parse_day(t) for i, t in _to_mapping(raw).items()}
    closes = [d[1] for i, d in days.items() if i < 5 and isinstance(d, tuple)]
    sat, sun = days.get(5), days.get(6)
    return {
        "known": bool(days),
        "avg_weekday_close": sum(closes) / len(closes) if closes else None,
        "weekend_closed": bool(days) and sat in ("closed", None) and sun in ("closed", None),
    }
