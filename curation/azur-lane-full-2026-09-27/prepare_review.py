"""Rank exact, game-record-backed Azur Lane form posts for editorial review.

The queue is evidence, not automatic approval. A tagged post establishes only
what Danbooru says about that image; the ship/skin manifest supplies separate
evidence that a named form is in the game.
"""

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
COPYRIGHT = "azur_lane"

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
DISTINCTIVE = {
    "fox_ears", "cat_ears", "rabbit_ears", "wolf_ears", "animal_ears",
    "fox_tail", "cat_tail", "dragon_tail", "tail", "horns", "wings",
    "pointy_ears", "rigging", "ship_rigging", "mechanical_tail",
    "maid", "maid_headdress", "crown", "tiara", "halo",
}
HAIR_STYLES = {
    "twintails", "ponytail", "side_ponytail", "braid", "hair_bun",
    "drill_hair", "long_hair", "short_hair", "medium_hair", "very_long_hair",
}
OUTFIT_FAMILIES = {
    "dress", "swimsuit", "bikini", "uniform", "kimono", "bodysuit",
    "armor", "leotard", "robe", "sundress",
}
MAIN_GARMENTS = {"shirt", "jacket", "coat", "skirt", "shorts", "pants", "sweater", "hoodie"}
PUBLISHER_HOSTS = {
    "azurlane.yo-star.com", "www.azurlane.yo-star.com",
    "www.azurlane.jp", "azurlane.jp",
    "www.azurlane.net", "azurlane.net", "blhx.com",
}
GAME_MIRRORS = {"azurlane.koumakan.jp", "azurlane.netojuu.com"}
FIELDS = [
    "character", "manifest_source", "source_id", "is_danbooru_tag",
    "status", "candidate_count", "score", "post_id", "wiki_title",
    "label", "source_tier", "source", "url", "visual_tags",
    "evidence_character_tag", "character_tags", "general_tags", "meta_tags",
    "form_description",
]


def read_csv(path):
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def norm(value):
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def stem(tag):
    return tag.removesuffix("_(azur_lane)")


def base(tag):
    return stem(tag).split("_(", 1)[0]


def variant(tag):
    match = re.search(r"_\(([^()]*)\)$", stem(tag))
    return match.group(1) if match else ""


def pick_visual_tags(general):
    tags = general.split()
    result = []

    def take(items, limit):
        for tag in items[:limit]:
            if tag not in result:
                result.append(tag)

    take([t for t in tags if t.endswith("_hair") and t[:-5] in COLORS], 2)
    take([t for t in tags if t.endswith("_eyes") and t[:-5] in COLORS], 2)
    species = [t for t in tags if t in DISTINCTIVE]
    species.sort(key=lambda t: (t in {"tail", "animal_ears", "wings"}, t))
    if any(t.endswith("_tail") for t in species):
        species = [t for t in species if t != "tail"]
    if any(t.endswith("_ears") and t != "animal_ears" for t in species):
        species = [t for t in species if t != "animal_ears"]
    take(species, 2)
    garments = [
        t for t in tags
        if any(t == g or t.endswith("_" + g) for g in GARMENTS)
        and not t.startswith(("holding_", "unworn_", "partially_", "removing_", "no_", "panties_under_"))
    ]
    garments = [t for t in garments if not any(x != t and x.endswith("_" + t) for x in garments)]
    def family(tag):
        return next((g for g in GARMENTS if tag == g or tag.endswith("_" + g)), tag)
    def garment_priority(tag):
        kind = family(tag)
        return (0 if kind in OUTFIT_FAMILIES else 1 if kind in MAIN_GARMENTS else 2,
                tag == kind, tag.startswith("multicolored_"), tag)
    garments.sort(key=garment_priority)
    family_counts = Counter()
    family_colors = set()
    selected_garments = []
    for tag in garments:
        kind = family(tag)
        colored = tag.split("_", 1)[0] in COLORS or tag.startswith("multicolored_")
        if family_counts[kind] >= 2 or (colored and kind in family_colors):
            continue
        selected_garments.append(tag)
        family_counts[kind] += 1
        if colored:
            family_colors.add(kind)
    take(selected_garments, 6)
    hair = [t for t in tags if t in HAIR_STYLES and t not in result]
    if "very_long_hair" in hair:
        hair.remove("long_hair") if "long_hair" in hair else None
    take(sorted(hair, key=lambda t: (t in {"long_hair", "short_hair", "medium_hair", "very_long_hair"}, t)), 2)
    return result[:11]


def source_tier(row):
    meta = row["meta_tags"].split()
    source = row["source"].strip()
    host = urlsplit(source).hostname or ""
    account = urlsplit(source).path.strip("/").split("/", 1)[0].casefold()
    if "game_asset" in meta:
        return "game_asset", 8
    if source.casefold() in {"game asset", "game file", "game files"}:
        return "game_file_label", 6
    if host in PUBLISHER_HOSTS:
        return "publisher", 7
    if host in {"twitter.com", "x.com"} and account in {"azurlane_staff", "azurlane_en"}:
        return "publisher", 7
    if host in GAME_MIRRORS:
        return "game_mirror", 5
    if "azurlane" in source.lower() and host in {"twitter.com", "x.com", "weibo.com"}:
        return "social_account_unverified", 2
    if "official_art" in meta:
        return "tagged_source_unverified", 1
    return "not_official_tagged", 0


