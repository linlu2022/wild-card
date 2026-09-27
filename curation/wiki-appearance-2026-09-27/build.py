"""Export nine conservative first-batch appearance packs from exact Wiki-linked posts.

Every selected tag below must occur on the supporting post. Selection and the
official in-work judgment are editorial decisions; audit.csv keeps the gaps.
"""

import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# post_id: exact character/form tag | visible general tags on that post
SELECTED = {
    "blue_archive": {
        "4447168": "aris_(blue_archive)|blue_hair blue_eyes school_uniform black_hairband jacket necktie",
        "11460939": "aris_(winter)_(blue_archive)|blue_eyes brown_coat blue_scarf earmuffs white_skirt black_pantyhose",
        "11437436": "asuna_(blue_archive)|brown_hair blue_eyes black_dress frilled_apron maid_headdress blue_choker",
        "11575883": "asuna_(bunny)_(blue_archive)|blonde_hair blue_eyes rabbit_ears black_pantyhose blue_bowtie",
        "4301865": "hoshino_(blue_archive)|pink_hair yellow_eyes school_uniform plaid_skirt fingerless_gloves halo",
        "4301860": "shiroko_(blue_archive)|grey_hair wolf_ears school_uniform pleated_skirt green_gloves",
        "11953294": "shiroko_(swimsuit)_(blue_archive)|grey_hair wolf_ears black_one-piece_swimsuit black_sandals jacket",
        "4369856": "yuuka_(blue_archive)|blue_hair blue_eyes black_jacket black_skirt blue_necktie",
        "5785246": "yuuka_(track)_(blue_archive)|blue_hair blue_eyes gym_uniform blue_jacket black_shirt",
        "11312971": "hina_(blue_archive)|purple_eyes blue_jacket black_skirt purple_thighhighs black_gloves",
        "8024215": "hina_(dress)_(blue_archive)|purple_eyes purple_dress purple_gloves purple_pantyhose high_ponytail",
    },
    "azur_lane": {
        "2957255": "enterprise_(azur_lane)|white_hair purple_eyes black_coat black_skirt white_hat black_thighhighs",
        "3052729": "enterprise_(starlight_oath)_(azur_lane)|white_hair purple_eyes wedding_dress crown white_bow",
        "2934193": "belfast_(azur_lane)|white_hair purple_eyes black_dress white_apron maid_headdress white_gloves",
        "3171227": "belfast_(the_pledge_of_claddagh)_(azur_lane)|white_hair blue_eyes wedding_dress blue_ribbon",
        "3779109": "akagi_(azur_lane)|black_hair red_eyes fox_ears fox_tail red_skirt wide_sleeves",
        "2967767": "akagi_(plum_and_snow)_(azur_lane)|black_hair red_eyes fox_ears fox_tail black_kimono red_choker",
        "3254439": "taihou_(azur_lane)|black_hair red_eyes red_kimono black_thighhighs twintails",
        "3764453": "taihou_(phoenix's_spring_song)_(azur_lane)|black_hair red_eyes red_dress black_gloves fishnet_thighhighs",
    },
    "genshin_impact": {
        "5304439": "amber_(genshin_impact)|brown_hair orange_eyes red_jacket brown_shorts red_hairband",
        "5577573": "amber_(100%_outrider)_(genshin_impact)|brown_hair brown_eyes red_jacket red_shorts red_ribbon",
        "4117035": "barbara_(genshin_impact)|blonde_hair blue_eyes white_dress mini_hat white_pantyhose",
        "4118677": "jean_(genshin_impact)|blonde_hair blue_eyes white_shirt black_gloves black_capelet",
        "4116150": "keqing_(genshin_impact)|purple_hair purple_eyes cone_hair_bun black_pantyhose purple_gloves",
        "7901424": "keqing_(opulent_splendor)_(genshin_impact)|purple_hair pink_eyes multicolored_dress brown_pantyhose cone_hair_bun",
        "6715359": "furina_(genshin_impact)|blue_hair blue_eyes blue_hat blue_jacket white_shorts mismatched_gloves",
        "4296018": "ganyu_(genshin_impact)|blue_hair purple_eyes bodystocking black_gloves detached_sleeves",
        "7901426": "ganyu_(twilight_blossom)_(genshin_impact)|blue_hair purple_eyes multicolored_dress black_gloves detached_sleeves",
    },
    "honkai_star_rail": {
        "7732499": "march_7th_(preservation)_(honkai:_star_rail)|blue_eyes blue_jacket blue_skirt black_choker black_gloves",
        "7732510": "march_7th_(hunt)_(honkai:_star_rail)|pink_hair pink_eyes black_dress red_jacket black_gloves",
        "8704009": "march_7th_(nascent_spring)_(honkai:_star_rail)|pink_hair blue_eyes blue_dress white_thighhighs blue_bowtie",
        "7691435": "acheron_(honkai:_star_rail)|purple_hair long_hair black_boots short_shorts",
        "7726554": "firefly_(honkai:_star_rail)|grey_hair green_eyes green_dress black_thighhighs black_headband",
        "9556115": "firefly_(spring_missive)_(honkai:_star_rail)|grey_hair green_hair grey_skirt white_shirt white_thighhighs",
        "7691440": "robin_(honkai:_star_rail)|long_hair purple_dress white_gloves halo",
        "12258549": "robin_(summeretto)_(honkai:_star_rail)|blue_hair green_eyes white_bikini sandals halo",
        "8704047": "the_herta_(honkai:_star_rail)|brown_hair purple_eyes black_dress witch_hat detached_sleeves",
        "7691377": "ruan_mei_(honkai:_star_rail)|black_hair green_eyes green_gloves hair_intakes",
        "10777843": "ruan_mei_(plumblossom_letter)_(honkai:_star_rail)|black_hair grey_eyes blue_dress blue_gloves hair_flower",
        "7689924": "silver_wolf_(honkai:_star_rail)|grey_hair grey_eyes black_jacket black_gloves short_shorts",
        "11189802": "silver_wolf_(lv.999)_(honkai:_star_rail)|grey_hair grey_eyes black_jacket black_shorts holographic_wings",
        "7691426": "black_swan_(honkai:_star_rail)|purple_hair veil black_gloves purple_sleeves",
        "9118597": "castorice_(honkai:_star_rail)|purple_hair purple_eyes white_dress white_thighhighs",
        "11215514": "castorice_(gossamer_flutter)_(honkai:_star_rail)|purple_hair purple_eyes purple_dress butterfly_hair_ornament",
    },
    "arknights": {
        "3563885": "amiya_(arknights)|brown_hair rabbit_ears black_jacket blue_skirt",
        "3877031": "amiya_(newsgirl)_(arknights)|brown_hair rabbit_ears black_hat ponytail",
        "3563838": "exusiai_(arknights)|red_hair halo white_jacket black_skirt",
        "3797934": "exusiai_(wild_operation)_(arknights)|red_hair halo jacket shorts",
        "3563868": "texas_(arknights)|grey_hair wolf_ears white_jacket black_shorts",
        "3799559": "texas_(winter_messenger)_(arknights)|black_hair wolf_ears white_jacket white_shorts",
        "4117242": "surtr_(arknights)|red_hair purple_eyes black_dress black_thighhighs",
        "4556350": "surtr_(liberte_echec)_(arknights)|red_hair purple_eyes black_shirt denim_skirt",
        "3563860": "skadi_(arknights)|grey_hair red_eyes black_hat grey_jacket",
        "4044987": "skadi_(waverider)_(arknights)|grey_hair red_eyes sun_hat sandals",
        "4496870": "kal'tsit_(arknights)|white_hair green_eyes green_dress jacket",
        "10839248": "kal'tsit_(remnant)_(arknights)|grey_hair green_eyes green_dress black_coat",
        "4179711": "mudrock_(arknights)|full_armor covered_face white_jacket black_boots",
        "4679495": "mudrock_(silent_night)_(arknights)|white_hair red_eyes black_bikini black_choker",
        "3563808": "ch'en_(arknights)|blue_hair red_eyes black_jacket black_shorts",
        "3794911": "ch'en_(ageless_afterglow)_(arknights)|blue_hair red_eyes red_dress black_shorts",
    },
    "endfield": {
        "10267123": "akekuri_(arknights)|red_hair blue_eyes animal_ears fingerless_gloves",
        "8680245": "arclight_(arknights)|blue_hair aqua_eyes horse_ears hoodie",
        "8679871": "avywenna_(arknights)|grey_hair aqua_eyes rabbit_ears armor",
        "8679765": "chen_qianyu_(arknights)|black_hair red_eyes white_skirt blue_capelet",
        "8680140": "ember_(arknights)|blue_hair orange_eyes armor halo",
        "10267280": "estella_(arknights)|blue_eyes cat_tail white_hat fingerless_gloves",
        "8571922": "female_endministrator_(arknights)|black_hair black_jacket white_sweater black_pantyhose",
        "10267390": "last_rite_(arknights)|blue_hair red_eyes pointy_ears blue_gloves",
        "8679725": "perlica_(arknights)|grey_hair aqua_eyes white_dress white_jacket bird_ears",
        "8679794": "xaihi_(arknights)|aqua_hair aqua_eyes black_dress black_pantyhose",
        "8680192": "yvonne_(arknights)|pink_hair black_gloves black_boots hair_intakes",
    },
    "fate_grand_order": {
        "11512188": "mash_kyrielight_(chaldea_uniform)|purple_hair purple_eyes white_jacket black_skirt white_necktie",
        "2101681": "jeanne_d'arc_(ruler)_(fate)|blonde_hair blue_eyes armor armored_boots crown",
        "8893963": "jeanne_d'arc_(swimsuit_archer)_(first_ascension)_(fate)|blonde_hair blue_eyes black_bikini blue_jacket platform_sandals",
        "9123129": "scathach_(lancer)_(fate)|purple_hair red_eyes purple_bodysuit shoulder_armor",
        "4496259": "scathach_(swimsuit_assassin)_(fate)|purple_hair red_eyes bikini bikini_skirt hair_flower",
        "9147551": "ishtar_(first_ascension)_(fate)|black_hair red_eyes black_thighhighs gold_earrings white_skirt",
        "9158886": "ishtar_(swimsuit_rider)_(fate)|black_hair red_eyes white_one-piece_swimsuit pink_jacket gold_earrings",
        "9166609": "ereshkigal_(fate)|blonde_hair red_eyes red_cape black_thighhighs black_choker",
        "8003029": "ereshkigal_(swimsuit_beast)_(fate)|blonde_hair red_eyes white_one-piece_swimsuit sandals",
        "9229851": "morgan_le_fay_(first_ascension)_(fate)|white_hair blue_eyes black_dress blue_choker black_boots",
        "7591341": "morgan_le_fay_(second_ascension)_(fate)|grey_hair blue_eyes black_dress blue_choker",
    },
    "vocaloid": {
        "6549225": "hatsune_miku|aqua_hair aqua_eyes aqua_necktie black_skirt black_thighhighs twintails",
        "662258": "hatsune_miku_(append)|aqua_hair long_hair detached_sleeves necktie twintails",
        "1482524": "hatsune_miku_(vocaloid3)|green_hair blue_eyes skirt necktie twintails",
        "4427252": "hatsune_miku_(nt)|aqua_hair aqua_eyes black_skirt white_shirt aqua_ribbon",
        "10921388": "hatsune_miku_(vocaloid6)|aqua_hair aqua_eyes black_skirt grey_shirt aqua_necktie",
        "4646426": "megurine_luka|pink_hair blue_eyes black_skirt black_thighhighs gold_boots",
        "2003104": "megurine_luka_(vocaloid4)|pink_hair aqua_eyes black_skirt black_thighhighs",
        "8926591": "meiko_(vocaloid)|brown_hair brown_eyes red_jacket red_skirt brown_boots",
        "1620945": "meiko_(vocaloid3)|brown_hair brown_eyes red_shirt red_skirt brown_boots",
        "2433899": "otomachi_una_(sugar)|blue_hair blue_eyes frilled_dress red_necktie",
        "2433900": "otomachi_una_(spicy)|blue_hair blue_eyes blonde_hair jacket red_necktie",
        "1044893": "yuzuki_yukari|purple_hair purple_eyes purple_dress purple_thighhighs rabbit_hood",
        "2940327": "kizuna_akari|white_hair blue_eyes black_coat orange_pantyhose",
        "1045204": "ia_(vocaloid)|grey_hair blue_eyes skirt thighhighs",
    },
    "touhou": {
        "6586872": "hakurei_reimu|black_hair red_eyes red_shirt red_skirt red_bow detached_sleeves",
        "6586873": "kirisame_marisa|blonde_hair red_eyes black_hat black_skirt white_apron",
        "6586874": "kochiya_sanae|green_hair green_eyes blue_skirt frog_hair_ornament snake_hair_ornament",
        "8331419": "flandre_scarlet|blonde_hair red_eyes red_skirt white_hat white_shirt",
    },
}

