from typing import Literal, Dict, Any
import json

Label = Literal["Y", "N"]

def predict_quit_next_5d(
    login_frequency_per_week: int,
    avg_daily_playtime_minutes: int,
    levels_gained_last_7d: int,
    character_class: str,
) -> Dict[str, Any]:
    """
    Predict if a player will quit the game in the next 5 days.

    Inputs:
      - login_frequency_per_week: 0–14 (int)
      - avg_daily_playtime_minutes: 0–600 (int)
      - levels_gained_last_7d: 0–100 (int)
      - character_class: e.g., "Warrior", "Mage", "Rogue", "Healer", "Necromancer", etc.

    Output:
      {
        "quit_next_5d": "Y" | "N",
        "probability": float in [0, 1],
        "factors": [list of short strings]
      }
    """
    # Basic validation and clamping
    lf = max(0, min(int(login_frequency_per_week), 14))
    pt = max(0, min(int(avg_daily_playtime_minutes), 600))
    lv = max(0, min(int(levels_gained_last_7d), 100))
    cls = str(character_class).strip() or "Unknown"

    # Normalize engagement to risk-like sub-scores (1=risky, 0=healthy)
    login_risk = 1.0 - (lf / 14.0)               # 0 logins -> 1.0 risk, 14 -> 0.0
    playtime_cap = 240.0                          # cap diminishing returns at 4h/day
    playtime_risk = 1.0 - min(pt, playtime_cap) / playtime_cap
    level_cap = 6.0                               # 6+ levels in 7d considered healthy
    level_risk = 1.0 - min(lv, level_cap) / level_cap

    # Weighted combination
    risk = 0.45 * login_risk + 0.35 * playtime_risk + 0.20 * level_risk

    # Small class interaction (secondary signal)
    class_adjustment = 0.0
    low_engagement = (lf <= 2) or (lv == 0) or (pt <= 15)
    high_engagement = (lf >= 6) and (lv >= 2) and (pt >= 45)

    if cls in {"Rogue", "Necromancer"} and low_engagement:
        class_adjustment += 0.05
    if cls in {"Warrior", "Healer"} and high_engagement:
        class_adjustment -= 0.05

    prob = max(0.0, min(1.0, risk + class_adjustment))
    label: Label = "Y" if prob >= 0.5 else "N"

    # Factor generation (2–4 concise reasons grounded in inputs)
    risk_factors = []
    if lf <= 2:
        risk_factors.append("Very low logins")
    elif lf <= 4:
        risk_factors.append("Below-average logins")

    if pt <= 15:
        risk_factors.append("Very low playtime")
    elif pt <= 45:
        risk_factors.append("Low playtime")

    if lv == 0:
        risk_factors.append("No progression")
    elif lv <= 1:
        risk_factors.append("Minimal progression")

    if cls in {"Rogue", "Necromancer"} and low_engagement:
        risk_factors.append(f"Class {cls} with low engagement")

    engagement_factors = []
    if lf >= 6:
        engagement_factors.append("High logins")
    elif lf == 5:
        engagement_factors.append("Moderate logins")

    if pt >= 120:
        engagement_factors.append("Very high playtime")
    elif pt >= 45:
        engagement_factors.append("Moderate playtime")

    if lv >= 4:
        engagement_factors.append("Strong progression")
    elif lv >= 2:
        engagement_factors.append("Some progression")

    if cls in {"Warrior", "Healer"} and high_engagement:
        engagement_factors.append(f"Class {cls} with strong engagement")

    factors = (risk_factors if label == "Y" else engagement_factors)[:4]

    return {
        "quit_next_5d": label,
        "probability": round(float(prob), 2),
        "factors": factors if factors else (
            ["Edge case metrics"] if label == "Y" else ["Balanced engagement"]
        ),
    }


if __name__ == "__main__":
    # Example usage
    example_inputs = [
        dict(login_frequency_per_week=0, avg_daily_playtime_minutes=0, levels_gained_last_7d=0, character_class="Warrior"),
        dict(login_frequency_per_week=7, avg_daily_playtime_minutes=90, levels_gained_last_7d=4, character_class="Warrior"),
        dict(login_frequency_per_week=2, avg_daily_playtime_minutes=40, levels_gained_last_7d=2, character_class="Necromancer"),
    ]
    for inp in example_inputs:
        print(json.dumps(predict_quit_next_5d(**inp)))