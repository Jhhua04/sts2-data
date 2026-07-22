import datetime
import html
import re
from wiki_urls import wiki_enemy_image_url, wiki_image_url, wiki_relic_image_url


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


_CHAR_COLORS = {
    "Ironclad": "#D62000", "Silent": "#5EBD00", "Defect": "#3EB3ED",
    "Regent": "#E36600", "Necrobinder": "#CD4EED", "Colorless": "#A3A3A3",
}
_TYPE_COLORS = {
    "Attack": "#ff8172", "Skill": "#70fa70", "Power": "#798dff",
}


def build_card_grid_html(rows, upgraded: bool, beta: bool) -> str:
    """Build the card grid tiles for the Cards page.

    `rows` is an iterable of dict-like records (e.g. from
    `df.to_dict("records")`) with keys: Card Name, Card Class, Type,
    Rarity, Cost, Offered, Picked, Wins, Pick Rate (%), Win Rate (%).
    """
    tiles = []
    for row in rows:
        raw_name = row["Card Name"]
        raw_character = row["Card Class"]
        raw_type = row["Type"]
        name = html.escape(str(raw_name))
        character = html.escape(str(raw_character))
        card_type = html.escape(str(raw_type))
        offered = int(row["Offered"])
        picked = int(row["Picked"])
        wins = int(row["Wins"])
        pick_rate = float(row["Pick Rate (%)"])
        win_rate = float(row["Win Rate (%)"])

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

        badge_color = _CHAR_COLORS.get(raw_character, "#555")
        type_color = _TYPE_COLORS.get(raw_type, "#555")
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

        tiles.append(
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

# =============================================================================
# RUN HISTORY
# =============================================================================

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

_RUN_CHAR_COLORS = {
    "Ironclad": "#D62000", "Silent": "#5EBD00", "Defect": "#3EB3ED",
    "Regent": "#E36600", "Necrobinder": "#CD4EED", "Colorless": "#A3A3A3",
}


def _asc_badge(asc: int) -> str:
    if asc == 0:
        color = "#22f379"
    elif asc >= 10:
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


def build_run_history_table_html(filtered) -> str:
    """Build the run-history HTML table (including header row).

    `filtered` is a list of run dicts with keys: timestamp, win,
    character, ascension, deck_size, deck, floor, killed_by.
    """
    rows_html = []
    for i, r in enumerate(filtered):
        dt = datetime.datetime.fromtimestamp(r["timestamp"]).strftime("%Y-%m-%d %H:%M")
        win_label = "✅ Win" if r["win"] else "💀 Loss"
        win_color = "#2ecc71" if r["win"] else "#e74c3c"
        # Raw values used for lookups/URLs; escaped versions for display text.
        raw_char = r.get("character", "")
        char_display = html.escape(str(raw_char))
        killed_by_display = html.escape(str(r["killed_by"])) if r["killed_by"] else ""
        char_color = _RUN_CHAR_COLORS.get(raw_char, "#aaa")
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
    return table_html