import re
import get_json

with open("cards.json") as f:
    _monster_json = get_json.get_json("monsters.json", "monsters", ["id", "name", "type", "image_url"])
_MONSTER_BY_ID = {r["id"]: r for r in _monster_json}

# ── Card name fixes ───────────────────────────────────────────────────────────
odd_relic_names = {"MeatOnTheBone" : "MeatontheBone", "SelfFormingClay": "Self-FormingClay", "SlingOfCourage" : "SlingofCourage", "TriBoomerang" : "Tri-Boomerang", 
                   "SwordOfJade" : "SwordofJade", "BagOfPreparation" : "BagofPreparation", "TeaOfDiscourtesy" : "TeaofDiscourtesy",
                   "ArtOfWar" : "ArtofWar", "BagOfMarbles" : "BagofMarbles", "DaughterOfTheWind" : "DaughteroftheWind", "ChosenCheese" : "TheChosenCheese",
                   "BloodSoakedRose" : "Blood-SoakedRose", "BookOfFiveRings" : "BookofFiveRings", "GoldPlatedCables" : "Gold-PlatedCables", "SealOfGold" : "SealofGold",
                   "SwordOfStone" : "SwordofStone", "RingOfTheSnake" : "RingoftheSnake", "Seaglass" : "SeaGlass", "RingOfTheDrake" : "RingoftheDrake"}
gif_cards = ["Mad Science"]
oddities = {"Howl from Beyond": "HowlFromBeyond", "Drum of Battle": "DrumOfBattle", "Pull from Below" : "PullFromBelow"}

def wiki_image_url(card_name: str, character: str, upgraded: bool, beta: bool) -> str:
    if card_name == "Clash" or card_name == "Dual Wield" or card_name == "Entrench":
        character = "Ironclad"
    elif card_name == "Caltrops" or card_name == "Distraction" or card_name == "Outmaneuver":
        character = "Silent"
    elif card_name == "Hello World" or card_name == "Rebound" or card_name == "Stack" or card_name == "Rip and Tear":
        character = "Defect"
    name_slug = re.sub(r'[^a-zA-Z0-9-]', '', card_name)
    if card_name in oddities:
        name_slug = oddities[card_name]
    extension = "gif" if card_name in gif_cards else "png"
    upgraded_str = "Plus" if upgraded else ""
    beta_str = "Beta-" if beta else ""
    return f"https://slaythespire.wiki.gg/images/StS2_{beta_str}{character}-{name_slug}{upgraded_str}.{extension}"


def wiki_enemy_image_url(enemy_name: str) -> str:
    if enemy_name == "Doormaker":
        return "https://slaythespire.wiki.gg/images/StS2_Doormaker-Scrutiny.webp?a9d24a=&format=original"
    image_url = _MONSTER_BY_ID.get(enemy_name.upper(), {}).get("image_url")
    return f"https://spire-codex.com{image_url}"


def wiki_relic_image_url(relic_name: str) -> str:
    name_slug = relic_name.replace(" ", "")
    if name_slug in odd_relic_names:
        name_slug = odd_relic_names[name_slug]
    return f"https://slaythespire.wiki.gg/images/StS2_{name_slug}.png"