import json
from pathlib import Path

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_competitions(root_dir):
    root = Path(root_dir)
    comps = read_json(root / "data" / "competitions.json")
    return comps

def list_matches(root_dir, competition_id, season_id):
    root = Path(root_dir)
    match_path = root / "data" / "matches" / str(competition_id) / f"{season_id}.json"
    return read_json(match_path)

def read_events(root_dir, match_id):
    root = Path(root_dir)
    ev_path = root / "data" / "events" / f"{match_id}.json"
    return read_json(ev_path)
