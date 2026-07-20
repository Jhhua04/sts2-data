import json
import os
import re
import parse_relic_info
import get_json
from config import PLAYER_ID, SAVE_FILE_PATH

# Folder path comes from config.py / STS2_SAVE_FOLDER env var, not hardcoded.
save_file_path = SAVE_FILE_PATH
test_file_path = os.path.join(SAVE_FILE_PATH, '1777443393.run') if SAVE_FILE_PATH else ''

# Separate dicts for singleplayer and multiplayer
cards = {}
mp_cards = {}

total_solo_runs = 0
total_mp_runs = 0

# --- Load cards.json ONCE at module load time ---
with open("cards.json") as f:
    _cards_json = get_json.get_json("cards.json", "cards", ["id", "name", "description", "color", "cost", "is_x_cost", "type", "rarity"])

_CARD_BY_ID = {r["id"]: r for r in _cards_json}
_SKIP_RARITIES = {"Basic", "Curse", "Quest"}
DESCRIPTION_REGEX = re.compile(r'\[.*?\]')

def get_card_info(card_name: str):
    card_info = _CARD_BY_ID[card_name.upper().replace(" ", "_")]
    cleaned_description = DESCRIPTION_REGEX.sub('', card_info["description"])
    if card_info["color"] == "event":
        card_info["color"] = "colorless"
    if card_info["is_x_cost"]:
        card_info["cost"] = "X"
    return (
        card_info["color"].title(),
        card_info["cost"],
        card_info["is_x_cost"],
        card_info["type"],
        card_info["rarity"],
        cleaned_description,
    )

# Cache clean_name results to avoid repeated dict lookups
_name_cache: dict[str, str | None] = {}

def clean_name(internal_id: str) -> str | None:
    """
    Safely turns 'CARD.TWIN_STRIKE' into 'Twin Strike'
    or 'RELIC.AKABEKO' into 'Akabeko'
    """
    if not internal_id:
        return None
    if internal_id in _name_cache:
        return _name_cache[internal_id]

    card = _CARD_BY_ID.get(internal_id.split('.')[-1])
    if card is None:
        _name_cache[internal_id] = None
        return None

    result = card["name"]
    _name_cache[internal_id] = result
    return result

def _ensure_card(card_id: str, card_dict: dict) -> "Card | None":
    """Return the Card for card_id, creating it if needed. Returns None if card should be skipped."""
    raw_id = card_id.split('.')[-1]
    card_data = _CARD_BY_ID.get(raw_id)
    if card_data is None or card_data["rarity"] in _SKIP_RARITIES:
        return None
    display_name = clean_name(card_id)
    if not display_name or display_name == "Grapple":
        return None
    if card_id not in card_dict:
        card_dict[card_id] = Card(card_id)
    return card_dict[card_id]


class Card:
    def __init__(self, name):
        self.name = clean_name(name)
        self.times_taken = 0
        self.times_offered = 0
        self.times_won = 0
        self.color, self.cost, self.is_x_cost, self.type, self.rarity, self.description = get_card_info(name.split('.')[-1])

    def get_data(self):
        pick_rate = (self.times_taken / self.times_offered * 100) if self.times_offered > 0 else 0
        win_rate = (self.times_won / self.times_taken * 100) if self.times_taken > 0 else 0
        return {
            'Card Name': self.name,
            'Card Class': self.color,
            'Color': self.color,
            'Cost': str(self.cost),
            'Is X Cost': self.is_x_cost,
            'Type': self.type,
            'Rarity': self.rarity,
            'Description': self.description,
            'Offered': self.times_offered,
            'Picked': self.times_taken,
            'Wins': self.times_won,
            'Pick Rate (%)': round(pick_rate, 2),
            'Win Rate (%)': round(win_rate, 2),
        }


def handle_relic_choices(point, relic_dict: dict):
    parse_relic_info.handle_relic_choices(point, relic_dict)

def handle_ancient_choices(point, card_dict: dict, relic_dict: dict):
    parse_relic_info.handle_ancient_relic_choices(point, relic_dict)

    player_stats = point.get('player_stats', [{}])
    card_choices = player_stats[0].get('card_choices')
    if card_choices:
        for card in card_choices:
            current_card_id = card.get("card").get("id")
            c = _ensure_card(current_card_id, card_dict)
            if c:
                c.times_offered += 1
                c.times_taken += 1

    card_gained = player_stats[0].get('cards_gained')
    if card_gained:
        for card in card_gained:
            current_card_id = card.get('id')
            c = _ensure_card(current_card_id, card_dict)
            if c:
                c.times_offered += 1
                c.times_taken += 1

    card_transformed = player_stats[0].get('cards_transformed')
    if card_transformed:
        for card in card_transformed:
            current_card_id = card.get('final_card').get('id')
            c = _ensure_card(current_card_id, card_dict)
            if c:
                c.times_offered += 1
                c.times_taken += 1
                if c.name == "Maul":
                    break


def handle_enemy_card_choices(point, card_dict: dict, relic_dict: dict):
    player_stats = point.get('player_stats', [{}])
    choices = player_stats[0].get('card_choices')
    if not choices:
        return
    for card in choices:
        current_card_id = card.get('card').get('id')
        c = _ensure_card(current_card_id, card_dict)
        if c:
            c.times_offered += 1
            if card.get('was_picked') == True:
                c.times_taken += 1
    if player_stats[0].get('relic_choices') is not None:
        handle_relic_choices(point, relic_dict)


