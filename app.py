import html
import streamlit as st
import pandas as pd
import os
import parse_card_info
import parse_enemy_info
import parse_relic_info
import parse_run_history
from wiki_urls import wiki_image_url
from html_builders import build_enemy_grid_html, build_relic_grid_html, clean_enemy_name, clean_encounter_name
from ui_styles import SHARED_CSS, TOOLTIP_JS
import tempfile
from config import SAVE_FILE_PATH, PLAYER_ID

st.set_page_config(page_title="StS2 Run Analytics", layout="wide")
st.title("🃏 Slay the Spire 2: Run Analytics Dashboard")

# ── Top-level page toggle ─────────────────────────────────────────────────────
data_source = st.sidebar.radio(
    "Data Source",
    ["Demo Data", "Upload Run Files", "Local Path (Dev)"],
    index=0
)

# Initialize a variable to hold the directory we want to parse
target_folder = None
uploaded_files = None
save_file_path = SAVE_FILE_PATH

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
    player_id = st.sidebar.text_input("Input your player ID", "", key="input_id")
    if uploaded_files and player_id:
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
    elif uploaded_files and not player_id:
        st.sidebar.warning("⚠️ Please enter your player ID to process uploaded files.")
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

def sp_mp_toggle(key: str) -> str:
    col_sp, col_mp = st.columns(2)
    mode = st.session_state.get(key, "SP")
    with col_sp:
        st.button(
            "⚔️ Singleplayer", 
            use_container_width=True,
            type="primary" if mode == "SP" else "secondary",
            on_click=update_card_mode,
            args=(key, "SP")
        )
    with col_mp:
        st.button(
            "👥 Multiplayer", 
            use_container_width=True,
            type="primary" if mode == "MP" else "secondary",
            on_click=update_card_mode,
            args=(key, "MP")
        )
    return st.session_state.get(key, "SP")

