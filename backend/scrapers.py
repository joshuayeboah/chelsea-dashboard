import os
import time
import logging
import unicodedata
from datetime import datetime
from dotenv import load_dotenv
import requests

from database import (
    get_all_players, upsert_performance, log_scrape
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
CHELSEA_ID = 49
PREMIER_LEAGUE_ID = 39
BLUECO_SEASONS = [2022, 2023, 2024, 2025, 2026]

HEADERS = {"x-apisports-key": API_KEY}

NAME_OVERRIDES = {
    "w. fofana": "Wesley Fofana",
    "d. fofana": "David Datro Fofana",
    "angelo": "Angelo Gabriel",
    "joao felix": "Joao Felix",
    "joao pedro": "Joao Pedro",
    "d. petrovic": "Djordje Petrovic",
    "robert sanchez": "Robert Sanchez",
    "e. fernandez": "Enzo Fernandez",
    "f. jorgensen": "Filip Jorgensen",
    "p. aubameyang": "Pierre-Emerick Aubameyang",
    "k. koulibaly": "Kalidou Koulibaly",
    "r. sterling": "Raheem Sterling",
    "m. caicedo": "Moises Caicedo",
    "r. lavia": "Romeo Lavia",
    "m. mudryk": "Mykhailo Mudryk",
    "c. palmer": "Cole Palmer",
    "n. jackson": "Nicolas Jackson",
    "m. gusto": "Malo Gusto",
    "l. colwill": "Levi Colwill",
    "b. badiashile": "Benoit Badiashile",
    "t. adarabioyo": "Tosin Adarabioyo",
    "n. madueke": "Noni Madueke",
    "c. nkunku": "Christopher Nkunku",
    "a. garnacho": "Alejandro Garnacho",
    "l. ugochukwu": "Lesley Ugochukwu",
    "k. dewsbury-hall": "Kiernan Dewsbury-Hall",
    "c. chukwuemeka": "Carney Chukwuemeka",
    "i. maatsen": "Ian Maatsen",
    "m. sarr": "Mamadou Sarr",
    "pedro neto": "Pedro Neto",
    "renato veiga": "Renato Veiga",
    "andrey santos": "Andrey Santos",
    "deivid washington": "Deivid Washington",
    "estevao": "Estevao Willian",
}


def _get(endpoint: str, params: dict) -> dict:
    try:
        time.sleep(1)
        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            headers=HEADERS,
            params=params,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        remaining = response.headers.get("x-ratelimit-requests-remaining", "?")
        logger.info(f"API requests remaining today: {remaining}")
        return data
    except requests.RequestException as e:
        logger.error(f"API request failed for {endpoint}: {e}")
        return {}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def _match_name(api_name: str, player_map: dict):
    api_lower = _normalize(api_name)

    if api_lower in NAME_OVERRIDES:
        target = _normalize(NAME_OVERRIDES[api_lower])
        return player_map.get(target)

    for db_name, player in player_map.items():
        if _normalize(db_name) == api_lower:
            return player

    api_last = api_lower.split()[-1] if api_lower.split() else ""
    if not api_last:
        return None

    matches = [
        player for db_name, player in player_map.items()
        if _normalize(db_name).split()[-1] == api_last
    ]

    return matches[0] if len(matches) == 1 else None


def scrape_performance():
    logger.info("Starting performance scrape...")
    success_count = 0
    fail_count = 0
    skipped_count = 0

    players = get_all_players()
    player_map = {_normalize(p["name"]): p for p in players}

    for season in BLUECO_SEASONS:
        logger.info(f"Fetching stats for {season}/{season+1} season...")
        season_str = f"{season}-{str(season + 1)[-2:]}"

        data = _get("players", {
            "team": CHELSEA_ID,
            "season": season,
            "league": PREMIER_LEAGUE_ID
        })

        if not data.get("response"):
            logger.warning(f"No player data for season {season}")
            continue

        total_pages = data.get("paging", {}).get("total", 1)

        for page in range(1, total_pages + 1):
            if page > 1:
                data = _get("players", {
                    "team": CHELSEA_ID,
                    "season": season,
                    "league": PREMIER_LEAGUE_ID,
                    "page": page
                })

            for entry in data.get("response", []):
                player_info = entry.get("player", {})
                name = player_info.get("name", "")
                stats_list = entry.get("statistics", [])

                if not stats_list:
                    continue

                stats = stats_list[0]
                games = stats.get("games", {})
                goals = stats.get("goals", {})
                shots = stats.get("shots", {})
                passes = stats.get("passes", {})
                dribbles = stats.get("dribbles", {})
                cards = stats.get("cards", {})

                minutes = games.get("minutes") or 0
                goals_scored = goals.get("total") or 0
                assists = goals.get("assists") or 0
                shots_total = shots.get("total") or 0
                shots_on = shots.get("on") or 0
                key_passes = passes.get("key") or 0
                dribbles_success = dribbles.get("success") or 0
                yellow_cards = cards.get("yellow") or 0
                red_cards = cards.get("red") or 0
                rating = float(games.get("rating") or 0.0)

                matched = _match_name(name, player_map)
                if not matched:
                    logger.warning(f"  No match for {name}")
                    fail_count += 1
                    continue

                signing_season = matched.get("season", "2022-23")
                if season_str < signing_season:
                    logger.info(f"  Skipping {name} {season_str} — signed in {signing_season}")
                    skipped_count += 1
                    continue

                upsert_performance(matched["id"], season_str, {
                    "minutes_played": minutes,
                    "goals": goals_scored,
                    "assists": assists,
                    "xg": 0.0,
                    "xa": 0.0,
                    "progressive_carries": 0,
                    "progressive_passes": 0,
                    "shots_total": shots_total,
                    "shots_on": shots_on,
                    "key_passes": key_passes,
                    "dribbles_success": dribbles_success,
                    "yellow_cards": yellow_cards,
                    "red_cards": red_cards,
                    "rating": rating,
                })

                logger.info(f"  ✓ {name} ({season_str}): {minutes}m {goals_scored}g {assists}a")
                success_count += 1

    message = f"Success: {success_count}, Skipped (pre-signing): {skipped_count}, Unmatched: {fail_count}"
    log_scrape("performance", "success" if fail_count == 0 else "partial", message)
    logger.info(f"Performance scrape complete. {message}")


def run_all_scrapers():
    """
    Refresh performance stats for the current roster. The roster itself
    (name, position, fee, nationality, age, market value) is hand-curated in
    transfers.json and loaded via seed.py — see main.py's lifespan — since
    API-Football doesn't reliably expose those fields for auto-discovery.
    """
    logger.info(f"Running all scrapers at {datetime.now().isoformat()}")
    try:
        scrape_performance()
    except Exception as e:
        logger.error(f"Performance scraper failed: {e}")
        log_scrape("performance", "failed", str(e))
    logger.info("All scrapers finished.")


if __name__ == "__main__":
    run_all_scrapers()