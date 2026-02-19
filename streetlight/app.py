import streamlit as st
import pandas as pd

from src.features import build_player_features, role_fit_scores
from src.press import press_intensity_heatmap, press_triggers, press_success_proxy
from src.tactics import recommend_patterns

st.set_page_config(page_title="Soccer Tactical Intelligence", layout="wide")

@st.cache_data
def load_events():
    return pd.read_parquet("data/processed/events.parquet")

@st.cache_data
def load_player_feats(events):
    return build_player_features(events)

events = load_events()
pfeats = load_player_feats(events)

st.title("⚽ Soccer Tactical Intelligence (EPL) — Portfolio App")

teams = sorted([t for t in events["team"].dropna().unique()])

left, right = st.columns([1, 1])

with left:
    st.subheader("Your Team / XI")
    team = st.selectbox("Team", teams)
    players = sorted([p for p in events[events["team"] == team]["player"].dropna().unique()])
    xi = st.multiselect("Select XI players (try 11)", players, default=players[:11])

with right:
    st.subheader("Opponent (optional)")
    opp = st.selectbox("Opponent team", ["(none)"] + teams)

if st.button("Run Tactical Intelligence"):
    st.divider()

    # --- Player intelligence table
    st.subheader("Player Intelligence Profiles (Role Fit + Axes)")
    team_pf = pfeats[pfeats["team"] == team].copy()
    team_pf = team_pf[team_pf["player"].isin(xi)].copy()

    if len(team_pf) == 0:
        st.error("No player feature rows found for selected XI.")
        st.stop()

    # compute role fits
    role_rows = []
    for _, r in team_pf.iterrows():
        scores = role_fit_scores(r)
        best_role = max(scores, key=scores.get)
        role_rows.append({
            "player": r["player"],
            "ball_progression": round(float(r["ball_progression"]), 2),
            "chance_creation": round(float(r["chance_creation"]), 2),
            "def_intensity": round(float(r["def_intensity"]), 2),
            "under_pressure_rate": round(float(r["under_pressure_rate"]), 3),
            "best_role": best_role,
            "best_role_score": round(float(scores[best_role]), 2),
        })

    st.dataframe(pd.DataFrame(role_rows).sort_values("best_role_score", ascending=False), use_container_width=True)

    # --- Team summary for tactical planner
    pr = float((1.0 - team_pf["under_pressure_rate"]).mean())
    team_summary = {
        "ball_progression": float(team_pf["ball_progression"].mean()),
        "chance_creation": float(team_pf["chance_creation"].mean()),
        "def_intensity": float(team_pf["def_intensity"].mean()),
        "press_resistance": pr
    }

    a, b, c, d = st.columns(4)
    a.metric("Ball Progression", f"{team_summary['ball_progression']:.2f}")
    b.metric("Chance Creation", f"{team_summary['chance_creation']:.2f}")
    c.metric("Def Intensity", f"{team_summary['def_intensity']:.2f}")
    d.metric("Press Resistance", f"{team_summary['press_resistance']:.2f}")

    # --- Press module
    st.subheader("Press Detection (Event-based Proxy)")
    heat, high_share, total_press = press_intensity_heatmap(events, team)
    st.write(f"Press events counted: **{total_press}** | High-press share (x≥60): **{high_share:.1%}**")
    st.dataframe(heat, use_container_width=True)

    st.subheader("Press Triggers (most common events immediately before your press actions)")
    trig = press_triggers(events, team)
    st.dataframe(trig.head(10), use_container_width=True)

    st.subheader("Press Success Proxy (recover soon after press)")
    succ = press_success_proxy(events, team, window_events=5)
    st.write(succ)

    # --- Tactical recommendations
    st.subheader("Tactical Engineering: Top Plans for Your XI")
    recs = recommend_patterns(team_summary)
    for r in recs:
        st.markdown(f"### {r['name']}  — score {r['score']:.2f}")
        st.write(r["why"])
