import pandas as pd
import numpy as np

def _is_pass(df):
    return df["type"].eq("Pass") & df["loc_x"].notna() & df["pass_end_x"].notna()

def _is_carry(df):
    return df["type"].eq("Carry") & df["loc_x"].notna()

def _is_shot(df):
    return df["type"].eq("Shot")

def _is_def_action(df):
    defensive = {
        "Pressure", "Duel", "Interception", "Ball Recovery",
        "Clearance", "Block", "Foul Committed"
    }
    return df["type"].isin(defensive)

def add_engineered_flags(df):
    df = df.copy()
    p = _is_pass(df)
    df["pass_len_x"] = np.nan
    df.loc[p, "pass_len_x"] = df.loc[p, "pass_end_x"] - df.loc[p, "loc_x"]

    # progressive pass (simple but effective for portfolio)
    df["prog_pass"] = False
    df.loc[p, "prog_pass"] = df.loc[p, "pass_len_x"] >= 15

    # final third entry by pass endpoint
    df["final_third_entry"] = False
    df.loc[p, "final_third_entry"] = (df.loc[p, "pass_end_x"] >= 80) & (df.loc[p, "loc_x"] < 80)

    # box entry pass
    df["box_entry_pass"] = False
    df.loc[p, "box_entry_pass"] = (df.loc[p, "pass_end_x"] >= 102) & (df.loc[p, "pass_end_y"].between(18, 62, inclusive="both"))

    df["is_pass"] = df["type"].eq("Pass")
    df["is_carry"] = df["type"].eq("Carry")
    df["is_shot"] = df["type"].eq("Shot")
    df["is_def"] = _is_def_action(df)

    return df

def build_player_features(events_df):
    df = add_engineered_flags(events_df)

    g = df.groupby(["team", "player"], dropna=True)

    feats = pd.DataFrame({
        "events": g.size(),
        "passes": g["is_pass"].sum(),
        "carries": g["is_carry"].sum(),
        "shots": g["is_shot"].sum(),
        "def_actions": g["is_def"].sum(),
        "prog_passes": g["prog_pass"].sum(),
        "final_third_entries": g["final_third_entry"].sum(),
        "box_entry_passes": g["box_entry_pass"].sum(),
        "under_pressure_rate": g["under_pressure"].mean(),
        "xg_sum": g["shot_xg"].sum(min_count=1)
    }).fillna(0.0).reset_index()

    # Normalize to “per 100 events” (stable without minutes played)
    feats["prog_pass_per_100"] = feats["prog_passes"] / (feats["events"] / 100.0)
    feats["def_actions_per_100"] = feats["def_actions"] / (feats["events"] / 100.0)
    feats["shots_per_100"] = feats["shots"] / (feats["events"] / 100.0)
    feats["box_entry_pass_per_100"] = feats["box_entry_passes"] / (feats["events"] / 100.0)
    feats["final_third_entries_per_100"] = feats["final_third_entries"] / (feats["events"] / 100.0)

    # Simple composite “intelligence” axes (interpretable for recruiters)
    feats["ball_progression"] = (
        0.6 * feats["prog_pass_per_100"] +
        0.4 * feats["final_third_entries_per_100"]
    )

    feats["chance_creation"] = (
        0.7 * feats["box_entry_pass_per_100"] +
        0.3 * feats["shots_per_100"]
    )

    feats["def_intensity"] = feats["def_actions_per_100"]

    return feats

def role_fit_scores(player_row):
    # Interpretable role scoring: perfect for portfolio narrative
    bp = float(player_row["ball_progression"])
    cc = float(player_row["chance_creation"])
    di = float(player_row["def_intensity"])
    up = float(player_row["under_pressure_rate"])

    # higher is better; under_pressure lower is better for press-resistance proxy
    press_resistance = max(0.0, 1.0 - up)

    return {
        "Deep Playmaker": 0.55 * bp + 0.25 * press_resistance + 0.20 * cc,
        "Box-to-Box 8": 0.35 * bp + 0.25 * cc + 0.40 * di,
        "Creative 10": 0.25 * bp + 0.60 * cc + 0.15 * press_resistance,
        "Pressing Forward": 0.20 * cc + 0.55 * di + 0.25 * shots_per_100_safe(player_row),
        "Ball-Winning Mid": 0.20 * bp + 0.10 * cc + 0.70 * di,
        "Wide Creator": 0.20 * bp + 0.70 * cc + 0.10 * press_resistance
    }

def shots_per_100_safe(r):
    try:
        return float(r["shots_per_100"])
    except Exception:
        return 0.0
