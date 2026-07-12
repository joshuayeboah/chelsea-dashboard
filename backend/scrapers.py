import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import requests
import unicodedata


from database import (
    get_all_players, upsert_player, upsert_performance,
    insert_market_value, log_scrape
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"
CHELSEA_ID = 49
PREMIER_LEAGUE_ID = 39
BLUECO_SEASONS = [2022, 2023, 2024, 2025]

HEADERS = {
    "x-apisports-key": API_KEY
}


def _get(endpoint: str, params: dict) -> dict:
    """Make a GET request to API-Football. Returns parsed JSON or empty dict."""
    try:
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


# Transfers scraper
def scrape_transfers():
    """
    Pull Chelsea's full transfer history from API-Football and upsert into DB.
    Covers all BlueCo era seasons (2022-present).
    """
    logger.info("Starting transfers scrape...")
    success_count = 0
    fail_count = 0

    data = _get("transfers", {"team": CHELSEA_ID})

    if not data.get("response"):
        logger.error("No transfer data returned from API")
        log_scrape("transfers", "failed", "Empty response")
        return

    transfers = data["response"]
    logger.info(f"Found {len(transfers)} transfer records")

    for record in transfers:
        player_info = record.get("player", {})
        name = player_info.get("name")

        if not name:
            continue

        for transfer in record.get("transfers", []):
            date_str = transfer.get("date", "")
            if not date_str:
                continue

            # Only process BlueCo era transfers (2022 onwards)
            try:
                year = int(date_str[:4])
                if year < 2022:
                    continue
            except (ValueError, TypeError):
                continue

            teams = transfer.get("teams", {})
            team_in = teams.get("in", {}).get("name", "")
            team_out = teams.get("out", {}).get("name", "")
            transfer_type = transfer.get("type", "N/A")

            is_incoming = "Chelsea" in team_in
            is_outgoing = "Chelsea" in team_out

            if not is_incoming and not is_outgoing:
                continue

            # Skip loan moves — we only want permanent transfers
            if transfer_type and transfer_type.lower() in ("loan", "n/a"):
                continue

            try:
                year = int(date_str[:4])
                month = int(date_str[5:7])
                is_post_blueco = (year > 2022) or (year == 2022 and month >= 5)
            except (ValueError, TypeError):
                continue

            if is_incoming and not is_post_blueco:
                continue

            fee = _parse_fee(transfer_type)
            season = _date_to_season(date_str)
            status = "sold" if is_outgoing and not is_incoming else "active"

            player_data = {
                "name": name,
                "position": "Unknown",
                "fee_million": fee if is_incoming else 0.0,
                "sale_fee_million": fee if is_outgoing else None,
                "season": season,
                "status": status,
            }

            try:
                upsert_player(player_data)
                success_count += 1
                logger.info(f"  ✓ {name} ({team_out} → {team_in}) £{fee}m")
            except Exception as e:
                logger.error(f"  ✗ Failed to upsert {name}: {e}")
                fail_count += 1

    message = f"Success: {success_count}, Failed: {fail_count}"
    log_scrape("transfers", "success" if fail_count == 0 else "partial", message)
    logger.info(f"Transfers scrape complete. {message}")


def _parse_fee(transfer_type: str) -> float:
    """
    Parse fee strings like '€45M', '£32M', 'Free', 'Loan', 'N/A' into float millions.
    """
    if not transfer_type or transfer_type in ("N/A", "Free", "Loan", "free", "loan"):
        return 0.0
    try:
        raw = transfer_type.replace("€", "").replace("£", "").replace(",", "").strip()
        if "M" in raw or "m" in raw:
            return float(raw.upper().replace("M", "").strip())
        elif "K" in raw or "k" in raw:
            return round(float(raw.upper().replace("K", "").strip()) / 1000, 2)
        else:
            return float(raw)
    except (ValueError, AttributeError):
        return 0.0


def _date_to_season(date_str: str) -> str:
    try:
        year = int(date_str[:4])
        month = int(date_str[5:7])
        if month >= 7:
            return f"{year}-{str(year + 1)[-2:]}"
        else:
            return f"{year - 1}-{str(year)[-2:]}"
    except (ValueError, TypeError):
        return "unknown"


# Performance stats scraper

def scrape_performance():
    """
    Pull season stats for all Chelsea players across BlueCo seasons.
    Updates minutes, goals, assists in the performance table.
    Note: xG/xA not available
    """
    logger.info("Starting performance scrape...")
    success_count = 0
    fail_count = 0

    players = get_all_players()
    player_map = {p["name"].lower(): p for p in players}

    for season in BLUECO_SEASONS:
        logger.info(f"Fetching stats for {season}/{season+1} season...")

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

                minutes = games.get("minutes") or 0
                goals_scored = goals.get("total") or 0
                assists = goals.get("assists") or 0
                position = games.get("position", "Unknown")

                season_str = f"{season}-{str(season + 1)[-2:]}"

                matched = _match_name(name, player_map)
                if not matched:
                    logger.warning(f"  No match for {name}")
                    fail_count += 1
                    continue

                

                upsert_performance(matched["id"], season_str, {
                    "minutes_played": minutes,
                    "goals": goals_scored,
                    "assists": assists,
                    "xg": matched.get("xg") or 0,
                    "xa": matched.get("xa") or 0,
                    "progressive_carries": matched.get("progressive_carries") or 0,
                    "progressive_passes": matched.get("progressive_passes") or 0,
                })

                logger.info(f"  ✓ {name} ({season_str}): {minutes}m {goals_scored}g {assists}a")
                success_count += 1

    message = f"Success: {success_count}, Unmatched: {fail_count}"
    log_scrape("performance", "success" if fail_count == 0 else "partial", message)
    logger.info(f"Performance scrape complete. {message}")



def _normalize(text: str) -> str:
    """Lowercase, strip accents, remove punctuation."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


NAME_OVERRIDES = {
    "w. fofana": "Wesley Fofana",
    "d. fofana": "David Datro Fofana",
    "ângelo": "Angelo Gabriel",
    "angelo": "Angelo Gabriel",
    "joão félix": "Joao Felix",
    "joão pedro": "Joao Pedro",
    "đ. petrović": "Djordje Petrovic",
    "robert sánchez": "Robert Sanchez",
    "e. fernández": "Enzo Fernandez",
    "f. jörgensen": "Filip Jorgensen",
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
}

def _match_name(api_name: str, player_map: dict):
    api_lower = api_name.lower().strip()
    
    # Manual overrides for ambiguous or differently formatted names
    if api_lower in NAME_OVERRIDES:
        target = NAME_OVERRIDES[api_lower].lower()
        return player_map.get(target)
    
    api_norm = _normalize(api_name)
    
    # Exact match after normalization
    for db_name, player in player_map.items():
        if _normalize(db_name) == api_norm:
            return player

    # Last name match — only if unambiguous
    api_last = api_norm.split()[-1] if api_norm.split() else ""
    if not api_last:
        return None

    matches = [
        player for db_name, player in player_map.items()
        if _normalize(db_name).split()[-1] == api_last
    ]

    if len(matches) == 1:
        return matches[0]

    return None


# Entry point
def run_all_scrapers():
    logger.info(f"Running all scrapers at {datetime.now().isoformat()}")
    try:
        scrape_performance()
    except Exception as e:
        logger.error(f"Performance scraper failed: {e}")
        log_scrape("performance", "failed", str(e))

    logger.info("All scrapers finished.")


if __name__ == "__main__":
    run_all_scrapers()