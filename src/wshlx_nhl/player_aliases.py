from __future__ import annotations

PLAYER_NAME_ALIASES = {
    "Mitchell Marner": "Mitch Marner",
    "Alexis Lafreniere": "Alexis Lafrenière",
    "Joe Veleno": "Joseph Veleno",
    "Michael Brandsegg-Nygard": "Michael Brandsegg-Nygård",
}


def historical_player_name(name: str) -> str:
    """Normalize sportsbook/display names to the historical-data canonical name."""
    return PLAYER_NAME_ALIASES.get(str(name).strip(), str(name).strip())
