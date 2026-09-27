# CSV and wildcard contract

Required CSV header, in this order:

```csv
character,copyright,trigger,core_tags,url
```

Example row (illustrative):

```csv
example_character_(summer_outfit),example_game,"example character summer outfit, example game","1girl, blue eyes, summer dress",https://danbooru.donmai.us/posts/1234567
```

The `copyright` column uses a canonical underscore tag; `character` uses the exact Danbooru form tag when available. A deliberately constructed form tag needs a documented game-record, base-character-tag, and post-image match. `trigger` is a human-readable display/prompt field for review and downstream CSV consumers; it is not used when building the wildcard line. `core_tags` is a comma-separated list of Danbooru general tags written with spaces for readability. `url` must point to the exact post supporting this form and its selected tags; a search URL or untagged `asset` URL is insufficient.

The exporter produces:

```text
example_game, example_character_(summer_outfit), 1girl, blue_eyes, summer_dress
```

One CSV row becomes one LF-terminated wildcard line. A file has one copyright scope, unique form tags, no empty tags, no duplicate tags within a row, and no empty lines. The exporter preserves CSV row order and normalizes only whitespace around comma-separated tags plus spaces to underscores. It does not infer aliases, genders, outfit status, or whether a chosen tag describes the correct form.

From the repository root:

```powershell
python .claude/skills/curate-character-wildcards/scripts/csv_to_wildcard.py --csv path/to/reviewed.csv --output wildcards/example_girls.txt --required-tag 1girl
python .claude/skills/curate-character-wildcards/scripts/csv_to_wildcard.py --csv path/to/reviewed.csv --output wildcards/example_girls.txt --required-tag 1girl --check
```

The first command checks CSV structure and writes the file. The second compares expected bytes with the existing file and exits nonzero on any mismatch, including encoding or line endings. `--required-tag` requires that tag to be first in every row. For multi-gender packs, omit it. The exporter does **not** query Danbooru or prove that `url` contains the selected tags; validate exact-post copyright, character, `1girl`, and every selected general tag against the saved inventory or supplemental result separately.

Before delivery, rerun the selection logic from saved metadata and check that `reviewed.csv` and the wildcard still match. Count included and excluded forms from the audit; compare those counts with the documentation. Confirm unique character/form keys, inspect any shared post used by several forms, and retain earlier reviewed rows only when they still pass. `image_audit.csv`, when present, describes **post/asset references in text** and does not contain downloaded images.

For Impact Pack compatibility, refer to the wildcard as `__example_girls__`. Repeat that token for multiple independent draws. Avoid `N#__example_girls__` when entries themselves contain commas: older parser behavior can split or combine prompt parts unexpectedly. Fixed-seed checks should verify the populated text and not only the loader's item count. Literal parentheses in character tags may be interpreted as weights by some downstream CLIP parsers; test the target encoder and escape them if needed. Keep the name-only `*_girls_name.txt` pack separate from this appearance pack.
