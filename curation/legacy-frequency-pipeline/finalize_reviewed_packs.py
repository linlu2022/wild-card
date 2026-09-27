"""Apply explicit review decisions and export character packs from draft CSVs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from csv_to_wildcard import FIELDS, build_output


COLORS = {"black", "white", "grey", "silver", "brown", "blonde", "red", "orange",
          "yellow", "green", "blue", "aqua", "purple", "pink"}
HAIR_MARKERS = {"multicolored hair", "streaked hair", "gradient hair", "two-tone hair",
                "colored inner hair"}
EYE_MARKERS = {"heterochromia", "multicolored eyes", "two-tone eyes"}


def read_draft(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"{path}: unexpected CSV header")
        return list(reader)


def resolve_color_conflicts(row: dict[str, str]) -> list[str]:
    tags = [tag.strip() for tag in row["core_tags"].split(",")]
    present = set(tags)
    removed = []
    kept = []
    seen = set()
    for tag in tags:
        words = tag.split()
        color_type = (words[1] if len(words) == 2 and words[0] in COLORS
                      and words[1] in {"hair", "eyes"} else None)
        markers = HAIR_MARKERS if color_type == "hair" else EYE_MARKERS
        if color_type and not present.intersection(markers) and color_type in seen:
            removed.append(tag)
            continue
        if color_type:
            seen.add(color_type)
        kept.append(tag)
    row["core_tags"] = ", ".join(kept)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--draft-dir", required=True, type=Path)
    parser.add_argument("--reviewed-dir", required=True, type=Path)
    parser.add_argument("--wildcards-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
        args.reviewed_dir.mkdir(parents=True, exist_ok=True)
        args.wildcards_dir.mkdir(parents=True, exist_ok=True)
        summary = {}
        for pack_name, choice in decisions.items():
            copyright_tag = choice["copyright"]
            draft = read_draft(args.draft_dir / f"{pack_name}_draft.csv")
            audit = json.loads((args.draft_dir / f"{pack_name}_audit.json").read_text(encoding="utf-8"))
            if audit["copyright"] != copyright_tag or audit["draft_count"] != len(draft):
                raise ValueError(f"{pack_name}: draft CSV and audit disagree")
            seen = {row["character"] for row in draft}
            exclude = set(choice.get("exclude", []))
            if not exclude <= seen:
                raise ValueError(f"{pack_name}: exclusions not in draft: {sorted(exclude - seen)}")
            rows = [row for row in draft if row["character"] not in exclude]
            by_name = {row["character"]: row for row in rows}
            inherited = choice.get("inherit_appearance", {})
            for name, parent in inherited.items():
                if name in seen or name in by_name or parent not in by_name:
                    raise ValueError(f"{pack_name}: invalid inheritance {name} <- {parent}")
                candidate = next((x for x in audit["characters"] if x["character"] == name), None)
                if candidate is None or candidate["status"] == "draft":
                    raise ValueError(f"{pack_name}: inherited character lacks a reviewed candidate: {name}")
                rows.append({"character": name, "copyright": copyright_tag,
                             "trigger": f"{name.replace('_', ' ')}, {copyright_tag.replace('_', ' ')}",
                             "core_tags": by_name[parent]["core_tags"],
                             "url": f"https://danbooru.donmai.us/posts?tags={quote(name, safe='')}"})
            color_resolutions = {}
            for row in rows:
                removed = resolve_color_conflicts(row)
                if removed:
                    color_resolutions[row["character"]] = removed
            rows.sort(key=lambda row: row["character"])
            reviewed_csv = args.reviewed_dir / f"{pack_name}_women.csv"
            with reviewed_csv.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            output, count = build_output(reviewed_csv, "1girl")
            wildcard = args.wildcards_dir / f"{pack_name}_women.txt"
            wildcard.write_bytes(output)
            sources = Counter(x.get("appearance_source") for x in audit["characters"]
                              if x["status"] == "draft" and x["character"] not in exclude)
            summary[pack_name] = {"copyright": copyright_tag, "candidate_count": audit["candidate_count"],
                                  "draft_count": len(draft), "final_count": count,
                                  "excluded": sorted(exclude), "inherited_appearance": inherited,
                                  "removed_conflicting_color_tags": color_resolutions,
                                  "appearance_sources": dict(sources),
                                  "reviewed_csv": str(reviewed_csv), "wildcard": str(wildcard)}
            print(f"{pack_name}: {len(draft)} draft -> {count} final", flush=True)
        (args.reviewed_dir / "review_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
