from fastapi import APIRouter, Query
import requests
import os
from datetime import datetime, timedelta

router = APIRouter()

# --- API KEYS ---
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY")
API_SPORTS_KEY = os.getenv("API_SPORTS_KEY")
SPORTSMONK_KEY = os.getenv("SPORTSMONK_KEY")
FOOTYSTATS_KEY = os.getenv("FOOTYSTATS_KEY")

# --- LEAGUE MAP ---
league_map = {
    "PL": {"id": 39, "name": "Premier League"},
    "Premier League": {"id": 39, "name": "Premier League"},
    "SA": {"id": 135, "name": "Serie A"},
    "Serie A": {"id": 135, "name": "Serie A"},
    "LL": {"id": 140, "name": "La Liga"},
    "La Liga": {"id": 140, "name": "La Liga"},
    "BL": {"id": 78, "name": "Bundesliga"},
    "Bundesliga": {"id": 78, "name": "Bundesliga"},
    "L1": {"id": 61, "name": "Ligue 1"},
    "Ligue 1": {"id": 61, "name": "Ligue 1"},
}

@router.get("/matches")
def get_upcoming_matches(
    league: str = Query(default="PL", description="League code or name, e.g. PL, SA, LL")
):
    try:
        info = league_map.get(league, league_map["PL"])
        today = datetime.utcnow().date()
        next_month = today + timedelta(days=30)  # only next 30 days

        # --- Primary API (Football-Data.org) ---
        url = f"https://api.football-data.org/v4/competitions/{league}/matches"
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if "matches" not in data:
            return {"league": info["name"], "matches": []}

        matches = []
        for m in data["matches"]:
            # Filter to only *upcoming* matches within 30 days
            match_date = datetime.strptime(m["utcDate"], "%Y-%m-%dT%H:%M:%SZ").date()
            if today <= match_date <= next_month and m["status"] in ["SCHEDULED", "TIMED"]:
                matches.append({
                    "home_team": m["homeTeam"]["name"],
                    "away_team": m["awayTeam"]["name"],
                    "date": match_date.strftime("%A, %d %B %Y"),
                    "time": m["utcDate"],
                    "home_logo": m["homeTeam"].get("crest", ""),
                    "away_logo": m["awayTeam"].get("crest", "")
                })

        return {"league": info["name"], "total_upcoming": len(matches), "matches": matches}

    except Exception as e:
        print(f"⚠️ Error fetching matches: {e}")
        return {"league": "Unknown", "matches": []}
