import pandas as pd

PRESS_EVENTS = {"Pressure", "Duel", "Interception", "Ball Recovery"}

def press_intensity_heatmap(events_df, team, grid_x=6, grid_y=4):
    d = events_df[(events_df["team"] == team) & (events_df["type"].isin(PRESS_EVENTS))].copy()
    d = d[d["loc_x"].notna() & d["loc_y"].notna()]

    # high press proxy: actions in opponent half
    d["is_high"] = d["loc_x"] >= 60

    d["zx"] = pd.cut(d["loc_x"], bins=grid_x, labels=False, include_lowest=True)
    d["zy"] = pd.cut(d["loc_y"], bins=grid_y, labels=False, include_lowest=True)

    heat = d.groupby(["zx", "zy"]).size().reset_index(name="count")
    high_share = float(d["is_high"].mean()) if len(d) else 0.0
    total = int(len(d))

    return heat, high_share, total

def press_triggers(events_df, team):
    # What event type happens right before this team's press events?
    d = events_df.sort_values(["match_id", "period", "minute", "second"]).copy()
    d["is_press"] = (d["team"] == team) & d["type"].isin(PRESS_EVENTS)

    triggers = []
    for mid, mdf in d.groupby("match_id"):
        mdf = mdf.reset_index(drop=True)
        press_idx = mdf.index[mdf["is_press"]].tolist()
        for i in press_idx:
            if i == 0:
                continue
            prev = mdf.loc[i - 1]
            triggers.append(prev["type"])

    if not triggers:
        return pd.DataFrame(columns=["prev_type", "count"])

    out = pd.Series(triggers).value_counts().reset_index()
    out.columns = ["prev_type", "count"]
    return out

def press_success_proxy(events_df, team, window_events=5):
    """
    Proxy success: after a press event, do we get a Ball Recovery / Interception soon?
    Using event-window instead of seconds keeps it simple and robust.
    """
    d = events_df.sort_values(["match_id", "period", "minute", "second"]).copy()
    d["is_team_press"] = (d["team"] == team) & d["type"].isin(PRESS_EVENTS)

    recover_types = {"Ball Recovery", "Interception"}
    successes = 0
    total = 0

    for mid, mdf in d.groupby("match_id"):
        mdf = mdf.reset_index(drop=True)
        idxs = mdf.index[mdf["is_team_press"]].tolist()
        for i in idxs:
            total += 1
            j = min(i + window_events, len(mdf) - 1)
            window = mdf.loc[i+1:j]
            if any((window["team"] == team) & (window["type"].isin(recover_types))):
                successes += 1

    rate = (successes / total) if total else 0.0
    return {"pre