@st.cache_data
def load_all_run_data(folder_path):
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

    # Initialize dictionaries locally
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
if target_folder and os.path.exists(target_folder):
    
    with st.spinner("Parsing run files..."):
        cards_data, mp_cards_data, relics_data, mp_relics_data, total_runs, total_mp_runs, enc_dict_sp, mon_dict_sp, \
        enc_to_mon,enc_dict_mp,mon_dict_mp,enc_kill_mp,enc_cat,mon_cat,enc_kill_sp, \
        solo_run_history, mp_run_history = load_all_run_data(target_folder)
    
    CUSTOM_SORT_ORDERS = {
    "Card Class": ["Colorless", "Defect", "Necrobinder", "Regent", "Silent", "Ironclad"],
    "Rarity": ["Event", "Ancient", "Rare", "Uncommon", "Common"],
    "Type": ["Power", "Skill", "Attack"],
    "Cost": ["X", "3", "2", "1", "0"],
    }

    # ── CARDS PAGE ────────────────────────────────────────────────────────────
    if page == "Cards":
        sp_mp_toggle("card_mode")

        card_mode = st.session_state.get("card_mode", "SP")
        active_cards_data = cards_data if card_mode == "SP" else mp_cards_data
        active_total_runs = total_runs if card_mode == "SP" else total_mp_runs

        if active_cards_data:
            card_list = [c.get_data() for c in active_cards_data.values()]
            df = pd.DataFrame(card_list)
            metrics_placeholder = st.sidebar.empty()

            st.sidebar.subheader("Filters")
            search = st.sidebar.text_input("Search card name", "", key="search")
            
            all_chars = ["Ironclad", "Silent", "Regent", "Necrobinder", "Defect", "Colorless"]
            selected_chars = st.sidebar.pills("Character", all_chars, default=None, key="char")
            all_rarity = ["Common", "Uncommon", "Rare", "Ancient", "Event"]
            selected_rarity = st.sidebar.pills("Rarity", all_rarity, default=None, key="rarity")
            all_types = ["Attack", "Skill", "Power"]
            selected_types = st.sidebar.pills("Types", all_types, default=None, key ="type")
            all_costs = ["0", "1", "2", "3", "X"]
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

            cards_html_parts = []
            for row in filtered.itertuples():
                raw_name = row._1
                raw_character = row._2
                raw_type = row.Type
                name = html.escape(str(raw_name))
                character = html.escape(str(raw_character))
                rarity = row.Rarity
                card_type = html.escape(str(raw_type))
                cost = row.Cost
                offered = int(row.Offered)
                picked = int(row.Picked)
                wins = int(row.Wins)
                pick_rate = float(row._12)
                win_rate = float(row._13)

                # Raw (unescaped) values are used for URL building and dict
                # lookups so HTML-escaping doesn't corrupt slugs or miss
                # known-value matches; escaped versions are display-only.
                img_url = wiki_image_url(raw_name, raw_character, upgraded, beta)
                initials = "".join(w[0] for w in raw_name.split()[:2]).upper()

                if win_rate >= 50:
                    wr_colour = "#2ecc71"
                elif win_rate >= 25:
                    wr_colour = "#f0a500"
                else:
                    wr_colour = "#e74c3c"

                pr_bar = min(pick_rate, 100)
                wr_bar = min(win_rate, 100)

                char_colors = {
                    "Ironclad": "#D62000", "Silent": "#5EBD00", "Defect": "#3EB3ED",
                    "Regent": "#E36600", "Necrobinder": "#CD4EED", "Colorless": "#A3A3A3",
                }
                type_colors = {
                    "Attack": "#ff8172", "Skill": "#70fa70", "Power": "#798dff",}

                badge_color = char_colors.get(raw_character, "#555")
                type_color = type_colors.get(raw_type, "#555")
                tooltip_html = (
                    f'<div class="tt-title">{name}</div>'
                    f'<div class="tt-char" style="color:{badge_color}">{character}</div>'
                    f'<table class="tt-table">'
                    f'<tr><td>Offered</td><td>{offered}</td></tr>'
                    f'<tr><td>Picked</td><td>{picked}</td></tr>'
                    f'<tr><td>Wins with card</td><td>{wins}</td></tr>'
                    f'<tr><td>Pick rate</td><td>{pick_rate:.1f}%</td></tr>'
                    f'<tr><td>Win rate</td><td style="color:{wr_colour};font-weight:600">{win_rate:.1f}%</td></tr>'
                    f'</table>'
                ).replace('"', '&quot;')

                cards_html_parts.append(
                    f'<div class="card-tile" data-tooltip="{tooltip_html}" data-badge="{badge_color}">'
                    f'  <div class="card-img-wrap">'
                    f'    <img src="{img_url}" class="card-art" alt="{name}"'
                    f'      onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
                    f'    <div class="card-art-placeholder" style="display:none">{initials}</div>'
                    f'  </div>'
                    f'  <div class="card-body">'
                    f'    <div class="card-name">{name}</div>'
                    f'    <div class="char-badge" style="background:{badge_color}22;color:{badge_color};'
                    f'border:1px solid {badge_color}55">{character}</div>'
                    f'    <div class="char-badge" style="background:{type_color}22;color:{type_color};'
                    f'border:1px solid {type_color}55">{card_type}</div>'
                    f'    <div class="stat-row">'
                    f'      <span class="stat-label">Pick</span>'
                    f'      <div class="bar-wrap"><div class="bar-fill bar-blue" style="width:{pr_bar}%"></div></div>'
                    f'      <span class="stat-val">{pick_rate:.1f}%</span>'
                    f'    </div>'
                    f'    <div class="stat-row">'
                    f'      <span class="stat-label">Win</span>'
                    f'      <div class="bar-wrap"><div class="bar-fill" style="width:{wr_bar}%;background:{wr_colour}"></div></div>'
                    f'      <span class="stat-val" style="color:{wr_colour}">{win_rate:.1f}%</span>'
                    f'    </div>'
                    f'  </div>'
                    f'</div>'
                )

            cards_html = "\n".join(cards_html_parts)
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
        sp_mp_toggle("mode")

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

            CATEGORY_ORDER = [
                ("boss",   "👑 Bosses"),
                ("elite",  "⚔️ Elites"),
                ("normal", "🗡️ Enemies"),
                ("weak",   "🗡️ Enemies"),
            ]

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

        sp_mp_toggle("relic_mode")

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
            SORT_COLS = ["Win Rate (%)", "Taken", "Wins", "Relic Name"]
            SORT_DEFAULTS = {"Win Rate (%)": "desc", "Taken": "desc", "Wins": "desc", "Relic Name": "asc"}

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
        import datetime

        sp_mp_toggle("history_mode")
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
            CHAR_COLORS = {
                "Ironclad": "#D62000", "Silent": "#5EBD00", "Defect": "#3EB3ED",
                "Regent": "#E36600", "Necrobinder": "#CD4EED", "Colorless": "#A3A3A3",
            }

            def _asc_badge(asc: int) -> str:
                if asc == 0:
                    color = "#22f379"
                if asc >= 10:
                    color = "#c678dd"
                elif asc >= 6:
                    color = "#e74c3c"
                elif asc >= 3:
                    color = "#f0a500"
                else:
                    color = "#5b8dee"
                return (
                    f'<span style="background:{color}22;color:{color};border:1px solid {color}55;'
                    f'border-radius:4px;padding:2px 8px;font-size:13px;font-weight:600">A{asc}</span>'
                )

            rows_html = []
            for i, r in enumerate(filtered):
                dt = datetime.datetime.fromtimestamp(r["timestamp"]).strftime("%Y-%m-%d %H:%M")
                win_label = "✅ Win" if r["win"] else "💀 Loss"
                win_color = "#2ecc71" if r["win"] else "#e74c3c"
                # Raw values used for lookups/URLs; escaped versions for display text.
                raw_char = r.get("character", "")
                char_display = html.escape(str(raw_char))
                killed_by_display = html.escape(str(r["killed_by"])) if r["killed_by"] else ""
                char_color = CHAR_COLORS.get(raw_char, "#aaa")
                killed_cell = (
                    f'<span style="color:#e74c3c;font-size:12px">{killed_by_display}</span>'
                    if killed_by_display else
                    '<span style="color:#444">—</span>'
                )
                row_bg = "#1a1a2e" if i % 2 == 0 else "#16162a"
                deck_cards = r.get("deck") or []
                deck_items_html = "".join(
                    (lambda n=name: (
                        f'<div class="deck-card"'
                        f' data-img="{wiki_image_url(n.rstrip("+"), raw_char, n.endswith("+"), False)}"'
                        f'>{html.escape(n)}</div>'
                    ))()
                    for name in deck_cards if name
                )
                rows_html.append(
                    f'<tr style="background:{row_bg}">'
                    f'  <td style="padding:8px 12px;color:#888;font-size:13px">{dt}</td>'
                    f'  <td style="padding:8px 12px;font-weight:600;color:{win_color}">{win_label}</td>'
                    f'  <td style="padding:8px 12px">'
                    f'    <span style="background:{char_color}22;color:{char_color};border:1px solid {char_color}55;'
                    f'border-radius:4px;padding:2px 8px;font-size:13px;font-weight:600">{char_display}</span>'
                    f'  </td>'
                    f'  <td style="padding:8px 12px;text-align:center">{_asc_badge(r["ascension"])}</td>'
                    f'  <td style="padding:8px 12px;text-align:center">'
                    f'    <span class="deck-wrap">'
                    f'      <span class="deck-trigger">{r["deck_size"]}</span>'
                    f'      <div class="deck-popup"><div class="deck-grid">{deck_items_html}</div></div>'
                    f'    </span>'
                    f'  </td>'
                    f'  <td style="padding:8px 12px;text-align:center;color:#ddd">{r["floor"]}</td>'
                    f'  <td style="padding:8px 12px">{killed_cell}</td>'
                    f'</tr>'
                )

            table_html = (
                '<table style="width:100%;border-collapse:collapse;font-family:sans-serif">'
                '<thead>'
                '<tr style="background:#12121f;border-bottom:2px solid #333355">'
                '  <th style="padding:10px 12px;text-align:left;color:#8888aa;font-size:13px;font-weight:600">Date</th>'
                '  <th style="padding:10px 12px;text-align:left;color:#8888aa;font-size:13px;font-weight:600">Outcome</th>'
                '  <th style="padding:10px 12px;text-align:left;color:#8888aa;font-size:13px;font-weight:600">Character</th>'
                '  <th style="padding:10px 12px;text-align:center;color:#8888aa;font-size:13px;font-weight:600">Ascension</th>'
                '  <th style="padding:10px 12px;text-align:center;color:#8888aa;font-size:13px;font-weight:600">Deck Size</th>'
                '  <th style="padding:10px 12px;text-align:center;color:#8888aa;font-size:13px;font-weight:600">Floors</th>'
                '  <th style="padding:10px 12px;text-align:left;color:#8888aa;font-size:13px;font-weight:600">Killed By</th>'
                '</tr>'
                '</thead>'
                '<tbody>'
                + "\n".join(rows_html) +
                '</tbody>'
                '</table>'
            )

            DECK_CSS = """
.deck-wrap { position: relative; display: inline-block; }
.deck-trigger {
    color: #f0a500; font-weight: 600;
    border-bottom: 1px dotted #f0a500; cursor: default;
}
.deck-popup {
    display: none; position: fixed;
    background: #12121f; border: 1px solid #333355;
    border-radius: 8px; padding: 10px 12px;
    z-index: 9999; min-width: 260px; max-width: 420px;
    box-shadow: 0 8px 32px #00000088;
    pointer-events: auto;
}
.deck-wrap:hover .deck-popup { display: block; }
/* also kept open by JS when mouse is inside popup */
.deck-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 5px;
}
.deck-card {
    position: relative;
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 4px; padding: 3px 7px;
    font-size: 12px; color: #ccc; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
    cursor: default;
    transition: border-color 0.15s, background 0.15s;
}
.deck-card:hover {
    border-color: #5b8dee;
    background: #1e1e3a;
    z-index: 2;
}
/* floating card image shown on individual card hover */
.deck-card-preview {
    display: none;
    position: fixed;
    z-index: 99999;
    pointer-events: none;
    border-radius: 8px;
    box-shadow: 0 8px 32px #000000cc;
    width: 180px;
    background: #1a1a2e;
    border: 1px solid #333355;
    overflow: hidden;
}
.deck-card-preview.visible { display: block; }
.deck-card-preview img {
    width: 100%;
    display: block;
    aspect-ratio: 3/4;
    object-fit: cover;
}
.deck-card-preview .preview-name {
    font-size: 12px; color: #ccc;
    padding: 4px 8px 6px;
    text-align: center;
    background: #12121f;
    border-top: 1px solid #2a2a4a;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.deck-card-preview .preview-placeholder {
    width: 100%; aspect-ratio: 3/4;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg, #2a2a4a 0%, #3a2060 100%);
    font-size: 28px; font-weight: 700; color: rgba(255,255,255,0.3);
}
"""
            DECK_JS = """
(function() {
    // Position & show deck popup; keep it open while hovering popup itself
    document.querySelectorAll('.deck-wrap').forEach(function(wrap) {
        var popup = wrap.querySelector('.deck-popup');
        var hideTimer = null;

        function showPopup() {
            clearTimeout(hideTimer);
            var r = wrap.getBoundingClientRect();
            var popW = popup.offsetWidth || 260;
            var left = r.left;
            if (left + popW > window.innerWidth - 10) {
                left = window.innerWidth - popW - 10;
            }
            popup.style.left = left + 'px';
            popup.style.top  = (r.bottom + 4) + 'px';
            popup.style.display = 'block';
        }

        function scheduleHide() {
            hideTimer = setTimeout(function() {
                popup.style.display = 'none';
                preview.classList.remove('visible');
            }, 80);
        }

        wrap.addEventListener('mouseenter', showPopup);
        wrap.addEventListener('mouseleave', scheduleHide);
        popup.addEventListener('mouseenter', function() { clearTimeout(hideTimer); });
        popup.addEventListener('mouseleave', scheduleHide);
    });

    // Single shared card-image preview element
    var preview = document.createElement('div');
    preview.className = 'deck-card-preview';
    preview.innerHTML = '<img src="" alt=""><div class="preview-name"></div>';
    document.body.appendChild(preview);

    var previewImg  = preview.querySelector('img');
    var previewName = preview.querySelector('.preview-name');

    document.querySelectorAll('.deck-card').forEach(function(card) {
        card.addEventListener('mouseenter', function() {
            var imgSrc = card.dataset.img || '';
            var name   = card.textContent.trim();

            previewName.textContent = name;
            previewImg.style.display = 'block';

            if (imgSrc) {
                previewImg.src = imgSrc;
                previewImg.onerror = function() { previewImg.style.display = 'none'; };
                previewImg.onload  = function() { previewImg.style.display = 'block'; };
            } else {
                previewImg.style.display = 'none';
            }

            preview.classList.add('visible');
            positionPreview(card);
        });

        card.addEventListener('mouseleave', function() {
            preview.classList.remove('visible');
        });
    });

    function positionPreview(card) {
        var rect   = card.getBoundingClientRect();
        var pw     = preview.offsetWidth  || 180;
        var ph     = preview.offsetHeight || 240;
        var vw     = window.innerWidth;
        var vh     = window.innerHeight;
        var MARGIN = 8;

        // Prefer right of the deck popup; fall back to left of deck popup
        var left = rect.right + MARGIN;
        if (left + pw > vw - MARGIN) left = rect.left - pw - MARGIN;
        if (left < MARGIN) left = MARGIN;

        // Vertically centre on card; clamp to viewport
        var top = rect.top + rect.height / 2 - ph / 2;
        if (top < MARGIN) top = MARGIN;
        if (top + ph > vh - MARGIN) top = vh - ph - MARGIN;

        preview.style.left = left + 'px';
        preview.style.top  = top  + 'px';
    }
})();
"""
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
        This is an unofficial, fan-made project. It is not affiliated with, endorsed by, or sponsored by Mega Crit. Slay the Spire 2 and all related game assets are the property of Mega Crit.

        Built using Python, Streamlit, and Pandas.

        © 2026 Jason Hua. All rights reserved. | https://github.com/Jhhua04/sts2-data
        """)

    if st.sidebar.button("Privacy, Terms, & Credits"):
        show_info_modal()

    if data_source == "Upload Run Files" and uploaded_files:
            temp_dir.cleanup()  
elif target_folder and not os.path.exists(target_folder):
    st.error("Folder path not found. Please check the directory.")
else:
    st.error("Folder path not found. Please check the directory.")