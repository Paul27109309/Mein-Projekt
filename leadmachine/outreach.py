"""Texte für die Ansprache (aus templates/) und den Anruf."""
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def form_message(lead: dict, demo_url: str) -> str:
    """Text je Branche aus templates/<segment>.txt; Platzhalter {firma} und {demo_url}."""
    path = TEMPLATE_DIR / f"{lead['segment']}.txt"
    if not path.exists():
        path = TEMPLATE_DIR / "sonstige.txt"
    return path.read_text(encoding="utf-8").format(firma=lead["name"], demo_url=demo_url)


def call_opener(lead: dict, sender: str) -> str:
    return (
        f"Guten Tag, hier ist {sender}. Ich habe für {lead['name']} einen Demo-Assistenten "
        f"gebaut und wollte kurz fragen, ob Sie ihn schon ausprobieren konnten. "
        f"Haben Sie zwei Minuten?"
    )
