---
name: curate-character-wildcards
description: Build, revise, or audit ComfyUI character wildcard files from Danbooru character data and a reviewed CSV. Use for franchise character prompt sets, official-art appearance curation, gender or variant checks, and CSV-to-wildcard export. Skip for ordinary wildcard expansion or unrelated tag lists.
---

# Curate character wildcards

Produce a traceable character CSV, then export a one-character-per-line wildcard for this project. Keep the source CSV as the reviewable artifact; a plausible-looking wildcard alone is not evidence that the character data is correct.

The [v2 design and audit corrections](../../../docs/character-curation-v2.md) record the September 2026 follow-up findings, recommended evidence model, and executable design exercises. Consult its corrections when auditing these packs. Production migration is not implemented; the existing drafting and finalizing scripts do not establish semantic approval. The design exercise's passing cases are not a measured character-recognition accuracy.

## Start with the requested scope

Determine the franchise copyright tag, character inclusion rule, gender policy, treatment of skins/aliases, desired wildcard name, and whether the user supplied a CSV. Use the user's choices from the current conversation; ask only about unresolved product decisions that change the output. If a vetted CSV is supplied, start at export and audit rather than fetching again.

Use paths relative to this repository. Put final wildcard files under `wildcards/`. Store source CSVs and temporary caches outside the package unless the user wants them committed. Do not put credentials or raw API responses in the repository.

## Source and curate

For a new dataset, follow [the source-to-CSV procedure](references/source-to-csv.md). Its main distinction is essential: derive **appearance from posts depicting the target as the single subject**, favoring copyright-matched official art, and assess **gender from broader character-associated evidence**. Base and form tags or confirmed aliases may co-tag one subject. A group illustration can contain `1girl` while the target is not the girl; a pet co-tagged with a girl is also not the girl. Treat sparse official-art coverage, unknown gender, conflicting traits, and aliases as review items, not silent facts.

Use an approved data source and bounded queries. Reuse cached responses, record query/provenance and denominators, and stop/report when coverage is insufficient. Accept credentials through the configured tool or an explicit environment variable; never search local application settings for keys.

For a large Danbooru batch, `scripts/draft_danbooru_pack.py` can generate a draft CSV and a per-character audit JSON using the public endpoints and an external cache directory. Inspect the audit, apply explicit review decisions, and only then export final files. The dated [curation decisions](../../../curation/character-packs-2026-09-26.json) and `scripts/finalize_reviewed_packs.py` show how this project's nine packs were finished; they are an example, not default exclusions for other franchises.

## Export and verify

The reviewed CSV has columns `character,copyright,trigger,core_tags,url`. `core_tags` is a comma-separated list of human-readable Danbooru tags; the wildcard line uses their original underscore form. Read [the CSV/export contract](references/csv-and-export.md) when creating or changing that format.

Run `scripts/csv_to_wildcard.py --csv <reviewed.csv> --output wildcards/<name>.txt` from the repository root. Add `--required-tag 1girl` for a female-only pack. Use `--check` to compare an existing wildcard to the CSV without rewriting it. The script verifies schema, duplicate characters, row content, UTF-8 without BOM, and LF line endings.

Before calling a pack complete, check row-level CSV ↔ wildcard equality, unique character names, intended copyright and gender scope, suspect variants, and the reported official-art fallback count. Then load the file through this project's wildcard loader (and Impact Pack if compatibility was requested), expand `__<name>__` with fixed seeds, and confirm that the returned text contains a complete single entry. If the running ComfyUI instance is unavailable, state that runtime expansion was not verified.

Report the row count, source coverage, fallback/review cases, any unresolved identity or tag conflicts, export result, and runtime test result. Do not turn an unresolved review item into an automatic exclusion.
