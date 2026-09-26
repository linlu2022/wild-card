"""Draft and audit a character CSV from Danbooru's public JSON endpoints.

This produces candidates for human review. It never claims semantic verification.
"""

from __future__ import annotations

import argparse
import collections
import concurrent.futures
import csv
import hashlib
import json
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


API = "https://danbooru.donmai.us"
FIELDS = ["character", "copyright", "trigger", "core_tags", "url"]
STOP = set("""
1girl 1boy 1other 2girls 2boys 2others 3girls multiple_girls multiple_boys
multiple_others solo solo_focus group duo siblings twins family official_art
official_alternate_costume alternate_costume highres absurdres lowres commentary
commentary_request symbol-only_commentary translated untranslated bad_id
second-party_source third-party_source artist_name twitter_username
looking_at_viewer looking_away looking_back looking_down looking_up
white_background simple_background black_background transparent_background
grey_background gradient_background outdoors indoors cowboy_shot upper_body
lower_body full_body portrait close-up from_side from_below from_above from_behind
open_mouth closed_mouth smile frown blush sweat tears saliva tongue tongue_out
teeth closed_eyes half-closed_eyes one_eye_closed glaring staring
standing sitting kneeling lying squatting holding arm_up arms_up hand_up hands_up
spread_legs crossed_legs parted_lips dutch_angle head_tilt depth_of_field
english_commentary japanese_commentary chinese_commentary
copyright_notice copyright_name character_name weapon dual_wielding
""".split())
BAD_PATTERNS = [re.compile(x) for x in (
    r"^(\d+(girls?|boys?|others?)|multiple_|solo|source_|artist_|rating:)",
    r"(background|commentary|watermark|signature|text|logo|border|frame)$",
    r"^(holding|sitting|standing|looking|facing|from|on_|in_|at_|against_|covering)_",
    r"(_focus|_shot|_view|_angle|_pose|_expression|_request)$",
)]
BUCKETS = [
    r"(_girl$|_boy$|^animal_ears|_ears$|^furry|_fur$|^horns?$|^wings?$|^tail$|_tail$|^halo$|^elf$|^android$|^robot_girl$|^oni$)",
    r"(_eyes$|_eyelashes$|_pupils$|^eyepatch$|^mole_under_eye$|^heterochromia$)",
    r"(^hair$|_hair$|^hair_|_bangs$|^bangs$|^sidelocks$|^ahoge$|^ponytail$|^twintails?$|^braid$|_braids?$|_bun$|^hime_cut$|^bob_cut$)",
    r"(_breasts?$|^breasts?$|^cleavage$|^mole_|^skin$|^bare_|_shoulders$|^midriff$|^navel$)",
    r"(^shirt$|_shirt$|^skirt$|_skirt$|^dress$|_dress$|^jacket$|_jacket$|^coat$|_coat$|^hoodie$|_hoodie$|^sweater$|_sweater$|^swimsuit$|_swimsuit$|^pants$|_pants$|^shorts$|_shorts$|^gloves$|_gloves$|^thighhighs$|_thighhighs$|^pantyhose$|^socks$|_socks$|^boots$|_boots$|^necktie$|_collar$|^sleeves$|_sleeves$|^uniform$|_uniform$|^apron$|^robe$|_robe$|^cape$|_cape$|^cloak$|_cloak$|^armor$|_armor$)",
    r"(^ribbon$|_ribbon$|^bow$|_bow$|^choker$|_choker$|^hairclip$|^hair_ornament$|^hairband$|^earrings?$|^hat$|_hat$|^glasses$|^necklace$|^jewelry$|^headband$|^headwear$|_headwear$)",
]
BUCKETS = [re.compile(x) for x in BUCKETS]
GENERIC = {
    "animal_ears": re.compile(r"_ears$"),
    "tail": re.compile(r"_tail$"),
    "breasts": re.compile(r"_breasts$"),
    "hair": re.compile(r"_hair$"),
    "gloves": re.compile(r"_gloves$"),
    "skirt": re.compile(r"_skirt$"),
    "shirt": re.compile(r"_shirt$"),
    "dress": re.compile(r"_dress$"),
    "jacket": re.compile(r"_jacket$"),
}


