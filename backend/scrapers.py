"""
scrapers.py — pulls live transfer and performance data from transfermarkt and fbref


Both sites block naive scrapers, so we use:
  - Realistic browser headers
  - Random delays between requests
  - Retry logic with backoff
"""

import time
import random
import logging
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from database import (
    get_all_players, upsert_player, upsert_performance,
    insert_market_value, log_scrape
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Shared HTTP helpers

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

TM_HEADERS = {
    **HEADERS,
    "Referer": "https://www.transfermarkt.com/",
}


def _get(url: str, headers: dict, retries: int = 3, delay: float = 2.0) -> Optional[BeautifulSoup]:
    """GET a page with retries and random delay. Returns BeautifulSoup or None."""
    for attempt in range(retries):
        try:
            _sleep(delay)
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            wait = delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}. Retrying in {wait:.1f}s")
            time.sleep(wait)
    logger.error(f"All {retries} attempts failed for {url}")
    return None


def _sleep(base: float = 2.0):
    """Random delay to avoid rate limiting."""
    time.sleep(base + random.uniform(0.5, 2.0))


# Transfermarkt scraper

# Chelsea's BlueCo-era squad page on Transfermarkt
CHELSEA_SQUAD_URL = "https://www.transfermarkt.com/fc-chelsea/kader/verein/631/saison_id/2024"

# Known Transfermarkt player IDs for BlueCo signings
# Format: "Player Name": "transfermarkt_id"
PLAYER_TM_IDS = {
    "Enzo Fernandez": "580195",
    "Moises Caicedo": "572479",
    "Nicolas Jackson": "768177",
    "Romeo Lavia": "826367",
    "Christopher Nkunku": "339018",
    "Mykhailo Mudryk": "660226",
    "Noni Madueke": "572479",
    "Malo Gusto": "658614",
    "Benoit Badiashile": "494762",
    "Levi Colwill": "768204",
    "Joao Felix": "461850",
    "Wesley Fofana": "548256",
    "Marc Cucurella": "339556",
    "Axel Disasi": "374396",
    "Cole Palmer": "700826",
    "Kiernan Dewsbury-Hall": "493946",
    "Tosin Adarabioyo": "339894",
    "Pedro Neto": "451911",
    "Jadon Sancho": "401173",
    "Filip Jorgensen": "700307",
}

TM_PLAYER_BASE = "https://www.transfermarkt.com/x/marktwertverlauf/spieler/{tm_id}"


def scrape_transfermarkt():
    """
    Pull current market values for all players from Transfermarkt.
    Updates market_values table and player status.
    """
    logger.info("Starting Transfermarkt scrape...")
    players = get_all_players()
    success_count = 0
    fail_count = 0

    for player in players:
        name = player["name"]
        tm_id = PLAYER_TM_IDS.get(name)

        if not tm_id:
            logger.warning(f"No Transfermarkt ID for {name} — skipping")
            continue

        url = f"https://www.transfermarkt.com/x/profil/spieler/{tm_id}"
        soup = _get(url, TM_HEADERS)

        if not soup:
            fail_count += 1
            continue

        market_value = _parse_tm_market_value(soup)

        if market_value is not None:
            insert_market_value(player["id"], market_value)
            logger.info(f"  ✓ {name}: £{market_value}m")
            success_count += 1
        else:
            logger.warning(f"  ✗ {name}: could not parse market value")
            fail_count += 1

    message = f"Success: {success_count}, Failed: {fail_count}"
    log_scrape("transfermarkt", "success" if fail_count == 0 else "partial", message)
    logger.info(f"Transfermarkt scrape complete. {message}")


def _parse_tm_market_value(soup: BeautifulSoup) -> Optional[float]:
    """
    Extract current market value from a Transfermarkt player profile page.
    Values are in format like '£85.00m' or '£500k'.
    """
    try:
        # Transfermarkt stores market value in this element
        value_elem = soup.find("a", {"class": "data-header__market-value-wrapper"})
        if not value_elem:
            # Fallback selector
            value_elem = soup.find("div", {"class": "tm-player-market-value-development__current-value"})

        if not value_elem:
            return None

        raw = value_elem.get_text(strip=True)
        return _parse_value_string(raw)
    except Exception as e:
        logger.error(f"Error parsing market value: {e}")
        return None


def _parse_value_string(raw: str) -> Optional[float]:
    """
    Convert strings like '£85.00m', '£500k', '€72m' to float millions.
    """
    try:
        raw = raw.replace("£", "").replace("€", "").replace(",", "").strip()
        if "m" in raw.lower():
            return float(raw.lower().replace("m", "").strip())
        elif "k" in raw.lower():
            return round(float(raw.lower().replace("k", "").strip()) / 1000, 2)
        else:
            return float(raw)
    except (ValueError, AttributeError):
        return None


# FBref scraper