def context_score(tag, context):
    label = context.get("label", "").strip()
    title = context.get("wiki_title", "")
    if label == "supplemental search":
        return 0
    if tag == title and norm(label).startswith("default"):
        return 12
    if tag == title and variant(tag):
        return 6
    if base(tag) != base(title):
        return -30
    if variant(tag):
        wanted = norm(variant(tag))
        observed = norm(label)
        if wanted and wanted == observed:
            return 12
        if wanted and (wanted in observed or observed in wanted) and len(observed) >= 5:
            return 7
        return -14
    return -18  # A base tag on another outfit is not a default image.


def main():
    manifest = {
        row["character"]: row
        for row in read_csv(ROOT / "curation/name-packs-2026-09-26/manifest.csv")
        if row["pack"] == COPYRIGHT
    }
    constructed_by_form = defaultdict(list)
    for tag, record in manifest.items():
        if record["is_danbooru_tag"] == "False" and "released_skin" in record["source"] and variant(tag):
            constructed_by_form[(base(tag), norm(variant(tag)))].append(tag)
    inventory = read_csv(HERE / "inventory.csv")
    supplemental = read_csv(HERE / "supplemental.csv")
    post_contexts = defaultdict(list)
    for row in inventory:
        if row["image_type"] == "post" and row["status"] == "candidate":
            post_contexts[row["image_id"]].append(row)
    for row in supplemental:
        post_contexts[row["image_id"]].append({
            **row, "wiki_title": row["searched_tag"],
            "label": "supplemental search", "form_description": "",
        })

    by_tag = defaultdict(list)
    for post_id, contexts in post_contexts.items():
        post = contexts[0]
        general = post["general_tags"].split()
        meta = post["meta_tags"].split()
        if COPYRIGHT not in post["copyright_tags"].split() or "official_art" not in meta or "1girl" not in general:
            continue
        if any(t in general for t in ("2girls", "3girls", "1boy", "multiple_girls")):
            continue
        tier, source_score = source_tier(post)
        substantive_bases = {
            base(character)
            for character in post["character_tags"].split()
            if character.endswith("_(azur_lane)")
            and base(character) not in {"manjuu", "grim"}
        }
        for tag in post["character_tags"].split():
            record = manifest.get(tag)
            if not record or record["is_danbooru_tag"] != "True":
                continue
            if "released_skin" not in record["source"] and tier not in {"game_asset", "publisher"}:
                continue
            scored_contexts = [(context_score(tag, row), row) for row in contexts]
            match, context = max(scored_contexts, key=lambda item: item[0])
            if match < 0:
                continue
            if match == 0 and (len(substantive_bases) != 1 or base(tag) not in substantive_bases):
                # Search results can tag a cameo, framed picture, doll, or
                # alternate ship. Without a matching Wiki Appearance row,
                # general tags cannot safely be assigned to that character.
                continue
            if match == 0 and not variant(tag) and (
                "official_alternate_costume" in general or "official_alternate_costume" in meta
            ):
                continue
            if not variant(tag) and match == 0 and any(
                other != tag and base(other) == base(tag) and variant(other)
                for other in post["character_tags"].split()
            ):
                continue
            score = source_score + match
            if "solo" in general:
                score += 2
            if "third-party_source" in meta:
                score -= 1
            if "promotional_art" in meta and "game_asset" not in meta:
                score -= 2
            by_tag[tag].append((score, post_id, post, context, tier, tag))

        # Some in-game skin names have no Danbooru form tag. A base character
        # Wiki can still link that exact named skin to a tagged official image.
        # Keep this mapping explicit; never infer it from a generic post alone.
        for context in contexts:
            if context.get("label") == "supplemental search":
                continue
            title = context.get("wiki_title", "")
            base_tag = base(title) + "_(azur_lane)"
            if base_tag not in post["character_tags"].split():
                continue
            if any(
                other != base_tag and base(other) == base(title) and variant(other)
                for other in post["character_tags"].split()
            ):
                continue
            for tag in constructed_by_form[(base(title), norm(context.get("label", "")))]:
                score = source_score + 12 + (2 if "solo" in general else 0)
                by_tag[tag].append((score, post_id, post, context, tier, base_tag))

    output = []
    for tag, record in sorted(manifest.items()):
        choices = sorted(by_tag.get(tag, []), key=lambda item: (item[0], int(item[1])), reverse=True)
        common = {
            "character": tag, "manifest_source": record["source"],
            "source_id": record["source_id"], "is_danbooru_tag": record["is_danbooru_tag"],
        }
        if not choices:
            output.append({**common, "status": "no_exact_tagged_post" if record["is_danbooru_tag"] == "True" else "official_name_without_tag", "candidate_count": 0})
            continue
        score, post_id, post, context, tier, evidence_tag = choices[0]
        visual = pick_visual_tags(post["general_tags"])
        status = ("candidate_constructed_form" if record["is_danbooru_tag"] == "False" else "candidate") if len(visual) >= 3 and tier in {"game_asset", "game_file_label", "publisher", "game_mirror"} else "needs_source_or_visual_review"
        output.append({
            **common, "status": status, "candidate_count": len(choices),
            "score": score, "post_id": post_id,
            "wiki_title": context["wiki_title"], "label": context["label"],
            "source_tier": tier, "source": post["source"].strip(),
            "url": post["url"], "visual_tags": " ".join(visual),
            "evidence_character_tag": evidence_tag,
            "character_tags": post["character_tags"],
            "general_tags": post["general_tags"], "meta_tags": post["meta_tags"],
            "form_description": context.get("form_description", "").replace("\r", " ").replace("\n", " ")[:300].strip(),
        })

    with (HERE / "review_queue.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    print("unique posts", len(post_contexts), "review rows", len(output), Counter(row["status"] for row in output))


if __name__ == "__main__":
    main()
