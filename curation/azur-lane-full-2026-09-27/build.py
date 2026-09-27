"""Export only source-backed Azur Lane forms selected from review_queue.csv."""

import csv
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIELDS = ["character", "copyright", "trigger", "core_tags", "url"]
ACCEPTED_TIERS = {"game_asset", "game_file_label", "publisher", "game_mirror"}
GAME_RECORD_OVERRIDES = {
    "alsace_(heat_beating_summer_sacrament)_(azur_lane)": "80503/805031",
    "goetz_von_berlichingen_(azur_lane)": "40507/405070",
    "honolulu_(summer_accident?!)_(azur_lane)": "10212/102122",
    'implacable_(shepherd_of_the_"lost")_(azur_lane)': "20707/207071",
    "le_malin_(muse)_(azur_lane)": "90112/901120",
}
TB_RELEASE = "https://azurlane.yo-star.com/news/2024/02/05/maintenance-notice-2-6-12-a-m-utc-7-2/"


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


def main():
    review = read_csv(HERE / "review_queue.csv")
    assert review, "run prepare_review.py first"
    posts = {}
    for path in (HERE / "inventory.csv", HERE / "supplemental.csv"):
        for post in read_csv(path):
            if post.get("image_id") and post.get("url", "").startswith("https://danbooru.donmai.us/posts/"):
                posts.setdefault(post["image_id"], post)
    old = {
        row["character"]: row
        for row in read_csv(ROOT / "curation/wiki-appearance-2026-09-27/azur_lane_reviewed.csv")
    }
    included = []
    audit = []
    for row in review:
        tag = row["character"]
        post_id = row["post_id"]
        effective_source_id = row["source_id"] or GAME_RECORD_OVERRIDES.get(tag, "")
        release_crosscheck = (TB_RELEASE if tag == "tb_(azur_lane)" else
                              "https://github.com/Fernando2603/AzurLane/blob/main/ship_skin.json" if tag in GAME_RECORD_OVERRIDES else "")
        prior_reviewed = tag in old and old[tag]["url"].rsplit("/", 1)[-1] == post_id
        if row["status"] == "official_name_without_tag":
            reason = "excluded_official_name_without_exact_tagged_image"
        elif row["status"] == "no_exact_tagged_post":
            reason = "excluded_no_exact_tagged_image"
        elif (row["status"] not in {"candidate", "candidate_constructed_form"} or row["source_tier"] not in ACCEPTED_TIERS) and not prior_reviewed:
            reason = "excluded_source_or_visible_tag_evidence_insufficient"
        elif not post_id or post_id not in posts:
            reason = "excluded_missing_post"
        else:
            post = posts[post_id]
            general = post["general_tags"].split()
            meta = post["meta_tags"].split()
            evidence_tag = row["evidence_character_tag"]
            assert evidence_tag in post["character_tags"].split(), (tag, post_id, "character")
            assert "azur_lane" in post["copyright_tags"].split(), (tag, post_id, "copyright")
            assert "official_art" in meta and "1girl" in general, (tag, post_id, "scope")
            assert "released_skin" in row["manifest_source"] or tag in GAME_RECORD_OVERRIDES or tag == "tb_(azur_lane)", tag
            if row["status"] == "candidate_constructed_form":
                assert row["is_danbooru_tag"] == "False" and tag != evidence_tag, tag
                assert row["label"] and row["label"] != "supplemental search", tag
            else:
                assert tag == evidence_tag, tag
            selected = row["visual_tags"].split()
            if prior_reviewed:
                selected = [part.strip().replace(" ", "_") for part in old[tag]["core_tags"].split(",")][1:]
            assert selected and set(selected) <= set(general), (tag, post_id, "selected tags")
            assert len(selected) == len(set(selected)), tag
            included.append({
                "character": tag, "copyright": "azur_lane",
                "trigger": tag.replace("_", " ") + ", azur lane",
                "core_tags": ", ".join(["1girl"] + [part.replace("_", " ") for part in selected]),
                "url": post["url"],
            })
            reason = (
                "included_prior_exact_post_review" if prior_reviewed and row["source_tier"] not in ACCEPTED_TIERS else
                "included_official_name_mapped_by_wiki_skin_label" if row["status"] == "candidate_constructed_form" else
                "included_exact_post_and_game_skin_record" if "released_skin" in row["manifest_source"] else
                "included_exact_post_and_official_source"
            )
        audit.append({
            "character": tag, "decision": "included" if reason.startswith("included") else "excluded",
            "reason": reason, "manifest_source": row["manifest_source"],
            "source_id": effective_source_id, "post_id": post_id,
            "wiki_title": row["wiki_title"], "label": row["label"],
            "evidence_character_tag": row["evidence_character_tag"],
            "release_crosscheck": release_crosscheck,
            "source_tier": row["source_tier"], "candidate_count": row["candidate_count"],
            "url": row["url"], "source": row["source"],
        })

    assert len({row["character"] for row in included}) == len(included)
    used_posts = defaultdict(list)
    for row in included:
        used_posts[row["url"]].append(row["character"])
    shared = {url: tags for url, tags in used_posts.items() if len(tags) > 1}
    audit_by_tag = {row["character"]: row for row in audit}
    for url, tags in shared.items():
        skin_ids = {
            tuple(sorted(part.rsplit("/", 1)[-1] for part in audit_by_tag[tag]["source_id"].split("+") if "/" in part))
            for tag in tags
        }
        assert len(skin_ids) == 1 and next(iter(skin_ids)), (url, tags, skin_ids)
    included.sort(key=lambda row: row["character"])
    write_csv(HERE / "reviewed.csv", FIELDS, included)
    write_csv(HERE / "audit.csv", list(audit[0]), audit)

    selected_by_post = defaultdict(list)
    for row in audit:
        if row["decision"] == "included":
            selected_by_post[row["post_id"]].append(row["character"])
    image_audit = {}
    for row in read_csv(HERE / "inventory.csv"):
        key = (row["image_type"], row["image_id"] or row["wiki_title"])
        if key in image_audit:
            image_audit[key]["wiki_titles"] += ";" + row["wiki_title"]
            image_audit[key]["labels"] += ";" + row["label"]
            continue
        if not row["image_id"]:
            decision = "coverage_gap_missing_wiki_or_appearance"
        elif row["image_type"] == "asset":
            decision = "excluded_asset_without_post_tags"
        elif row["image_id"] in selected_by_post:
            decision = "included_supporting_post"
        else:
            decision = "excluded_no_qualifying_form_evidence"
        image_audit[key] = {
            "image_type": row["image_type"], "image_id": row["image_id"],
            "status": row["status"], "wiki_titles": row["wiki_title"],
            "labels": row["label"], "decision": decision,
            "selected_forms": ";".join(selected_by_post.get(row["image_id"], [])),
            "url": row["url"], "source": row["source"].strip(),
        }
    if image_audit:
        rows = sorted(image_audit.values(), key=lambda row: (row["image_type"], int(row["image_id"] or 0), row["wiki_titles"]))
        write_csv(HERE / "image_audit.csv", list(rows[0]), rows)
    print("included", len(included), "of", len(review), "forms")
    print("excluded", dict(Counter(row["reason"] for row in audit if row["decision"] == "excluded")))
    print("shared exact source posts", len(shared), "examples", list(shared.items())[:10])


if __name__ == "__main__":
    main()