# FBref Chelsea squad stats page (2024-25 Premier League)
FBREF_CHELSEA_URL = "https://fbref.com/en/squads/cff3d9bb/2024-2025/Chelsea-Stats"

# Standard stats table on FBref squad pages
FBREF_STATS_TABLE_ID = "stats_standard_9"


def scrape_fbref():
    """
    Pull current season performance stats for all Chelsea players from FBref.
    Updates the performance table.
    """
    logger.info("Starting FBref scrape...")

    soup = _get(FBREF_CHELSEA_URL, HEADERS, delay=3.0)
    if not soup:
        log_scrape("fbref", "failed", "Could not fetch FBref squad page")
        return

    stats = _parse_fbref_stats_table(soup)

    if not stats:
        log_scrape("fbref", "failed", "Could not parse stats table")
        return

    players = get_all_players()
    player_map = {p["name"].lower(): p for p in players}

    success_count = 0
    fail_count = 0
    current_season = "2024-25"

    for fbref_name, stat_row in stats.items():
        # Try to match FBref name to our player records
        matched_player = _match_player_name(fbref_name, player_map)

        if not matched_player:
            logger.warning(f"  No match found for FBref player: {fbref_name}")
            fail_count += 1
            continue

        upsert_performance(matched_player["id"], current_season, stat_row)
        logger.info(f"  ✓ {matched_player['name']}: {stat_row['minutes_played']} mins, "
                    f"{stat_row['goals']}g {stat_row['assists']}a")
        success_count += 1

    message = f"Success: {success_count}, Failed/unmatched: {fail_count}"
    log_scrape("fbref", "success" if fail_count == 0 else "partial", message)
    logger.info(f"FBref scrape complete. {message}")


def _parse_fbref_stats_table(soup: BeautifulSoup) -> dict:
    """
    Parse the standard stats table from FBref squad page.
    Returns dict keyed by player name.
    """
    stats = {}

    table = soup.find("table", {"id": FBREF_STATS_TABLE_ID})
    if not table:
        # FBref sometimes wraps tables in a div with a comment — try alternate
        logger.warning("Standard stats table not found by ID, trying alternate selector")
        table = soup.find("table", {"class": "stats_table"})

    if not table:
        logger.error("Could not find stats table on FBref page")
        return stats

    tbody = table.find("tbody")
    if not tbody:
        return stats

    for row in tbody.find_all("tr"):
        # Skip spacer rows
        if row.get("class") and "spacer" in row.get("class"):
            continue

        cells = row.find_all(["td", "th"])
        if not cells:
            continue

        try:
            name_cell = row.find("td", {"data-stat": "player"})
            if not name_cell:
                continue

            name = name_cell.get_text(strip=True)
            if not name:
                continue

            def get_stat(stat_name, default=0):
                cell = row.find("td", {"data-stat": stat_name})
                if not cell:
                    return default
                val = cell.get_text(strip=True)
                try:
                    return float(val) if "." in val else int(val)
                except (ValueError, TypeError):
                    return default

            stats[name] = {
                "minutes_played": get_stat("minutes"),
                "goals": get_stat("goals"),
                "assists": get_stat("assists"),
                "xg": get_stat("xg"),
                "xa": get_stat("xg_assist"),
                "progressive_carries": get_stat("progressive_carries"),
                "progressive_passes": get_stat("progressive_passes"),
            }

        except Exception as e:
            logger.error(f"Error parsing row: {e}")
            continue

    logger.info(f"Parsed {len(stats)} players from FBref table")
    return stats


def _match_player_name(fbref_name: str, player_map: dict) -> Optional[dict]:
    """
    Match an FBref player name to our database records.
    FBref uses full names which may differ slightly from our records.
    """
    fbref_lower = fbref_name.lower().strip()

    # Exact match first
    if fbref_lower in player_map:
        return player_map[fbref_lower]

    # Partial match — check if any part of the FBref name matches
    for db_name, player in player_map.items():
        db_parts = set(db_name.split())
        fbref_parts = set(fbref_lower.split())
        # If last name matches, that's good enough
        if db_parts & fbref_parts:
            return player

    return None


# ---------------------------------------------------------------------------
# Run all scrapers
# ---------------------------------------------------------------------------

def run_all_scrapers():
    """Entry point called by the scheduler."""
    logger.info(f"Running all scrapers at {datetime.now().isoformat()}")
    try:
        scrape_transfermarkt()
    except Exception as e:
        logger.error(f"Transfermarkt scraper failed: {e}")
        log_scrape("transfermarkt", "failed", str(e))

    try:
        scrape_fbref()
    except Exception as e:
        logger.error(f"FBref scraper failed: {e}")
        log_scrape("fbref", "failed", str(e))

    logger.info("All scrapers finished.")


if __name__ == "__main__":
    run_all_scrapers()