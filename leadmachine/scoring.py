"""Passung eines Unternehmens (0-100) und Interesse eines Leads (0-100).

Alle Gewichte stehen hier oben und lassen sich nach den ersten echten
Gesprächen anpassen.
"""
from .hours import analyse

TIER_A = 70
TIER_B = 50
CALL_AT = 60  # ab diesem Interesse-Wert wird angerufen

PITCH = {
    "praxis": "Anrufe gehen unter, während das Team behandelt, und nach Feierabend meldet sich niemand.",
    "handwerk": "Anrufe kommen auf der Baustelle oder abends, und ein verpasster Anruf ist ein verlorener Auftrag.",
    "sonstige": "Anfragen außerhalb der Öffnungszeiten bleiben unbeantwortet.",
}


def score_fit(lead: dict) -> tuple[int, list[str]]:
    pts, why = 0, []

    def add(n: int, text: str):
        nonlocal pts
        pts += n
        why.append(f"{n:+d} {text}")

    if lead["segment"] in ("handwerk", "praxis"):
        add(20, f"Zielbranche ({lead['segment']})")
    if not lead["website"]:
        add(-100, "keine Website")
    elif lead.get("checked") == "fehler":
        add(-10, "Website nicht erreichbar oder gesperrt")

    try:
        reviews = int(float(lead["reviews"] or 0))
    except ValueError:
        reviews = 0
    if 15 <= reviews <= 300:
        add(15, f"{reviews} Bewertungen: aktiver Betrieb mit Kundenvolumen")
    elif reviews > 300:
        add(5, f"{reviews} Bewertungen: eher größerer Betrieb")
    elif reviews < 5:
        add(-10, "kaum Bewertungen: wenig Kundenverkehr")

    h = analyse(lead["hours_raw"])
    if h["known"]:
        close = h["avg_weekday_close"]
        if close is not None and close <= 17.5:
            add(15, f"schließt im Schnitt um {close:.0f}:{int((close % 1) * 60):02d} Uhr")
        if h["weekend_closed"]:
            add(10, "am Wochenende geschlossen")

    if lead.get("checked") == "ja":
        if lead["has_chatbot"] == "nein":
            add(15, "kein Chatbot auf der Website")
        else:
            add(-25, f"hat schon einen Chatbot ({lead['chatbot_name']})")
        if lead["emergency_text"] == "ja":
            add(10, "wirbt mit Notdienst/24h: Telefon rund um die Uhr wäre Gold wert")
        if lead["has_contact_form"] == "ja":
            add(5, "Kontaktformular vorhanden (erlaubter Erstkontakt)")
    return max(0, min(100, pts)), why


def tier(score: int) -> str:
    return "A" if score >= TIER_A else "B" if score >= TIER_B else "C"


def score_all(leads: list[dict]) -> None:
    for lead in leads:
        s, why = score_fit(lead)
        lead["score"] = s
        lead["tier"] = tier(s)
        lead["reasons"] = "; ".join(why)
        lead["pitch"] = PITCH.get(lead["segment"], PITCH["sonstige"])


# ---- Interesse (nach dem Demo-Bot) --------------------------------------
EVENTS = {
    "demo_gestartet": 15,
    "mehr_als_5_nachrichten": 15,
    "preisfrage": 20,
    "wiederholter_besuch": 10,
    "email_geantwortet": 25,
    "termin_gebucht": 40,
    "abmeldung": -100,
}


def score_intent(events: list[str]) -> int:
    seen = {e.strip().lower() for e in events}
    return max(0, min(100, sum(EVENTS.get(e, 0) for e in seen)))
