"""Small per-post visual tag selection shared by the remaining one-off audits."""

from collections import Counter

COLORS = {
    "black", "white", "grey", "gray", "brown", "blonde", "blue", "aqua",
    "green", "yellow", "orange", "red", "pink", "purple", "silver",
    "gold", "light_brown", "dark_brown", "light_blue", "dark_blue",
    "light_purple", "dark_purple", "light_pink", "dark_pink",
}
GARMENTS = (
    "dress", "skirt", "shirt", "jacket", "coat", "shorts", "pants",
    "swimsuit", "bikini", "uniform", "kimono", "sweater", "hoodie",
    "apron", "pantyhose", "thighhighs", "boots", "shoes", "socks",
    "gloves", "scarf", "necktie", "bowtie", "choker", "hat", "headdress",
    "hairband", "cape", "capelet", "leotard", "sailor_collar",
    "bodysuit", "armor", "corset", "sundress", "sarong", "robe",
)
OUTFITS = {"dress", "swimsuit", "bikini", "uniform", "kimono", "bodysuit", "armor", "leotard", "robe", "sundress"}
MAIN = {"shirt", "jacket", "coat", "skirt", "shorts", "pants", "sweater", "hoodie"}
FEATURES = {
    "fox_ears", "cat_ears", "rabbit_ears", "wolf_ears", "horse_ears",
    "animal_ears", "fox_tail", "cat_tail", "dragon_tail", "tail",
    "horns", "wings", "pointy_ears", "halo", "mechanical_halo",
    "rigging", "ship_rigging", "maid", "maid_headdress", "crown", "tiara",
    "vision_(genshin_impact)", "demon_wings", "angel_wings",
}
HAIR_STYLES = {
    "twintails", "ponytail", "side_ponytail", "braid", "hair_bun",
    "drill_hair", "long_hair", "short_hair", "medium_hair", "very_long_hair",
}


def pick_visual_tags(general):
    tags = general.split()
    result = []

    def take(items, limit):
        for tag in items[:limit]:
            if tag not in result:
                result.append(tag)

    take([tag for tag in tags if tag.endswith("_hair") and tag[:-5] in COLORS], 2)
    take([tag for tag in tags if tag.endswith("_eyes") and tag[:-5] in COLORS], 2)
    features = [tag for tag in tags if tag in FEATURES]
    features.sort(key=lambda tag: (tag in {"tail", "animal_ears", "wings", "halo"}, tag))
    if any(tag.endswith("_tail") for tag in features):
        features = [tag for tag in features if tag != "tail"]
    if any(tag.endswith("_ears") and tag != "animal_ears" for tag in features):
        features = [tag for tag in features if tag != "animal_ears"]
    take(features, 2)

    garments = [
        tag for tag in tags
        if any(tag == kind or tag.endswith("_" + kind) for kind in GARMENTS)
        and not tag.startswith(("holding_", "unworn_", "partially_", "removing_", "no_", "panties_under_"))
    ]
    garments = [tag for tag in garments if not any(other != tag and other.endswith("_" + tag) for other in garments)]

    def family(tag):
        return next((kind for kind in GARMENTS if tag == kind or tag.endswith("_" + kind)), tag)

    garments.sort(key=lambda tag: (
        0 if family(tag) in OUTFITS else 1 if family(tag) in MAIN else 2,
        tag == family(tag), tag.startswith("multicolored_"), tag,
    ))
    counts = Counter()
    colored = set()
    selected = []
    for tag in garments:
        kind = family(tag)
        is_color = tag.split("_", 1)[0] in COLORS or tag.startswith("multicolored_")
        if counts[kind] >= 2 or (is_color and kind in colored):
            continue
        selected.append(tag)
        counts[kind] += 1
        if is_color:
            colored.add(kind)
    take(selected, 6)
    hair = [tag for tag in tags if tag in HAIR_STYLES and tag not in result]
    if "very_long_hair" in hair and "long_hair" in hair:
        hair.remove("long_hair")
    take(sorted(hair, key=lambda tag: (tag in {"long_hair", "short_hair", "medium_hair", "very_long_hair"}, tag)), 2)
    return result[:11]