def handle_shop_choices(point, card_dict: dict, relic_dict: dict):
    player_stats = point.get('player_stats', [{}])
    cards_taken = player_stats[0].get('cards_gained')
    if cards_taken:
        for card in cards_taken:
            current_card_id = card.get('id')
            c = _ensure_card(current_card_id, card_dict)
            if c:
                c.times_offered += 1
                c.times_taken += 1
    handle_relic_choices(point, relic_dict)


def handle_elite_choices(point, card_dict: dict, relic_dict: dict):
    handle_enemy_card_choices(point, card_dict, relic_dict)
    handle_relic_choices(point, relic_dict)


def handle_unknown_choices(point, card_dict: dict, relic_dict: dict):
    rooms = point.get('rooms', [{}])
    room_type = rooms[0].get('room_type')
    player_stats = point.get('player_stats', [{}])

    if room_type == 'monster':
        handle_enemy_card_choices(point, card_dict, relic_dict)
    elif room_type == 'shop':
        handle_shop_choices(point, card_dict, relic_dict)
    elif room_type == 'treasure':
        handle_relic_choices(point, relic_dict)
    elif room_type == 'event':
        if point.get('rooms')[0].get('model_id') == "EVENT.REFLECTIONS":
            return
        cards_taken = player_stats[0].get('cards_gained')
        if cards_taken:
            for card in cards_taken:
                current_card_id = card.get('id')
                c = _ensure_card(current_card_id, card_dict)
                if c:
                    c.times_offered += 1
                    c.times_taken += 1
        card_transformed = player_stats[0].get('cards_transformed')
        if card_transformed:
            for card in card_transformed:
                current_card_id = card.get('final_card').get('id')
                c = _ensure_card(current_card_id, card_dict)
                if c:
                    c.times_offered += 1
                    c.times_taken += 1
        if player_stats[0].get('relic_choices') is not None:
            handle_relic_choices(point, relic_dict)


def _read_file(file_path, card_dict: dict, relic_dict: dict, is_multiplayer: bool, player_id=PLAYER_ID):
    """
    Core file reading logic shared by both singleplayer and multiplayer.
    Callers pass in the appropriate card_dict, relic_dict and the expected is_multiplayer flag.
    """
    global total_solo_runs, total_mp_runs
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        map_data = data.get('map_point_history', [])
        if not map_data:
            return

        if data.get('was_abandoned') == True:
            return

        run_is_multiplayer = len(map_data[0][0].get('player_stats')) > 1
        if run_is_multiplayer != is_multiplayer:
            return

        if is_multiplayer:
            total_mp_runs += 1
        else:
            total_solo_runs += 1

        _handlers = {
            'ancient': lambda p: handle_ancient_choices(p, card_dict, relic_dict),
            'monster': lambda p: handle_enemy_card_choices(p, card_dict, relic_dict),
            'boss': lambda p: (handle_enemy_card_choices(p, card_dict, relic_dict), handle_relic_choices(p, relic_dict)),
            'shop': lambda p: handle_shop_choices(p, card_dict, relic_dict),
            'elite': lambda p: handle_elite_choices(p, card_dict, relic_dict),
            'treasure': lambda p: handle_relic_choices(p, relic_dict),
            'unknown': lambda p: handle_unknown_choices(p, card_dict, relic_dict),
        }

        for act in map_data:
            for point in act:
                if is_multiplayer:
                    my_stats = next(
                        (p for p in point.get('player_stats', []) if p.get('player_id') == int(player_id)),
                        None
                    )
                    if my_stats is None:
                        continue  # skip points where we can't find our player
                    point = {**point, 'player_stats': [my_stats]}

                handler = _handlers.get(point.get('map_point_type'))
                if handler:
                    handler(point)

        if data.get('win') == True:
            player_data = data.get('players', [{}])
            if is_multiplayer:
                for player in player_data:
                    if player.get('id') == PLAYER_ID:
                        player_data = [player]
                        break
            unique_in_deck = set()
            for c in player_data[0].get('deck', []):
                card_id = c.get('id')
                if card_id and card_id not in unique_in_deck:
                    unique_in_deck.add(card_id)
                    card_obj = _ensure_card(card_id, card_dict)
                    if card_obj:
                        card_obj.times_won += 1
            parse_relic_info.record_relic_wins(player_data, relic_dict, file_path, is_multiplayer)

    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        print(f"Error processing {os.path.basename(file_path)}: {e} on line {e.__traceback__.tb_lineno} in {os.path.basename(__file__)}")


def read_file_single_player(file_path):
    _read_file(file_path, cards, parse_relic_info.relics, is_multiplayer=False)


def read_file_multiplayer(file_path, player_id):
    is_multiplayer = True
    _read_file(file_path, mp_cards, parse_relic_info.mp_relics, is_multiplayer, player_id)


def read_all_files_in_folder(folder_path, player_id):
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.run'):
            full_path = os.path.join(folder_path, file_name)
            read_file_single_player(full_path)
            read_file_multiplayer(full_path, player_id)


if __name__ == "__main__":
    print("------------------")
    # read_all_files_in_folder(save_file_path)
    read_file_multiplayer(test_file_path)
    print(parse_relic_info.mp_relics["RELIC.LASTING_CANDY"].get_data())