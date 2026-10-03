"""Firmen über die Google Places API (New) suchen."""
import json
import os
import time
import urllib.request

from .importers import normalize

URL = "https://places.googleapis.com/v1/places:searchText"
MASK = ",".join([
    "places.id", "places.displayName", "places.formattedAddress",
    "places.nationalPhoneNumber", "places.websiteUri", "places.rating",
    "places.userRatingCount", "places.regularOpeningHours.weekdayDescriptions",
    "places.primaryTypeDisplayName", "places.businessStatus", "nextPageToken",
])


def _post(body: dict, key: str) -> dict:
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": key,
            "X-Goog-FieldMask": MASK,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def search(branche: str, stadt: str, max_results: int = 60) -> list[dict]:
    key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not key:
        raise SystemExit("GOOGLE_PLACES_API_KEY fehlt (siehe README, Schritt 'Google-Schlüssel').")
    body = {"textQuery": f"{branche} in {stadt}", "languageCode": "de", "regionCode": "DE", "pageSize": 20}
    leads: list[dict] = []
    while len(leads) < max_results:
        data = _post(body, key)
        for p in data.get("places", []):
            if p.get("businessStatus", "OPERATIONAL") != "OPERATIONAL":
                continue
            row = normalize(
                {
                    "name": p.get("displayName", {}).get("text", ""),
                    "website": p.get("websiteUri", ""),
                    "phone": p.get("nationalPhoneNumber", ""),
                    "address": p.get("formattedAddress", ""),
                    "city": stadt,
                    "category": p.get("primaryTypeDisplayName", {}).get("text", "") or branche,
                    "rating": p.get("rating", ""),
                    "reviews": p.get("userRatingCount", ""),
                    "hours_raw": " | ".join(
                        p.get("regularOpeningHours", {}).get("weekdayDescriptions", [])
                    ),
                    "place_id": p.get("id", ""),
                },
                "google_places",
            )
            if row:
                leads.append(row)
        token = data.get("nextPageToken")
        if not token:
            break
        body["pageToken"] = token
        time.sleep(1.5)
    return leads[:max_results]
