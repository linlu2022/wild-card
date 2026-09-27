"""Find tagged official-art posts for name tags missed by Wiki Appearance links.

Public Danbooru API responses remain in the collector's external cache. This
file saves only compact candidate evidence for later subject/source review.
"""

import argparse
import csv
import sys
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / ".claude/skills/curate-character-wildcards/scripts"))
import collect_wiki_appearance as wiki

FIELDS = [
    "searched_tag", "image_id", "url", "created_at", "source",
    "character_tags", "copyright_tags", "general_tags", "meta_tags",
    "query_returned", "query_limit", "status",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, help="Optional one-tag-per-line rescue search list")
    parser.add_argument("--output", type=Path, default=HERE / "supplemental.csv")
    args = parser.parse_args()
    names = {
        line.partition(",")[0].strip()
        for line in (ROOT / "wildcards/blue_archive_girls_name.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    original = list(csv.DictReader((HERE / "inventory.csv").open(encoding="utf-8", newline="")))
    found = {
        tag
        for row in original
        if row["image_type"] == "post"
        and "blue_archive" in row["copyright_tags"].split()
        and "official_art" in row["meta_tags"].split()
        and "1girl" in row["general_tags"].split()
        for tag in row["character_tags"].split()
        if tag in names
    }
    missing = sorted(
        {line.strip() for line in args.targets.read_text(encoding="utf-8").splitlines() if line.strip()}
        if args.targets else names - found
    )
    out = []
    for number, tag in enumerate(missing, 1):
        query = urlencode({"tags": tag + " official_art", "limit": "100"})
        posts = wiki.get_json("/posts.json?" + query) or []
        for post in posts:
            characters = post.get("tag_string_character", "").split()
            copyrights = post.get("tag_string_copyright", "").split()
            if tag not in characters or "blue_archive" not in copyrights:
                continue
            out.append({
                "searched_tag": tag, "image_id": post["id"],
                "url": wiki.BASE + f"/posts/{post['id']}",
                "created_at": post.get("created_at", ""),
                "source": post.get("source", ""),
                "character_tags": " ".join(characters),
                "copyright_tags": " ".join(copyrights),
                "general_tags": post.get("tag_string_general", ""),
                "meta_tags": post.get("tag_string_meta", ""),
                "query_returned": len(posts), "query_limit": 100,
                "status": "candidate" if "1girl" in post.get("tag_string_general", "").split() else "not_1girl",
            })
        print(f"{number}/{len(missing)} {tag}: {len(posts)} results", flush=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    print(f"Searched {len(missing)} missing tags; saved {len(out)} matching candidates")


if __name__ == "__main__":
    main()
