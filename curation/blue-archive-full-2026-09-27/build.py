"""Finalize the evidence-backed Blue Archive appearance pack from review_queue.csv."""

import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STRONG = {"game_asset", "publisher", "game_mirror"}
ELIGIBLE = {"candidate_released", "candidate_npc_or_story"}
FIELDS = ["character", "copyright", "trigger", "core_tags", "url"]
RELEASE_CROSSCHECK = {
    "asuna_(school_uniform)_(blue_archive)": (
        "5828043", "https://bluearchive.wiki/wiki/Asuna_(School_Uniform)"
    ),
}


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    review = read_csv(HERE / "review_queue.csv")
    old = {row["character"]: row for row in read_csv(ROOT / "curation/wiki-appearance-2026-09-27/blue_archive_reviewed.csv")}
    all_posts = {}
    for path in (HERE / "inventory.csv", HERE / "supplemental.csv", HERE / "rescue.csv"):
        for row in read_csv(path):
            if row["image_id"] and row["url"].startswith("https://danbooru.donmai.us/posts/"):
                all_posts.setdefault(row["image_id"], row)

    included = []
    audit = []
    for row in review:
        tag = row["character"]
        evidence_id = row["post_id"]
        status = row["status"]
        tier = row["source_tier"]
        crosscheck = RELEASE_CROSSCHECK.get(tag)
        manually_verified = bool(crosscheck and crosscheck[0] == evidence_id)
        if status == "excluded_external_collaboration":
            decision, reason = "excluded", "external collaboration design; no in-game release evidence"
        elif status == "no_tagged_post":
            decision, reason = "excluded", "no exact tagged post with official-art and single-girl evidence"
        elif (status not in ELIGIBLE or tier not in STRONG) and not manually_verified:
            decision, reason = "excluded", "original source or in-work form evidence insufficient"
        elif not evidence_id:
            decision, reason = "excluded", "no exact source post"
        else:
            post = all_posts[evidence_id]
            chars = post["character_tags"].split()
            general = post["general_tags"].split()
            meta = post["meta_tags"].split()
            assert tag in chars, (tag, evidence_id, "character")
            assert "blue_archive" in post["copyright_tags"].split(), (tag, evidence_id, "copyright")
            assert "official_art" in meta and "1girl" in general, (tag, evidence_id, "scope")
            selected_tags = row["visual_tags"].split()
            if tag in old and old[tag]["url"].rsplit("/", 1)[-1] == evidence_id:
                selected_tags = [part.strip().replace(" ", "_") for part in old[tag]["core_tags"].split(",")][1:]
            assert selected_tags and set(selected_tags) <= set(general), (tag, evidence_id, "general tags")
            assert len(selected_tags) == len(set(selected_tags)), tag
            included.append({
                "character": tag, "copyright": "blue_archive",
                "trigger": tag.replace("_", " ") + ", blue archive",
                "core_tags": ", ".join(["1girl"] + [part.replace("_", " ") for part in selected_tags]),
                "url": row["url"],
            })
            decision, reason = "included", (
                "released student plus independent costume page" if manually_verified else
                "released student match" if row["released_student"] == "True" else "game/story image"
            )

        audit.append({
            "character": tag, "in_name_pack": row["in_name_pack"],
            "released_student": row["released_student"],
            "decision": decision, "reason": reason,
            "post_id": evidence_id, "wiki_title": row["wiki_title"],
            "label": row["label"], "source_tier": tier,
            "release_crosscheck": crosscheck[1] if manually_verified else "",
            "candidate_count": row["candidate_count"],
            "url": row["url"], "source": row["source"],
        })
    assert len({row["character"] for row in included}) == len(included)
    included.sort(key=lambda row: row["character"])
    write_csv(HERE / "reviewed.csv", FIELDS, included)
    write_csv(HERE / "audit.csv", list(audit[0]), audit)
    print("included", len(included), "of", len(review), "candidate tags", Counter(row["reason"] for row in audit if row["decision"] == "excluded"))


if __name__ == "__main__":
    main()
