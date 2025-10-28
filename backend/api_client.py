import os
import requests
import logging
from datetime import datetime
from cachetools import TTLCache
from typing import Any, Dict, Optional, List

# ---------------------------
# Environment & Config
# ---------------------------
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY", "your_football_data_api_key")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "your_api_football_key")
SPORTMONKS_KEY = os.getenv("SPORTMONKS_KEY", "your_sportmonks_key")

# Cache responses (max 50 entries, 5 min TTL)
cache = TTLCache(maxsize=50, ttl=300)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("football_api")


# ---------------------------
# Helpers
# ---------------------------
def format_date(utc_str: Optional[str]) -> Optional[str]:
    """Convert UTC string to human-readable format."""
    if not utc_str:
        return None
    try:
        return datetime.strptime(utc_str, "%Y-%m-%dT%H:%M:%SZ").strftime(
            "%A, %d %B %Y %H:%M UTC"
        )
    except Exception:
        return utc_str


def normalize_football_data_match(m: dict) -> dict:
    return {
        "home_team": m["homeTeam"]["name"],
        "away_team": m["awayTeam"]["name"],
        "home_logo": m["homeTeam"].get("crest"),
        "away_logo": m["awayTeam"].get("crest"),
        "matchday": m.get("matchday"),
        "date": format_date(m.get("utcDate")),
        "status": m.get("status"),
        "score": {
            "home": m["score"]["fullTime"].get("home"),
            "away": m["score"]["fullTime"].get("away"),
        },
    }


def normalize_api_football_match(m: dict) -> dict:
    fixture = m.get("fixture", {})
    teams = m.get("teams", {})
    goals = m.get("goals", {})
    return {
        "home_team": teams.get("home", {}).get("name"),
        "away_team": teams.get("away", {}).get("name"),
        "home_logo": teams.get("home", {}).get("logo"),
        "away_logo": teams.get("away", {}).get("logo"),
        "matchday": fixture.get("round"),
        "date": format_date(fixture.get("date")),
        "status": fixture.get("status", {}).get("short"),
        "score": {"home": goals.get("home"), "away": goals.get("away")},
    }


def normalize_sportmonks_match(m: dict) -> dict:
    home = m.get("homeTeam", {}) or m.get("participants", [{}])[0]
    away = m.get("awayTeam", {}) or m.get("participants", [{}])[1]
    return {
        "home_team": home.get("name"),
        "away_team": away.get("name"),
        "home_logo": home.get("image_path"),
        "away_logo": away.get("image_path"),
        "matchday": m.get("round", {}).get("name"),
        "date": format_date(m.get("starting_at")),
        "status": m.get("time", {}).get("status"),
        "score": {
            "home": m.get("scores", {}).get("localteam_score"),
            "away": m.get("scores", {}).get("visitorteam_score"),
        },
    }


# ---------------------------
# API Fetchers
# ---------------------------
def fetch_from_football_data(league: str, mode: str) -> Optional[Dict[str, Any]]:
    endpoints = {
        "upcoming": f"https://api.football-data.org/v4/competitions/{league}/matches?status=SCHEDULED",
        "live": f"https://api.football-data.org/v4/competitions/{league}/matches?status=LIVE",
        "results": f"https://api.football-data.org/v4/competitions/{league}/matches?status=FINISHED",
    }
    try:
        r = requests.get(endpoints[mode], headers={"X-Auth-Token": FOOTBALL_DATA_KEY}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            data["source"] = "football-data.org"
            return data
        logger.warning(f"⚠️ Football-Data returned {r.status_code}")
    except Exception as e:
        logger.error(f"Football-Data error: {e}")
    return None


def fetch_from_api_football(league: str, mode: str) -> Optional[Dict[str, Any]]:
    endpoints = {
        "upcoming": f"https://v3.football.api-sports.io/fixtures?league={league}&next=10",
        "live": "https://v3.football.api-sports.io/fixtures?live=all",
        "results": f"https://v3.football.api-sports.io/fixtures?league={league}&last=10",
    }
    try:
        r = requests.get(endpoints[mode], headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            data["source"] = "api-football"
            return data
        logger.warning(f"⚠️ API-Football returned {r.status_code}")
    except Exception as e:
        logger.error(f"API-Football error: {e}")
    return None


def fetch_from_sportmonks(league: str, mode: str) -> Optional[Dict[str, Any]]:
    endpoints = {
        "upcoming": f"https://api.sportmonks.com/v3/football/fixtures/upcoming?api_token={SPORTMONKS_KEY}",
        "live": f"https://api.sportmonks.com/v3/football/livescores/now?api_token={SPORTMONKS_KEY}",
        "results": f"https://api.sportmonks.com/v3/football/fixtures/finished?api_token={SPORTMONKS_KEY}",
    }
    try:
        r = requests.get(endpoints[mode], timeout=10)
        if r.status_code == 200:
            data = r.json()
            data["source"] = "sportmonks"
            return data
        logger.warning(f"⚠️ SportMonks returned {r.status_code}")
    except Exception as e:
        logger.error(f"SportMonks error: {e}")
    return None


# ---------------------------
# Fallback Chain (Auto Retry)
# ---------------------------
def fetch_matches(league: str, mode: str) -> Dict[str, Any]:
    cache_key = f"{league}_{mode}"
    if cache_key in cache:
        logger.info(f"✅ Returning cached {league}-{mode} data")
        return cache[cache_key]

    logger.info(f"🔍 Fetching {mode} matches for {league}...")

    providers = [
        ("football-data.org", fetch_from_football_data),
        ("api-football", fetch_from_api_football),
        ("sportmonks", fetch_from_sportmonks),
    ]

    for name, func in providers:
        logger.info(f"→ Trying {name}...")
        data = func(league, mode)
        if data:
            logger.info(f"✅ Success with {name}")
            cache[cache_key] = data
            return data
        else:
            logger.warning(f"❌ {name} failed, trying next provider...")

    logger.error("🚨 All providers failed!")
    raise Exception("All APIs failed to fetch match data")


# ---------------------------
# Normalization
# ---------------------------
def normalize_matches(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    source = data.get("source")
    if source == "football-data.org":
        return [normalize_football_data_match(m) for m in data.get("matches", [])]
    elif source == "api-football":
        return [normalize_api_football_match(m) for m in data.get("response", [])]
    elif source == "sportmonks":
        return [normalize_sportmonks_match(m) for m in data.get("data", [])]
    return []
