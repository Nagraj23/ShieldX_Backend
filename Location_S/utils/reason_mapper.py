from typing import Dict

# ---- Central Reason Configuration ----
# This file is the SINGLE SOURCE OF TRUTH for location reasons

REASON_CONFIG: Dict[str, Dict] = {
    "SOS": {
        "is_emergency": True,
        "priority": "HIGH",
        "notify": True
    },
    "LOCATION_SHARE": {
        "is_emergency": False,
        "priority": "MEDIUM",
        "notify": True
    },
    "JOURNEY_START": {
        "is_emergency": False,
        "priority": "LOW",
        "notify": True
    },
    "JOURNEY_UPDATE": {
        "is_emergency": False,
        "priority": "LOW",
        "notify": False   # ❌ do NOT notify every update
    },
    "JOURNEY_END": {
        "is_emergency": False,
        "priority": "LOW",
        "notify": True
    }
}

def get_reason_config(reason: str) -> Dict:
    """
    Returns behavior config for a given reason.
    Falls back to safe defaults.
    """
    return REASON_CONFIG.get(
        reason,
        {
            "is_emergency": False,
            "priority": "LOW",
            "notify": False
        }
    )
