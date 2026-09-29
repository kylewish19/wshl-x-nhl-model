from __future__ import annotations

TEAM_NAME_TO_ABBREV = {
    "Florida Panthers": "FLA",
    "Carolina Hurricanes": "CAR",
    "Montreal Canadiens": "MTL",
    "Toronto Maple Leafs": "TOR",
    "New York Rangers": "NYR",
    "Boston Bruins": "BOS",
    "Vancouver Canucks": "VAN",
    "Edmonton Oilers": "EDM",
    "Chicago Blackhawks": "CHI",
    "Vegas Golden Knights": "VGK",
}


def team_abbrev(name_or_abbrev: str) -> str:
    value = str(name_or_abbrev).strip()
    if value in TEAM_NAME_TO_ABBREV.values():
        return value
    if value not in TEAM_NAME_TO_ABBREV:
        raise KeyError(f"Unknown NHL team name: {value}")
    return TEAM_NAME_TO_ABBREV[value]
