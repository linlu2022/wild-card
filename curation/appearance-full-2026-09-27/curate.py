"""One-off evidence review for the remaining franchise appearance packs.

Run after collecting Wiki Appearance JSON and, optionally, tagged-post search
results. The output is a conservative candidate audit, not proof that a game
roster or community tags are infallible.
"""

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from common import pick_visual_tags

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONFIG = {
    "genshin_impact": {
        "dir": "genshin-full-2026-09-27", "copyright": "genshin_impact",
        "suffix": "_(genshin_impact)", "release": ("released_outfit",),
        "publisher_hosts": {"genshin.hoyoverse.com", "act.hoyoverse.com", "act.mihoyo.com"},
        "publisher_accounts": {"genshinimpact", "genshin_jp", "genshin_7"},
        "mirror_hosts": {"genshin-impact.fandom.com", "homdgcat.wiki"},
        "wikia_path": "/genshin-impact/",
        "legacy_variant_requires_game_record": True,
    },
    "honkai_star_rail": {
        "dir": "star-rail-full-2026-09-27", "copyright": "honkai:_star_rail",
        "suffix": "_(honkai:_star_rail)", "release": ("official_update",),
        "publisher_hosts": {"hsr.hoyoverse.com", "act.hoyoverse.com", "act.mihoyo.com", "act-webstatic.hoyoverse.com"},
        "publisher_accounts": {"honkaistarrail", "honkaistarrail_en"},
        "mirror_hosts": {"honkai-star-rail.fandom.com", "houkai-star-rail.fandom.com", "star-rail.fandom.com", "homdgcat.wiki", "hsr20.hakush.in", "hsr.gachabase.net", "act-upload.mihoyo.com"},
        "wikia_path": "/honkai-star-rail/",
        "variant_requires_appearance_context": True,
        "exclude_redundant_aliases": {"herta_(honkai:_star_rail)"},
    },
    "arknights": {
        "dir": "arknights-full-2026-09-27", "copyright": "arknights",
        "suffix": "_(arknights)", "release": ("released_skin",),
        "publisher_hosts": {"ak.hypergryph.com", "arknights.global", "webusstatic.yo-star.com"},
        "publisher_accounts": {"arknightsen", "arknightsstaff"},
        "mirror_hosts": {"aceship.github.io", "prts.wiki", "media.prts.wiki", "arknights.wiki.gg", "ak.gamepress.gg", "gamepress.gg"},
        "wikia_path": "/arknights/",
    },
    "endfield": {
        "dir": "endfield-full-2026-09-27", "copyright": "arknights:_endfield",
        "suffix": "_(arknights)", "release": (),
        "publisher_hosts": {"endfield.hypergryph.com", "endfield.gryphline.com", "web-static.hg-cdn.com"},
        "publisher_accounts": {"arknightsendfield", "akendfieldjp"},
        "mirror_hosts": {"endfield.wiki.gg"},
        "wikia_path": "/arknights-endfield/",
    },
    "fate_grand_order": {
        "dir": "fgo-full-2026-09-27", "copyright": "fate/grand_order",
        "suffix": "_(fate)", "release": ("female_servant",),
        "publisher_hosts": {"fate-go.us", "www.fate-go.jp", "news.fate-go.jp"},
        "publisher_accounts": {"fatego_usa", "fgoproject"},
        "mirror_hosts": {"static.atlasacademy.io", "apps.atlasacademy.io", "fategrandorder.fandom.com"},
        "wikia_path": "/fate-grand-order/",
        "exclude_redundant_aliases": {
            "okita_souji_(koha-ace)", "mordred_(fate/apocrypha)",
            "kama_(teenager)_(fate)", "kama_(young)_(fate)",
        },
    },
    "vocaloid": {
        "dir": "vocaloid-full-2026-09-27", "copyright": "vocaloid",
        "suffix": "_(vocaloid)", "release": (),
        "publisher_hosts": {
            "piapro.net", "blog.piapro.net", "sonicwire.com", "www.crypton.co.jp", "ec.crypton.co.jp",
            "vocalomakets.com", "www.vocalomakets.com", "www.ssw.co.jp",
            "www.1stplace.co.jp", "www.vocaloid.com", "www.ah-soft.com",
            "www.v-flower.jp", "www.gynoid.co.jp", "gynoid.co.jp",
            "www.rana0909.jp", "vocaloidproject.com", "www.goodsmileracing.com",
        },
        "publisher_accounts": {"cfm_miku_en", "vocalomakets", "vocaloid_yamaha", "goodsmileracing"},
        "mirror_hosts": {"vocaloid.fandom.com", "vocaloid.wiki"},
        "wikia_path": "/vocaloid/",
        "variant_requires_appearance_context": True,
        "exclude_redundant_aliases": {"racing_miku"},
    },
    "touhou": {
        "dir": "touhou-full-2026-09-27", "copyright": "touhou",
        "suffix": "", "release": (),
        "publisher_hosts": {"gensoueclipse.jp", "ifi.games", "www.ifi.games", "touhou-project.news"},
        "publisher_accounts": {"korindo"},
        "mirror_hosts": {"thwiki.cc", "en.touhouwiki.net"},
        "wikia_path": "/touhou/",
        "variant_requires_appearance_context": True,
        "non_costume_companion_tags": {"konpaku_youmu_(ghost)"},
    },
}
REVIEW_FIELDS = [
    "character", "manifest_source", "source_id", "is_danbooru_tag",
    "status", "candidate_count", "score", "post_id", "wiki_title",
    "label", "source_tier", "source", "url", "visual_tags",
    "evidence_character_tag", "character_tags", "general_tags", "meta_tags",
]
REVIEWED_FIELDS = ["character", "copyright", "trigger", "core_tags", "url"]
STRONG = {"game_asset", "game_file_label", "publisher", "game_mirror"}