class Client:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._next_request = 0.0
        self._local = threading.local()

    def get(self, endpoint: str, params: dict) -> object:
        key = hashlib.sha256(json.dumps([endpoint, params], sort_keys=True).encode()).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        if not hasattr(self._local, "session"):
            self._local.session = requests.Session()
            self._local.session.headers.update({"User-Agent": "wild-card character curation/0.1 (public data)"})
        error = None
        for attempt in range(4):
            with self._lock:
                delay = max(0, self._next_request - time.monotonic())
                self._next_request = max(self._next_request, time.monotonic()) + 0.25
            if delay:
                time.sleep(delay)
            try:
                response = self._local.session.get(API + endpoint, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict) and data.get("success") is False:
                    raise ValueError(data.get("message", "API returned success=false"))
                tmp = path.with_suffix(".tmp")
                tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                tmp.replace(path)
                return data
            except (requests.RequestException, ValueError) as exc:
                error = exc
                time.sleep(min(2 ** attempt, 8))
        raise RuntimeError(f"{endpoint} {params}: {error}")


def related_frequencies(data: dict) -> dict[str, float]:
    return {x["tag"]["name"]: float(x.get("frequency") or 0) for x in data.get("related_tags", [])}


def choose_tags(posts: list[dict], character_names: set[str], copyright_tag: str) -> list[str]:
    counts = collections.Counter(tag for post in posts for tag in post["tag_string_general"].split())
    candidates = [(tag, count / len(posts)) for tag, count in counts.items()
                  if tag not in STOP and tag not in character_names and tag != copyright_tag
                  and not any(pattern.search(tag) for pattern in BAD_PATTERNS)
                  and any(pattern.search(tag) for pattern in BUCKETS)]
    candidates.sort(key=lambda item: (-item[1], item[0]))
    floor = 0.20
    for probe in (0.50, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20):
        if sum(rate >= probe for _, rate in candidates) >= 8:
            floor = probe
            break
    candidates = [(tag, rate) for tag, rate in candidates if rate >= floor][:40]
    names = {tag for tag, _ in candidates}
    selected = []
    for tag, rate in candidates:
        bucket = next((i for i, pattern in enumerate(BUCKETS) if pattern.search(tag)), len(BUCKETS))
        if (bucket == 4 and rate < 0.55) or (bucket == 5 and rate < 0.35):
            continue
        if tag in GENERIC and any(other != tag and GENERIC[tag].search(other) for other in names):
            continue
        if tag in {"animal_ears", "tail", "furry", "furry_female"} and rate < 0.35:
            continue
        selected.append((tag, rate))
    def sort_key(item: tuple[str, float]) -> tuple[int, float, str]:
        tag, rate = item
        bucket = next((i for i, pattern in enumerate(BUCKETS) if pattern.search(tag)), len(BUCKETS))
        return bucket, -rate, tag
    return [tag for tag, _ in sorted(selected, key=sort_key)[:20]]


def assess_gender(freq: dict[str, float], solo: list[dict]) -> tuple[str, str]:
    g, b = freq.get("1girl", 0), freq.get("1boy", 0)
    fm, ff = freq.get("furry_male", 0), freq.get("furry_female", 0)
    mf = freq.get("male_focus", 0)
    if (fm > ff + 0.20 and fm > 0.25) or mf > 0.15 or b > g + 0.10:
        return "male", "broader posts favor male tags"
    if len(solo) >= 3:
        solo_g = sum("1girl" in p["tag_string_general"].split() for p in solo) / len(solo)
        if solo_g < 0.50 and ff < 0.50:
            return "unknown", "single-subject posts do not support female"
        if solo_g >= 0.50 and g >= b:
            return "female", "broader and single-character evidence agree"
    if g >= 0.60 and g >= b + 0.30 and mf < 0.05 and fm <= ff:
        return "female", "strong broader co-occurrence; sparse solo art"
    return "unknown", "gender evidence insufficient or mixed"


