"""Website prüfen: Chatbot, Online-Terminbuchung, Kontaktformular, Notdienst."""
import re
import time
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (compatible; LeadMachineBot/1.0)"
MAX_BYTES = 500_000

CHATBOTS = {
    "tawk.to": "Tawk.to", "intercom": "Intercom", "drift.com": "Drift", "tidio": "Tidio",
    "crisp.chat": "Crisp", "zdassets": "Zendesk", "zopim": "Zendesk", "userlike": "Userlike",
    "hs-scripts": "HubSpot", "livechatinc": "LiveChat", "botpress": "Botpress",
    "landbot": "Landbot", "manychat": "ManyChat", "freshchat": "Freshchat",
    "botbuildr": "BotBuildr", "whatsapp-widget": "WhatsApp-Widget",
}
BOOKING = {
    "doctolib": "Doctolib", "jameda": "Jameda", "samedi": "samedi", "terminland": "Terminland",
    "calendly": "Calendly", "clickdoc": "ClickDoc", "onlinetermin": "Online-Termin",
    "online-termin": "Online-Termin", "timify": "Timify", "etermin": "eTermin",
}
EMERGENCY = re.compile(r"notdienst|24\s*/\s*7|24\s*stunden|24-stunden|rund um die uhr|notfall", re.I)


class _Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = 0
        self.textareas = 0
        self.links: list[tuple[str, str]] = []
        self._href = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "form":
            self.forms += 1
        elif tag == "textarea":
            self.textareas += 1
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None


def _allowed(url: str) -> bool:
    p = urlparse(url)
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{p.scheme}://{p.netloc}/robots.txt")
    try:
        rp.read()
    except Exception:
        return True
    return rp.can_fetch(UA, url)


def fetch(url: str) -> str | None:
    if not _allowed(url):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(MAX_BYTES).decode(resp.headers.get_content_charset() or "utf-8", "replace")
    except Exception:
        return None


def analyse_html(html: str, base_url: str, kontakt_html: str | None = None) -> dict:
    low = html.lower()
    page = _Page()
    page.feed(html)
    contact_url = ""
    for href, text in page.links:
        if href and re.search(r"kontakt|contact", f"{href} {text}", re.I):
            contact_url = urljoin(base_url, href)
            break
    forms, areas = page.forms, page.textareas
    if kontakt_html:
        k = _Page()
        k.feed(kontakt_html)
        forms, areas = forms + k.forms, areas + k.textareas
    chat = next((n for key, n in CHATBOTS.items() if key in low), "")
    book = next((n for key, n in BOOKING.items() if key in low), "")
    return {
        "has_chatbot": "ja" if chat else "nein",
        "chatbot_name": chat,
        "has_booking": "ja" if book else "nein",
        "booking_name": book,
        "has_contact_form": "ja" if (forms and areas) else "nein",
        "contact_url": contact_url,
        "emergency_text": "ja" if EMERGENCY.search(html) else "nein",
    }


def enrich_lead(lead: dict) -> dict:
    url = lead["website"]
    html = fetch(url)
    if html is None:
        lead["checked"] = "fehler"
        return lead
    kontakt = None
    first = analyse_html(html, url)
    if first["contact_url"] and not first["has_contact_form"] == "ja":
        kontakt = fetch(first["contact_url"])
    lead.update(analyse_html(html, url, kontakt))
    lead["checked"] = "ja"
    return lead


def enrich_all(leads: list[dict], delay: float = 1.0, force: bool = False) -> int:
    n = 0
    for lead in leads:
        if not lead["website"] or (lead.get("checked") == "ja" and not force):
            continue
        enrich_lead(lead)
        n += 1
        time.sleep(delay)
    return n