def read_csv(path):
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def norm(value):
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def stem(tag, config):
    return tag.removesuffix(config["suffix"])


def base(tag, config):
    return stem(tag, config).split("_(", 1)[0]


def variant(tag, config):
    match = re.search(r"_\(([^()]*)\)$", stem(tag, config))
    return match.group(1) if match else ""


def source_tier(row, config):
    source = row["source"].strip()
    meta = row["meta_tags"].split()
    parts = urlsplit(source)
    host = (parts.hostname or "").casefold()
    account = parts.path.strip("/").split("/", 1)[0].casefold()
    if "game_asset" in meta:
        if config["copyright"] == "vocaloid" and host not in config["publisher_hosts"]:
            return "source_unverified", 1
        return "game_asset", 8
    if source.casefold() in {"game asset", "game file", "game files", "game rip"}:
        return "game_file_label", 6
    if host in config["publisher_hosts"]:
        return "publisher", 7
    if host in {"x.com", "twitter.com", "mobile.twitter.com"} and account in config["publisher_accounts"]:
        return "publisher", 7
    if host in config["mirror_hosts"]:
        return "game_mirror", 5
    if config["copyright"] == "arknights" and host == "raw.githubusercontent.com" and any(
        parts.path.casefold().startswith(prefix) for prefix in (
            "/arknightsassets/arknightsassets/", "/aceship/arknight-images/", "/puppiizsunniiz/arknight-images/"
        )
    ):
        return "game_mirror", 5
    wikia_paths = {config["wikia_path"]}
    if config["copyright"] == "genshin_impact":
        wikia_paths.add("/gensin-impact/")
    if config["copyright"] == "honkai:_star_rail":
        wikia_paths.add("/houkai-star-rail/")
    if host in {"static.wikia.nocookie.net", "vignette.wikia.nocookie.net"} and any(path in source.casefold() for path in wikia_paths):
        return "game_mirror", 5
    return "source_unverified", 1


def context_score(tag, row, config):
    title = row.get("wiki_title", "")
    label = row.get("label", "").strip()
    if label == "supplemental search":
        return 0
    if tag == title and norm(label).startswith("default"):
        return 12
    if tag == title and not label:
        return 7
    if tag == title and variant(tag, config):
        return 6
    if base(tag, config) != base(title, config):
        return -30
    if variant(tag, config):
        wanted, observed = norm(variant(tag, config)), norm(label)
        if wanted and wanted == observed:
            return 12
        if wanted and observed and (wanted in observed or observed in wanted) and len(observed) >= 5:
            return 7
        return -14
    return -18


