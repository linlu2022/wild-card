"""Export the manually selected first ZZZ appearance batch from inventory.csv."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# Post ID: (exact Danbooru character tag, selected general tags from that post).
# Each outfit has its own row; tags are deliberately sparse and visual.
SELECTED = {
    "9749899": ("alice_thymefield", "rabbit_ears blonde_hair long_hair low_twintails heterochromia green_skirt white_shirt black_pantyhose fingerless_gloves sphere_hair_ornament"),
    "9749900": ("alice_thymefield_(sea_of_thyme)", "rabbit_ears blonde_hair long_hair low_twintails heterochromia swimsuit apron frilled_skirt choker sandals sphere_hair_ornament"),
    "9426375": ("anby_demara", "grey_hair short_hair orange_eyes green_jacket black_skirt crop_top black_thighhighs fingerless_gloves thigh_strap"),
    "8991458": ("anby_demara_(silver_soldier)", "grey_hair short_hair yellow_eyes white_skirt black_shorts black_thighhighs white_gloves black_hairband boots"),
    "8974626": ("astra_yao", "black_hair long_hair blunt_bangs red_eyes white_dress white_hairband pearl_necklace earrings thigh_strap"),
    "8974627": ("astra_yao_(chandelier)", "black_hair long_hair blunt_bangs purple_eyes black_dress white_hairband pearl_necklace earrings detached_sleeves"),
    "9426379": ("belle_(zenless_zone_zero)", "blue_hair short_hair green_eyes black_shirt grey_shorts single_thighhigh fingerless_gloves orange_belt orange_socks"),
    "9426420": ("belle_(delicate_sunlight)_(zenless_zone_zero)", "blue_hair short_hair green_eyes chinese_clothes dress white_pantyhose tassel_earrings hair_ornament"),
    "10146033": ("belle_(summer_skies)_(zenless_zone_zero)", "blue_hair short_hair green_eyes bucket_hat orange_bikini white_shirt tied_shirt orange_shorts sandals"),
    "11635927": ("belle_(brilliance_of_stars)_(zenless_zone_zero)", "blue_hair short_hair green_eyes school_uniform miniskirt pleated_skirt black_hat black_socks"),
    "9426380": ("ellen_joe", "shark_girl shark_tail black_hair red_hair red_eyes short_hair maid black_dress black_pantyhose maid_headdress metal_collar scar_on_tail"),
    "9426381": ("ellen_joe_(on_campus)", "shark_girl shark_tail black_hair red_hair red_eyes short_hair school_uniform white_shirt black_skirt brown_pantyhose loafers"),
    "8580073": ("hoshimi_miyabi", "fox_ears black_hair long_hair blunt_bangs red_eyes blue_cape black_skirt fingerless_gloves pantyhose katana"),
    "11321529": ("hoshimi_miyabi_(dignified_blossom)", "fox_ears black_hair long_hair hime_cut red_eyes black_dress white_dress japanese_clothes wide_sleeves hair_flower"),
    "8283381": ("jane_doe_(zenless_zone_zero)", "animal_ears tail black_hair long_hair grey_eyes black_shirt black_shorts grey_jacket grey_pantyhose red_nails"),
    "10728982": ("jane_doe_(nocturne_of_light)_(zenless_zone_zero)", "mouse_ears mouse_tail black_hair red_hair green_eyes two-tone_one-piece_swimsuit o-ring_one-piece_swimsuit fishnet_sleeves"),
    "9426383": ("luciana_de_montefio", "blonde_hair long_hair side_ponytail orange_eyes black_hat black_jacket black_shorts black_boots spiked_helmet"),
    "12026917": ("luciana_de_montefio_(princess_on_holiday)", "blonde_hair very_long_hair side_ponytail red_eyes white_bikini pink_jacket visor_cap yellow_scrunchie high_heel_sandals"),
    "11017351": ("nangong_yu", "black_hair pink_hair medium_hair twintails red_eyes halo mechanical_wings white_dress black_thighhighs"),
    "11017352": ("nangong_yu_(rhapsody's_muse)", "black_hair pink_hair medium_hair twintails red_eyes purple_halo mechanical_wings black_skirt black_thighhighs sailor_collar"),
    "7813605": ("nicole_demara", "pink_hair long_hair green_eyes mole_under_eye crop_top black_shorts black_thighhighs single_thighhigh heart_collar"),
    "9426378": ("nicole_demara_(cunning_cutie)", "pink_hair long_hair green_eyes mole denim_shorts crop_top pink_arm_warmers pink_leg_warmers fishnet_socks"),
    "11882348": ("remielle_dan", "pink_hair long_hair purple_eyes mechanical_wings white_wings white_dress white_pantyhose white_thighhighs"),
    "11882349": ("remielle_dan_(moonlight_whispers)", "pink_hair long_hair purple_eyes mechanical_wings black_wings black_dress black_thighhighs hairclip"),
    "11882351": ("remielle_dan_(seashade_pas_seul)", "pink_hair purple_eyes white_wings white_one-piece_swimsuit high_heel_sandals pink_nails bracelet"),
    "12024164": ("sigrid_de_l'azur", "horse_ears horse_tail blonde_hair very_long_hair high_ponytail blue_eyes white_boots bridal_gauntlets"),
    "12024169": ("sigrid_de_l'azur_(majestic_wavechaser)", "horse_ears horse_tail blonde_hair very_long_hair high_ponytail blue_one-piece_swimsuit white_one-piece_swimsuit goggles_on_head blue_sandals"),
    "10734339": ("sunna_(zenless_zone_zero)", "green_hair long_hair ponytail green_eyes white_shirt red_necktie pink_arm_warmers striped_leg_warmers white_thighhighs wings"),
    "10734340": ("sunna_(afternoon_tea_break)_(zenless_zone_zero)", "long_hair black_dress black_garter_straps red_bow ghost_hair_ornament white_thighhighs white_wings"),
    "9638441": ("ukinami_yuzuha", "red_hair very_long_hair low_twintails white_bow skirt sweater striped_thighhighs thigh_strap"),
    "9638442": ("ukinami_yuzuha_(tanuki_in_broad_daylight)", "red_hair very_long_hair low_twintails green_eyes pink_one-piece_swimsuit white_one-piece_swimsuit heart-shaped_eyewear hair_bow"),
    "11626417": ("velina_airgid", "white_hair very_long_hair purple_eyes pointy_ears blue_dress white_thighhighs gold_ascot gold_earrings"),
    "11626419": ("velina_airgid_(shade_of_leisure)", "grey_hair very_long_hair purple_eyes pointy_ears black_shirt grey_skirt black_boots blue_nails"),
    "9196669": ("vivian_banshee", "purple_hair long_hair red_eyes pointy_ears mole_under_eye drill_hair white_dress black_skirt pantyhose umbrella"),
    "10146034": ("vivian_banshee_(iris_of_the_shore)", "purple_hair long_hair red_eyes pointy_ears mole_under_eye frilled_one-piece_swimsuit purple_nails parasol high_heel_sandals"),
    "9424179": ("yixuan_(zenless_zone_zero)", "white_hair very_long_hair yellow_eyes black_shorts black_gloves hairclip armlet"),
    "9426385": ("yixuan_(trails_of_ink)_(zenless_zone_zero)", "white_hair long_hair yellow_eyes black_shirt black_pantyhose black_shoes blue_rose hairclip"),
}


def main():
    inventory = list(csv.DictReader((HERE / "inventory.csv").open(encoding="utf-8", newline="")))
    by_id = {row["image_id"]: row for row in inventory if row["image_type"] == "post"}
    assert len(SELECTED) == len(set(SELECTED))
    out = []
    for post_id, (tag, tags_text) in SELECTED.items():
        row = by_id[post_id]
        general = set(row["general_tags"].split())
        chars = set(row["character_tags"].split())
        tags = tags_text.split()
        missing = set(tags) - general
        assert not missing, (post_id, missing)
        assert tag in chars, (post_id, tag, chars)
        assert "zenless_zone_zero" in row["copyright_tags"].split(), post_id
        assert "1girl" in general and "official_art" in row["meta_tags"].split(), post_id
        assert len(tags) == len(set(tags)), post_id
        out.append({
            "character": tag,
            "copyright": "zenless_zone_zero",
            "trigger": tag.replace("_", " ") + ", zenless zone zero",
            "core_tags": ", ".join(["1girl"] + [part.replace("_", " ") for part in tags]),
            "url": row["url"],
        })
    out.sort(key=lambda item: item["character"])
    with (HERE / "reviewed.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["character", "copyright", "trigger", "core_tags", "url"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    audit = {}
    for row in inventory:
        key = (row["image_type"], row["image_id"])
        if key in audit:
            audit[key]["wiki_titles"] += ";" + row["wiki_title"]
            continue
        if row["image_type"] == "asset":
            decision = "deferred_asset_without_post_tags"
        elif row["image_id"] in SELECTED:
            decision = "included_first_batch"
        elif "1girl" not in row["general_tags"].split():
            decision = "deferred_not_single_girl_evidence"
        elif "official_art" not in row["meta_tags"].split():
            decision = "deferred_source_verification"
        else:
            decision = "deferred_outside_first_batch_or_subject_check"
        audit[key] = {
            "image_type": row["image_type"],
            "image_id": row["image_id"],
            "wiki_titles": row["wiki_title"],
            "label": row["label"],
            "decision": decision,
            "url": row["url"],
            "source": row.get("source", ""),
        }
    with (HERE / "audit.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["image_type", "image_id", "wiki_titles", "label", "decision", "url", "source"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(audit.values(), key=lambda item: (item["image_type"], int(item["image_id"]))))
    print(f"reviewed {len(out)} rows, {len({r['character'] for r in out})} unique tags")


if __name__ == "__main__":
    main()