def isolated_subject(posts: list[dict], name: str) -> tuple[list[dict], str | None, str]:
    exact = [p for p in posts if set(p["tag_string_character"].split()) == {name}]
    if len(exact) >= 5:
        return exact, None, "single-character"
    root = name.split("_(", 1)[0]
    variants = [p for p in posts
                if name in p["tag_string_character"].split()
                and all(tag == name or tag.startswith(root + "_(")
                        for tag in p["tag_string_character"].split())
                and "1girl" in p["tag_string_general"].split()
                and "1boy" not in p["tag_string_general"].split()
                and "2girls" not in p["tag_string_general"].split()
                and "multiple_girls" not in p["tag_string_general"].split()]
    if len(variants) >= 5:
        return variants, None, "variant-cotag"
    co_tags = collections.Counter(tag for p in posts
                                   for tag in set(p["tag_string_character"].split()) - {name})
    if not co_tags:
        return exact, None, "single-character"
    alias, count = co_tags.most_common(1)[0]
    if count < 5 or count < 0.70 * len(posts):
        return exact, None, "single-character"
    alias_posts = [p for p in posts
                   if set(p["tag_string_character"].split()) == {name, alias}
                   and "1girl" in p["tag_string_general"].split()
                   and "1boy" not in p["tag_string_general"].split()
                   and "2girls" not in p["tag_string_general"].split()
                   and "multiple_girls" not in p["tag_string_general"].split()]
    if len(alias_posts) >= 5:
        return alias_posts, alias, "alias-cotag"
    return exact, None, "single-character"


