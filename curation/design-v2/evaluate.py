"""Offline design exercise, not a production curator or an accuracy benchmark.

Run from any directory: python curation/design-v2/evaluate.py
The model consumes explicit review conclusions; it cannot establish their truth.
Probes execute selected current helpers on counterexamples without network/GPU use.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = {
    "identity": "verified", "gender": "female", "scope": "allowed",
    "form": "official", "relations": "verified", "binding": "exact",
    "source": "verified_official", "traits": "verified",
    "conflicts": "resolved", "alias": "distinct",
}
ENUMS = {
    "identity": {"verified", "unknown", "companion_object"},
    "gender": {"female", "male", "unknown"},
    "scope": {"allowed", "outside", "unknown"},
    "form": {"official", "fan", "umbrella", "unknown"},
    "relations": {"verified", "cooccurrence", "unknown"},
    "binding": {"exact", "other_form", "ambiguous_group", "unknown"},
    "source": {"verified_official", "verified_archive", "official_tag_only", "fan_only", "missing"},
    "traits": {"verified", "unreviewed", "blind_inheritance"},
    "conflicts": {"resolved", "unresolved", "marker_only"},
    "alias": {"distinct", "verified_existing", "unverified"},
}


def proposed_gate(record: dict) -> str:
    """Illustrate admission rules AFTER evidence review, with no numeric confidence."""
    if any(record.get(key) not in allowed for key, allowed in ENUMS.items()):
        return "needs_review"
    if record["identity"] == "companion_object" or record["gender"] == "male":
        return "excluded"
    if record["scope"] == "outside" or record["form"] == "fan":
        return "excluded"
    if record["identity"] != "verified" or record["gender"] != "female":
        return "needs_review"
    if record["scope"] != "allowed" or record["form"] != "official":
        return "needs_review"
    if record["relations"] != "verified" or record["binding"] != "exact":
        return "needs_review"
    if record["conflicts"] != "resolved" or record["alias"] == "unverified":
        return "needs_review"
    if record["alias"] == "verified_existing":
        return "merge_reference"
    if record["source"] not in {"verified_official", "verified_archive"}:
        return "identity_only"
    if record["traits"] != "verified":
        return "needs_review"
    return "release_full"


# These are declared review states, not freshly established facts about all named roles.
CASES = [
    ("S01", "Anastella: reviewed companion object, female co-tags cannot admit it", {"identity": "companion_object"}, "excluded"),
    ("S02", "Binah: reviewed fan anthropomorphism", {"form": "fan", "source": "fan_only"}, "excluded"),
    ("S03", "Canonically female robot with verified design", {}, "release_full"),
    ("S04", "SAM trigger with human Firefly appearance", {"binding": "other_form"}, "needs_review"),
    ("S05", "SAM armor design after identity and form review", {}, "release_full"),
    ("S06", "Nagisa default receives swimsuit evidence", {"binding": "other_form"}, "needs_review"),
    ("S07", "Nagisa swimsuit with corresponding official design", {}, "release_full"),
    ("S08", "One verified official design can support a sparse new role", {"image_count": 1}, "release_full"),
    ("S09", "Hundreds of fan posts do not establish canonical appearance", {"source": "fan_only", "image_count": 200}, "identity_only"),
    ("S10", "Official_art tag alone is not origin verification", {"source": "official_tag_only"}, "identity_only"),
    ("S11", "Identity remains unknown despite many girl tags", {"identity": "unknown", "image_count": 10000}, "needs_review"),
    ("S12", "Male identity in female fan depictions", {"gender": "male", "source": "fan_only"}, "excluded"),
    ("S13", "Unknown gender is not guessed from anatomy", {"gender": "unknown"}, "needs_review"),
    ("S14", "Frequent co-tag is not a verified identity relation", {"relations": "cooccurrence"}, "needs_review"),
    ("S15", "Group art without target-bound visual evidence", {"binding": "ambiguous_group"}, "needs_review"),
    ("S16", "Group image reviewed with located target and derived features", {}, "release_full"),
    ("S17", "True multicolored eyes after location-specific verification", {"eye_tags": ["pink_eyes", "blue_eyes", "multicolored_eyes"]}, "release_full"),
    ("S18", "Multicolor marker alone cannot resolve conflicting evidence", {"conflicts": "marker_only"}, "needs_review"),
    ("S19", "Unexplained long and short hair", {"conflicts": "unresolved"}, "needs_review"),
    ("S20", "Verified same character and same form alias", {"alias": "verified_existing"}, "merge_reference"),
    ("S21", "Similar feature sets do not prove alias identity", {"alias": "unverified"}, "needs_review"),
    ("S22", "Real alternate form with few visible differences", {}, "release_full"),
    ("S23", "Racing Miku copied blindly from base", {"traits": "blind_inheritance"}, "needs_review"),
    ("S24", "New age or robot form cannot blindly inherit body traits", {"traits": "blind_inheritance"}, "needs_review"),
    ("S25", "FGO membership unresolved from copyright co-tag", {"scope": "unknown"}, "needs_review"),
    ("S26", "Official in-game collaboration allowed by chosen scope", {}, "release_full"),
    ("S27", "Promo-only depiction excluded by chosen scope", {"scope": "outside"}, "excluded"),
    ("S28", "Unavailable source with previously verified archived evidence", {"source": "verified_archive"}, "release_full"),
    ("S29", "Unavailable source with no evidence retained", {"source": "missing"}, "identity_only"),
    ("S30", "Duplicate images cannot upgrade official-tag evidence", {"source": "official_tag_only", "image_count": 1000000}, "identity_only"),
    ("S31", "Generic family name has no selected concrete form", {"form": "umbrella"}, "needs_review"),
    ("S32", "Unreviewed features remain blocked even with official sources", {"traits": "unreviewed"}, "needs_review"),
    ("S33", "Missing classification fails closed", {"gender": None}, "needs_review"),
    ("S34", "An officially female companion CHARACTER is not a companion object", {}, "release_full"),
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def actual_probes(comfy_root: Path) -> dict:
    scripts = ROOT / ".claude/skills/curate-character-wildcards/scripts"
    sys.path.insert(0, str(scripts))
    draft = load_module("design_probe_draft", scripts / "draft_danbooru_pack.py")
    finalizer = load_module("design_probe_finalizer", scripts / "finalize_reviewed_packs.py")
    def posts(tags, general="1girl blue_eyes long_hair", duplicate=False):
        return [{"id": 1 if duplicate else i + 1, "tag_string_character": tags,
                 "tag_string_general": general} for i in range(6)]
    probes = {}
    for key, target, records in [
        ("companion_cotag", "doll", posts("doll owner")),
        ("base_form_swimsuit", "nagisa_(blue_archive)", posts("nagisa_(blue_archive) nagisa_(swimsuit)_(blue_archive)")),
        ("one_image_six_reposts", "subject", posts("subject", duplicate=True)),
        ("exact_character_but_two_girls", "subject", posts("subject", general="2girls blue_eyes long_hair")),
    ]:
        selected, alias, relation = draft.isolated_subject(records, target)
        probes[key] = {"accepted_posts": len(selected), "possible_alias": alias,
                       "method": relation, "current_rule_accepts": len(selected) >= 5}
        assert len(selected) == 6, (key, "current helper changed; revise the design evidence")
    row = {"core_tags": "1girl, brown eyes, green eyes"}
    removed = finalizer.resolve_color_conflicts(row)
    probes["color_frequency_tiebreak"] = {"kept": row["core_tags"], "removed": removed}
    assert removed == ["green eyes"]
    markers = {"core_tags": "1girl, pink eyes, blue eyes, multicolored eyes"}
    assert finalizer.resolve_color_conflicts(markers) == []
    probes["multicolored_eyes_preserved"] = True

    source_path = comfy_root / "comfy/sd1_clip.py"
    if source_path.is_file():
        raw = source_path.read_bytes()
        tree = ast.parse(raw.decode("utf-8-sig"))
        names = {"parse_parentheses", "token_weights", "escape_important", "unescape_important"}
        funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        assert len(funcs) == 4
        namespace = {}
        exec(compile(ast.Module(body=funcs, type_ignores=[]), str(source_path), "exec"), namespace)
        def parse(value):
            return [(namespace["unescape_important"](text), weight)
                    for text, weight in namespace["token_weights"](namespace["escape_important"](value), 1.0)]
        plain = parse("circe_(fate)")
        escaped = parse(r"circe_\(fate\)")
        assert plain == [("circe_", 1.0), ("fate", 1.1)]
        assert escaped == [("circe_(fate)", 1.0)]
        probes["comfy_weighted_parentheses"] = {"source": "comfy/sd1_clip.py",
            "source_sha256": hashlib.sha256(raw).hexdigest(), "plain": plain, "escaped": escaped,
            "scope": "Extracted local parser functions; weighted mode only; no model tokenization or generation"}
    else:
        probes["comfy_weighted_parentheses"] = {"skipped": "Local ComfyUI parser unavailable"}

    engine = load_module("design_probe_engine", ROOT / "wildcard_engine.py")
    engine.wildcard_dict = {"design_case": ["1girl, red_hair"]}
    output = engine.process("__design_case__, __design_case__", seed=11)
    assert output == "1girl, red_hair, 1girl, red_hair"
    probes["repeated_wildcard_has_no_global_dedup"] = output
    engine.wildcard_dict = {"design_case": [r"circe_\(fate\), 1girl"]}
    output = engine.process("__design_case__", seed=11)
    assert output == r"circe_\(fate\), 1girl"
    probes["engine_preserves_parenthesis_escapes"] = output
    return probes


def baseline() -> dict:
    packs = {}
    eye_markers = {"heterochromia", "multicolored_eyes", "two-tone_eyes"}
    eye_colors = {f"{c}_eyes" for c in "black white grey silver brown red orange yellow green blue aqua purple pink".split()}
    for path in sorted((ROOT / "wildcards").glob("*_women.txt")):
        raw = path.read_bytes()
        lines = raw.decode("utf-8").splitlines()
        same_traits = defaultdict(list)
        eye_flags = []
        for index, line in enumerate(lines, 1):
            parts = line.split(", ")
            tags = set(parts[3:])
            same_traits[tuple(sorted(tags))].append({"line": index, "tag": parts[1]})
            if len(tags & eye_colors) > 1 and not tags & eye_markers:
                eye_flags.append({"line": index, "tag": parts[1]})
        packs[path.stem] = {"sha256": hashlib.sha256(raw).hexdigest(), "rows": len(lines),
            "rows_with_parentheses": sum("(" in s or ")" in s for s in lines),
            "identical_trait_groups": [v for v in same_traits.values() if len(v) > 1],
            "multiple_eye_colors_without_markers": eye_flags}
    return {"total_rows": sum(p["rows"] for p in packs.values()), "packs": packs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results.json"))
    parser.add_argument("--comfy-root", type=Path, default=ROOT.parents[1])
    args = parser.parse_args()
    scenarios = []
    for case_id, title, changes, expected in CASES:
        record = {**BASE, **changes}
        actual = proposed_gate(record)
        scenarios.append({"id": case_id, "scenario": title, "changes_from_base": changes,
                          "expected": expected, "actual": actual, "passed": expected == actual})
    # Missing ANY essential field cannot release. Counts cannot bypass an evidence gate.
    missing_fields = {}
    for key in BASE:
        record = {**BASE}
        del record[key]
        missing_fields[key] = proposed_gate(record) == "needs_review"
    all_passed = all(c["passed"] for c in scenarios) and all(missing_fields.values())
    code_files = ["wildcard_engine.py", ".claude/skills/curate-character-wildcards/scripts/draft_danbooru_pack.py",
                  ".claude/skills/curate-character-wildcards/scripts/finalize_reviewed_packs.py",
                  ".claude/skills/curate-character-wildcards/scripts/csv_to_wildcard.py"]
    result = {"purpose": "Design model consistency and current-code counterexamples; NOT semantic accuracy",
              "design_version": "v2.3", "python": sys.version.split()[0],
              "probe_code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in code_files},
              "baseline": baseline(), "reviewed_base_case": BASE, "scenarios": scenarios,
              "missing_field_checks": missing_fields, "current_code_probes": actual_probes(args.comfy_root),
              "model_passed": all_passed}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Design cases: {sum(c['passed'] for c in scenarios)}/{len(scenarios)}; missing fields: {sum(missing_fields.values())}/{len(missing_fields)}")
    print(f"Baseline: {result['baseline']['total_rows']} rows; output: {args.output.name}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
