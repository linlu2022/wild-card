"""Prepare compact per-form candidates for the full Blue Archive review.

The output is a review queue, not an automatically approved wildcard pack.
"""

import csv
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

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
)
DISTINCTIVE = {
    "halo", "mechanical_halo", "aqua_halo", "blue_halo", "pink_halo",
    "purple_halo", "black_halo", "white_halo", "yellow_halo", "red_halo",
    "rabbit_ears", "wolf_ears", "cat_ears", "fox_ears", "horse_ears",
    "animal_ears", "pointy_ears", "angel_wings", "demon_wings",
    "twintails", "ponytail", "side_ponytail", "braid", "hair_bun",
    "drill_hair", "long_hair", "short_hair", "medium_hair", "very_long_hair",
    "school_uniform", "gym_uniform", "maid", "maid_headdress",
    "one-piece_swimsuit", "frilled_apron", "hair_flower", "hair_ornament",
    "cross_hair_ornament", "frog_hair_ornament", "snake_hair_ornament",
}
HAIR_STYLES = {
    "twintails", "ponytail", "side_ponytail", "braid", "hair_bun",
    "drill_hair", "long_hair", "short_hair", "medium_hair", "very_long_hair",
}
OFFICIAL_HOSTS = {
    "webusstatic.yo-star.com", "bluearchive.nexon.com",
    "jarvis.dn.nexoncdn.co.kr", "nxm-clw-cdn.dn.nexoncdn.co.kr",
}
GAME_MIRRORS = {"bluearchive.wiki", "bluearchive.wikiru.jp", "static.wikitide.net"}
with (HERE / "verified_youtube.csv").open(encoding="utf-8", newline="") as verified_stream:
    VERIFIED_YOUTUBE = {row["url"] for row in csv.DictReader(verified_stream)}
COLLAB_WORDS = (
    "collaboration", "collab", "j league", "j-league", "mom's touch",
    "mahjong soul", "mahjongsoul", "pizza hut", "rakuten", "muninsa",
    "candy", "hoyofair", "merch", "concert", "illustration book",
    "flowery charms", "dimension poptown", "kujibikido",
)


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def pick_visual_tags(general):
    tags = general.split()
    result = []
    def take(items, limit):
        for tag in items[:limit]:
            if tag not in result:
                result.append(tag)
    hair = [t for t in tags if t.endswith("_hair") and t[:-5] in COLORS]
    eyes = [t for t in tags if t.endswith("_eyes") and t[:-5] in COLORS]
    take(hair, 2)
    take(eyes, 2)
    species = [t for t in tags if t in DISTINCTIVE and (t.endswith("_ears") or t.endswith("_wings") or "halo" in t)]
    species.sort(key=lambda t: (t in {"halo", "animal_ears"}, t))
    if any(t.endswith("_halo") or t == "mechanical_halo" for t in species):
        species = [t for t in species if t != "halo"]
    if any(t.endswith("_ears") and t != "animal_ears" for t in species):
        species = [t for t in species if t != "animal_ears"]
    take(species, 2)
    garments = [t for t in tags if any(t == g or t.endswith("_" + g) for g in GARMENTS)
                and not t.startswith(("holding_", "unworn_", "partially_", "removing_", "no_"))]
    garments = [t for t in garments if not any(x != t and x.endswith("_" + t) for x in garments)]
    garments.sort(key=lambda t: (t in GARMENTS, t.endswith("_shoes") or t == "shoes", t))
    take(garments, 5)
    hair_style = [t for t in tags if t in HAIR_STYLES and t not in result]
    if "very_long_hair" in hair_style:
        hair_style = [t for t in hair_style if t != "long_hair"]
    hair_style.sort(key=lambda t: (t in {"long_hair", "short_hair", "medium_hair", "very_long_hair"}, t))
    take(hair_style, 2)
    return result[:10]


def source_tier(row):
    source = row["source"].strip()
    host = urlsplit(source).hostname or ""
    meta = row["meta_tags"].split()
    if "game_asset" in meta:
        return "game_asset", 6
    source_lower = source.lower()
    if source in VERIFIED_YOUTUBE or host in OFFICIAL_HOSTS or "blue_archivejp" in source_lower or "en_bluearchive" in source_lower:
        return "publisher", 5
    if host == "static.wikia.nocookie.net" and "/blue-archive/images/" in source_lower:
        return "game_mirror", 4
    if host in GAME_MIRRORS:
        return "game_mirror", 4
    if "official_art" in meta and host in {"twitter.com", "x.com", "www.youtube.com"}:
        return "social_unverified", 2
    if "official_art" in meta:
        return "source_unverified", 1
    return "not_official_tagged", 0


def form_stem(tag):
    return tag.removesuffix("_(blue_archive)")


def normalized_label(value):
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def looks_related(tag, wiki_title):
    base = form_stem(wiki_title).split("_(", 1)[0]
    return form_stem(tag) == base or form_stem(tag).startswith(base + "_(") or form_stem(tag).startswith(base + "_")


