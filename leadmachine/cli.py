"""Befehle: search, import, enrich, score, export, intent, pipeline."""
import argparse
import os

from . import enrich, importers, outreach, places, scoring
from .model import FIELDS, LEADS_FILE, OUT_DIR, load_leads, read_csv, save_leads, write_csv


def _store(new: list[dict]) -> None:
    existing = read_csv(LEADS_FILE) if LEADS_FILE.exists() else []
    merged, added = importers.merge(existing, new)
    save_leads(merged)
    print(f"{added} neue Firmen gespeichert, insgesamt {len(merged)} ({LEADS_FILE}).")


def cmd_search(a):
    _store(places.search(a.branche, a.stadt, a.max))


def cmd_import(a):
    _store(importers.import_file(a.datei, a.source))


def cmd_enrich(a):
    leads = load_leads()
    n = enrich.enrich_all(leads, delay=a.delay, force=a.force)
    save_leads(leads)
    print(f"{n} Websites geprüft.")


def cmd_score(a):
    leads = load_leads()
    scoring.score_all(leads)
    save_leads(leads)
    counts = {t: sum(1 for l in leads if l["tier"] == t) for t in "ABC"}
    print(f"Bewertet: A={counts['A']}  B={counts['B']}  C={counts['C']}")


def cmd_export(a):
    leads = [l for l in load_leads() if l["tier"] in a.tiers and l["website"]]
    leads.sort(key=lambda l: int(l["score"] or 0), reverse=True)
    links = {}
    if os.path.exists(a.demo_links):
        links = {importers.domain_of(r["website"]): r["demo_url"] for r in read_csv(a.demo_links)}
    # 1) Liste für den BotBuildr-Upload
    write_csv(OUT_DIR / "botbuildr_upload.csv", leads, ["name", "website", "phone", "city", "segment"])
    # 2) Ansprache-Liste mit fertigem Text
    rows = []
    for l in leads:
        demo = links.get(l["domain"], "{DEMO-LINK}")
        rows.append({**l, "demo_url": demo,
                     "formular_text": outreach.form_message(l, demo),
                     "anruf_einstieg": outreach.call_opener(l, a.absender)})
    write_csv(OUT_DIR / "ansprache.csv", rows,
              ["name", "tier", "score", "phone", "website", "contact_url", "demo_url",
               "pitch", "reasons", "formular_text", "anruf_einstieg"])
    print(f"{len(leads)} Leads exportiert nach {OUT_DIR}/ (botbuildr_upload.csv, ansprache.csv).")


def cmd_intent(a):
    by_company: dict[str, list[str]] = {}
    for r in read_csv(a.datei):
        firma = r["firma"]
        if "ereignis" in r:  # Format 1: eine Zeile je Ereignis
            by_company.setdefault(firma, []).append(r["ereignis"])
            continue
        # Format 2: eine Zeile je Firma mit Zahlen aus dem Demo-Bot
        msgs = int(float(r.get("nachrichten") or 0))
        events = by_company.setdefault(firma, [])
        if msgs >= 1:
            events.append("demo_gestartet")
        if msgs >= 6:
            events.append("mehr_als_5_nachrichten")
        if int(float(r.get("tage_aktiv") or 0)) >= 2:
            events.append("wiederholter_besuch")
        if (r.get("antwort") or "").lower() == "ja":
            events.append("email_geantwortet")
        if (r.get("termin") or "").lower() == "ja":
            events.append("termin_gebucht")
    ranked = sorted(((scoring.score_intent(ev), f) for f, ev in by_company.items()), reverse=True)
    rows = [{"firma": f, "interesse": s, "aktion": "ANRUFEN" if s >= scoring.CALL_AT else "weiter automatisch"}
            for s, f in ranked]
    write_csv(OUT_DIR / "anrufliste.csv", rows, ["firma", "interesse", "aktion"])
    for r in rows:
        print(f"{r['interesse']:>3}  {r['aktion']:<20} {r['firma']}")


def cmd_pipeline(a):
    cmd_enrich(argparse.Namespace(delay=a.delay, force=False))
    cmd_score(a)
    cmd_export(a)


def main(argv=None):
    p = argparse.ArgumentParser(prog="leadmachine")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="Firmen über Google Maps suchen")
    s.add_argument("--branche", required=True)
    s.add_argument("--stadt", required=True)
    s.add_argument("--max", type=int, default=60)
    s.set_defaults(fn=cmd_search)

    s = sub.add_parser("import", help="Outscraper-/eigene CSV einlesen")
    s.add_argument("datei")
    s.add_argument("--source", default="outscraper")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("enrich", help="Websites prüfen")
    s.add_argument("--delay", type=float, default=1.0)
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_enrich)

    s = sub.add_parser("score", help="Passung bewerten")
    s.set_defaults(fn=cmd_score)

    for name, fn, help_ in (("export", cmd_export, "Listen für BotBuildr und Ansprache"),
                            ("pipeline", cmd_pipeline, "prüfen + bewerten + exportieren")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--tiers", default="AB")
        s.add_argument("--absender", default="Paul")
        s.add_argument("--demo-links", default="data/demo_links.csv")
        if name == "pipeline":
            s.add_argument("--delay", type=float, default=1.0)
        s.set_defaults(fn=fn)

    s = sub.add_parser("intent", help="Anrufliste aus Demo-Bot-Ereignissen")
    s.add_argument("datei", help="CSV: firma,ereignis ODER firma,nachrichten[,tage_aktiv,antwort,termin]")
    s.set_defaults(fn=cmd_intent)

    a = p.parse_args(argv)
    a.fn(a)
