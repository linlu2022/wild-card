# Historical frequency-based character pipeline

These two scripts generated earlier character packs and are retained only so the dated [v2 design probes](../design-v2/evaluate.py) and [old pack records](../../docs/character-packs.md) remain inspectable. They are not part of the active skill workflow. Use the [Wiki Appearance procedure](../../.claude/skills/curate-character-wildcards/SKILL.md) for new appearance packs.

`finalize_reviewed_packs.py` imports the active `csv_to_wildcard.py`; when running the historical script directly, add `.claude/skills/curate-character-wildcards/scripts` to `PYTHONPATH`. The design probe sets this path itself.
