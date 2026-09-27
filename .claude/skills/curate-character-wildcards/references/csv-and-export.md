# CSV and wildcard contract

Required CSV header, in this order:

```csv
character,copyright,trigger,core_tags,url
```

Example row (illustrative):

```csv
example_character_(summer_outfit),example_game,"example character summer outfit, example game","1girl, blue eyes, summer dress",https://danbooru.donmai.us/posts/1234567
```

The `character` and `copyright` columns use canonical underscore tags. A separate official form uses its own character tag when Danbooru has one. `trigger` is a human-readable display/prompt field for review and downstream CSV consumers; it is not used when building the wildcard line. `core_tags` is a comma-separated list of Danbooru general tags written with spaces for readability. `url` must point to the exact image post supporting this form and its selected tags; a search URL is insufficient.

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

The first command writes the file after validating the full CSV. The second compares expected bytes with the existing file and exits nonzero on any mismatch, including encoding or line endings. `--required-tag` requires that tag to be first in every row. For multi-gender packs, omit it.

For Impact Pack compatibility, refer to the wildcard as `__example_girls__`. Repeat that token for multiple independent draws. Avoid `N#__example_girls__` when entries themselves contain commas: older parser behavior can split or combine prompt parts unexpectedly. Fixed-seed checks should verify the populated text and not only the loader's item count. Literal parentheses in character tags may be interpreted as weights by some downstream CLIP parsers; test the target encoder and escape them if needed.
