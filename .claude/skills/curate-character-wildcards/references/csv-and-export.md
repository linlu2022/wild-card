# CSV and wildcard contract

Required CSV header, in this order:

```csv
character,copyright,trigger,core_tags,url
```

Example row (illustrative):

```csv
example_character,example_game,"example character, example game","1girl, blue eyes, long hair",https://danbooru.donmai.us/posts?tags=example_character
```

The `character` and `copyright` columns use canonical underscore tags. `trigger` is a human-readable display/prompt field for review and downstream CSV consumers; it is not used when building the wildcard line. `core_tags` is a comma-separated list of Danbooru general tags written with spaces for readability. `url` points to source evidence. Validate that the URL actually corresponds to the row; a search URL alone does not prove every selected trait.

The exporter produces:

```text
example_game, example_character, 1girl, blue_eyes, long_hair
```

One CSV row becomes one LF-terminated wildcard line. A file has one copyright scope, unique character tags, no empty tags, no duplicate tags within a row, and no empty lines. The exporter preserves CSV row order and normalizes only whitespace around comma-separated tags plus spaces to underscores. It does not infer aliases, genders, or whether a chosen tag describes the correct character.

From the repository root:

```powershell
python .claude/skills/curate-character-wildcards/scripts/csv_to_wildcard.py --csv path/to/reviewed.csv --output wildcards/example_women.txt --required-tag 1girl
python .claude/skills/curate-character-wildcards/scripts/csv_to_wildcard.py --csv path/to/reviewed.csv --output wildcards/example_women.txt --required-tag 1girl --check
```

The first command writes the file after validating the full CSV. The second compares expected bytes with the existing file and exits nonzero on any mismatch, including encoding or line endings. `--required-tag` requires that tag to be first in every row. For multi-gender packs, omit it.

For Impact Pack compatibility, refer to the wildcard as `__example_women__`. Repeat that token for multiple independent draws. Avoid `N#__example_women__` when entries themselves contain commas: older parser behavior can split or combine prompt parts unexpectedly. Fixed-seed checks should verify the populated text and not only the loader's item count.
