---
name: curate-character-wildcards
description: Build or audit ComfyUI character appearance wildcards from Danbooru character Wiki Appearance entries, their linked post tags, and a traceable per-form CSV. Use for official in-work outfits, default forms, skins, and variants. Skip for name-only packs or ordinary wildcard expansion.
---

# Curate character appearance wildcards

Use the [Wiki Appearance → post → per-form CSV procedure](references/wiki-appearance-to-csv.md). One row represents one character in one specific official in-work appearance. Do not pool tags from all posts for a character, rank features by post frequency, or copy a base form's traits into a costume without evidence from that costume.

The [2026-09-27 Zenless batch](../../../docs/zenless-girls-2026-09-27.md) is the worked example. Its [`collect.py`](../../../curation/zenless-appearance-2026-09-27/collect.py), [`inventory.csv`](../../../curation/zenless-appearance-2026-09-27/inventory.csv), [`build.py`](../../../curation/zenless-appearance-2026-09-27/build.py), [`reviewed.csv`](../../../curation/zenless-appearance-2026-09-27/reviewed.csv), and [`audit.csv`](../../../curation/zenless-appearance-2026-09-27/audit.csv) show the exact evidence and decisions. The example scripts are tied to Zenless Zone Zero; adapt them to another franchise rather than copying their character choices.

## 1. Fix the requested scope

Read the current conversation before asking anything: franchise copyright tag, female/other inclusion rule, official server and date cutoff, whether all official in-work outfits are separate entries, output name, and what to do with any existing pack. Ask only when a missing product choice changes the output. If the user supplies a vetted roster or CSV, reuse it. Keep a partial first batch labeled as partial; do not imply complete franchise coverage.

Write active wildcard files under `wildcards/`. If replacing a pack, archive its former file outside active wildcard roots and check for another copy in Impact Pack or configured wildcard folders. Preserve unrelated workspace changes.

## 2. Inventory Wiki appearances

Start from the project's name pack, a franchise Wiki roster, or another documented roster. Fetch each canonical Danbooru character Wiki page and parse its `Appearance` entries (`!post #…` and `!asset #…`). Follow outfit links to the form Wiki page where available. Record the Wiki title, update time, form label, image ID, post URL, original image source, copyright/character/general/meta tags, and any missing data. Deduplicate image IDs while keeping every Wiki page that cited them. The reusable public-API inventory command is `scripts/collect_wiki_appearance.py`; read its help before running. Fetch JSON metadata only; do not download image binaries. Use bounded queries and do not commit credentials or whole API responses.

An `asset` has no post general tags. Search for an exact matching post with usable tags; if none exists, exclude that form from the active wildcard and record the gap in the audit. A Wiki page with no `Appearance` is a coverage gap, not proof that the character or outfit does not exist.

## 3. Decide per form and per tag

For each candidate, check the exact character/form tag in the linked post, the requested franchise copyright, the subject shown, and evidence that this is an official in-work appearance. A form Wiki label, `official_art`, `official_alternate_costume`, `1girl`, or `solo` helps locate evidence but cannot prove those facts alone. Prefer an original official source; mark third-party mirrors and uncertain release status in the audit. Co-tagged pets, props, printed characters, and groups require subject attribution before taking any general tag.

Select a short list of visible identity, clothing, and accessory tags **from that form's linked image**. Exclude composition, pose, expression, background, image quality, source metadata, and other subjects. Check conflicts within one form; never average default and costume tags together. Keep exact Danbooru character tags where they exist. If a form lacks enough evidence, defer it with a reason instead of fabricating its appearance. A form may have only a few strong tags.

Maintain an inventory of all candidates and an audit decision for each unique image or form (`included`, `deferred`, `excluded`, or `alias/reference`) with a concrete reason. Keep source URLs and any exceptions. An automated assertion that tags occur on a post verifies provenance only; it does not mean the image, identity, or release status was visually verified.

## 4. Export and verify

Use the [CSV and wildcard contract](references/csv-and-export.md). The reviewed CSV columns are `character,copyright,trigger,core_tags,url`; `url` must point to the exact supporting post for that row. Put `1girl` first in `core_tags` only after female subject scope has been checked. Use `scripts/csv_to_wildcard.py --csv <reviewed.csv> --output wildcards/<name>.txt --required-tag 1girl`, then repeat with `--check` to compare exact bytes. Keep CSV, inventory, audit, and selection logic with the project when traceability is requested.

Check row count, unique form tags, correct copyright, selected tag membership in the specific post, duplicate source images, unresolved conflicts, and UTF-8/LF output. Load `__<name>__` through this project's wildcard engine with several fixed seeds and verify complete deterministic strings. If runtime ComfyUI or Impact Pack compatibility was requested, test it there too; otherwise report that it was not tested. Report coverage as included identities/forms versus discovered candidates, all deferred reasons, source-tier exceptions, and verification results. Do not present community Wiki or Danbooru labels as independent proof of official release.
