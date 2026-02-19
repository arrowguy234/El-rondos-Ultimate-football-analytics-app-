def recommend_patterns(team_summary, opp_summary=None):
    """
    team_summary: dict with keys like ball_progression, chance_creation, def_intensity, press_resistance
    opp_summary: optional dict (later), we can still do v1 without it
    """
    bp = team_summary["ball_progression"]
    cc = team_summary["chance_creation"]
    di = team_summary["def_intensity"]
    pr = team_summary["press_resistance"]

    patterns = []

    # Pattern 1: bait press -> vertical
    score1 = 0.45 * pr + 0.35 * bp + 0.20 * cc
    patterns.append({
        "name": "Bait press → vertical into striker + layoff (3rd man)",
        "why": "Punishes aggressive pressing: invite pressure, then break lines quickly.",
        "score": score1
    })

    # Pattern 2: overload half-space
    score2 = 0.50 * bp + 0.40 * cc + 0.10 * pr
    patterns.append({
        "name": "Half-space overload + third-man run",
        "why": "Creates a free man between lines and breaks compact blocks.",
        "score": score2
    })

    # Pattern 3: counterpress traps
    score3 = 0.60 * di + 0.20 * pr + 0.20 * bp
    patterns.append({
        "name": "Counterpress trap after loss (5-second rule)",
        "why": "Win the ball high and attack before the opponent is set.",
        "score": score3
    })

    # Pattern 4: switch play
    score4 = 0.60 * bp + 0.20 * pr + 0.20 * cc
    patterns.append({
        "name": "Fast switch to weak side",
        "why": "Stretches defensive compactness and creates 1v1 wide.",
        "score": score4
    })

    patterns = so