def curate(pack):
    config = CONFIG[pack]
    directory = ROOT / "curation" / config["dir"]
    inventory = read_csv(directory / "inventory.csv")
    assert inventory, f"missing inventory: {directory}"
    supplemental = read_csv(directory / "supplemental.csv") + read_csv(directory / "rescue.csv")
    manifest = {
        row["character"]: row
        for row in read_csv(ROOT / "curation/name-packs-2026-09-26/manifest.csv")
        if row["pack"] == pack
    }
    prior = {
        row["character"]: row
        for row in read_csv(ROOT / f"curation/wiki-appearance-2026-09-27/{pack}_reviewed.csv")
    }
    for tag in prior:
        manifest.setdefault(tag, {
            "character": tag, "source": "prior_reviewed_appearance_pack",
            "source_id": "", "is_danbooru_tag": "True",
        })
    if pack == "vocaloid":
        for row in inventory:
            if row["wiki_title"] == "racing_miku" and row["image_type"] == "post":
                for tag in row["character_tags"].split():
                    if re.fullmatch(r"racing_miku_\(20\d\d\)", tag):
                        manifest.setdefault(tag, {
                            "character": tag, "source": "wiki_racing_miku_year_form",
                            "source_id": "", "is_danbooru_tag": "True",
                        })
    constructed = defaultdict(list)
    for tag, record in manifest.items():
        normalized_variant = norm(variant(tag, config))
        if record["is_danbooru_tag"] == "False" and normalized_variant and any(term in record["source"] for term in config["release"]):
            constructed[(base(tag, config), normalized_variant)].append(tag)

    post_contexts = defaultdict(list)
    posts = {}
    for row in inventory:
        if row["image_type"] == "post" and row["status"] == "candidate":
            post_contexts[row["image_id"]].append(row)
            posts.setdefault(row["image_id"], row)
    for row in supplemental:
        post_contexts[row["image_id"]].append({
            **row, "wiki_title": row["searched_tag"], "label": "supplemental search",
        })
        posts.setdefault(row["image_id"], row)

    by_tag = defaultdict(list)
    for post_id, contexts in post_contexts.items():
        post = contexts[0]
        general = post["general_tags"].split()
        meta = post["meta_tags"].split()
        if config["copyright"] not in post["copyright_tags"].split() or "official_art" not in meta or "1girl" not in general:
            continue
        if any(re.fullmatch(r"[2-9]\d*(?:girls|boys)", term) or term in {"1boy", "multiple_girls", "multiple_boys"} for term in general):
            continue
        tier, source_score = source_tier(post, config)
        identities = {
            base(character, config)
            for character in post["character_tags"].split()
            if character in manifest and base(character, config) not in {"manjuu", "grim", "baron_bunny", "dodoco"}
        }
        for tag in post["character_tags"].split():
            record = manifest.get(tag)
            if not record or record["is_danbooru_tag"] != "True":
                continue
            co_tags = [other for other in post["character_tags"].split() if other != tag and other in manifest]
            if config["copyright"] == "fate/grand_order":
                source_lower = post["source"].casefold()
                if "aprilfool" in source_lower or (not variant(tag, config) and "/craft-essence/" in source_lower):
                    continue
                if any(stem(other, config).startswith(stem(tag, config) + "_(") for other in co_tags):
                    continue
            if config["copyright"] == "arknights" and co_tags and (
                any(base(other, config) != base(tag, config) for other in co_tags)
                or (not variant(tag, config) and any(base(other, config) == base(tag, config)
                    and variant(other, config) for other in co_tags))
                or (variant(tag, config) and any(base(other, config) == base(tag, config)
                    and variant(other, config) and variant(other, config) != variant(tag, config)
                    for other in co_tags))
            ):
                continue
            if config.get("variant_requires_appearance_context") and variant(tag, config) and all(
                row.get("label") == "supplemental search" for row in contexts
            ):
                continue
            if config.get("legacy_variant_requires_game_record") and variant(tag, config) and not any(term in record["source"] for term in config["release"]):
                continue
            match, context = max(
                ((context_score(tag, row, config), row) for row in contexts),
                key=lambda item: item[0],
            )
            if tag in prior and prior[tag]["url"].rsplit("/", 1)[-1] == post_id:
                match = max(match, 12)
            if match < 0:
                continue
            if match == 0 and (len(identities) != 1 or base(tag, config) not in identities):
                continue
            if match == 0 and not variant(tag, config) and "official_alternate_costume" in general:
                continue
            if match == 0 and not variant(tag, config) and any(
                other != tag and other not in config.get("non_costume_companion_tags", set())
                and base(other, config) == base(tag, config) and variant(other, config)
                for other in post["character_tags"].split()
            ):
                continue
            score = source_score + match + (2 if "solo" in general else 0)
            if tag in prior and prior[tag]["url"].rsplit("/", 1)[-1] == post_id:
                score += 20
            if "third-party_source" in meta:
                score -= 1
            if "promotional_art" in meta and "game_asset" not in meta:
                score -= 2
            by_tag[tag].append((score, post_id, post, context, tier, tag))

        for context in contexts:
            if context.get("label") == "supplemental search":
                continue
            title = context.get("wiki_title", "")
            matching = [other for other in post["character_tags"].split()
                        if other in manifest and base(other, config) == base(title, config)]
            if not matching:
                continue
            form_title = norm(context.get("form_title", ""))
            ranked = sorted(matching, key=lambda other: (
                bool(variant(other, config)) and norm(variant(other, config)) in form_title,
                not bool(variant(other, config)),
            ), reverse=True)
            evidence_tag = ranked[0]
            for tag in constructed[(base(title, config), norm(context.get("label", "")))]:
                by_tag[tag].append((source_score + 12 + (2 if "solo" in general else 0), post_id, post, context, tier, evidence_tag))

    review = []
    for tag, record in sorted(manifest.items()):
        common = {
            "character": tag, "manifest_source": record["source"],
            "source_id": record["source_id"], "is_danbooru_tag": record["is_danbooru_tag"],
        }
        if tag in config.get("exclude_redundant_aliases", set()):
            review.append({**common, "status": "redundant_alias", "candidate_count": 0})
            continue
        if tag in config.get("non_costume_companion_tags", set()):
            review.append({**common, "status": "companion_not_scope", "candidate_count": 0})
            continue
        choices = sorted(by_tag.get(tag, []), key=lambda item: (item[0], int(item[1])), reverse=True)
        if not choices:
            review.append({**common, "status": "official_name_without_tag" if record["is_danbooru_tag"] == "False" else "no_exact_tagged_post", "candidate_count": 0})
            continue
        def eligible(choice):
            _, choice_id, choice_post, choice_context, choice_tier, _ = choice
            visual_count = len(pick_visual_tags(choice_post["general_tags"]))
            released = any(term in record["source"] for term in config["release"])
            prior_exact = tag in prior and prior[tag]["url"].rsplit("/", 1)[-1] == choice_id
            strong_source = choice_tier in STRONG and (
                released or choice_tier in {"game_asset", "publisher"}
                or (choice_tier == "game_mirror" and choice_context["label"] != "supplemental search")
            )
            return visual_count >= 3 and (strong_source or prior_exact)
        qualified = [choice for choice in choices if eligible(choice)]
        score, post_id, post, context, tier, evidence_tag = (qualified or choices)[0]
        visual = pick_visual_tags(post["general_tags"])
        has_release = any(term in record["source"] for term in config["release"])
        prior_exact = tag in prior and prior[tag]["url"].rsplit("/", 1)[-1] == post_id
        good_source = tier in STRONG and (has_release or tier in {"game_asset", "publisher"} or (tier == "game_mirror" and context["label"] != "supplemental search"))
        if len(visual) < 3 or (not good_source and not prior_exact):
            status = "needs_source_or_visual_review"
        else:
            status = "candidate_constructed_form" if record["is_danbooru_tag"] == "False" else "candidate"
        review.append({
            **common, "status": status, "candidate_count": len(choices),
            "score": score, "post_id": post_id, "wiki_title": context["wiki_title"],
            "label": context["label"], "source_tier": tier,
            "source": post["source"].strip(), "url": post["url"],
            "visual_tags": " ".join(visual), "evidence_character_tag": evidence_tag,
            "character_tags": post["character_tags"], "general_tags": post["general_tags"],
            "meta_tags": post["meta_tags"],
        })
    review = [{field: row.get(field, "") for field in REVIEW_FIELDS} for row in review]
    write_csv(directory / "review_queue.csv", REVIEW_FIELDS, review)

    selected = []
    audit = []
    for row in review:
        tag, post_id, status = row["character"], row["post_id"], row["status"]
        if status in {"candidate", "candidate_constructed_form"}:
            post = posts[post_id]
            general, meta = post["general_tags"].split(), post["meta_tags"].split()
            evidence_tag = row["evidence_character_tag"]
            assert evidence_tag in post["character_tags"].split(), (tag, post_id)
            assert config["copyright"] in post["copyright_tags"].split(), (tag, post_id)
            assert "official_art" in meta and "1girl" in general, (tag, post_id)
            if status == "candidate_constructed_form":
                assert tag != evidence_tag and row["is_danbooru_tag"] == "False" and row["label"] != "supplemental search", tag
            else:
                assert tag == evidence_tag, tag
            tags = row["visual_tags"].split()
            if tag in prior and prior[tag]["url"].rsplit("/", 1)[-1] == post_id:
                tags = [part.strip().replace(" ", "_") for part in prior[tag]["core_tags"].split(",")][1:]
            assert tags and len(tags) == len(set(tags)) and set(tags) <= set(general), (tag, post_id)
            selected.append({
                "character": tag, "copyright": config["copyright"],
                "trigger": tag.replace("_", " ") + ", " + config["copyright"].replace("_", " "),
                "core_tags": ", ".join(["1girl"] + [part.replace("_", " ") for part in tags]),
                "url": post["url"],
            })
            reason = "included_exact_form_post" if status == "candidate" else "included_official_name_from_matching_wiki_form"
        else:
            reason = (
                "excluded_alias_covered_by_specific_forms" if status == "redundant_alias" else
                "excluded_companion_not_female_character" if status == "companion_not_scope" else
                "excluded_no_independent_form_tag" if status == "official_name_without_tag" else
                "excluded_no_exact_tagged_post" if status == "no_exact_tagged_post" else
                "excluded_source_or_visual_evidence_insufficient"
            )
        audit.append({
            "character": tag, "decision": "included" if reason.startswith("included") else "excluded",
            "reason": reason, "manifest_source": row["manifest_source"], "source_id": row["source_id"],
            "post_id": post_id, "wiki_title": row["wiki_title"], "label": row["label"],
            "source_tier": row["source_tier"], "candidate_count": row["candidate_count"],
            "url": row["url"], "source": row["source"],
        })
    by_source = defaultdict(list)
    for row in selected:
        by_source[row["url"]].append(row["character"])
    ambiguous = {
        tag for url, tags in by_source.items() if len(tags) > 1
        for tag in tags
        if len({next(a["source_id"] for a in audit if a["character"] == member) for member in tags}) > 1
    }
    if ambiguous:
        selected = [row for row in selected if row["character"] not in ambiguous]
        for row in audit:
            if row["character"] in ambiguous:
                row["decision"], row["reason"] = "excluded", "excluded_shared_post_subject_ambiguous"
    assert len({row["character"] for row in selected}) == len(selected)
    selected.sort(key=lambda row: row["character"])
    write_csv(directory / "reviewed.csv", REVIEWED_FIELDS, selected)
    write_csv(directory / "audit.csv", list(audit[0]), audit)

    selected_ids = {row["url"].rsplit("/", 1)[-1] for row in selected}
    image_audit = {}
    for row in inventory:
        key = (row["image_type"], row["image_id"] or row["wiki_title"])
        if key in image_audit:
            image_audit[key]["wiki_titles"] += ";" + row["wiki_title"]
            continue
        if not row["image_id"]:
            decision = "coverage_gap_missing_wiki_or_appearance"
        elif row["image_type"] == "asset":
            decision = "excluded_asset_without_post_tags"
        elif row["image_id"] in selected_ids:
            decision = "included_supporting_post"
        else:
            decision = "excluded_no_qualifying_form_evidence"
        image_audit[key] = {
            "image_type": row["image_type"], "image_id": row["image_id"],
            "status": row["status"], "wiki_titles": row["wiki_title"],
            "label": row["label"], "decision": decision,
            "url": row["url"], "source": row["source"].strip(),
        }
    write_csv(directory / "image_audit.csv", list(next(iter(image_audit.values()))), sorted(
        image_audit.values(), key=lambda row: (row["image_type"], int(row["image_id"] or 0), row["wiki_titles"]),
    ))
    print(pack, "posts", len(post_contexts), "forms", len(review), "included", len(selected),
          "excluded", dict(Counter(row["reason"] for row in audit if row["decision"] == "excluded")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", choices=sorted(CONFIG), required=True)
    curate(parser.parse_args().pack)
