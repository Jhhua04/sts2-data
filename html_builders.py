import html
import re
from wiki_urls import wiki_enemy_image_url, wiki_relic_image_url


# =============================================================================
# NAME CLEANERS
# =============================================================================

def clean_enemy_name(raw_id: str) -> str:
    part = raw_id.split('.')[-1]
    spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', part)
    return spaced.title()


# Encounter names: strip generic prefixes like "Test_Subject_" and normalise
# Boss/Elite suffixes so we get e.g. "Doormaker Boss" or "Slime Elite".
_FILLER_PREFIXES = re.compile(
    r'^(test_subject|encounter|unknown)[_\s]+', re.IGNORECASE
)

def clean_encounter_name(raw_id: str) -> str:
    """Return a clean display name for an encounter ID.

    Rules:
    - Strip known filler prefixes (Test_Subject_, etc.)
    - If the ID ends with _BOSS or _ELITE, replace the suffix with ' Boss'
      or ' Elite' so it reads naturally.
    - Otherwise fall back to normal title-casing.
    """
    part = raw_id.split('.')[-1]  # drop any ENCOUNTER. prefix

    # Detect and strip trailing _BOSS / _ELITE (case-insensitive)
    suffix = ""
    part_upper = part.upper()
    if part_upper.endswith("_BOSS"):
        suffix = " Boss"
        part = part[:-5]
    elif part_upper.endswith("_ELITE"):
        suffix = " Elite"
        part = part[:-6]

    # Strip generic filler prefixes
    part = _FILLER_PREFIXES.sub("", part)

    # Convert SCREAMING_SNAKE or CamelCase → spaced title
    # First replace underscores with spaces
    part = part.replace("_", " ").strip()
    # Then split CamelCase
    part = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', part)
    return part.title() + suffix


# =============================================================================
# HTML BUILDERS
# =============================================================================

def build_enemy_grid_html(rows, mode: str) -> str:
    tiles = []
    for row in rows:
        name = html.escape(str(row["Name"]))
        encounters = int(row["Encounters"])
        avg_dmg = float(row["Avg Damage Taken"])
        deaths_to = int(row.get("Deaths to", 0))
        members = row.get("Members", "")

        if avg_dmg <= 8:
            dmg_colour = "#2ecc71"
        elif avg_dmg <= 18:
            dmg_colour = "#f0a500"
        else:
            dmg_colour = "#e74c3c"

        dmg_bar_w = min(avg_dmg / 40 * 100, 100)

        # ── ENCOUNTER TILE: large card, full-size portraits side by side ──────
        if mode == "Encounters" and members:
            member_list = [m.strip() for m in members.split(",") if m.strip()]
            seen: dict = {}
            for m in member_list:
                seen[m] = seen.get(m, 0) + 1

            portrait_parts = []
            for m in member_list:
                murl = wiki_enemy_image_url(m)
                m_safe = html.escape(m)
                minitials = "".join(w[0] for w in m.split()[:2]).upper()
                portrait_parts.append(
                    f'<div class="enc-portrait-wrap">'
                    f'  <div class="enc-portrait-img-wrap">'
                    f'    <img src="{murl}" class="enc-portrait-img" alt="{m_safe}"'
                    f'      onerror="this.style.display=\'none\';'
                    f'this.nextElementSibling.style.display=\'flex\';">'
                    f'    <div class="enc-portrait-placeholder">{minitials}</div>'
                    f'  </div>'
                    f'  <div class="enc-portrait-name">{m_safe.replace("_", " ")}</div>'
                    f'</div>'
                )

            portraits_html = "\n".join(portrait_parts)

            tiles.append(
                f'<div class="enc-tile">'
                f'  <div class="enc-portraits-row">{portraits_html}</div>'
                f'  <div class="card-body">'
                f'    <div class="card-name enc-name">{name.replace("_", " ")}</div>'
                f'    <div class="stat-row">'
                f'      <span class="stat-label-enemy">Encountered</span>'
                f'      <span class="stat-val-plain">{encounters}</span>'
                f'    </div>'
                f'    <div class="stat-row">'
                f'      <span class="stat-label-enemy">Killed By</span>'
                f'      <span class="stat-val-plain">{deaths_to}</span>'
                f'    </div>'
                f'    <div class="stat-row">'
                f'      <span class="stat-label">Dmg</span>'
                f'      <div class="bar-wrap">'
                f'        <div class="bar-fill" style="width:{dmg_bar_w:.1f}%;background:{dmg_colour}"></div>'
                f'      </div>'
                f'      <span class="stat-val" style="color:{dmg_colour}">{avg_dmg:.1f}</span>'
                f'    </div>'
                f'  </div>'
                f'</div>'
            )

        # ── MONSTER TILE ──────────────────────────────────────────────────────
        else:
            img_url = wiki_enemy_image_url(name)
            initials = "".join(w[0] for w in name.split()[:2]).upper()
            tiles.append(
                f'<div class="enc-tile">'
                f'  <div class="enc-portraits-row">'
                f'    <div class="enc-portrait-wrap">'
                f'      <div class="enc-portrait-img-wrap">'
                f'        <img src="{img_url}" class="enc-portrait-img" alt="{name.replace("_", " ")}"'
                f'          onerror="this.style.display=\'none\';'
                f'this.nextElementSibling.style.display=\'flex\';">'
                f'        <div class="enc-portrait-placeholder">{initials}</div>'
                f'      </div>'
                f'    </div>'
                f'  </div>'
                f'  <div class="card-body">'
                f'    <div class="card-name enc-name">{name.replace("_", " ")}</div>'
                f'    <div class="stat-row">'
                f'      <span class="stat-label-enemy">Encountered</span>'
                f'      <span class="stat-val-plain">{encounters}</span>'
                f'    </div>'
                f'    <div class="stat-row">'
                f'      <span class="stat-label">Dmg</span>'
                f'      <div class="bar-wrap">'
                f'        <div class="bar-fill" style="width:{dmg_bar_w:.1f}%;background:{dmg_colour}"></div>'
                f'      </div>'
                f'      <span class="stat-val" style="color:{dmg_colour}">{avg_dmg:.1f}</span>'
                f'    </div>'
                f'  </div>'
                f'</div>'
            )

    return "\n".join(tiles)


