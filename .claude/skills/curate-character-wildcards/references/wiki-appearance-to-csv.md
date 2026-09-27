# Wiki Appearance to per-form CSV

This is the active source procedure for appearance packs. The [Zenless first batch](../../../../docs/zenless-girls-2026-09-27.md) illustrates it with Vivian Banshee's default form and Iris of the Shore. The character Wiki lists a separate Appearance reference for each; the linked posts supply separate character and general tags. The [nine-franchise audits](../../../../docs/nine-franchise-girls-2026-09-27.md) illustrate larger candidate reviews and exclusions.

## Evidence chain

For each candidate, record:

| Layer | What to save | What it establishes |
| --- | --- | --- |
| Roster | Character tag, franchise, source | Discovery only; not gender or outfit proof |
| Character Wiki | Title, update time, Appearance image IDs and labels | Which design the Wiki claims each image depicts |
| Form Wiki | Form title, description, Appearance link | A named form and its claimed status |
| Post | Post ID, original source field, character/copyright/general/meta tags | The exact candidate tags and provenance for one image |
| Decision | Selected form tag, selected visual tags, inclusion/exclusion, reason | Why a row may be exported |

The Wiki and its tags are community maintained. Check official identity and in-scope use against a publisher source, game record, or clearly identified game-resource mirror where available. Record mirrors and `game_asset`/game-file-only sources as lower-confidence evidence; do not call them direct official confirmation. A post tagged `official_art` is not automatically official. A form described as a skin is not automatically released in the requested game or date range. Post creation time is not an outfit release date.

Use `scripts/collect_wiki_appearance.py --names <name-pack-or-list.txt> --output <inventory.csv>` from this skill directory. It reads the first comma-separated field of each nonempty line as a candidate Wiki title. The script fetches public **JSON only** with bounded workers, keeps a local JSON cache, and writes fields needed for review. It does not fetch or store image binaries; neither should follow-up searches. Keep the inventory, not API keys or full raw response dumps, in the project. For a large roster, cap a trial run and state the unqueried remainder; a final full review should cover the agreed candidate roster.

When a Wiki is missing, `Appearance` is empty, or an `asset` lacks tags, search Danbooru posts for the exact character/form tag plus the franchise scope. Inspect returned post tags and original source; log the query and result count. The dated [multi-franchise supplemental collector](../../../../curation/appearance-full-2026-09-27/collect_supplemental.py) illustrates this step; its package configuration and source-tier choices need revalidation for another project. An `asset` reference may still lead to an accepted form **if a separate qualifying post is found**. Otherwise exclude the form from the active wildcard and retain the gap in the audit.

## Form decision

1. Normalize aliases only when the Wiki, post tags, or another source supports the identity relation. A base tag and costume tag on the same post can describe one design. Another character tag can also describe a pet, doll, printed image, or second person.
2. Bind one exact post to one named form. Prefer its exact form tag in `tag_string_character`. A documented official costume name without an independent Danbooru form tag is an exception only when a game roster confirms the costume, the post's base character matches, and the chosen image/source clearly binds that costume; record the constructed trigger and exception. Otherwise exclude the unbound form. Never silently reuse the base tag for another outfit.
3. Check the requested franchise tag and female subject. `1girl`, `solo`, and the number of character tags are insufficient alone when companions, dolls, printed people, or group art appear. Exclude companion-only tags and generic aliases already represented by specific forms.
4. Check official in-scope status separately from Danbooru tags. Distinguish game outfit, story appearance, licensed derivative game, voicebank product art, promotional design, and external-game card according to the user's scope. Check the requested official server/date with release evidence where possible; record uncertainty rather than assigning false precision.
5. Choose visual tags only from that post's `tag_string_general`, with subject attribution. Use separate rows for separate forms. Do not inherit, aggregate, or frequency-average across forms. Keep colors only when they make sense for that form; unresolved conflicts are review items.
6. Record a decision and reason for every discovered candidate. No matching tagged post, ambiguous subject, unbound costume, weak source, uncertain scope, or non-game promotional design means **excluded from the active output**. The audit can retain such candidates for explanation; their absence does not prove the design itself is nonexistent.

## Concrete Zenless example

- [Vivian Wiki](https://danbooru.donmai.us/wiki_pages/vivian_banshee) points to [default post 9196669](https://danbooru.donmai.us/posts/9196669) and [Iris post 10146034](https://danbooru.donmai.us/posts/10146034).
- Default can use `vivian_banshee, white_dress, black_skirt, umbrella`; Iris can use `vivian_banshee_(iris_of_the_shore), frilled_one-piece_swimsuit, parasol`.
- Exclude `solo`, `full_body`, `transparent_background`, `holding`, and other scene/pose tags. The costume's swimsuit tags do not leak into the default row.
- The [sample selection table](../../../../curation/zenless-appearance-2026-09-27/build.py) validates every chosen general tag against its exact post. That automated check does not validate the picture itself.

## Source and credential discipline

Use documented public endpoints or an already authorized connector. Bound calls and retries; reuse saved inventory instead of immediately querying again. Fetch tags and metadata, not images or thumbnails. Never search local application settings for keys, and never commit credentials or full raw API responses. If the source lacks enough coverage, report the gap rather than switching silently to loosely associated fan art.
