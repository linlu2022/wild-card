"""One-off Danbooru Wiki Appearance inventory for the ZZZ wildcard batch."""

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = "https://danbooru.donmai.us"
HEADERS = {"User-Agent": "wild-card-curation/1.0 (personal research)"}
ENTRY = re.compile(r"^\s*\*\s*!(post|asset)\s*#(\d+)([^\r\n]*)", re.M | re.I)
LINK = re.compile(r"\[\[([^]|]+)(?:\|([^]]*))?\]\]")


def get_json(path):
    response = requests.get(BASE + path, headers=HEADERS, timeout=25)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def wiki(title):
    return get_json("/wiki_pages/" + quote(title, safe="()_'_") + ".json")


def inventory_one(title):
    page = wiki(title)
    if page is None:
        return []
    rows = []
    for kind, image_id, raw in ENTRY.findall(page["body"]):
        link = LINK.search(raw)
        form_title = link.group(1).strip() if link else ""
        label = link.group(2).strip() if link and link.group(2) else raw.lstrip(": ").strip()
        rows.append({
            "wiki_title": title,
            "wiki_updated_at": page["updated_at"],
            "image_type": kind.lower(),
            "image_id": image_id,
            "form_title": form_title,
            "label": label,
            "wiki_url": BASE + "/wiki_pages/" + quote(title, safe="()_'_"),
        })
    return rows


def image_one(key):
    kind, image_id = key
    if kind == "asset":
        item = get_json(f"/media_assets/{image_id}.json")
        return {"md5": item["md5"] if item else "", "url": BASE + f"/media_assets/{image_id}"}
    item = get_json(f"/posts/{image_id}.json")
    if item is None:
        return {"error": "post_missing"}
    return {
        "source": item.get("source", ""),
        "general_tags": item.get("tag_string_general", ""),
        "character_tags": item.get("tag_string_character", ""),
        "copyright_tags": item.get("tag_string_copyright", ""),
        "meta_tags": item.get("tag_string_meta", ""),
        "parent_id": item.get("parent_id") or "",
        "md5": item.get("md5", ""),
        "url": BASE + f"/posts/{image_id}",
    }


def main():
    names = [line.partition(",")[0] for line in (ROOT / "wildcards/zenless_zone_zero_girls_name.txt").read_text(encoding="utf-8").splitlines()]
    with ThreadPoolExecutor(max_workers=4) as pool:
        nested = list(pool.map(inventory_one, names))
    rows = [row for group in nested for row in group]
    keys = sorted({(row["image_type"], row["image_id"]) for row in rows})
    with ThreadPoolExecutor(max_workers=4) as pool:
        images = dict(zip(keys, pool.map(image_one, keys)))
    for row in rows:
        row.update(images[(row["image_type"], row["image_id"])])
    rows.sort(key=lambda row: (row["wiki_title"], row["image_type"], int(row["image_id"])))
    fields = ["wiki_title", "wiki_updated_at", "image_type", "image_id", "form_title", "label", "wiki_url", "url", "source", "character_tags", "copyright_tags", "general_tags", "meta_tags", "parent_id", "md5", "error"]
    HERE.mkdir(parents=True, exist_ok=True)
    with (HERE / "inventory.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"names": len(names), "entries": len(rows), "unique_images": len(keys), "posts": sum(row["image_type"] == "post" for row in rows), "assets": sum(row["image_type"] == "asset" for row in rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
