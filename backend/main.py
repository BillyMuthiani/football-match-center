from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone, timedelta

load_dotenv()

app = FastAPI(title="Football Match Center")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys from .env
API_SPORTS_KEY = os.getenv("API_SPORTS_KEY")
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY")
SPORTS_MONK_KEY = os.getenv("SPORTS_MONK_KEY")
FOOTYSTATS_KEY = os.getenv("FOOTYSTATS_KEY")

# League mapping
LEAGUE_IDS = {
    "Premier League": 39,
    "Serie A": 135,
    "La Liga": 140,
    "Bundesliga": 78,
    "Ligue 1": 61
}
@app.get("/matches")
def get_upcoming_matches(league: str = Query("Premier League", description="League name e.g. Premier League")):
    league_id = LEAGUE_IDS.get(league)
    if not league_id:
        return {"error": f"League '{league}' not found."}

    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=7)

    # Primary source: API-SPORTS
    try:
        url = (
            f"https://v3.football.api-sports.io/fixtures"
            f"?league={league_id}&season=2025&from={today}&to={end_date}"
        )
        headers = {"x-apisports-key": API_SPORTS_KEY}
        response = requests.get(url, headers=headers)
        data = response.json()

        if data.get("response"):
            matches = [
                {
                    "home": match["teams"]["home"]["name"],
                    "away": match["teams"]["away"]["name"],
                    "home_logo": match["teams"]["home"]["logo"],
                    "away_logo": match["teams"]["away"]["logo"],
                    "date": match["fixture"]["date"]
                }
                for match in data["response"]
            ]
            if matches:
                return {"league": league, "matches": matches}
    except Exception as e:
        print(f"⚠️ API-Sports failed: {e}")

    # Fallback: Football-Data.org
    try:
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        url = f"https://api.football-data.org/v4/competitions/{league_id}/matches?status=SCHEDULED"
        response = requests.get(url, headers=headers)
        data = response.json()
        matches = [
            {
                "home": m["homeTeam"]["name"],
                "away": m["awayTeam"]["name"],
                "date": m["utcDate"]
            }
            for m in data.get("matches", [])
            if datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).date() >= today
        ]
        if matches:
            return {"league": league, "matches": matches}
    except Exception as e:
        print(f"⚠️ Football-Data fallback failed: {e}")

    # Fallback: SportsMonk (if API key exists)
    if SPORTS_MONK_KEY:
        try:
            url = f"https://api.sportmonks.com/v3/football/fixtures/between/{today}/{end_date}?leagues={league_id}&api_token={SPORTS_MONK_KEY}"
            response = requests.get(url)
            data = response.json()
            matches = [
                {
                    "home": f["participants"][0]["name"] if f["participants"] else "TBD",
                    "away": f["participants"][1]["name"] if len(f["participants"]) > 1 else "TBD",
                    "date": f["starting_at"]
                }
                for f in data.get("data", [])
            ]
            if matches:
                return {"league": league, "matches": matches}
        except Exception as e:
            print(f"⚠️ SportsMonk failed: {e}")

    # Fallback: FootyStats (if API key exists)
    if FOOTYSTATS_KEY:
        try:
            url = f"https://api.footystats.org/league-matches?key={FOOTYSTATS_KEY}&league_id={league_id}"
            response = requests.get(url)
            data = response.json()
            matches = [
                {
                    "home": m["home_name"],
                    "away": m["away_name"],
                    "date": m["date"]
                }
                for m in data.get("data", [])
                if datetime.fromisoformat(m["date"]).date() >= today
            ]
            if matches:
                return {"league": league, "matches": matches}
        except Exception as e:
            print(f"⚠️ FootyStats failed: {e}")

    return {"league": league, "matches": []}
    