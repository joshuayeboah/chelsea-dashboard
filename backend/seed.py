import json
from pathlib import Path
from database import init_db, upsert_player, upsert_performance, insert_market_value

DATA_PATH = Path(__file__).parent / "transfers.json"


def seed():
    print("Initialising database...")
    init_db()

    with open(DATA_PATH) as f:
        players = json.load(f)

    print(f"Seeding {len(players)} players...")

    for p in players:
        # Insert the player
        player_id = upsert_player({
            "name": p["name"],
            "position": p["position"],
            "nationality": p["nationality"],
            "age_at_signing": p["age_at_signing"],
            "fee_million": p["fee_million"],
            "sale_fee_million": p.get("sale_fee_million"),
            "season": p["season"],
            "contract_years": p["contract_years"],
            "status": p["status"],
        })

        # Insert aggregated performance stats under their signing season
        upsert_performance(player_id, p["season"], {
            "minutes_played": p["minutes_played"],
            "goals": p["goals"],
            "assists": p["assists"],
            "xg": p["xg"],
            "xa": p["xa"],
            "progressive_carries": p["progressive_carries"],
            "progressive_passes": p["progressive_passes"],
        })

        # Insert current market value as first snapshot
        insert_market_value(player_id, p["market_value_now"])

        print(f"  ✓ {p['name']}")

    print("\nSeed complete. Database is ready.")


if __name__ == "__main__":
    seed()