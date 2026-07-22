import json
import os
import streamlit as st
import parse_card_info
import parse_enemy_info
import parse_run_history
import parse_relic_info


def detect_player_ids(folder_path: str) -> set:
    all_player_ids = set()
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return all_player_ids

    for file_name in os.listdir(folder_path):
        if not file_name.endswith(".run"):
            continue
        file_path = os.path.join(folder_path, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            players = data.get("players", [{}])
            for p in players:
                pid = p.get("id")
                if pid is not None:
                    all_player_ids.add(pid)
        except Exception as e:
            print(
                f"Error processing {os.path.basename(file_path)}: {e} "
                f"on line {e.__traceback__.tb_lineno} in {os.path.basename(__file__)}"
            )
    return all_player_ids


@st.cache_data
def load_all_run_data(folder_path, player_id):
    parse_card_info.cards = {}
    parse_card_info.mp_cards = {}
    parse_relic_info.relics = {}
    parse_relic_info.mp_relics = {}
    parse_card_info.total_solo_runs = 0
    parse_card_info.total_mp_runs = 0

    parse_enemy_info.encounter_dict = {}
    parse_enemy_info.monster_dict = {}
    parse_enemy_info.encounter_to_monster = {}
    parse_enemy_info.encounter_dict_mp = {}
    parse_enemy_info.monster_dict_mp = {}
    parse_enemy_info.encounter_killed_mp = {}
    parse_enemy_info.encounter_category = {}
    parse_enemy_info.monster_category = {}
    parse_enemy_info.encounter_killed = {}

    parse_run_history.solo_runs.clear()
    parse_run_history.mp_runs.clear()

    parse_card_info.read_all_files_in_folder(folder_path, player_id)
    parse_enemy_info.read_all_files_in_folder(folder_path, player_id)
    parse_run_history.read_all_files_in_folder(folder_path, player_id)
    
    return (
        dict(parse_card_info.cards),
        dict(parse_card_info.mp_cards),
        dict(parse_relic_info.relics),
        dict(parse_relic_info.mp_relics),
        parse_card_info.total_solo_runs,
        parse_card_info.total_mp_runs,
        dict(parse_enemy_info.encounter_dict),
        dict(parse_enemy_info.monster_dict),
        dict(parse_enemy_info.encounter_to_monster),
        dict(parse_enemy_info.encounter_dict_mp),
        dict(parse_enemy_info.monster_dict_mp),
        dict(parse_enemy_info.encounter_killed_mp),
        dict(parse_enemy_info.encounter_category),
        dict(parse_enemy_info.monster_category),
        dict(parse_enemy_info.encounter_killed),
        list(parse_run_history.solo_runs),
        list(parse_run_history.mp_runs),
    )