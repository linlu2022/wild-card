"""Export a reviewed character CSV to an Impact Pack-compatible wildcard file."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


FIELDS = ["character", "copyright", "trigger", "core_tags", "url"]


def canonical_tag(value: str, label: str, line_number: int) -> str:
    tag = value.strip()
    if not tag or any(char.isspace() or char in ",|\r\n" for char in tag):
        raise ValueError(f"CSV line {line_number}: invalid {label}: {value!r}")
    return tag


def build_output(csv_path: Path, required_tag: str | None = None) -> tuple[bytes, int]:
    raw = csv_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("CSV must be UTF-8 without BOM")
    with csv_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"CSV header must be exactly: {','.join(FIELDS)}")

        seen_characters: set[str] = set()
        copyrights: set[str] = set()
        lines: list[str] = []
        for row in reader:
            line_number = reader.line_num
            if None in row or any(row[field] is None for field in FIELDS):
                raise ValueError(f"CSV line {line_number}: malformed row")
            character = canonical_tag(row["character"], "character", line_number)
            copyright_tag = canonical_tag(row["copyright"], "copyright", line_number)
            if character in seen_characters:
                raise ValueError(f"CSV line {line_number}: duplicate character {character}")
            if not row["trigger"].strip() or not row["url"].strip():
                raise ValueError(f"CSV line {line_number}: trigger and url are required")

            tags = [tag.strip().replace(" ", "_") for tag in row["core_tags"].split(",")]
            if not tags or any(not tag or "\r" in tag or "\n" in tag or "|" in tag for tag in tags):
                raise ValueError(f"CSV line {line_number}: empty or invalid core tag")
            if len(tags) != len(set(tags)):
                raise ValueError(f"CSV line {line_number}: duplicate core tag")
            if required_tag and tags[0] != required_tag:
                raise ValueError(f"CSV line {line_number}: {required_tag} must be the first core tag")

            seen_characters.add(character)
            copyrights.add(copyright_tag)
            lines.append(", ".join([copyright_tag, character, *tags]))

    if not lines:
        raise ValueError("CSV has no character rows")
    if len(copyrights) != 1:
        raise ValueError("CSV mixes copyright tags; make one wildcard file per copyright")
    return ("\n".join(lines) + "\n").encode("utf-8"), len(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True, help="Reviewed character CSV")
    parser.add_argument("--output", type=Path, required=True, help="Wildcard .txt path")
    parser.add_argument("--required-tag", help="Require this tag on every character, e.g. 1girl")
    parser.add_argument("--check", action="store_true", help="Compare with existing output without writing")
    args = parser.parse_args()

    try:
        required_tag = canonical_tag(args.required_tag, "required tag", 0) if args.required_tag else None
        output, count = build_output(args.csv, required_tag)
        if args.check:
            if not args.output.is_file() or args.output.read_bytes() != output:
                raise ValueError(f"{args.output} does not match the reviewed CSV")
            print(f"OK: {count} rows match {args.output}")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(output)
            print(f"Wrote {count} rows to {args.output}")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