def main():
    inventory = read_csv(HERE / "inventory.csv")
    supplemental = read_csv(HERE / "supplemental.csv") + read_csv(HERE / "rescue.csv")
    manifest = {row["character"]: row for row in read_csv(ROOT / "curation/name-packs-2026-09-26/manifest.csv") if row["pack"] == "blue_archive"}
    original_tags = set(manifest)
    by_post = defaultdict(list)
    for row in inventory:
        if row["image_type"] == "post":
            by_post[row["image_id"]].append(row)
    supplemental_new = 0
    for row in supplemental:
        if row["image_id"] not in by_post:
            by_post[row["image_id"]].append({**row, "wiki_title": row["searched_tag"], "label": "supplemental search", "form_description": "", "image_type": "post"})
            supplemental_new += 1
    by_tag = defaultdict(list)
    for post_id, rows in by_post.items():
        row = rows[0]
        if "blue_archive" not in row["copyright_tags"].split() or "official_art" not in row["meta_tags"].split() or "1girl" not in row["general_tags"].split():
            continue
        for tag in row["character_tags"].split():
            if not tag.endswith("_(blue_archive)"):
                continue
            related = [r for r in rows if looks_related(tag, r["wiki_title"]) or r["wiki_title"] == tag]
            if tag not in original_tags and not related:
                continue
            best_context = max(related or rows, key=lambda r: (bool(r.get("form_description")), r["wiki_title"] == tag))
            tier, score = source_tier(row)
            meta = row["meta_tags"].split()
            general = row["general_tags"].split()
            if "solo" in general: score += 1
            if "game_asset" in meta and "promotional_art" in meta: score -= 2
            if "third-party_source" in meta: score -= 1
            if "1boy" in general or "2girls" in general: score -= 3
            is_base_tag = "_(" not in form_stem(tag)
            context_label = best_context["label"].lower().strip()
            if is_base_tag and tag == best_context["wiki_title"]:
                if context_label.startswith("default") or not context_label:
                    score += 8
                elif context_label != "supplemental search":
                    score -= 8
            if is_base_tag and any(other != tag and other.startswith(form_stem(tag) + "_(") for other in row["character_tags"].split()):
                score -= 8
            if context_label.startswith("default") and tag == best_context["wiki_title"]:
                score += 4
            if not is_base_tag and context_label and context_label != "supplemental search":
                variant = re.search(r"_\(([^()]*)\)$", form_stem(tag))
                variant_text = normalized_label(variant.group(1)) if variant else ""
                label_text = normalized_label(context_label)
                if variant_text and label_text == variant_text:
                    score += 7
                elif variant_text and variant_text in label_text:
                    score += 3
                else:
                    score -= 4
            if tag != best_context["wiki_title"] and best_context["label"].lower().startswith("default"):
                score -= 4
            text = " ".join([tag, best_context.get("label", ""), best_context.get("form_description", ""), source_tier(row)[0]]).lower().replace("_", " ")
            if any(word in text for word in COLLAB_WORDS): score -= 8
            by_tag[tag].append((score, post_id, row, best_context, tier))

    out = []
    for tag in sorted(original_tags | set(by_tag)):
        choices = sorted(by_tag[tag], key=lambda x: (x[0], int(x[1])), reverse=True)
        manifest_row = manifest.get(tag, {})
        released = "released_student" in manifest_row.get("source", "")
        if choices:
            score, post_id, row, context, tier = choices[0]
            visual = pick_visual_tags(row["general_tags"])
            status = "candidate_released" if released else "candidate_npc_or_story"
            review_text = " ".join([tag, context["label"], context.get("form_description", ""), row["source"]]).lower().replace("_", " ")
            external_collab = any(word in review_text for word in COLLAB_WORDS)
            if external_collab and not released:
                status = "excluded_external_collaboration"
            if score < 3 or len(visual) < 3:
                if status != "excluded_external_collaboration":
                    status = "needs_source_or_visual_review"
            if tag not in original_tags and tier not in {"game_asset", "publisher", "game_mirror"}:
                if status != "excluded_external_collaboration":
                    status = "needs_in_work_release_review"
            out.append({
                "character": tag, "in_name_pack": tag in original_tags,
                "released_student": released, "status": status,
                "candidate_count": len(choices), "score": score, "post_id": post_id,
                "wiki_title": context["wiki_title"], "label": context["label"],
                "source_tier": tier, "source": row["source"].strip(),
                "url": row["url"], "visual_tags": " ".join(visual),
                "character_tags": row["character_tags"],
                "meta_tags": row["meta_tags"],
                "form_description": context.get("form_description", "").replace("\r", " ").replace("\n", " ")[:300].strip(),
            })
        else:
            out.append({
                "character": tag, "in_name_pack": tag in original_tags,
                "released_student": released, "status": "no_tagged_post",
                "candidate_count": 0, "score": "", "post_id": "", "wiki_title": "",
                "label": "", "source_tier": "", "source": "", "url": "",
                "visual_tags": "", "character_tags": "", "meta_tags": "", "form_description": "",
            })
    path = HERE / "review_queue.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(out[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    from collections import Counter
    print("unique posts", len(by_post), "supplemental unique", supplemental_new)
    print("review rows", len(out), Counter(r["status"] for r in out))


if __name__ == "__main__":
    main()
