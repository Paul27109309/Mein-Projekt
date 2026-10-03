import json
import unittest

from leadmachine import enrich, importers, scoring
from leadmachine.hours import analyse, parse_day


class HoursTest(unittest.TestCase):
    def test_ampm(self):
        self.assertEqual(parse_day("7AM-4PM"), (7, 16))
        self.assertEqual(parse_day("8:00 AM – 5:30 PM"), (8, 17.5))

    def test_24h_and_closed(self):
        self.assertEqual(parse_day("08:00–17:00"), (8, 17))
        self.assertEqual(parse_day("Geschlossen"), "closed")

    def test_week_json_and_pipe(self):
        raw = json.dumps({"Monday": "7AM-4PM", "Saturday": "Closed", "Sunday": "Closed"})
        h = analyse(raw)
        self.assertEqual(h["avg_weekday_close"], 16)
        self.assertTrue(h["weekend_closed"])
        h = analyse("Montag: 08:00–17:00 | Samstag: Geschlossen | Sonntag: Geschlossen")
        self.assertEqual(h["avg_weekday_close"], 17)
        self.assertFalse(analyse("")["known"])


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.leads = importers.import_file("sample_data/outscraper_beispiel.csv")

    def test_import(self):
        self.assertEqual(len(self.leads), 4)
        self.assertEqual(self.leads[0]["segment"], "handwerk")
        self.assertEqual(self.leads[1]["segment"], "praxis")
        self.assertEqual(self.leads[1]["domain"], "praxis-beispiel.de")

    def test_dedupe(self):
        merged, added = importers.merge(list(self.leads), self.leads)
        self.assertEqual(added, 0)

    def test_scoring_order(self):
        html = "<html><form><textarea></textarea></form>Notdienst 24 Stunden</html>"
        self.leads[0].update(enrich.analyse_html(html, "https://x.de"))
        self.leads[0]["checked"] = "ja"
        scoring.score_all(self.leads)
        by = {l["name"]: l for l in self.leads}
        self.assertEqual(by["Elektro Müller GmbH"]["tier"], "A")
        self.assertEqual(by["Bauer Dachdeckerei"]["tier"], "C")  # keine Website
        self.assertLess(by["Autohaus Groß AG"]["score"], by["Elektro Müller GmbH"]["score"])

    def test_chatbot_penalty(self):
        info = enrich.analyse_html("<script src='https://embed.tawk.to/x'></script>", "https://x.de")
        self.assertEqual(info["has_chatbot"], "ja")

    def test_intent(self):
        self.assertGreaterEqual(scoring.score_intent(["demo_gestartet", "preisfrage", "termin_gebucht"]), 60)
        self.assertEqual(scoring.score_intent(["abmeldung", "termin_gebucht"]), 0)


if __name__ == "__main__":
    unittest.main()
