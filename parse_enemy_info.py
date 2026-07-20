import json
import os
from config import PLAYER_ID, SAVE_FILE_PATH
import get_json

save_file_path = SAVE_FILE_PATH
test_file_path = os.path.join(SAVE_FILE_PATH, '1783906905.run') if SAVE_FILE_PATH else ''

encounter_dict = {}
monster_dict = {}
encounter_to_monster = {}
encounter_category = {}   # enc_id -> "boss" | "elite" | "normal" | "weak"
monster_category = {}     # mon_id -> "boss" | "elite" | "normal" | "weak"
encounter_killed = {}

encounter_dict_mp = {}
monster_dict_mp = {}
encounter_killed_mp = {}


with open("cards.json") as f:
    _monster_json = get_json.get_json("monsters.json", "monsters", ["id", "name", "type", "image_url"])
_MONSTER_BY_ID = {r["id"]: r for r in _monster_json}

def get_averages(dict):
    for key in dict:
        avg = sum(dict[key]) / len(dict[key])
        print(f"{key}: {round(avg)}") 

def process_encounter(point, encounter_dict, monster_dict, is_multiplayer, category="normal", player_id=PLAYER_ID):
    rooms = point.get('rooms', [{}])
    encounter_type = rooms[0].get('model_id')
    monsters = rooms[0].get("monster_ids")
    if monsters[0] == "MONSTER.DOOR":
        monsters[0] = "MONSTER.DOORMAKER"
    if is_multiplayer:
        my_stats = next(
                        (p for p in point.get('player_stats', []) if p.get('player_id') == int(player_id)),
                        None
                    )
        point = {**point, 'player_stats': [my_stats]}
    damage_taken = point.get('player_stats')[0].get("damage_taken")
    
    encounter_type = encounter_type.split('.')[-1]
    if encounter_type not in encounter_to_monster:
        encounter_to_monster[encounter_type] = []
        for monster in monsters:
            monster = monster.split('.')[-1]
            if monster == "OSTY":
                continue
            encounter_to_monster[encounter_type].append(monster)
    if encounter_type not in encounter_dict:
        encounter_dict[encounter_type] = []
    encounter_dict[encounter_type].append(damage_taken)
    encounter_category[encounter_type] = category

    dupe = set()
    for monster in monsters:
        monster = monster.split('.')[-1]
        if monster not in monster_dict:
            monster_dict[monster] = []
        if monster in dupe:
            continue
        monster_dict[monster].append(damage_taken)
        dupe.add(monster)
        monster_category[monster] = category

def process_unknown_encounter(point, encounter_dict, monster_dict, is_multiplayer: bool, player_id=PLAYER_ID):
    rooms = point.get('rooms', [{}])
    if rooms[0].get('room_type') == "monster":
        process_encounter(point, encounter_dict, monster_dict, is_multiplayer, player_id)

def read_file(file_path, encounter_dict, monster_dict, is_multiplayer: bool, player_id=PLAYER_ID):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        map_data = data.get('map_point_history', [])
        if not map_data:
            return
            
        # Validation for abandoned or multiplayer
        if data.get('was_abandoned') == True:
            return
        
        run_is_multiplayer = len(map_data[0][0].get('player_stats')) > 1
        if run_is_multiplayer != is_multiplayer:
            return

        killed_by = data.get('killed_by_encounter', "")
        if killed_by and killed_by != "NONE.NONE" and is_multiplayer:
            encounter_killed_mp[killed_by.split('.')[-1]] = encounter_killed.get(killed_by.split('.')[-1], 0) + 1
        elif killed_by and killed_by != "NONE.NONE" and is_multiplayer == False:
            encounter_killed[killed_by.split('.')[-1]] = encounter_killed.get(killed_by.split('.')[-1], 0) + 1
        
        for act in map_data:
            for point in act:
                if point.get("map_point_type") in ["monster", "elite", "boss"]:
                    cat = point.get("map_point_type")  # "monster" -> normal, "elite", "boss"
                    if cat == "monster":
                        cat = "normal"
                    #print(cat)
                    process_encounter(point, encounter_dict, monster_dict, is_multiplayer, cat, player_id)
                elif point.get("map_point_type") == "unknown":
                    process_unknown_encounter(point, encounter_dict, monster_dict, is_multiplayer)
        
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        print(f"Error processing {os.path.basename(file_path)}: {e} on line {e.__traceback__.tb_lineno} in {os.path.basename(__file__)}")

def read_file_single_player(file_path):
    read_file(file_path, encounter_dict, monster_dict, is_multiplayer=False)

def read_file_multiplayer(file_path, player_id):
    is_multiplayer = True
    read_file(file_path, encounter_dict_mp, monster_dict_mp,is_multiplayer, player_id)

def read_all_files_in_folder(folder_path, player_id):
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.run'):
            file_path = os.path.join(folder_path, file_name)
            read_file_single_player(file_path)
            read_file_multiplayer(file_path, player_id)

if __name__ == "__main__":
    print("HI")