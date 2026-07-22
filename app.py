import streamlit as st
import pandas as pd
import os
import data_load
import constants
import render
import streamlit_widgets

from html_builders import (build_card_grid_html,
                           build_enemy_grid_html,
                           build_relic_grid_html,
                           build_run_history_table_html,
                           clean_enemy_name,
                           clean_encounter_name,
                           DECK_CSS,
                           DECK_JS)
from ui_styles import SHARED_CSS, TOOLTIP_JS
import tempfile
from config import SAVE_FILE_PATH, PLAYER_ID

st.set_page_config(page_title="StS2 Run Analytics", layout="wide")
st.title("🃏 Slay the Spire 2: Run Analytics Dashboard")

# ── Top-level page toggle ───────────────────────────────────────────────────
data_source = st.sidebar.radio(
    "Data Source",
    ["Demo Data", "Upload Run Files", "Local Path (Dev)"],
    index=0
)

# Initialize a variable to hold the directory we want to parse
target_folder = None
uploaded_files = None
save_file_path = SAVE_FILE_PATH
all_player_ids = set()

if data_source == "Demo Data":
    target_folder = "example_runs"
    player_id = PLAYER_ID
    if not os.path.exists(target_folder):
        st.sidebar.error(f"⚠️ Directory '{target_folder}' not found. Please create it and add example JSON files.")

