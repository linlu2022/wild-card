"""Inventory Danbooru character Wiki Appearance images for one wildcard batch.

This gathers candidates and provenance; it does not decide gender, official status,
subject attribution, or which general tags should enter a prompt.
"""

import argparse
import csv
import hashlib
import json
import re
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlencode

import requests


BASE = "https://danbooru.donmai.us"
HEADERS = {"User-Agent": "wild-card-curation/1.0 (personal research)"}
CACHE_DIR = Path(tempfile.gettempdir()) / "wild-card-danbooru-wiki-cache"
MIN_INTERVAL = 0.65
RATE_LOCK = threading.Lock()
LAST_REQUEST = 0.0
ENTRY = re.compile(r"^\s*\*\s*!(post|asset)\s*#(\d+)([^\r\n]*)", re.M | re.I)
LINK = re.compile(r"\[\[([^]|]+)(?:\|([^]]*))?\]\]")
FIELDS = [
    "wiki_title", "wiki_updated_at", "status", "image_type", "image_id",
    "form_title", "label", "wiki_url", "form_wiki_url", "form_wiki_status",
    "form_wiki_updated_at", "form_description", "url", "source",
    "character_tags", "copyright_tags", "general_tags", "meta_tags", "md5",
]


def get_json(path):
    global LAST_REQUEST
    cache_path = CACHE_DIR / (hashlib.sha256(path.encode("utf-8")).hexdigest() + ".json")
    if cache_path.is_file():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    last_error = None
    for attempt in range(5):
        with RATE_LOCK:
            remaining = LAST_REQUEST + MIN_INTERVAL - time.monotonic()
            if remaining > 0:
                time.sleep(remaining)
            LAST_REQUEST = time.monotonic()
        try:
            response = requests.get(BASE + path, headers=HEADERS, timeout=25)
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(min(30.0, 2.0 * (2 ** attempt)))
            continue
        if response.status_code == 404:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_path.write_text("null", encoding="utf-8")
            return None
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "")
            delay = min(30.0, float(retry_after)) if retry_after.replace(".", "", 1).isdigit() else min(30.0, 2.0 * (2 ** attempt))
            time.sleep(delay)
            continue
        if 500 <= response.status_code < 600:
            last_error = RuntimeError(f"HTTP {response.status_code}")
            time.sleep(min(30.0, 2.0 * (2 ** attempt)))
            continue
        response.raise_for_status()
        result = response.json()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(f".{threading.get_ident()}.tmp")
        temporary.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        temporary.replace(cache_path)
        return result
    raise RuntimeError(f"Danbooru request failed after 5 attempts: {path}: {last_error}")


def wiki_url(title):
    return BASE + "/wiki_pages/" + quote(title.replace(" ", "_"), safe="()_'")


def candidate_titles(path):
    seen = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        title = line.partition(",")[0].strip()
        if not title or title.startswith("#") or title in {"character", "wiki_title"}:
            continue
        if title not in seen:
            seen.add(title)
            yield title


def appearance_section(body):
    section = []
    heading_level = None
    for line in body.splitlines():
        heading = re.match(r"^h([1-6])\.\s*(.+?)\s*$", line, re.I)
        if heading:
            level = int(heading.group(1))
            if heading_level is not None and level <= heading_level:
                break
            if heading_level is None and heading.group(2).casefold() == "appearance":
                heading_level = level
            continue
        if heading_level is not None:
            section.append(line)
    return "\n".join(section)


def read_wiki(title):
    url = wiki_url(title)
    page = get_json(url[len(BASE):] + ".json")
    base = {"wiki_title": title, "wiki_url": url}
    if page is None:
        return [{**base, "status": "wiki_missing"}]
    base["wiki_updated_at"] = page.get("updated_at", "")
    appearances = []
    for kind, image_id, raw in ENTRY.findall(appearance_section(page.get("body", ""))):
        link = LINK.search(raw)
        appearances.append({
            **base,
            "status": "candidate",
            "image_type": kind.lower(),
            "image_id": image_id,
            "form_title": link.group(1).strip() if link else "",
            "label": link.group(2).strip() if link and link.group(2) else raw.lstrip(": ").strip(),
        })
    return appearances or [{**base, "status": "appearance_missing"}]


def read_form(title):
    url = wiki_url(title)
    page = get_json(url[len(BASE):] + ".json")
    if page is None:
        return {"form_wiki_url": url, "form_wiki_status": "missing"}
    description = re.split(r"(?m)^h[1-6]\.\s+", page.get("body", ""), maxsplit=1)[0].strip()
    description = "\n".join(line.rstrip() for line in description.splitlines())
    return {
        "form_wiki_url": url,
        "form_wiki_status": "found",
        "form_wiki_updated_at": page.get("updated_at", ""),
        "form_description": description[:600],
    }