def inspect_candidate(client: Client, candidate: dict, copyright_tag: str,
                      all_names: set[str], excluded_copyrights: set[str]) -> dict:
    name = candidate["tag"]["name"]
    report = {"character": name, "candidate_frequency": candidate.get("frequency"),
              "candidate_post_count": candidate["tag"].get("post_count")}
    try:
        related = client.get("/related_tag.json", {"query": name, "category": 0, "limit": 150})
        freq = related_frequencies(related)
        reports = []
        # Sample a recent and an older page; one event's costume art can dominate page 1.
        for page in (1, 3):
            posts = client.get("/posts.json", {"tags": f"{name} official_art", "limit": 100,
                                                "page": page,
                                                "only": "id,tag_string_general,tag_string_character,tag_string_copyright"})
            if not isinstance(posts, list):
                raise ValueError("posts endpoint returned a non-list")
            reports.extend(posts)
            target = [p for p in reports
                      if copyright_tag in p["tag_string_copyright"].split()
                      and not excluded_copyrights.intersection(p["tag_string_copyright"].split())]
            isolated, alias, relation = isolated_subject(target, name)
            if len(posts) < 100:
                break
        solo = [p for p in target if set(p["tag_string_character"].split()) == {name}]
        report.update({"official_scanned": len(reports), "official_copyright": len(target),
                       "single_character_official": len(solo),
                       "gender_frequencies": {x: round(freq.get(x, 0), 3) for x in
                                              ("1girl", "1boy", "furry_male", "furry_female", "male_focus")}})
        appearance_posts = isolated
        appearance_label = relation + " official art"
        if alias:
            report["possible_alias"] = alias
        if len(isolated) < 5:
            fan_posts = client.get("/posts.json", {"tags": f"{name} {copyright_tag}", "limit": 100,
                                                   "only": "id,tag_string_general,tag_string_character,tag_string_copyright"})
            fan_solo, fan_alias, fan_relation = isolated_subject(
                [p for p in fan_posts if copyright_tag in p["tag_string_copyright"].split()
                 and not excluded_copyrights.intersection(p["tag_string_copyright"].split())], name)
            report["single_character_general_posts"] = len(fan_solo)
            if len(fan_solo) >= 5:
                appearance_posts = fan_solo
                appearance_label = fan_relation + " all-post fallback"
                if fan_alias:
                    report["possible_alias"] = fan_alias
        gender, gender_reason = assess_gender(freq, appearance_posts)
        report.update({"gender": gender, "gender_reason": gender_reason})
        if len(target) < 3:
            report["status"] = "review: fewer than 3 copyright-matched official posts"
            return report
        if gender != "female":
            report["status"] = "review: gender not confirmed female" if gender == "unknown" else "excluded: male"
            return report
        if len(appearance_posts) >= 5:
            source = appearance_posts
        elif len(solo) >= 1:
            source = target
            appearance_label = "group-art fallback"
        else:
            report["status"] = "review: no single-character appearance evidence"
            return report
        report["appearance_source"] = appearance_label
        report["appearance_denominator"] = len(source)
        tags = choose_tags(source, all_names, copyright_tag)
        report["core_tags"] = tags
        min_tags = 3 if appearance_label.endswith("official art") and len(source) >= 5 else 5
        if len(tags) < min_tags:
            report["status"] = f"review: fewer than {min_tags} usable appearance tags"
            return report
        report["status"] = "draft"
        return report
    except Exception as exc:
        report["status"] = "error"
        report["error"] = str(exc)
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copyright", required=True)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--audit-json", required=True, type=Path)
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--min-frequency", type=float, default=0.0005)
    parser.add_argument("--candidate-limit", type=int, default=500)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--allow-pattern", help="Optional regex for narrow character families")
    parser.add_argument("--exclude-copyright", action="append", default=[],
                        help="Ignore posts also carrying this copyright (repeatable)")
    args = parser.parse_args()
    client = Client(args.cache_dir)
    try:
        data = client.get("/related_tag.json", {"query": args.copyright, "category": 4,
                                                 "limit": args.candidate_limit})
        candidates = data["related_tags"]
    except Exception as exc:
        print(f"Candidate discovery failed: {exc}", file=sys.stderr)
        return 1
    if args.allow_pattern:
        pattern = re.compile(args.allow_pattern)
        candidates = [x for x in candidates if pattern.search(x["tag"]["name"])]
    candidates = [x for x in candidates if x.get("frequency", 0) >= args.min_frequency]
    all_names = {x["tag"]["name"] for x in candidates}
    print(f"{args.copyright}: inspecting {len(candidates)} candidates", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(inspect_candidate, client, item, args.copyright, all_names,
                               set(args.exclude_copyright))
                   for item in candidates]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(future.result())
            if i % 25 == 0 or i == len(candidates):
                accepted = sum(x["status"] == "draft" for x in results)
                print(f"{args.copyright}: {i}/{len(candidates)}, draft={accepted}", flush=True)
    results.sort(key=lambda x: x["character"])
    rows = []
    for x in results:
        if x["status"] == "draft":
            name = x["character"]
            rows.append([name, args.copyright,
                         f"{name.replace('_', ' ')}, {args.copyright.replace('_', ' ')}",
                         ", ".join(["1girl", *(tag.replace("_", " ") for tag in x["core_tags"])]),
                         f"{API}/posts?tags={quote(name, safe='')}"])
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(FIELDS)
        writer.writerows(rows)
    args.audit_json.parent.mkdir(parents=True, exist_ok=True)
    audit = {"copyright": args.copyright, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
             "candidate_count": len(candidates),
             "candidate_source": f"{API}/related_tag.json?query={args.copyright}&category=4",
             "candidate_limit": args.candidate_limit, "min_frequency": args.min_frequency,
             "excluded_copyrights": args.exclude_copyright,
             "draft_count": len(rows), "status_counts": dict(collections.Counter(x["status"] for x in results)),
             "characters": results}
    args.audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{args.copyright}: wrote {len(rows)} draft rows; review {args.audit_json}", flush=True)
    return 0 if all(x["status"] != "error" for x in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
