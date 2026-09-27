# Wiki Appearance to per-form CSV

This is the active source procedure for appearance packs. The [Zenless first batch](../../../../docs/zenless-girls-2026-09-27.md) illustrates it with Vivian Banshee's default form and Iris of the Shore. The character Wiki lists a separate Appearance image for each, and the linked posts have separate character and general tags. That relationship is the unit of curation.

## Evidence chain

For each candidate, record:

| Layer | What to save | What it establishes |
| --- | --- | --- |
| Roster | Character tag, franchise, source | Discovery only; not gender or outfit proof |
| Character Wiki | Title, update time, Appearance image IDs and labels | Which design the Wiki claims each image depicts |
| Form Wiki | Form title, description, Appearance link | A named form and its claimed status |
| Post | Post ID, original source URL, character/copyright/general/meta tags, image URL | The exact candidate tags and source for this image |
| Decision | Selected form tag, selected visual tags, exclusions, status, reason | Why a row may be exported |

The Wiki and its tags are community maintained. Where official in-work status matters, check the original source and game/release evidence as available. If the image source is a mirror, record that limitation. A post tagged `official_art` is not automatically official. A form described on a Wiki as a skin is not automatically released in the requested game or date range.

Use `scripts/collect_wiki_appearance.py --names <name-pack-or-list.txt> --output <inventory.csv>` from this skill directory. It reads the first comma-separated field of each nonempty line as a candidate Wiki title. The script fetches public JSON endpoints with a bounded number of workers and writes only the fields required for review. The output may be kept in project curation records; do not put API keys or raw response dumps in the repo. For a large roster, cap the first run and state the unqueried remainder.

## Form decision

1. Normalize aliases only when the Wiki, post tags, or another source supports the identity relation. A base tag and costume tag on the same post can describe one design. Another character tag can also describe a pet, doll, printed image, or second person.
2. Bind the post to one named form. Prefer an exact form tag in `tag_string_character`. If a form Wiki exists but the post has no form tag, record the naming gap and decide explicitly; do not silently reuse the base tag for a different outfit.
3. Check the requested franchise tag and female subject. `1girl`, `solo`, and the number of character tags are insufficient alone when companions or group art appear.
4. Check official in-work status and date from the form description and original source where possible. Record uncertainty rather than assigning false precision.
5. Choose visual tags only from that post's `tag_string_general`, with subject attribution. Use separate rows for separate forms. Do not inherit, aggregate, or frequency-average across forms. Keep colours as tagged for that form only when they make sense in the image; unresolved colour conflicts are review items.
6. Record all unsolved candidates in the audit, including `asset` without a matching tagged post, empty Appearance sections, dead links, uncertain gender, non-game promotional designs, and images with multiple possible subjects. `deferred` is not `excluded`.

## Concrete Zenless example

- [Vivian Wiki](https://danbooru.donmai.us/wiki_pages/vivian_banshee) points to [default post 9196669](https://danbooru.donmai.us/posts/9196669) and [Iris post 10146034](https://danbooru.donmai.us/posts/10146034).
- Default can use `vivian_banshee, white_dress, black_skirt, umbrella`; Iris can use `vivian_banshee_(iris_of_the_shore), frilled_one-piece_swimsuit, parasol`.
- Exclude `solo`, `full_body`, `transparent_background`, `holding`, and other scene/pose tags. The costume's swimsuit tags do not leak into the default row.
- The [sample selection table](../../../../curation/zenless-appearance-2026-09-27/build.py) validates every chosen general tag against its exact post. That automated check does not validate the picture itself.

## Source and credential discipline

Use documented public endpoints or an already authorized connector. Bound calls and retries; reuse saved inventory instead of immediately querying again. Never search local application settings for keys, and never commit credentials or full raw API responses. If the source lacks enough coverage, report the coverage gap rather than switching silently to loosely associated fan art.
