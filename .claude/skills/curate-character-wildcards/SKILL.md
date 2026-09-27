---
name: curate-character-wildcards
description: Build or audit ComfyUI character appearance wildcards from Danbooru Wiki Appearance entries and exact post tags. Use for sourced official character designs, game outfits, skins, and variants; not for name-only packs or ordinary wildcard expansion.
---

# Curate character appearance wildcards

Use the [Wiki Appearance → post → per-form CSV procedure](references/wiki-appearance-to-csv.md). One row represents one character in one specific design within the requested franchise scope. Select visual tags from its own supporting post; never pool posts, rank traits by frequency, or copy default traits into a variant.

The [Zenless first batch](../../../docs/zenless-girls-2026-09-27.md) shows the original per-image method. The [nine-franchise review](../../../docs/nine-franchise-girls-2026-09-27.md) and its linked full-pack audits show how the same method was extended to name-pack candidates, exact-tag rescue searches, exclusions, and a reproducible export. Project curation scripts contain dated, franchise-specific choices; adapt their criteria and verify them for a new scope.

## 1. Fix the requested scope

Read the current conversation before asking anything: franchise copyright tag, subject rule, official server and date cutoff, whether official variants are separate entries, output name, and treatment of the existing pack. Ask only when a missing product choice changes the output. Reuse a supplied roster or CSV as the candidate baseline. A completed review of that baseline does **not** establish that every franchise character or outfit was discovered; label both the candidate boundary and unreviewed remainder.

Write active wildcard files under `wildcards/`. If replacing a pack, archive its former file outside active wildcard roots and check for another copy in Impact Pack or configured wildcard folders. Preserve unrelated workspace changes.

## 2. Inventory Wiki appearances

Start from the name pack, a franchise Wiki roster, or another documented roster. Query each canonical Danbooru character Wiki's `Appearance` entries (`!post #…` and `!asset #…`), and linked form Wikis when present. Record Wiki title, update time, form label, image ID, exact post URL, original source field, copyright/character/general/meta tags, and missing data. Deduplicate image IDs without losing which Wiki pages cited them. Use `scripts/collect_wiki_appearance.py --help` for the reusable public-API collector. Fetch JSON metadata **only**; do not download images, thumbnails, or other image binaries. Bound API calls, reuse the cache/inventory, and do not commit credentials or raw API dumps.

For gaps, search the **exact character/form tag** for tagged posts, including relevant game-asset evidence, and record query terms and limits. A Wiki `asset` has no post general tags: find a matching tagged post or exclude the form from the active wildcard with a recorded reason. A missing Wiki or `Appearance` is a coverage gap, not proof the design does not exist.

## 3. Decide per form and per tag

For each candidate, check one exact post for the form tag when one exists, requested copyright, `1girl` when the pack is female-only, and every exported general tag. A form without its own Danbooru tag needs the documented game-roster, base-character-tag, and post-image exception in the [procedure](references/wiki-appearance-to-csv.md). Establish official status and in-scope use separately from post tags: a Wiki form label, `official_art`, `official_alternate_costume`, `game_asset`, `1girl`, or `solo` alone cannot prove it. Prefer original publisher/game evidence; identify mirrors, game-file labels, missing sources, and release uncertainty in the audit. Do not infer an outfit's release date from a post date.

Select a short list of visible identity, clothing, and accessory tags **from that form's exact post**. Exclude composition, pose, expression, background, image quality, source metadata, and tags belonging to pets, props, printed characters, or other people. Check conflicts within one form; a base-character tag on a costume post does not establish the default outfit. Keep exact Danbooru form tags where they exist; avoid generic aliases that duplicate specific forms. If exact post or official design evidence is insufficient, **exclude the row from the active wildcard** and state why. Never invent tags from an asset, a costume name, or another post.

Maintain a candidate/form audit with `included` or `excluded` and concrete reasons, plus an image-level audit when several Wikis cite one image. Keep exact post and original-source references, source-tier exceptions, query gaps, and scope distinctions (for example, a licensed derivative game versus a mainline work, or a voicebank design versus an external game card). Preserve existing approved rows only after rechecking the same evidence. A programmatic tag-membership assertion verifies provenance, not visual correctness or release status.

## 4. Export and verify

Use the [CSV and wildcard contract](references/csv-and-export.md). The reviewed CSV columns are `character,copyright,trigger,core_tags,url`; `url` must point to the exact supporting post for that row. Put `1girl` first in `core_tags` only after female subject scope has been checked. Use `scripts/csv_to_wildcard.py --csv <reviewed.csv> --output wildcards/<name>.txt --required-tag 1girl`, then repeat with `--check` to compare exact bytes. Keep the inventory, search log, reviewed CSV, inclusion/exclusion audit, and selection logic alongside the delivered pack.

Check row count, unique form tags, copyright, exact-post tag membership, duplicate/ambiguous source images, unresolved conflicts, and UTF-8/LF output. Rebuild with the recorded selection logic and rerun `--check`; the reviewed CSV and active wildcard must still match byte for byte. Load `__<name>__` through this project's wildcard engine with fixed seeds and inspect complete strings. Test in a running ComfyUI only if requested or needed for a concrete compatibility risk; otherwise say it was not tested. Report included versus excluded candidate counts, missing-source reasons, source-tier exceptions, date/roster limitations, and verification results. Never present community tags or mirrors as independent proof of an official release.
