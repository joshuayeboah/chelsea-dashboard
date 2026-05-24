from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import math
from pathlib import Path

app = FastAPI(title="Chelsea Transfer Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent / "transfers.json"

def load_transfers():
    with open(DATA_PATH) as f:
        return json.load(f)

POSITION_GROUPS = {
    "GK": ["GK"],
    "DEF": ["CB", "RB", "LB"],
    "MID": ["DM", "CM", "AM"],
    "FWD": ["FW"],
}

def get_position_group(position: str) -> str:
    for group, positions in POSITION_GROUPS.items():
        if position in positions:
            return group
    return "OTHER"

def compute_metrics(player: dict) -> dict:
    minutes = player["minutes_played"]
    fee = player["fee_million"]
    nineties = minutes / 90 if minutes > 0 else 0

    cost_per_90 = round(fee / nineties, 2) if nineties > 0 else None

    # Goal contributions per 90
    gc = player["goals"] + player["assists"]
    gc_per_90 = round(gc / nineties, 2) if nineties > 0 else 0

    # xG + xA per 90
    xg_xa = player["xg"] + player["xa"]
    xg_xa_per_90 = round(xg_xa / nineties, 2) if nineties > 0 else 0

    # Value score: market_value / fee (>1 = appreciated, <1 = depreciated)
    # Free transfers get a special treatment
    if fee > 0:
        value_score = round(player["market_value_now"] / fee, 2)
    else:
        value_score = None  # Free transfers shown separately

    # Minutes utilisation: % of possible minutes played (rough 3800 per full season)
    seasons_at_club = max(1, _seasons_active(player["season"]))
    available_minutes = seasons_at_club * 3800
    minutes_util = round((minutes / available_minutes) * 100, 1)

    # Injury flag: less than 40% utilisation
    injury_flag = minutes_util < 40

    return {
        **player,
        "position_group": get_position_group(player["position"]),
        "nineties": round(nineties, 1),
        "cost_per_90": cost_per_90,
        "gc_per_90": gc_per_90,
        "xg_xa_per_90": xg_xa_per_90,
        "value_score": value_score,
        "minutes_util": minutes_util,
        "injury_flag": injury_flag,
        "profit_loss": round(player["market_value_now"] - fee, 1),
    }

def _seasons_active(season_signed: str) -> int:
    """Rough count of seasons a player has been at the club."""
    season_map = {
        "2022-23": 3,
        "2023-24": 2,
        "2024-25": 1,
        "2025-26": 1,
    }
    return season_map.get(season_signed, 1)


@app.get("/")
def root():
    return {"message": "Chelsea Transfer Dashboard API"}


@app.get("/transfers")
def get_transfers(
    position_group: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_fee: Optional[float] = Query(None),
    max_fee: Optional[float] = Query(None),
):
    transfers = load_transfers()
    results = [compute_metrics(p) for p in transfers]

    if position_group:
        results = [r for r in results if r["position_group"] == position_group.upper()]
    if season:
        results = [r for r in results if r["season"] == season]
    if status:
        results = [r for r in results if r["status"] == status]
    if min_fee is not None:
        results = [r for r in results if r["fee_million"] >= min_fee]
    if max_fee is not None:
        results = [r for r in results if r["fee_million"] <= max_fee]

    return {"count": len(results), "transfers": results}


@app.get("/metrics/summary")
def get_summary():
    transfers = load_transfers()
    players = [compute_metrics(p) for p in transfers]

    total_spend = sum(p["fee_million"] for p in players)
    total_current_value = sum(p["market_value_now"] for p in players)
    total_profit_loss = round(total_current_value - total_spend, 1)

    paid_signings = [p for p in players if p["fee_million"] > 0]
    avg_cost_per_90 = None
    if paid_signings:
        valid = [p["cost_per_90"] for p in paid_signings if p["cost_per_90"] is not None]
        avg_cost_per_90 = round(sum(valid) / len(valid), 2) if valid else None

    injured_count = sum(1 for p in players if p["injury_flag"])

    by_position = {}
    for group in ["GK", "DEF", "MID", "FWD"]:
        group_players = [p for p in players if p["position_group"] == group]
        by_position[group] = {
            "count": len(group_players),
            "total_spend": round(sum(p["fee_million"] for p in group_players), 1),
            "avg_minutes_util": round(
                sum(p["minutes_util"] for p in group_players) / len(group_players), 1
            ) if group_players else 0,
        }

    seasons = sorted(set(p["season"] for p in players))
    by_season = {}
    for s in seasons:
        sp = [p for p in players if p["season"] == s]
        by_season[s] = {
            "count": len(sp),
            "total_spend": round(sum(p["fee_million"] for p in sp), 1),
        }

    return {
        "total_spend_million": round(total_spend, 1),
        "total_current_value_million": round(total_current_value, 1),
        "total_profit_loss_million": total_profit_loss,
        "avg_cost_per_90_thousand": round(avg_cost_per_90 * 1000, 1) if avg_cost_per_90 else None,
        "injured_underutilised_count": injured_count,
        "signings_count": len(players),
        "by_position": by_position,
        "by_season": by_season,
    }


@app.get("/metrics/value-quadrants")
def get_value_quadrants():
    """
    For now I'm trying to classify players into four quadrants but its more complex than that:
    - Stars: high minutes, high performance
    - Wasted spend: high fee, low minutes
    - Bargains: low fee, high performance
    - Dead weight: low minutes, low performance
    """
    transfers = load_transfers()
    players = [compute_metrics(p) for p in transfers]

    paid = [p for p in players if p["fee_million"] > 0]
    if not paid:
        return {"quadrants": {}}

    avg_fee = sum(p["fee_million"] for p in paid) / len(paid)
    avg_util = sum(p["minutes_util"] for p in paid) / len(paid)

    for p in players:
        high_fee = p["fee_million"] > avg_fee
        high_util = p["minutes_util"] > avg_util

        if high_fee and high_util:
            p["quadrant"] = "star"
        elif high_fee and not high_util:
            p["quadrant"] = "wasted_spend"
        elif not high_fee and high_util:
            p["quadrant"] = "bargain"
        else:
            p["quadrant"] = "deadweight"

    return {
        "avg_fee_benchmark": round(avg_fee, 1),
        "avg_util_benchmark": round(avg_util, 1),
        "players": players,
    }


@app.get("/metrics/squad-gaps")
def get_squad_gaps():
    """Identify positional depth and age profile issues."""
    transfers = load_transfers()
    players = [compute_metrics(p) for p in transfers]
    active = [p for p in players if p["status"] in ("active", "loan")]

    depth = {}
    for group in ["GK", "DEF", "MID", "FWD"]:
        group_players = [p for p in active if p["position_group"] == group]
        ages = [p["age_at_signing"] + _seasons_active(p["season"]) for p in group_players]
        depth[group] = {
            "count": len(group_players),
            "avg_age": round(sum(ages) / len(ages), 1) if ages else 0,
            "under_23": sum(1 for a in ages if a < 23),
            "over_27": sum(1 for a in ages if a > 27),
            "players": [p["name"] for p in group_players],
        }

    return {"depth_by_position": depth}


@app.get("/seasons")
def get_seasons():
    transfers = load_transfers()
    seasons = sorted(set(p["season"] for p in transfers))
    return {"seasons": seasons}
