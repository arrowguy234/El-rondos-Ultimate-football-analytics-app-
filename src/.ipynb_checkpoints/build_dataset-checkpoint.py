import pandas as pd
from pathlib import Path
from ingest_statsbomb import list_competitions, list_matches, read_events

def flatten_location(x):
    if isinstance(x, list) and len(x) >= 2:
        return x[0], x[1]
    return None, None

def build_events_table(open_data_repo, competition_id, season_id, out_path):
    matches = list_matches(open_data_repo, competition_id, season_id)

    rows = []
    for m in matches:
        match_id = m["match_id"]
        home = m["home_team"]["home_team_name"]
        away = m["away_team"]["away_team_name"]

        events = read_events(open_data_repo, match_id)
        for e in events:
            loc_x, loc_y = flatten_location(e.get("location"))
            typ = (e.get("type") or {}).get("name")

            team = (e.get("team") or {}).get("name")
            player = (e.get("player") or {}).get("name")

            pass_end_x, pass_end_y = None, None
            if "pass" in e and isinstance(e["pass"], dict):
                pass_end_x, pass_end_y = flatten_location(e["pass"].get("end_location"))

            shot_xg = None
            if "shot" in e and isinstance(e["shot"], dict):
                shot_xg = e["shot"].get("statsbomb_xg")

            rows.append({
                "match_id": match_id,
                "home_team": home,
                "away_team": away,
                "team": team,
                "player": player,
                "period": e.get("period"),
                "minute": e.get("minute"),
                "second": e.get("second"),
                "type": typ,
                "possession": e.get("possession"),
                "play_pattern": (e.get("play_pattern") or {}).get("name"),
                "loc_x": loc_x,
                "loc_y": loc_y,
                "pass_end_x": pass_end_x,
                "pass_end_y": pass_end_y,
                "under_pressure": bool(e.get("under_pressure", False)),
                "shot_xg": shot_xg
            })

    df = pd.DataFrame(rows)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    return df

if __name__ == "__main__":
    # Example: pick a comp/season after inspecting competitions.json
    repo = "data/raw/statsbomb-open-data"
    df = build_events_table(repo, competition_id=2, season_id=44, out_path="data/processed/events.parquet")
    print(df.head())
    print("Saved:", len(df), "rows")