COPYRIGHT = {
    "blue_archive": "blue_archive", "azur_lane": "azur_lane",
    "genshin_impact": "genshin_impact", "honkai_star_rail": "honkai:_star_rail",
    "arknights": "arknights", "endfield": "arknights:_endfield",
    "fate_grand_order": "fate/grand_order", "vocaloid": "vocaloid",
    "touhou": "touhou",
}


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(name, selections):
    inventory = list(csv.DictReader((HERE / f"{name}_inventory.csv").open(encoding="utf-8", newline="")))
    posts = {row["image_id"]: row for row in inventory if row["image_type"] == "post"}
    reviewed = []
    for post_id, definition in selections.items():
        char, _, chosen = definition.partition("|")
        row = posts[post_id]
        tags = chosen.split()
        assert set(tags) <= set(row["general_tags"].split()), (name, post_id, set(tags) - set(row["general_tags"].split()))
        assert char in row["character_tags"].split(), (name, post_id, char)
        assert COPYRIGHT[name] in row["copyright_tags"].split(), (name, post_id, "copyright")
        assert "official_art" in row["meta_tags"].split(), (name, post_id, "official_art")
        assert "1girl" in row["general_tags"].split(), (name, post_id, "1girl")
        assert len(tags) == len(set(tags)), (name, post_id, "duplicate tags")
        reviewed.append({
            "character": char, "copyright": COPYRIGHT[name],
            "trigger": char.replace("_", " ") + ", " + COPYRIGHT[name].replace("_", " "),
            "core_tags": ", ".join(["1girl"] + [tag.replace("_", " ") for tag in tags]),
            "url": row["url"],
        })
    assert len({r["character"] for r in reviewed}) == len(reviewed), name
    reviewed.sort(key=lambda row: row["character"])
    write_csv(HERE / f"{name}_reviewed.csv", ["character", "copyright", "trigger", "core_tags", "url"], reviewed)

    audit = {}
    for row in inventory:
        key = (row["image_type"], row["image_id"] or row["wiki_title"])
        if key in audit:
            audit[key]["wiki_titles"] += ";" + row["wiki_title"]
            continue
        if not row["image_id"]:
            reason = "deferred_missing_wiki_or_appearance"
        elif row["image_type"] == "asset":
            reason = "deferred_asset_without_post_tags"
        elif row["image_id"] in selections:
            reason = "included_first_batch"
        elif not row["character_tags"]:
            reason = "deferred_missing_character_tags"
        elif "1girl" not in row["general_tags"].split():
            reason = "deferred_subject_attribution_or_not_single_girl"
        elif "official_art" not in row["meta_tags"].split():
            reason = "deferred_official_in_work_verification"
        else:
            reason = "deferred_outside_first_batch_or_in_work_verification"
        audit[key] = {
            "image_type": row["image_type"], "image_id": row["image_id"],
            "status": row["status"],
            "wiki_titles": row["wiki_title"], "label": row["label"],
            "decision": reason, "url": row["url"], "source": row["source"].strip(),
        }
    write_csv(HERE / f"{name}_audit.csv", ["image_type", "image_id", "status", "wiki_titles", "label", "decision", "url", "source"],
              sorted(audit.values(), key=lambda r: (r["image_type"], int(r["image_id"] or 0), r["wiki_titles"])))
    counts = Counter(row["decision"] for row in audit.values())
    print(name, len(reviewed), "rows", len(audit), "candidates", dict(counts))


if __name__ == "__main__":
    assert len(SELECTED) == len(COPYRIGHT) == 9
    for pack, selected in SELECTED.items():
        build(pack, selected)
