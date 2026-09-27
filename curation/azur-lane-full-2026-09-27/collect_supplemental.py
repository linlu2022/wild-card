"""Search exact tagged posts for Azur Lane forms absent from Wiki Appearance.

Writes each query immediately so an interrupted large run can resume without
repeating successful API calls. Raw API responses remain in the external cache.
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


def read_csv(path):
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-queries", type=int, default=3000)
    parser.add_argument("--interval", type=float, default=0.8)
    args = parser.parse_args()
    if args.interval < 0.3:
        parser.error("--interval must be at least 0.3 seconds")
    wiki.MIN_INTERVAL = args.interval

    queue = read_csv(HERE / "review_queue.csv")
    targets = [
        row["character"] for row in queue
        if row["is_danbooru_tag"] == "True"
        and row["status"] != "candidate"
        and "released_skin" in row["manifest_source"]
    ]
    log_path = HERE / "search_log.csv"
    searched = {row["searched_tag"] for row in read_csv(log_path)}
    remaining = [tag for tag in targets if tag not in searched][:args.max_queries]
    post_path = HERE / "supplemental.csv"
    post_exists = post_path.is_file()
    log_exists = log_path.is_file()
    with post_path.open("a", encoding="utf-8", newline="") as post_stream, log_path.open("a", encoding="utf-8", newline="") as log_stream:
        writer = csv.DictWriter(post_stream, fieldnames=FIELDS, lineterminator="\n")
        logger = csv.DictWriter(log_stream, fieldnames=["searched_tag", "query_returned", "matching_posts"], lineterminator="\n")
        if not post_exists:
            writer.writeheader()
        if not log_exists:
            logger.writeheader()
        for number, tag in enumerate(remaining, 1):
            path = "/posts.json?" + urlencode({"tags": tag + " official_art", "limit": "100"})
            posts = wiki.get_json(path) or []
            matched = 0
            for post in posts:
                characters = post.get("tag_string_character", "").split()
                copyrights = post.get("tag_string_copyright", "").split()
                if tag not in characters or "azur_lane" not in copyrights:
                    continue
                general = post.get("tag_string_general", "")
                writer.writerow({
                    "searched_tag": tag, "image_id": post["id"],
                    "url": wiki.BASE + f"/posts/{post['id']}",
                    "created_at": post.get("created_at", ""),
                    "source": post.get("source", ""),
                    "character_tags": " ".join(characters),
                    "copyright_tags": " ".join(copyrights),
                    "general_tags": general,
                    "meta_tags": post.get("tag_string_meta", ""),
                    "query_returned": len(posts), "query_limit": 100,
                    "status": "candidate" if "1girl" in general.split() else "not_1girl",
                })
                matched += 1
            post_stream.flush()
            logger.writerow({"searched_tag": tag, "query_returned": len(posts), "matching_posts": matched})
            log_stream.flush()
            if number % 25 == 0 or number == len(remaining):
                print(f"searched {number}/{len(remaining)}; latest {tag}: {matched} matching posts", flush=True)
    print(f"Complete: {len(remaining)} new queries; {len([tag for tag in targets if tag not in searched]) - len(remaining)} still unqueried")


if __name__ == "__main__":
    main()
