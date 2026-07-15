import json
import re
import get_json

relics = {}
mp_relics = {}

# --- Load relics.json ONCE at module load time ---
# --- Load cards.json ONCE at module load time ---
_relics_json = get_json.get_json("relics.json", "relics")

_RELIC_BY_ID = {r["id"]: r for r in _relics_json}

_SEAGLASS_IDS = {"RELIC.SILENT", "RELIC.NECROBINDER", "RELIC.IRONCLAD", "RELIC.REGENT", "RELIC.DEFECT"}

# Cache cleaned descriptions to avoid repeated regex on the same relic
_description_cache: dict[str, str] = {}
DESCRIPTION_REGEX = re.compile(r'\[.*?\]')

def get_relic_descriptions(relic_name: str) -> str:
    if relic_name in _description_cache:
        return _description_cache[relic_name]
    description = _RELIC_BY_ID[relic_name]["description"]
    cleaned = DESCRIPTION_REGEX.sub('', description)
    _description_cache[relic_name] = cleaned
    return cleaned


class Relic:
    def __init__(self, name):
        self.name = name
        self.times_taken = 0
        self.times_won = 0
        self.description = get_relic_descriptions(name.upper().replace(" ", "_")) if name != "Seaglass" else "SEA_GLASS"

    def get_data(self):
        win_rate = (self.times_won / self.times_taken * 100) if self.times_taken > 0 else 0
        return {
            'Relic Name': self.name,
            'Taken': self.times_taken,
            'Wins': self.times_won,
            'Win Rate (%)': round(win_rate, 2),
            'Description': self.description,
        }


def _ensure_relic(relic_id: str, relic_dict: dict) -> Relic:
    """Return the Relic for relic_id, creating it if needed."""
    if relic_id not in relic_dict:
        relic_dict[relic_id] = Relic(_clean_name(relic_id))
    return relic_dict[relic_id]


def handle_relic_choices(point, relic_dict: dict):
    player_stats = point.get('player_stats', [{}])
    relic_choices = player_stats[0].get('relic_choices')
    if relic_choices:
        for relic in relic_choices:
            current_relic_id = relic.get('choice')
            r = _ensure_relic(current_relic_id, relic_dict)
            if relic.get('was_picked') == True:
                r.times_taken += 1


def handle_ancient_relic_choices(point, relic_dict: dict):
    """Handles only the relic portion of ancient node choices."""
    player_stats = point.get('player_stats', [{}])
    choices = player_stats[0].get('ancient_choice', [])
    for relic in choices:
        current_relic_id = "RELIC." + relic.get('TextKey')
        if current_relic_id in _SEAGLASS_IDS:
            current_relic_id = "RELIC.SEA_GLASS"
        if relic.get('was_chosen') and current_relic_id == "RELIC.TOUCH_OF_OROBAS":
            current_relic_id = player_stats[0].get('relic_choices')[1].get('choice')
        r = _ensure_relic(current_relic_id, relic_dict)
        if relic.get('was_chosen') == True:
            r.times_taken += 1


def record_relic_wins(player_data, relic_dict: dict, file_path, is_mp):
    """Mark every relic the player held at run end as a win."""
    for r in player_data[0].get('relics', []):
        relic_id = r.get('id')
        if relic_id:
            _ensure_relic(relic_id, relic_dict).times_won += 1


def _clean_name(internal_id: str) -> str:
    """
    Turns 'RELIC.AKABEKO' into 'Akabeko'.
    Mirrors the clean_name logic in parse_card_info for relic IDs.
    """
    if not internal_id:
        return "Unknown"
    return internal_id.split('.')[-1].replace("_", " ").title()