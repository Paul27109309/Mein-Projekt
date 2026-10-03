"""Texte für die Ansprache (Kontaktformular) und den Anruf."""

TIMING = {
    "praxis": "während der Behandlungszeiten und nach Feierabend",
    "handwerk": "wenn Sie auf der Baustelle sind oder nach Feierabend",
    "sonstige": "außerhalb Ihrer Öffnungszeiten",
}


def form_message(lead: dict, demo_url: str, sender: str) -> str:
    when = TIMING.get(lead["segment"], TIMING["sonstige"])
    return (
        f"Guten Tag,\n\n"
        f"ich habe mir die Website von {lead['name']} angesehen und dazu einen kleinen "
        f"KI-Assistenten vorbereitet, der Anfragen beantwortet, {when}. "
        f"Sie können ihn hier ohne Anmeldung ausprobieren: {demo_url}\n\n"
        f"Wenn Sie das interessiert, antworten Sie mir gern kurz. "
        f"Wenn nicht, genügt eine Zeile, dann melde ich mich nicht wieder.\n\n"
        f"Freundliche Grüße\n{sender}"
    )


def call_opener(lead: dict) -> str:
    return (
        f"Guten Tag, hier ist {{name}}. Ich habe für {lead['name']} einen Demo-Assistenten "
        f"gebaut und wollte kurz fragen, ob Sie ihn schon ausprobieren konnten. "
        f"Haben Sie zwei Minuten?"
    )