elif data_source == "Upload Run Files":
    player_id = None
    uploaded_files = st.sidebar.file_uploader(
        "Upload Slay the Spire 2 RUN files",
        type=["run"],
        accept_multiple_files=True,
        help="Navigate to your AppData/SlaytheSpire2 history folder and upload the RUN files."
    )
    player_id_col, clear_id_col = st.sidebar.columns([3, 1], vertical_alignment="bottom")
    with player_id_col:
        player_id = st.text_input("Input your player ID", key="input_id")
    with clear_id_col:
        st.button("Clear", on_click=streamlit_widgets.clear_id, key="clear_btn", use_container_width=True)
    if uploaded_files:
        temp_dir = tempfile.TemporaryDirectory()
        target_folder = temp_dir.name
        for uploaded_file in uploaded_files:
            # Strip any directory components from the filename before joining
            # it to target_folder, so a crafted upload name like
            # "../../.ssh/authorized_keys" can't write outside the temp dir.
            safe_name = os.path.basename(uploaded_file.name)
            file_path = os.path.join(target_folder, safe_name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        all_player_ids = data_load.detect_player_ids(target_folder)
        if len(all_player_ids) == 1:
                # If there's only one player_id then there are only singplayer runs
                player_id = 1
        if not player_id:
            if len(all_player_ids) == 0:
                st.sidebar.info("No player IDs could be detected in the uploaded files.")
            st.sidebar.warning("⚠️ Please enter your player ID above to process uploaded files.")
            options = [str(pid) for pid in sorted(all_player_ids)]
            player_id = st.sidebar.pills("Detected Player IDs", 
                                         options, default=None, 
                                         key="detected_ids",
                                         on_change=streamlit_widgets.update_player_id)            
            st.stop()
    else:
        st.info("📤 Upload one or more RUN files in the sidebar to view your custom dashboard.")

elif data_source == "Local Path (Dev)":
    player_id = PLAYER_ID
    target_folder = st.sidebar.text_input(
        "Enter Run History Folder Path:",
        value= save_file_path if save_file_path else "",
        key = "local_path"
    )

page = st.sidebar.radio("View", ["Cards", "Enemies", "Relics", "Run History"], horizontal=True)
# =============================================================================
# DATA LOADING & RENDERING
# =============================================================================

def update_card_mode(key: str, new_mode: str):
    st.session_state[key] = new_mode

if target_folder and os.path.exists(target_folder):
    
    with st.spinner("Parsing run files..."):
        cards_data, mp_cards_data, relics_data, mp_relics_data, total_runs, total_mp_runs, enc_dict_sp, mon_dict_sp, \
        enc_to_mon,enc_dict_mp,mon_dict_mp,enc_kill_mp,enc_cat,mon_cat,enc_kill_sp, \
        solo_run_history, mp_run_history = data_load.load_all_run_data(target_folder, player_id)
    
    CUSTOM_SORT_ORDERS = constants.CUSTOM_SORT_ORDERS

    # ── CARDS PAGE ────────────────────────────────────────────────────────────
    if page == "Cards":
        render.sp_mp_toggle("card_mode")

        card_mode = st.session_state.get("card_mode", "SP")
        active_cards_data = cards_data if card_mode == "SP" else mp_cards_data
        active_total_runs = total_runs if card_mode == "SP" else total_mp_runs

        if active_cards_data:
            card_list = [c.get_data() for c in active_cards_data.values()]
            df = pd.DataFrame(card_list)
            metrics_placeholder = st.sidebar.empty()

            st.sidebar.subheader("Filters")
            search = st.sidebar.text_input("Search card name", "", key="search")
            
            all_chars = constants.ALL_CHARACTERS
            selected_chars = st.sidebar.pills("Character", all_chars, default=None, key="char")
            all_rarity = constants.ALL_RARITIES
            selected_rarity = st.sidebar.pills("Rarity", all_rarity, default=None, key="rarity")
            all_types = constants.ALL_TYPES
            selected_types = st.sidebar.pills("Types", all_types, default=None, key ="type")
            all_costs = constants.ALL_COSTS
            selected_costs = st.sidebar.pills("Cost (Unupgraded)", all_costs, default=None, key="cost")
            sort_by = st.sidebar.selectbox(
                "Sort by", ["Win Rate (%)", "Pick Rate (%)", "Picked", "Offered", "Wins", "Card Name", "Card Class", "Rarity", "Type", "Cost"],
                key = "sort_by"
            )
            if sort_by in CUSTOM_SORT_ORDERS:
                df[sort_by] = pd.Categorical(df[sort_by], categories=CUSTOM_SORT_ORDERS[sort_by], ordered=True)
            sort_asc = st.sidebar.checkbox("Ascending", value=False, key="sort_asc")
            upgraded = st.sidebar.checkbox("Upgraded", value=False, key="upgraded")
            beta = st.sidebar.checkbox("Beta Art", value=False, key="beta")
            max_picked = int(df["Picked"].max())
            if st.session_state.get("min_picked", 0) > max_picked:
                st.session_state["min_picked"] = 0
            min_picked = st.sidebar.slider("Min times picked", 0, max_picked, key="min_picked")

            max_offered = int(df["Offered"].max())
            if st.session_state.get("min_offered", 0) > max_offered:
                st.session_state["min_offered"] = 0
            min_offered = st.sidebar.slider("Min times offered", 0, max_offered, key="min_offered")

            filtered = df.copy()
            if search:
                filtered = filtered[filtered["Card Name"].str.contains(search, case=False, na=False)]
            if selected_chars:
                filtered = filtered[filtered["Card Class"] == selected_chars]
            if selected_rarity:
                filtered = filtered[filtered["Rarity"] == selected_rarity]
            if selected_types:
                filtered = filtered[filtered["Type"] == selected_types]
            if selected_costs:
                filtered = filtered[filtered["Cost"] == selected_costs]
            filtered = filtered[filtered["Picked"] >= min_picked]
            filtered = filtered[filtered["Offered"] >= min_offered]
            filtered = filtered.sort_values(by=sort_by, ascending=sort_asc)
            st.markdown("---")

            card_rows = filtered.to_dict("records")
            cards_html = build_card_grid_html(card_rows, upgraded, beta)
            num_cards = len(filtered)

            with metrics_placeholder.container():
                m1, m2 = st.columns(2)
                m1.metric("Total Runs", active_total_runs)
                m2.metric("Visible Cards", num_cards)

            component_html = (
                f"<style>{SHARED_CSS}</style>"
                f'<div id="card-portal-tooltip"></div>'
                f'<div class="grid">{cards_html}</div>'
                f"<script>{TOOLTIP_JS}</script>"
            )
            cols_approx = 8
            rows_approx = max(1, -(-num_cards // cols_approx))
            full_pad = 340 if num_cards > 100 else 0
            height_px = rows_approx * 330 + 80 + full_pad
            st.iframe(component_html, height=height_px)
        else:
            st.info(f"No valid {'solo' if card_mode == 'SP' else 'multiplayer'} runs found in the specified directory.")

    # ── ENEMIES PAGE ──────────────────────────────────────────────────────────
    elif page == "Enemies":
        render.sp_mp_toggle("mode")

        mode = st.session_state.get("mode", "SP")
        enc_dict = enc_dict_sp if mode == "SP" else enc_dict_mp
        mon_dict = mon_dict_sp if mode == "SP" else mon_dict_mp
        enc_kill = enc_kill_sp if mode == "SP" else enc_kill_mp

        if enc_dict or mon_dict:
            metrics_placeholder = st.sidebar.empty()
            enemy_mode = st.sidebar.radio("Show", ["Encounters", "Monsters"], horizontal=True)

            st.sidebar.subheader("Filters")
            search = st.sidebar.text_input("Search name", "")
            sort_by = st.sidebar.selectbox("Sort by", ["Avg Damage Taken", "Encounters", "Name"])
            sort_asc = st.sidebar.checkbox("Ascending", value=False)
            max_enc = max((len(v) for v in (enc_dict if enemy_mode == "Encounters" else mon_dict).values()), default=200)
            min_enc = st.sidebar.slider("Min encounters", 0, max_enc, 0)

            if enemy_mode == "Encounters":
                rows = []
                for enc_id, dmg_list in enc_dict.items():
                    name = clean_encounter_name(enc_id)
                    members = enc_to_mon.get(enc_id, [])
                    member_names = ", ".join(clean_enemy_name(m) for m in members)    
                    rows.append({
                        "Name": name,
                        "Encounters": len(dmg_list),
                        "Avg Damage Taken": round(sum(dmg_list) / len(dmg_list), 1),
                        "Deaths to": enc_kill.get(enc_id, 0),
                        "Members": member_names,
                        "Category": enc_cat.get(enc_id, "normal"),
                    })
            else:
                rows = []
                for mon_id, dmg_list in mon_dict.items():
                    name = clean_enemy_name(mon_id)
                    rows.append({
                        "Name": name,
                        "Encounters": len(dmg_list),
                        "Avg Damage Taken": round(sum(dmg_list) / len(dmg_list), 1),
                        "Members": "",
                        "Category": mon_cat.get(mon_id, "normal"),
                    })

            df = pd.DataFrame(rows)
            if search:
                df = df[df["Name"].str.contains(search, case=False, na=False)]
            df = df[df["Encounters"] >= min_enc]
            df = df.sort_values(by=sort_by, ascending=sort_asc)

            num_visible = len(df)
            with metrics_placeholder.container():
                m1, m2 = st.columns(2)
                m1.metric("Total Runs", total_runs)
                m2.metric(f"Visible {enemy_mode}", num_visible)

            st.markdown("---")

            CATEGORY_ORDER = constants.CATEGORY_ORDER

            all_html_parts = []
            seen_enemy_header = False
            for cat_key, cat_label in CATEGORY_ORDER:
                cat_rows = df[df["Category"] == cat_key].to_dict("records")
                if not cat_rows:
                    continue
                grid_class = "enc-grid"
                grid_html = build_enemy_grid_html(cat_rows, enemy_mode)
                # Merge normal + weak under one header
                if cat_key in ("normal", "weak"):
                    if not seen_enemy_header:
                        all_html_parts.append(f'<div class="section-header">{cat_label}</div>')
                        seen_enemy_header = True
                    all_html_parts.append(f'<div class="{grid_class}">{grid_html}</div>')
                else:
                    all_html_parts.append(
                        f'<div class="section-header">{cat_label}</div>'
                        f'<div class="{grid_class}">{grid_html}</div>'
                    )

            combined_html = "\n".join(all_html_parts)
            component_html = (
                f"<style>{SHARED_CSS}</style>"
                f'<div id="card-portal-tooltip"></div>'
                f'{combined_html}'
            )

            if enemy_mode == "Encounters":
                rows_approx = max(1, -(-num_visible // 4))
                height_px = min(rows_approx * 350 + 1000, 17000)
            else:
                cols_approx = 6
                rows_approx = max(1, -(-num_visible // cols_approx))
                height_px = min(rows_approx * 300 + 1000, 17500)

            st.iframe(component_html, height=height_px)
        else:
            st.info(f"No valid {'solo' if mode == 'SP' else 'multiplayer'} runs found in the specified directory.")

    # ── RELICS PAGE ───────────────────────────────────────────────────────────
    elif page == "Relics":
        render.sp_mp_toggle("relic_mode")

        relic_mode = st.session_state.get("relic_mode", "SP")
        active_relics_data = relics_data if relic_mode == "SP" else mp_relics_data
        active_total_runs = total_runs if relic_mode == "SP" else total_mp_runs

        if active_relics_data:
            relic_list = [r.get_data() for r in active_relics_data.values() if r.name]
            df = pd.DataFrame(relic_list)
            metrics_placeholder = st.sidebar.empty()
            st.sidebar.subheader("Filters")
            search = st.sidebar.text_input("Search relic name", "")
            max_picked = int(df["Taken"].max()) if not df.empty else 10
            min_picked = st.sidebar.slider("Min times picked", 0, max_picked, 0)

            # ── Sort priority builder ─────────────────────────────────────────
            SORT_COLS = constants.RELIC_SORT_COLS
            SORT_DEFAULTS = constants.RELIC_SORT_DEFAULTS

            st.sidebar.markdown("**Sort priority**")
            st.sidebar.caption("Reorder columns; toggle ↑ ↓ per column.")

            if "relic_sort_priority" not in st.session_state:
                st.session_state.relic_sort_priority = SORT_COLS.copy()
            if "relic_sort_dirs" not in st.session_state:
                st.session_state.relic_sort_dirs = SORT_DEFAULTS.copy()

            priority = st.session_state.relic_sort_priority
            dirs = st.session_state.relic_sort_dirs

            for rank, col in enumerate(priority):
                col_left, col_mid, col_right = st.sidebar.columns([0.55, 0.22, 0.22])
                col_left.markdown(f"**{rank+1}.** {col}")
                if col_mid.button("↑", key=f"up_{col}", disabled=(rank == 0)):
                    i = priority.index(col)
                    priority[i], priority[i-1] = priority[i-1], priority[i]
                    st.rerun()
                if col_right.button("↓", key=f"dn_{col}", disabled=(rank == len(priority)-1)):
                    i = priority.index(col)
                    priority[i], priority[i+1] = priority[i+1], priority[i]
                    st.rerun()

                dir_val = dirs.get(col, "desc")
                toggled = st.sidebar.checkbox(
                    "Ascending",
                    value=(dir_val == "asc"),
                    key=f"dir_{col}",
                )
                dirs[col] = "asc" if toggled else "desc"

            filtered = df.copy()
            if search:
                filtered = filtered[filtered["Relic Name"].str.contains(search, case=False, na=False)]
            filtered = filtered[filtered["Taken"] >= min_picked]
            ascending_flags = [dirs[col] == "asc" for col in priority]
            filtered = filtered.sort_values(by=priority, ascending=ascending_flags)

            num_relics = len(filtered)
            with metrics_placeholder.container():
                m1, m2 = st.columns(2)
                m1.metric("Total Runs", active_total_runs)
                m2.metric("Visible Relics", num_relics)

            st.markdown("---")

            relic_rows = filtered.to_dict("records")
            grid_html = build_relic_grid_html(relic_rows)
            component_html = (
                f"<style>{SHARED_CSS}</style>"
                f'<div id="card-portal-tooltip"></div>'
                f'<div class="grid">{grid_html}</div>'
                f"<script>{TOOLTIP_JS}</script>"
            )
            cols_approx = 8
            rows_approx = max(1, -(-num_relics // cols_approx))
            height_px = rows_approx * 270 + 80
            st.iframe(component_html, height=height_px)
        else:
            st.info(f"No valid {'solo' if relic_mode == 'SP' else 'multiplayer'} runs found in the specified directory.")

    # ── RUN HISTORY PAGE ──────────────────────────────────────────────────────
    elif page == "Run History":
        render.sp_mp_toggle("history_mode")
        history_mode = st.session_state.get("history_mode", "SP")
        active_runs = solo_run_history if history_mode == "SP" else mp_run_history

        if active_runs:
            st.sidebar.subheader("Filters")
            all_chars = sorted({r["character"] for r in active_runs if r["character"]})
            selected_char = st.sidebar.selectbox("Character", ["All"] + all_chars)

            outcome = st.sidebar.radio("Outcome", ["All", "Wins", "Losses"], horizontal=True)

            all_ascs = sorted({r["ascension"] for r in active_runs})
            asc_options = ["All"] + [str(a) for a in all_ascs]
            selected_asc = st.sidebar.selectbox("Ascension", asc_options)

            sort_by = st.sidebar.selectbox(
                "Sort by", ["Date", "Ascension", "Floor Reached", "Deck Size", "Character"]
            )
            sort_asc = st.sidebar.checkbox("Ascending", value=False)

            # ── Apply filters ─────────────────────────────────────────────────
            filtered = active_runs
            if selected_char != "All":
                filtered = [r for r in filtered if r["character"] == selected_char]
            if outcome == "Wins":
                filtered = [r for r in filtered if r["win"]]
            elif outcome == "Losses":
                filtered = [r for r in filtered if not r["win"]]
            if selected_asc != "All":
                filtered = [r for r in filtered if r["ascension"] == int(selected_asc)]

            sort_key_map = {
                "Date": lambda r: r["timestamp"],
                "Ascension": lambda r: r["ascension"],
                "Floor Reached": lambda r: r["floor"],
                "Deck Size": lambda r: r["deck_size"],
                "Character": lambda r: r["character"],
            }
            filtered = sorted(filtered, key=sort_key_map[sort_by], reverse=not sort_asc)

            # ── Summary metrics ───────────────────────────────────────────────
            total_shown = len(filtered)
            wins_shown = sum(1 for r in filtered if r["win"])
            win_pct = wins_shown / total_shown * 100 if total_shown else 0
            avg_deck = sum(r["deck_size"] for r in filtered) / total_shown if total_shown else 0
            avg_floor = sum(r["floor"] for r in filtered) / total_shown if total_shown else 0
            asc_vals = [r["ascension"] for r in filtered]
            max_asc = max(asc_vals) if asc_vals else 0

            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Runs Shown", total_shown)
            m2.metric("Wins", wins_shown)
            m3.metric("Win Rate", f"{win_pct:.1f}%")
            m4.metric("Avg Deck Size", f"{avg_deck:.1f}")
            m5.metric("Avg Floor", f"{avg_floor:.1f}")
            m6.metric("Highest Ascension", max_asc)

            st.markdown("---")

            # ── Build the run history HTML table ──────────────────────────────
            table_html = build_run_history_table_html(filtered)

            component_html = (
                f"<style>body{{background:#0d0d1a;margin:0;padding:0}}"
                f"table{{border-radius:8px;overflow:hidden}}"
                f"tr:hover td{{background:#222240!important;transition:background 0.1s}}"
                f"{DECK_CSS}</style>"
                f"{table_html}"
                f"<script>{DECK_JS}</script>"
            )

            row_h = 38
            header_h = 50
            height_px = min(len(filtered) * row_h + header_h + 30, 10000)
            st.iframe(component_html, height=height_px)

        else:
            st.info(f"No valid {'solo' if history_mode == 'SP' else 'multiplayer'} runs found in the specified directory.")
    
    @st.dialog("Privacy, Terms, & Credits")
    def show_info_modal():
        st.markdown("""
        Data Processing & Privacy -
        This dashboard is designed to analyze your Slay the Spire 2 run history. All data parsing and visualization are performed in-memory during your active session.
        
        No Data Storage: Uploaded save files, run histories, and local file structures are strictly processed temporarily in the session state. None of your gameplay data, Steam IDs, or personal information is saved, logged, or transmitted to any external databases.
        
        No Tracking: This tool does not use marketing cookies, track individual users across sessions, or collect personally identifiable information.

        Disclaimer of Liability -
        This application is provided "as-is" without any warranties, express or implied. While this tool only reads data and does not modify your game client, you assume all responsibility for its use. It is always recommended to maintain regular backups of your local save directories.
        The developer shall not be held liable for any data loss, game corruption, or unforeseen technical issues arising from the use of this dashboard.

        Affiliation & Credits -
        This is an unofficial, fan-made project. It is not affiliated with, endorsed by, or sponsored by Mega Crit. Slay the Spire 2 and all related game assets are the property of Mega Crit. Images taken from slay the spire wiki and the spire codex.

        Built using Python, Streamlit, and Pandas.

        © 2026 Jason Hua. All rights reserved. | https://github.com/Jhhua04/sts2-data
        """)

    if st.sidebar.button("Privacy, Terms, & Credits"):
        show_info_modal()

    if data_source == "Upload Run Files" and uploaded_files:
            temp_dir.cleanup()  
    print("-----------------------------------------------------------------")
elif target_folder and not os.path.exists(target_folder):
    st.error("Folder path not found. Please check the directory.")
else:
    st.error("Folder path not found. Please check the directory.")