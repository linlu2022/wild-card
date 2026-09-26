# From character data to a reviewed CSV

This procedure captures the final method used for the `zenless_women` pack. Its thresholds are starting points for a new franchise, not universal classification rules. Keep query provenance and assess whether the source's tagging conventions support the method before applying it elsewhere.

## 1. Discover candidates

Find Danbooru category-4 character tags associated with the requested copyright. Search both names with the copyright suffix and aliases without it. Tag search results are candidates, not proof of franchise membership. Confirm association from posts whose `tag_string_copyright` contains the target copyright. Do not infer identity or gender solely from the tag spelling or apparent name.

Record each candidate's canonical character tag, alias/variant relation, source URL, tag count, and why it was included. Set a finite query limit and cache the response. If the API truncates a candidate's posts, record the cap and its effect on coverage.

## 2. Separate evidence by question

For **appearance**, query official-art posts associated with the candidate. Retain posts with the requested copyright. A post is single-character evidence only when its set of character tags equals `{candidate}`. Neither `solo`, `1girl`, nor the absence of `multiple_girls` proves this. Count general tags over those posts and divide each tag's count by the number of usable posts. Keep that denominator per character.

If there are fewer than about five usable single-character official-art posts, broader official-art data may be used as a fallback, but label the row for review. Multi-character art can leak another character's hair, eyes, clothing, or body traits. With no usable official art, leave the row unresolved or use another explicitly documented source; do not present scraped co-occurrence as confirmed appearance.

For **gender**, use broader character-associated posts or related-tag frequencies, plus manual inspection for ambiguous cases. Official-art group images are a poor gender classifier. Compare `1girl`, `1boy`, and, where relevant, furry and focus tags; distinguish the target from companions. The ZZZ run used heuristic thresholds for these frequencies. Recalibrate them per source and manually review near-boundary, low-sample, and contradictory cases. Unknown gender remains unknown.

## 3. Select core tags

Use conditional frequency `P(tag | usable posts for character)`, rather than raw global popularity. Rank/select the top candidates **before** grouping them into traits; otherwise large generic buckets can crowd out distinctive features. Group useful tags by species, eyes, hair, body, clothing, and accessories. Prefer stable, visible identity traits.

Remove copyright and character names from `core_tags`; the exporter supplies them separately. Exclude composition, pose, camera angle, background, mood, quality, artist/source metadata, other characters, and content outside the user's intended prompt style. Resolve contradictory tags such as mutually exclusive hair colors through image inspection. A high frequency can still reflect a recurring companion, costume, or mislabeled post.

For the ZZZ run, exploratory settings included a frequency floor that relaxed from 0.5 toward 0.2, a top-40 candidate pool, a final roughly 20-tag cap, and a stricter threshold for generic species tags. These numbers are tuning examples. Keep the selection criteria and exceptions in an audit note so another person can reproduce the judgment.

## 4. Produce and review the CSV

Write `character,copyright,trigger,core_tags,url` in UTF-8 without BOM. Use the exact Danbooru character/copyright tags in their columns; write comma-separated, human-readable core tags (spaces in place of underscores). For a female-only pack, `1girl` should be first in `core_tags` after the target has passed gender review. Keep rows sorted by canonical character tag and check for duplicates or aliases representing the same person.

Inspect outliers before export: unusually low official-art count, fallback to group art, nearly identical trait sets across different characters, conflicting colors/species, uncertain gender, and skin or costume variants. A variant may be valid or unwanted depending on the user's pack definition.

In the original ZZZ dataset, 32 of 68 rows needed broader official-art fallback. `anastella_(zenless_zone_zero)` resembled `alexandrina_sebastiane` suspiciously, and several named variants were unresolved product choices. These are **case-specific review flags**, not rules to delete those entries from future runs. The existence of 68 valid output lines did not resolve those semantic questions.

## Source and credential discipline

Prefer official APIs or an already configured connector. If a network proxy or paid scraper is necessary, use only the access method authorized for that task, cap calls and retries, and cache successful responses. Keep API keys out of commands, logs, scripts, CSVs, and commits. A previous experimental script searched a local Claude configuration for a key; that behavior is intentionally excluded from this skill.