def post_metadata(image_id, item):
    if item is None:
        return {"status": "post_missing", "url": BASE + f"/posts/{image_id}"}
    return {
        "status": "candidate",
        "source": item.get("source", ""),
        "character_tags": item.get("tag_string_character", ""),
        "copyright_tags": item.get("tag_string_copyright", ""),
        "general_tags": item.get("tag_string_general", ""),
        "meta_tags": item.get("tag_string_meta", ""),
        "md5": item.get("md5", ""),
        "url": BASE + f"/posts/{image_id}",
    }


def read_post_batch(image_ids):
    tags = "id:" + ",".join(image_ids) + " order:custom"
    path = "/posts.json?" + urlencode({
        "tags": tags, "limit": str(len(image_ids)),
        "only": "id,source,tag_string_character,tag_string_copyright,tag_string_general,tag_string_meta,md5",
    })
    items = get_json(path)
    if not isinstance(items, list):
        raise RuntimeError(f"Danbooru post batch returned unexpected data: {image_ids[:3]}")
    by_id = {str(item["id"]): item for item in items}
    return {image_id: post_metadata(image_id, by_id.get(image_id)) for image_id in image_ids}


def main():
    global CACHE_DIR, MIN_INTERVAL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--names", type=Path, required=True, help="One Wiki title per line, or name-pack lines starting with the title")
    parser.add_argument("--output", type=Path, required=True, help="Candidate inventory CSV")
    parser.add_argument("--max-pages", type=int, default=500, help="Maximum number of Wiki pages to request (default: 500)")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent requests, 1 to 4 (default: 4)")
    parser.add_argument("--request-interval", type=float, default=0.65, help="Minimum seconds between uncached requests (default: 0.65)")
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR, help="External cache for successful API responses")
    parser.add_argument("--skip-form-wikis", action="store_true", help="Keep form titles but skip separate form-Wiki requests")
    parser.add_argument("--post-batch-size", type=int, default=50, help="Post IDs per tag-only API request (default: 50)")
    parser.add_argument("--refresh", action="store_true", help="Replace an existing inventory with new API data")
    args = parser.parse_args()
    if not 1 <= args.workers <= 4 or not 1 <= args.max_pages <= 5000:
        parser.error("--workers must be 1..4 and --max-pages must be 1..5000")
    if args.request_interval < 0.3:
        parser.error("--request-interval must be at least 0.3 seconds")
    if not 1 <= args.post_batch_size <= 100:
        parser.error("--post-batch-size must be 1..100")
    CACHE_DIR = args.cache_dir
    MIN_INTERVAL = args.request_interval
    if args.output.exists() and not args.refresh:
        parser.error(f"{args.output} already exists; reuse it or pass --refresh")

    titles = list(candidate_titles(args.names))
    selected = titles[:args.max_pages]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        groups = list(pool.map(read_wiki, selected))
    rows = [row for group in groups for row in group]
    form_titles = sorted({row["form_title"] for row in rows if row.get("form_title")})
    if args.skip_form_wikis:
        forms = {
            title: {"form_wiki_url": wiki_url(title), "form_wiki_status": "not_queried"}
            for title in form_titles
        }
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            forms = dict(zip(form_titles, pool.map(read_form, form_titles)))
    keys = sorted({(row["image_type"], row["image_id"]) for row in rows if row.get("image_id")})
    post_ids = sorted((image_id for kind, image_id in keys if kind == "post"), key=int)
    batches = [post_ids[index:index + args.post_batch_size] for index in range(0, len(post_ids), args.post_batch_size)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        batch_results = list(pool.map(read_post_batch, batches))
    images = {("asset", image_id): {
        "status": "asset_no_post_tags", "url": BASE + f"/media_assets/{image_id}",
    } for kind, image_id in keys if kind == "asset"}
    for result in batch_results:
        images.update({("post", image_id): metadata for image_id, metadata in result.items()})
    for row in rows:
        if row.get("form_title"):
            row.update(forms[row["form_title"]])
        if row.get("image_id"):
            row.update(images[(row["image_type"], row["image_id"])])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Queried {len(selected)}/{len(titles)} Wiki titles; {len(rows)} inventory rows; "
          f"{sum(row.get('status') == 'wiki_missing' for row in rows)} missing Wikis; "
          f"{sum(row.get('status') == 'appearance_missing' for row in rows)} without Appearance; "
          f"{len(titles) - len(selected)} unqueried by cap. Output: {args.output}")


if __name__ == "__main__":
    main()
