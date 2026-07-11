import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "chelsea.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            position        TEXT NOT NULL,
            nationality     TEXT,
            age_at_signing  INTEGER,
            fee_million     REAL DEFAULT 0.0,
            sale_fee_million REAL,
            season          TEXT,
            contract_years  INTEGER,
            status          TEXT DEFAULT 'active',
            transfermarkt_id TEXT,
            fbref_id        TEXT,
            last_updated    TEXT
        );

        CREATE TABLE IF NOT EXISTS performance (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id           INTEGER NOT NULL,
            season              TEXT NOT NULL,
            minutes_played      INTEGER DEFAULT 0,
            goals               INTEGER DEFAULT 0,
            assists             INTEGER DEFAULT 0,
            xg                  REAL DEFAULT 0.0,
            xa                  REAL DEFAULT 0.0,
            progressive_carries INTEGER DEFAULT 0,
            progressive_passes  INTEGER DEFAULT 0,
            last_updated        TEXT,
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE(player_id, season)
        );

        CREATE TABLE IF NOT EXISTS market_values (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id       INTEGER NOT NULL,
            market_value    REAL,
            recorded_date   TEXT,
            FOREIGN KEY (player_id) REFERENCES players(id)
        );

        CREATE TABLE IF NOT EXISTS scrape_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            scraper     TEXT NOT NULL,
            status      TEXT NOT NULL,
            message     TEXT,
            ran_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()
    print("Database initialised.")


def get_all_players():
    """Return all players with their latest market value and aggregated performance."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.*,
            mv.market_value as market_value_now,
            COALESCE(SUM(perf.minutes_played), 0) as minutes_played,
            COALESCE(SUM(perf.goals), 0) as goals,
            COALESCE(SUM(perf.assists), 0) as assists,
            COALESCE(SUM(perf.xg), 0.0) as xg,
            COALESCE(SUM(perf.xa), 0.0) as xa,
            COALESCE(SUM(perf.progressive_carries), 0) as progressive_carries,
            COALESCE(SUM(perf.progressive_passes), 0) as progressive_passes
        FROM players p
        LEFT JOIN (
            SELECT player_id, market_value
            FROM market_values
            WHERE id IN (
                SELECT MAX(id) FROM market_values GROUP BY player_id
            )
        ) mv ON mv.player_id = p.id
        LEFT JOIN performance perf ON perf.player_id = p.id
        GROUP BY p.id
    """)

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_players_with_filters(position_group=None, season=None, status=None, min_fee=None, max_fee=None):
    """Filtered version of get_all_players."""
    players = get_all_players()

    POSITION_GROUPS = {
        "GK": ["GK"],
        "DEF": ["CB", "RB", "LB"],
        "MID": ["DM", "CM", "AM"],
        "FWD": ["FW"],
    }

    if position_group:
        allowed = POSITION_GROUPS.get(position_group.upper(), [])
        players = [p for p in players if p["position"] in allowed]
    if season:
        players = [p for p in players if p["season"] == season]
    if status:
        players = [p for p in players if p["status"] == status]
    if min_fee is not None:
        players = [p for p in players if p["fee_million"] >= min_fee]
    if max_fee is not None:
        players = [p for p in players if p["fee_million"] <= max_fee]

    return players


def upsert_player(player: dict) -> int:
    """Insert or update a player record. Returns the player id."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM players WHERE name = ?", (player["name"],))
    row = cursor.fetchone()

    if row:
        player_id = row["id"]
        cursor.execute("""
            UPDATE players SET
                position = ?,
                nationality = ?,
                age_at_signing = ?,
                fee_million = ?,
                sale_fee_million = ?,
                season = ?,
                contract_years = ?,
                status = ?,
                transfermarkt_id = ?,
                last_updated = datetime('now')
            WHERE id = ?
        """, (
            player.get("position"),
            player.get("nationality"),
            player.get("age_at_signing"),
            player.get("fee_million", 0),
            player.get("sale_fee_million"),
            player.get("season"),
            player.get("contract_years"),
            player.get("status", "active"),
            player.get("transfermarkt_id"),
            player_id,
        ))
    else:
        cursor.execute("""
            INSERT INTO players
                (name, position, nationality, age_at_signing, fee_million,
                 sale_fee_million, season, contract_years, status, transfermarkt_id, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            player["name"],
            player.get("position"),
            player.get("nationality"),
            player.get("age_at_signing"),
            player.get("fee_million", 0),
            player.get("sale_fee_million"),
            player.get("season"),
            player.get("contract_years"),
            player.get("status", "active"),
            player.get("transfermarkt_id"),
        ))
        player_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return player_id


def upsert_performance(player_id: int, season: str, stats: dict):
    """Insert or update performance stats for a player/season."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO performance
            (player_id, season, minutes_played, goals, assists, xg, xa,
             progressive_carries, progressive_passes, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(player_id, season) DO UPDATE SET
            minutes_played = excluded.minutes_played,
            goals = excluded.goals,
            assists = excluded.assists,
            xg = excluded.xg,
            xa = excluded.xa,
            progressive_carries = excluded.progressive_carries,
            progressive_passes = excluded.progressive_passes,
            last_updated = excluded.last_updated
    """, (
        player_id,
        season,
        stats.get("minutes_played", 0),
        stats.get("goals", 0),
        stats.get("assists", 0),
        stats.get("xg", 0.0),
        stats.get("xa", 0.0),
        stats.get("progressive_carries", 0),
        stats.get("progressive_passes", 0),
    ))

    conn.commit()
    conn.close()


def insert_market_value(player_id: int, value: float):
    """Record a market value snapshot."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO market_values (player_id, market_value, recorded_date)
        VALUES (?, ?, date('now'))
    """, (player_id, value))

    conn.commit()
    conn.close()


def log_scrape(scraper: str, status: str, message: str = ""):
    """Log a scraper run to the scrape_log table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scrape_log (scraper, status, message) VALUES (?, ?, ?)",
        (scraper, status, message)
    )
    conn.commit()
    conn.close()