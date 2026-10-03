# Lead-Maschine für KI-Assistenten (Handwerk und Arztpraxen)

Findet über Google Maps passende Firmen, prüft deren Website, bewertet die Passung
und bereitet alles für BotBuildr (Demo-Bots) und die Ansprache vor.
Es braucht nur Python 3.11 und keine zusätzlichen Pakete.

## Ablauf

```
Firmen finden → Website prüfen → Passung bewerten → BotBuildr-Upload → Ansprache → Interesse messen → Anruf
 (search/import)   (enrich)         (score)           (export)          (du)        (intent)           (du)
```

## Schritt für Schritt

**1. Firmen finden** (eine der beiden Möglichkeiten)

```bash
# a) Outscraper-Export (CSV) einlesen
python3 -m leadmachine import meine_outscraper_liste.csv

# b) direkt über Google Places suchen (braucht einen API-Schlüssel, siehe unten)
export GOOGLE_PLACES_API_KEY=dein_schluessel
python3 -m leadmachine search --branche "Elektriker" --stadt "München" --max 60
```

**2. Prüfen, bewerten, exportieren** (ein Befehl)

```bash
python3 -m leadmachine pipeline --absender "Dein Name"
```

Das erzeugt zwei Dateien im Ordner `out/`:

| Datei | Inhalt |
|---|---|
| `botbuildr_upload.csv` | Liste der besten Firmen (Name und Website) für den CSV-Upload in BotBuildr |
| `ansprache.csv` | je Firma: Score, Begründung, Telefon, Kontaktformular-Link und fertiger Text |

**3. Demo-Links zurückspielen.** BotBuildr baut je Firma einen Demo-Bot. Lege eine Datei
`data/demo_links.csv` mit den Spalten `website,demo_url` an und führe `python3 -m leadmachine export` erneut aus.
Dann steht der richtige Link in jedem Text.

**4. Interesse messen.** Sobald BotBuildr (oder n8n) Ereignisse liefert, schreibe sie in eine CSV
mit den Spalten `firma,ereignis`. Dann:

```bash
python3 -m leadmachine intent signals.csv
```

Ergebnis: `out/anrufliste.csv`. Bei 60 Punkten oder mehr steht dort **ANRUFEN**.
Erlaubte Ereignisse: `demo_gestartet`, `mehr_als_5_nachrichten`, `preisfrage`,
`wiederholter_besuch`, `email_geantwortet`, `termin_gebucht`, `abmeldung`.

## Wie bewertet wird

Die Passung (0-100) steht in `leadmachine/scoring.py`. Die Gewichte lassen sich nach den
ersten Gesprächen anpassen. Beispiele: Zielbranche +20, 15-300 Bewertungen +15, schließt vor 17:30 Uhr +15,
kein Chatbot auf der Website +15, wirbt mit Notdienst +10. Hat die Firma schon einen Chatbot, gibt es -25.
Stufe A ab 70, B ab 50, C darunter. Die Begründung steht je Firma in der Spalte `reasons`.

## Google-Schlüssel (nur für die Suche über Google Places)

1. In der Google Cloud Console ein Projekt anlegen und die **Places API (New)** aktivieren.
2. Einen API-Schlüssel erzeugen und auf diese API beschränken.
3. Ein Rechnungskonto hinterlegen, das verlangt Google. Es gibt ein monatliches Gratis-Kontingent.
   **Prüfe die aktuellen Preise selbst und stelle ein Budgetlimit (Warnung) ein**, damit nichts Unerwartetes anfällt.

## Rechtliches

Die Software erzeugt nur Listen und Texte. Unaufgeforderte Werbe-E-Mails an Firmen sind in Deutschland
ohne Einwilligung unzulässig (§ 7 UWG). Dieses Projekt verschickt deshalb **keine** E-Mails und liest
keine E-Mail-Adressen aus Websites aus. Wege und Einschränkungen stehen in `docs/kanaele.md`.
Das ist keine Rechtsberatung.

## Tests

```bash
python3 -m unittest discover -s tests -v
```
