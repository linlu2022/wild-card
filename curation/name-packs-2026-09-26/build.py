"""One-off, dated export of name-only wildcard packs.

The legacy appearance packs supply already selected character tags. Live game
tables add released students and ship skins. Danbooru is used only to choose an
existing tag spelling; a tag's existence is not evidence of official release.
Raw upstream responses are cached outside the repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CACHE = Path(tempfile.gettempdir()) / "wild-card-name-packs-2026-09-26"
SOURCES = {
    "blue_archive_students": "https://schaledb.com/data/en/students.min.json",
    "azur_lane_skins": "https://raw.githubusercontent.com/Fernando2603/AzurLane/main/ship_skin.json",
    "arknights_skins_cn": "https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/master/cn/gamedata/excel/skin_table.json",
    "arknights_skins_en": "https://raw.githubusercontent.com/ArknightsAssets/ArknightsGamedata/master/en/gamedata/excel/skin_table.json",
    "fgo_servants": "https://api.atlasacademy.io/export/JP/basic_servant_lang_en.json",
    "genshin_outfits": "https://genshin-db-api.vercel.app/api/v5/outfits?query=names&matchCategories=true&verboseCategories=true",
}
PACKS = {
    "zenless_zone_zero": ("zenless_women.txt", "zenless_zone_zero"),
    "blue_archive": ("blue_archive_women.txt", "blue_archive"),
    "azur_lane": ("azur_lane_women.txt", "azur_lane"),
    "genshin_impact": ("genshin_impact_women.txt", "genshin_impact"),
    "honkai_star_rail": ("honkai_star_rail_women.txt", "honkai:_star_rail"),
    "arknights": ("arknights_women.txt", "arknights"),
    "endfield": ("endfield_women.txt", "arknights:_endfield"),
    "fate_grand_order": ("fate_grand_order_women.txt", "fate/grand_order"),
    "vocaloid": ("vocaloid_women.txt", "vocaloid"),
    "touhou": ("touhou_women.txt", "touhou"),
}
# Explicit corrections established in the prior audit. The original appearance
# files are preserved for comparison and need a separate appearance rebuild.
FALSE_FEMALE = {
    "zenless_zone_zero": {"anastella_(zenless_zone_zero)"},
    "blue_archive": {"binah_(blue_archive)"},
}
FGO_SAME_FORM_ALIASES = {
    "altria_pendragon_(fate)": "artoria_pendragon_(fate)",
    "jeanne_d'arc_(alter)_(fate)": "jeanne_d'arc_alter_(fate)",
    "medea_(lily)_(fate)": "medea_lily_(fate)",
    "mysterious_heroine_x_(alter)_(fate)": "mysterious_heroine_x_alter_(fate)",
    "tam_lin_gawain_(fate)": "barghest_(fate)",
    "tam_lin_lancelot_(fate)": "melusine_(fate)",
    "tam_lin_tristan_(fate)": "baobhan_sith_(fate)",
}
FGO_NAME_SPELLINGS = {
    "aesc_the_rain_witch": "aesc_(rain_witch)",
    "attila_the_san(ta)": "altera_the_santa",
    "cnoc_na_riabh_yaraan-doo": "cnoc_na_riabh",
    "frankenstein": "frankenstein's_monster",
}
CANONICAL_TAGS = {
    "arknights": {
        "bagpipe_(queen_no_1)_(arknights)": "bagpipe_(queen_no._1)_(arknights)",
    },
    "fate_grand_order": {
        "atalanta_(alter)_(fate)": "atalanta_alter_(fate)",
        "ibaraki-douji_(fate)": "ibaraki_douji_(fate)",
        "ibuki-douji_(fate)": "ibuki_douji_(fate)",
        "minamoto-no-raikou_(fate)": "minamoto_no_raikou_(fate)",
        "nitocris_(alter)_(fate)": "nitocris_alter_(fate)",
        "sen-no-rikyu_(fate)": "sen_no_rikyu_(fate)",
        "shuten-douji_(fate)": "shuten_douji_(fate)",
        "tamamo-no-mae_(fate)": "tamamo_no_mae_(fate)",
    },
}
TAG_PATTERNS = {
    "zenless_zone_zero": "*_(zenless_zone_zero)",
    "blue_archive": "*_(blue_archive)",
    "azur_lane": "*_(azur_lane)",
    "arknights": "*_(arknights)",
    "fate_grand_order": "*_(fate)",
    "genshin_impact": "*_(genshin_impact)",
    "honkai_star_rail": "*_(honkai:_star_rail)",
}
ZENLESS_OFFICIAL_OUTFITS = {
    "sunna_(delusions_in_business)_(zenless_zone_zero)": "Sunna: Delusions in Business",
    "aria_(human)_(cuteness_loading)_(zenless_zone_zero)": "Aria: Cuteness Loading",
    "nangong_yu_(heartfelt_support)_(zenless_zone_zero)": "Nangong Yu: Heartfelt Support",
}
ZENLESS_OUTFIT_SOURCE = "https://zenless.hoyoverse.com/m/en-us/news/166191"
STAR_RAIL_OFFICIAL_OUTFITS = {
    "march_7th_(nascent_spring)_(honkai:_star_rail)":
        "https://www.hoyolab.com/article/36260996",
    "castorice_(gossamer_flutter)_(honkai:_star_rail)":
        "https://www.hoyolab.com/article/44742273",
}


def slug(value: str) -> str:
    value = value.strip().strip("'\"“”")
    value = value.replace("ß", "ss").replace("Æ", "Ae").replace("æ", "ae")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    value = value.replace("&", "and").replace("’", "'")
    value = re.sub(r"[^\w()'%-]+", "_", value, flags=re.UNICODE).strip("_")
    return value


def get_json(session: requests.Session, url: str, key: str) -> tuple[object, dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / f"{key}.json"
    if target.exists():
        raw = target.read_bytes()
        cached = True
    else:
        response = session.get(url, timeout=45)
        response.raise_for_status()
        raw = response.content
        # Validate before caching an API error or HTML proxy response.
        json.loads(raw)
        target.write_bytes(raw)
        cached = False
    data = json.loads(raw)
    return data, {
        "url": url,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "cached": cached,
        "fetched_utc": datetime.fromtimestamp(target.stat().st_mtime, timezone.utc).isoformat(),
    }


def danbooru_tags(session: requests.Session, pattern: str, key: str) -> tuple[set[str], list[dict]]:
    names: set[str] = set()
    provenance: list[dict] = []
    for page in range(1, 16):
        url = (
            "https://danbooru.donmai.us/tags.json?"
            f"search%5Bname_matches%5D={quote(pattern, safe='')}&"
            f"search%5Bcategory%5D=4&limit=1000&page={page}"
        )
        data, meta = get_json(session, url, f"danbooru_{key}_{page}")
        if not isinstance(data, list):
            raise ValueError(f"Danbooru returned non-list for {key} page {page}")
        page_names = {item["name"] for item in data if item.get("category") == 4}
        names.update(page_names)
        meta.update({"page": page, "rows": len(data)})
        provenance.append(meta)
        if len(data) < 1000:
            break
        time.sleep(0.25)
    else:
        raise RuntimeError(f"Danbooru tag pagination exceeded 15 pages for {key}")
    return names, provenance


def add(rows: dict[str, dict], tag: str, copyright: str, source: str,
        source_id: str = "", matched_tag: bool = True) -> None:
    if not tag or "," in tag or "\n" in tag or "\r" in tag:
        raise ValueError(f"Invalid name: {tag!r}")
    if tag in rows:
        rows[tag]["sources"].add(source)
        if source_id:
            rows[tag]["source_ids"].add(source_id)
        rows[tag]["matched_tag"] |= matched_tag
    else:
        rows[tag] = {
            "copyright": copyright, "sources": {source},
            "source_ids": {source_id} if source_id else set(),
            "matched_tag": matched_tag,
        }


def merge_known_aliases(packs: dict) -> dict[str, list[str]]:
    merged = {}
    for key, aliases in CANONICAL_TAGS.items():
        rows = packs[key]
        merged[key] = []
        for alias, canonical in aliases.items():
            if alias not in rows:
                continue
            if canonical not in rows:
                raise ValueError(f"Canonical tag absent: {canonical}")
            source = rows.pop(alias)
            rows[canonical]["sources"].update(source["sources"])
            rows[canonical]["source_ids"].update(source["source_ids"])
            rows[canonical]["matched_tag"] |= source["matched_tag"]
            merged[key].append(alias)
    return merged


def baseline() -> tuple[dict[str, dict[str, dict]], dict]:
    result = {}
    report = {}
    for key, (filename, copyright) in PACKS.items():
        path = ROOT / "wildcards" / filename
        rows = {}
        omitted = []
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            parts = line.split(", ")
            if len(parts) < 3 or parts[0] != copyright or parts[2] != "1girl":
                raise ValueError(f"Unexpected legacy row: {path}: {line[:90]}")
            tag = parts[1]
            if tag in FALSE_FEMALE.get(key, set()):
                omitted.append(tag)
                continue
            add(rows, tag, copyright, "legacy_appearance_pack")
        result[key] = rows
        report[key] = {"legacy_rows": len(rows), "known_false_removed": omitted}
    return result, report


def choose_tag(candidates: list[str], tags: set[str]) -> str | None:
    return next((candidate for candidate in candidates if candidate in tags), None)


def choose_existing_or_tag(candidates: list[str], rows: dict, tags: set[str]) -> str | None:
    verified_existing = {name for name, row in rows.items() if row["matched_tag"]}
    return choose_tag(candidates, verified_existing) or choose_tag(candidates, tags)


def add_blue_archive(rows: dict, students: dict, tags: set[str], *, include_untagged: bool) -> dict:
    stats = Counter()
    for student_id, student in students.items():
        if not any(student.get("IsReleased", [])):
            continue
        name = student["Name"]
        if not name or name.startswith("CH"):
            stats["unusable_name"] += 1
            continue
        official = f"{slug(name)}_(blue_archive)"
        alternatives = [official, slug(name)]
        match = re.fullmatch(r"(.+?)_\((school|pop_idol)\)", slug(name))
        if match:
            alias = "school_uniform" if match.group(2) == "school" else "idol"
            alternatives.insert(0, f"{match.group(1)}_({alias})_(blue_archive)")
        candidate = choose_existing_or_tag(alternatives, rows, tags)
        if candidate is not None:
            add(rows, candidate, "blue_archive", "released_student+danbooru_tag", student_id)
            stats["matched_official_record"] += 1
        elif include_untagged:
            add(rows, official, "blue_archive", "released_student_official_name", student_id,
                matched_tag=False)
            stats["official_name_fallback"] += 1
        else:
            stats["untagged_official_record"] += 1
    return dict(stats)


def add_azur_lane(rows: dict, ships: dict, tags: set[str], *, include_untagged: bool) -> dict:
    stats = Counter()
    for ship_id, ship in ships.items():
        ship_name = ship["name"]
        ship_slug = slug(ship_name)
        if not ship_slug:
            stats["unusable_name"] += len(ship.get("skins", {}))
            continue
        for skin_id, skin in ship.get("skins", {}).items():
            skin_name = skin.get("name") or ""
            is_default = skin.get("type") == "Default" or skin_name == ship_name
            if skin.get("type") == "Retrofit" and skin_name == f"{ship_name} (Retrofit)":
                skin_name = "Retrofit"
            official = (f"{ship_slug}_(azur_lane)" if is_default else
                        f"{ship_slug}_({slug(skin_name)})_(azur_lane)")
            short = ship_slug if is_default else f"{ship_slug}_({slug(skin_name)})"
            candidate = choose_existing_or_tag([official, short], rows, tags)
            source_id = f"{ship_id}/{skin_id}"
            if candidate:
                add(rows, candidate, "azur_lane", "released_skin+danbooru_tag", source_id)
                stats["matched_official_record"] += 1
            elif include_untagged:
                add(rows, official, "azur_lane", "released_skin_official_name", source_id,
                    matched_tag=False)
                stats["official_name_fallback"] += 1
            else:
                stats["untagged_official_record"] += 1
    return dict(stats)


def base_name(tag: str) -> str:
    return tag.split("_(", 1)[0].replace("'", "").replace("_", "")


def add_arknights(rows: dict, cn: dict, en: dict, tags: set[str],
                   *, include_untagged: bool) -> dict:
    stats = Counter()
    known_female_bases = {base_name(name) for name in rows}
    en_skins = en["charSkins"]
    for skin_id, skin in cn["charSkins"].items():
        char_id = skin["charId"]
        english = en_skins.get(skin_id)
        # Existing female roster is the gender gate; the game table itself does
        # not publish a machine-readable gender field.
        model_name = ((english or {}).get("displaySkin") or {}).get("modelName")
        if not model_name:
            # A newer CN-only skin can still use the model name from its base.
            base_skin = next((x for x in en_skins.values() if x["charId"] == char_id), None)
            model_name = ((base_skin or {}).get("displaySkin") or {}).get("modelName")
        if not model_name:
            stats["no_english_identity"] += 1
            continue
        character_slug = slug(model_name)
        if base_name(character_slug) not in known_female_bases:
            stats["outside_known_female_roster"] += 1
            continue
        en_title = ((english or {}).get("displaySkin") or {}).get("skinName")
        cn_title = (skin.get("displaySkin") or {}).get("skinName")
        title = en_title or cn_title
        official = (f"{character_slug}_(arknights)" if not title else
                    f"{character_slug}_({slug(title)})_(arknights)")
        short = character_slug if not title else f"{character_slug}_({slug(title)})"
        candidate = choose_existing_or_tag([official, short], rows, tags)
        if candidate:
            add(rows, candidate, "arknights", "released_skin+danbooru_tag", skin_id)
            stats["matched_official_record"] += 1
        elif include_untagged:
            add(rows, official, "arknights", "released_skin_official_name", skin_id,
                matched_tag=False)
            stats["official_name_fallback"] += 1
        else:
            stats["untagged_official_record"] += 1
    return dict(stats)


def add_fgo(rows: dict, servants: list, tags: set[str], *, include_untagged: bool) -> dict:
    stats = Counter()
    for servant in servants:
        if not any(trait.get("name") == "genderFemale" for trait in servant.get("traits", [])):
            continue
        name = servant.get("name", "")
        if not name:
            stats["unusable_name"] += 1
            continue
        name_slug = slug(name)
        official = f"{name_slug}_(fate)"
        alternative = FGO_NAME_SPELLINGS.get(name_slug, name_slug)
        alternative = re.sub(r"^altria(?=_|$)", "artoria", alternative)
        alternative = re.sub(r"^atalante(?=_|$)", "atalanta", alternative)
        alternative = re.sub(r"^elisabeth(?=_|$)", "elizabeth", alternative)
        candidates = [official, name_slug, f"{alternative}_(fate)", alternative]
        candidate = choose_existing_or_tag(candidates, rows, tags)
        if official in FGO_SAME_FORM_ALIASES and FGO_SAME_FORM_ALIASES[official] in rows:
            candidate = FGO_SAME_FORM_ALIASES[official]
        source_id = str(servant["id"])
        if candidate:
            add(rows, candidate, "fate/grand_order", "female_servant+danbooru_tag", source_id)
            stats["matched_official_record"] += 1
        elif include_untagged:
            add(rows, official, "fate/grand_order", "female_servant_official_name", source_id,
                matched_tag=False)
            stats["official_name_fallback"] += 1
        else:
            stats["untagged_official_record"] += 1
    return dict(stats)


def add_zenless(rows: dict, tags: set[str], *, include_untagged: bool) -> dict:
    stats = Counter()
    for tag, title in ZENLESS_OFFICIAL_OUTFITS.items():
        if tag in tags:
            add(rows, tag, "zenless_zone_zero", "official_event+danbooru_tag", title)
            stats["matched_official_outfit"] += 1
        elif include_untagged:
            add(rows, tag, "zenless_zone_zero", "official_event_name", title,
                matched_tag=False)
            stats["official_name_fallback"] += 1
        else:
            stats["untagged_official_outfit"] += 1
    return dict(stats)


def add_genshin(rows: dict, outfits: list, tags: set[str], *, include_untagged: bool) -> dict:
    stats = Counter()
    known_female_bases = {base_name(name) for name in rows}
    for outfit in outfits:
        character = slug(outfit["characterName"])
        if base_name(character) not in known_female_bases:
            stats["outside_known_female_roster"] += 1
            continue
        title = slug(outfit["name"])
        is_default = outfit["isDefault"]
        official = (f"{character}_(genshin_impact)" if is_default else
                    f"{character}_({title})_(genshin_impact)")
        candidates = [official]
        if is_default:
            candidates.append(character)
        else:
            candidates.append(f"{character}_({title})")
        candidate = choose_existing_or_tag(candidates, rows, tags)
        source_id = str(outfit["id"])
        if candidate:
            add(rows, candidate, "genshin_impact", "released_outfit+danbooru_tag", source_id)
            stats["matched_official_record"] += 1
        elif include_untagged:
            add(rows, official, "genshin_impact", "released_outfit_official_name", source_id,
                matched_tag=False)
            stats["official_name_fallback"] += 1
        else:
            stats["untagged_official_record"] += 1
    return dict(stats)


def add_star_rail(rows: dict, tags: set[str], *, include_untagged: bool) -> dict:
    stats = Counter()
    for tag, url in STAR_RAIL_OFFICIAL_OUTFITS.items():
        if tag in tags:
            add(rows, tag, "honkai:_star_rail", "official_update+danbooru_tag", url)
            stats["matched_official_outfit"] += 1
        elif include_untagged:
            add(rows, tag, "honkai:_star_rail", "official_update_name", url,
                matched_tag=False)
            stats["official_name_fallback"] += 1
        else:
            stats["untagged_official_outfit"] += 1
    return dict(stats)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-untagged", action="store_true",
                        help="Include official costume names with no Danbooru character tag")
    args = parser.parse_args()
    session = requests.Session()
    session.headers["User-Agent"] = "wild-card-one-off-curation/1.0"
    packs, baseline_report = baseline()
    sources = {}
    data = {}
    for key, url in SOURCES.items():
        data[key], sources[key] = get_json(session, url, key)
    tag_data = {}
    for key, pattern in TAG_PATTERNS.items():
        tag_data[key], sources[f"danbooru_{key}"] = danbooru_tags(session, pattern, key)
    sources["zenless_official_outfits"] = {
        "url": ZENLESS_OUTFIT_SOURCE, "published": "2026-09-21",
        "outfits": list(ZENLESS_OFFICIAL_OUTFITS.values()),
    }
    sources["star_rail_official_outfits"] = list(STAR_RAIL_OFFICIAL_OUTFITS.values())

    supplemental = {
        "zenless_zone_zero": add_zenless(packs["zenless_zone_zero"], tag_data["zenless_zone_zero"],
                                         include_untagged=args.include_untagged),
        "blue_archive": add_blue_archive(packs["blue_archive"], data["blue_archive_students"],
                                         tag_data["blue_archive"], include_untagged=args.include_untagged),
        "azur_lane": add_azur_lane(packs["azur_lane"], data["azur_lane_skins"],
                                   tag_data["azur_lane"], include_untagged=args.include_untagged),
        "arknights": add_arknights(packs["arknights"], data["arknights_skins_cn"],
                                   data["arknights_skins_en"], tag_data["arknights"],
                                   include_untagged=args.include_untagged),
        "fate_grand_order": add_fgo(packs["fate_grand_order"], data["fgo_servants"],
                                    tag_data["fate_grand_order"],
                                    include_untagged=args.include_untagged),
        "genshin_impact": add_genshin(packs["genshin_impact"], data["genshin_outfits"],
                                      tag_data["genshin_impact"],
                                      include_untagged=args.include_untagged),
        "honkai_star_rail": add_star_rail(packs["honkai_star_rail"],
                                          tag_data["honkai_star_rail"],
                                          include_untagged=args.include_untagged),
    }
    alias_merges = merge_known_aliases(packs)
    manifest_path = HERE / "manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["pack", "character", "copyright", "source", "source_id", "is_danbooru_tag"])
        for key, (_, copyright) in PACKS.items():
            lines = []
            for tag, row in sorted(packs[key].items()):
                lines.append(f"{tag}, {copyright}")
                writer.writerow([key, tag, copyright, "+".join(sorted(row["sources"])),
                                 "+".join(sorted(row["source_ids"])), row["matched_tag"]])
            target = ROOT / "wildcards" / f"{key}_girls_name.txt"
            target.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
            baseline_report[key]["exported_rows"] = len(lines)
            baseline_report[key]["official_name_without_danbooru_tag"] = sum(
                not row["matched_tag"] for row in packs[key].values())
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "include_untagged": args.include_untagged,
        "sources": sources,
        "packs": baseline_report,
        "official_record_matching": supplemental,
        "merged_alias_tags": alias_merges,
        "limitations": [
            "Legacy rows were previously auto-curated and have not been individually verified against official release data.",
            "This batch supplements official records for ZZZ, Blue Archive, Azur Lane, Genshin, HSR, Arknights and FGO; other packs retain legacy coverage.",
            "Official-name fallback strings are not confirmed Danbooru tags and may not trigger costume concepts in image models.",
        ],
    }
    (HERE / "report.json").write_bytes(
        (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    print(json.dumps({"packs": baseline_report, "matching": supplemental}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
