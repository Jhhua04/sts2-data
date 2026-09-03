import re
import get_json

with open("cards.json") as f:
    _monster_json = get_json.get_json("monsters.json", "monsters", ["id", "name", "type", "image_url"])
    _cards_json = get_json.get_json("cards.json", "cards", ["id", "name", "image_url_card", "image_url_card_upg"])
    _relics_json = get_json.get_json("relics.json", "relics", ["id", "name", "image_url"])
_MONSTER_BY_ID = {r["id"]: r for r in _monster_json}
_CARDS_BY_NAME = {r["name"]: r for r in _cards_json}
_RELICS_BY_NAME = {r["name"]: r for r in _relics_json}
# ── Card name fixes ───────────────────────────────────────────────────────────
odd_relic_names = {
    "Blood Soaked Rose": "Blood-Soaked Rose",
    "Fake Anchor": "Anchor???",
    "Fake Blood Vial": "Blood Vial???",
    "Fake Happy Flower": "Happy Flower???",
    "Fake Lees Waffle": "Lee's Waffle???",
    "Fake Mango": "Mango???",
    "Fake Merchants Rug": "The Merchant's Rug???",
    "Fake Orichalcum": "Orichalcum???",
    "Fake Snecko Eye": "Snecko Eye???",
    "Fake Strike Dummy": "Strike Dummy???",
    "Fake Venerable Tea Set": "Venerable Tea Set???",
    "Gold Plated Cables": "Gold-Plated Cables",
    "Lords Parasol": "Lord's Parasol",
    "Sea Glass": "Sea Glass",
    "Self Forming Clay": "Self-Forming Clay",
    "Tri Boomerang": "Tri-Boomerang",
    "Tanxs Whistle": "Tanx's Whistle",
    "Captains Wheel": "Captain's Wheel",
    "Mr Struggles": "Mr. Struggles",
    "Dollys Mirror": "Dolly's Mirror",
    "Pandoras Box": "Pandora's Box",
    "Wongos Mystery Ticket": "Wongo's Mystery Ticket",
    "Lees Waffle": "Lee's Waffle",
    "Chosen Cheese" : "The Chosen Cheese",
}
gif_cards = ["Mad Science"]\

def wiki_image_url(card_name: str, character: str, upgraded: bool, beta: bool) -> str:
    if card_name in gif_cards:
            return f"https://slaythespire.wiki.gg/images/StS2_Colorless-MadScience.gif"
    if beta:
        beta_card = re.sub(r"[ ]", "_", card_name)
        beta_card = re.sub(r"[^a-zA-Z0-9_]", "", beta_card).lower()
        return f"https://cdn.spire-codex.com/game/v0.107.1/cards/beta/{beta_card}_plus.webp" if upgraded else f"https://cdn.spire-codex.com/game/v0.107.1/cards/beta/{beta_card}.webp"
    image_url = _CARDS_BY_NAME.get(card_name).get("image_url_card_upg" if upgraded else "image_url_card")
    return image_url

def wiki_enemy_image_url(enemy_name: str) -> str:
    if enemy_name == "Doormaker":
        return "https://slaythespire.wiki.gg/images/StS2_Doormaker-Scrutiny.webp?a9d24a=&format=original"
    elif enemy_name == "Crusher":
        return "https://slaythespire.wiki.gg/images/StS2_Crusher.png?c9aae6=&format=original"
    elif enemy_name == "Rocket":
        return "https://slaythespire.wiki.gg/images/StS2_Rocket.png?c9aae6=&format=original"
    image_url = _MONSTER_BY_ID.get(enemy_name.upper(), {}).get("image_url")
    return f"https://spire-codex.com{image_url}"

def wiki_relic_image_url(relic_name: str) -> str:
    if relic_name in odd_relic_names:
        relic_name = odd_relic_names[relic_name]
    if "Paels" in relic_name:
        relic_name = re.sub(r"Paels", "Pael's", relic_name)
    if "Neows" in relic_name:
        relic_name = re.sub(r"Neows", "Neow's", relic_name)
    relic_name = re.sub(
        r"\b(Of|On|(?<!^)The)\b", 
        lambda m: m.group(0).lower(), 
        relic_name
        )
    print(relic_name)
    image_url = _RELICS_BY_NAME.get(relic_name).get("image_url")
    return f"https://spire-codex.com{image_url}"