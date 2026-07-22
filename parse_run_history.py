import json
import os
from parse_card_info import clean_name
from config import PLAYER_ID, SAVE_FILE_PATH

test_file_path = os.path.join(SAVE_FILE_PATH, '1777443393.run') if SAVE_FILE_PATH else ''
# Each entry: dict with keys run_id, is_multiplayer, win, character, ascension, deck_size, floor, timestamp, killed_by
solo_runs = []
mp_runs = []


# ── Helpers ──────────────────────────────────────────────────────────────────

_CLASS_MAP = {
    "IRONCLAD": "Ironclad",
    "SILENT": "Silent",
    "DEFECT": "Defect",
    "WATCHER": "Watcher",
    "REGENT": "Regent",
    "NECROBINDER": "Necrobinder",
}

def _clean_class(raw: str) -> str:
    """Turn 'CHARACTER.REGENT' or 'REGENT' into 'Regent'."""
    key = raw.split(".")[-1].upper()
    return _CLASS_MAP.get(key, raw.split(".")[-1].title())


def _deck_size(player_entry: dict) -> int:
    return len(player_entry.get("deck", []))


def _floor_reached(map_data: list) -> int:
    """Count total map points visited as a proxy for floor reached."""
    total = 0
    for act in map_data:
        total += len(act)
    return total


def _killed_by(raw: str) -> str:
    if not raw or raw == "NONE.NONE":
        return ""
    return raw.split(".")[-1].replace("_", " ").title()

def _get_deck(player_entry: dict) -> list:
    full_deck = []
    for item in player_entry.get("deck", []):
        name = clean_name(item.get('id', ''))
        if name and "current_upgrade_level" in item:
            name += "+"
        full_deck.append(name)
    return full_deck

# ── File reader ───────────────────────────────────────────────────────────────

def read_file(file_path: str, player_id=PLAYER_ID):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        print(f"Run history: error reading {os.path.basename(file_path)}: {e}")
        return

    if data.get("was_abandoned"):
        return

    map_data = data.get("map_point_history", [])
    if not map_data:
        return

    is_multiplayer = len(map_data[0][0].get("player_stats", [])) > 1

    win = data.get("win") == True
    floor = _floor_reached(map_data)
    killed = _killed_by(data.get("killed_by_encounter", ""))
    asc = data.get("ascension", 0)
    run_id = os.path.splitext(os.path.basename(file_path))[0]

    # Derive timestamp from filename (STS2 saves are Unix-timestamp named)
    try:
        ts = int(run_id)
    except ValueError:
        ts = int(os.path.getmtime(file_path))

    players = data.get("players", [{}])

    if is_multiplayer:
        my_player = next(
            (p for p in players if p.get("id") == int(player_id)), None
        )
        if my_player is None:
            return
        char = _clean_class(my_player.get("character", ""))
        ds = _deck_size(my_player)
        deck = _get_deck(my_player)
        mp_runs.append({
            "run_id": run_id,
            "is_multiplayer": True,
            "win": win,
            "character": char,
            "ascension": asc,
            "deck_size": ds,
            "deck": deck,
            "floor": floor,
            "timestamp": ts,
            "killed_by": killed,
        })
    else:
        player = players[0] if players else {}
        char = _clean_class(player.get("character", ""))
        ds = _deck_size(player)
        deck = _get_deck(player)
        solo_runs.append({
            "run_id": run_id,
            "is_multiplayer": False,
            "win": win,
            "character": char,
            "ascension": asc,
            "deck_size": ds,
            "deck": deck,
            "floor": floor,
            "timestamp": ts,
            "killed_by": killed,
        })


def read_all_files_in_folder(folder_path: str, player_id):
    if not os.path.exists(folder_path):
        print(f"Run history: folder not found: {folder_path}")
        return
    for filename in os.listdir(folder_path):
        if filename.endswith(".run"):
            read_file(os.path.join(folder_path, filename), player_id)
    # Sort newest first
    solo_runs.sort(key=lambda r: r["timestamp"], reverse=True)
    mp_runs.sort(key=lambda r: r["timestamp"], reverse=True)


if __name__ == "__main__":
    read_file(test_file_path)
    print(mp_runs)