def build_relic_grid_html(rows) -> str:
    tiles = []
    for row in rows:
        raw_name = str(row["Relic Name"] or "Unknown")
        name = html.escape(raw_name)
        picked = int(row["Taken"])
        wins = int(row["Wins"])
        win_rate = float(row["Win Rate (%)"])
        description = html.escape(str(row["Description"]))

        if win_rate >= 50:
            wr_colour = "#2ecc71"
        elif win_rate >= 25:
            wr_colour = "#f0a500"
        else:
            wr_colour = "#e74c3c"

        wr_bar = min(win_rate, 100)

        img_url = wiki_relic_image_url(raw_name)
        initials = "".join(w[0] for w in raw_name.split()[:2]).upper()
        tooltip_html = (
            f'<div class="tt-title">{name}</div>'
            f'<div class="tt-desc">{description}</div>'
            f'<table class="tt-table">'
            f'<tr><td>Taken</td><td>{picked}</td></tr>'
            f'<tr><td>Wins with relic</td><td>{wins}</td></tr>'
            f'<tr><td>Win rate</td><td style="color:{wr_colour};font-weight:600">{win_rate:.1f}%</td></tr>'
            f'</table>'
        ).replace('"', '&quot;')

        tiles.append(
            f'<div class="card-tile" data-tooltip="{tooltip_html}">'
            f'  <div class="relic-img-wrap">'
            f'    <img src="{img_url}" class="relic-art" alt="{name}"'
            f'      onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';">'
            f'    <div class="card-art-placeholder relic-placeholder" style="display:none">{initials}</div>'
            f'  </div>'
            f'  <div class="card-body">'
            f'    <div class="card-name">{name}</div>'
            f'    <div class="stat-row">'
            f'      <span class="stat-label">Taken</span>'
            f'      <span class="stat-val">{picked}</span>'
            f'    </div>'
            f'    <div class="stat-row">'
            f'      <span class="stat-label">Win</span>'
            f'      <div class="bar-wrap"><div class="bar-fill" style="width:{wr_bar:.1f}%;background:{wr_colour}"></div></div>'
            f'      <span class="stat-val" style="color:{wr_colour}">{win_rate:.1f}%</span>'
            f'    </div>'
            f'  </div>'
            f'</div>'
        )
    return "\n".join(tiles)