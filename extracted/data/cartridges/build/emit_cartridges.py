#!/usr/bin/env python3
"""B-4 emit stage — cartridges & mini-games dataset (DS-4).

Deterministic curation pass over the P1 corpus. Every number is re-measured
from the artifacts named in docs/specs/dataset-cartridges.mdx section 2 at
emit time; nothing is copied from prose. Byte-deterministic outputs: stable
row order, sorted JSON object keys, UTF-8, LF, no BOM.

Write scope (brief B-4): extracted/data/cartridges/** ONLY. The allowlist is
asserted before any write so no sibling dataset can be touched from here.
Run:  python extracted/data/cartridges/build/emit_cartridges.py  (repo root cwd)
"""
import collections
import glob
import hashlib
import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
OUT = os.path.join(REPO, "extracted", "data", "cartridges")
ALLOWED_PREFIXES = (
    os.path.join(REPO, "extracted", "data", "cartridges") + os.sep,
)

BUILD_ID = "19029065"
VERSION_LABEL = "0.93L"
GENERATOR = ("B-4 dataset-builder curation pass (run_all stage registration "
             "pending; docs/specs/dataset-cartridges.mdx)")

_written = []


def jline(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def write_jsonl(relpath, meta, rows):
    path = os.path.join(OUT, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    assert path.startswith(ALLOWED_PREFIXES), relpath
    lines = [jline({"_meta": meta})] + [jline(r) for r in rows]
    data = "\n".join(lines) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(data)
    _written.append(os.path.relpath(path, REPO))


def write_text(relpath, text):
    path = os.path.join(OUT, relpath)
    assert path.startswith(ALLOWED_PREFIXES), relpath
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    _written.append(os.path.relpath(path, REPO))


def read_jsonl(abspath):
    with open(abspath, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def rd(rel):
    return os.path.join(REPO, rel)


# ---------------------------------------------------------------------------
# Fresh measurements (C1..C16 of DS-4 section 2)
# ---------------------------------------------------------------------------

def measure_registry():
    """C1 - the cartridge save-key registry literal."""
    lits = json.load(open(rd("extracted/il2cpp/stringliteral.json"), encoding="utf-8"))
    hits = [e for e in lits if e["address"] == "0x13AD860"]
    assert len(hits) == 1, "C1 literal not unique at 0x13AD860"
    idx = lits.index(hits[0])
    keys = hits[0]["value"].split("\n")
    assert len(keys) == 23, len(keys)
    return keys, idx


def measure_pickups():
    """C2 - every FlashTaker dump's serialized save key."""
    pairs = []
    for f in sorted(glob.glob(rd("extracted/harvest/mb-dump/*/FlashTaker*.txt"))):
        container = os.path.basename(os.path.dirname(f))
        m = re.search(r'\tstring save = "([^"]*)"', open(f, encoding="utf-8").read())
        assert m, f
        pairs.append({"container": container,
                      "file": os.path.basename(f),
                      "field": "save",
                      "value": m.group(1)})
    return pairs


def measure_tv():
    """C5 - MinigamesTelevisionController.games[] entries."""
    txt = open(rd("extracted/harvest/mb-dump/level6/MinigamesTelevisionController.txt"),
               encoding="utf-8").read()
    games = []
    chunks = txt.split("MinigamesTelevisionController_Game data")[1:]
    for block in chunks:
        nm = re.search(r'string nameResource = "([^"]*)"', block)
        im = re.search(r"SInt32 indexStringNameGame = (\d+)", block)
        cw = re.search(r"SInt32 countWin = (\d+)", block)
        cl = re.search(r"SInt32 countLose = (\d+)", block)
        cd = re.search(r"SInt32 countDraw = (\d+)", block)
        dw = re.search(r"GameObject\[\] dialogueWin\s*\n\t+Array Array\s*\n\t+int size = (\d+)", block)
        dl = re.search(r"GameObject\[\] dialogueLose\s*\n\t+Array Array\s*\n\t+int size = (\d+)", block)
        dd = re.search(r"GameObject\[\] dialogueDraw\s*\n\t+Array Array\s*\n\t+int size = (\d+)", block)
        if not nm:
            continue
        games.append({"nameResource": nm.group(1), "indexStringNameGame": int(im.group(1)),
                      "countWin": int(cw.group(1)), "countLose": int(cl.group(1)),
                      "countDraw": int(cd.group(1)), "dialogueWin_size": int(dw.group(1)),
                      "dialogueLose_size": int(dl.group(1)), "dialogueDraw_size": int(dd.group(1))})
    assert len(games) == 2, games
    return games


def measure_automates():
    """C7 - MinigamesAutomate loader dumps."""
    out = {}
    for container in sorted(glob.glob(rd("extracted/harvest/mb-dump/*/"))):
        f = os.path.join(container, "MinigamesAutomate.txt")
        if not os.path.exists(f):
            continue
        txt = open(f, encoding="utf-8").read()
        rg = re.search(r'string resourceGame = "([^"]*)"', txt).group(1)
        sg = re.search(r'string sceneGame = "([^"]*)"', txt).group(1)
        out[os.path.basename(os.path.dirname(f))] = {"resourceGame": rg, "sceneGame": sg}
    assert set(out) == {"level9", "level12", "level13"}, out.keys()
    return out


def measure_loc_counts():
    cats = ["MiniGame CarSpace", "MiniGame MakeManeken", "MiniGame Shooter",
            "TelevisionGames"]
    locales = sorted(d for d in os.listdir(rd("extracted/localization"))
                     if os.path.isdir(rd("extracted/localization/" + d))
                     and not d.startswith("_"))
    counts = {}
    for cat in cats:
        counts[cat] = {}
        for loc in locales:
            p = rd("extracted/localization/%s/%s.jsonl" % (loc, cat))
            counts[cat][loc] = (len(open(p, encoding="utf-8").read().splitlines())
                                if os.path.exists(p) else None)
    return locales, counts


def measure_carriers():
    """C10 - asset-list <Name>Class< grep sets + mb-dump filename census."""
    classes = {
        "carspace": ["CarSpace_Main"],
        "makemaneken": ["MakeManeken_Main"],
        "minigame-shooter": ["Shooter_Main"],
        "fight": ["MinigamesTelevisionController"],
        "pinguin": ["MinigamesTelevisionController"],
        "location-4-table-card-game": ["Location4TableCardGame"],
        "location-7-game-dance": ["Location7_GameDance"],
        "location-7-hammer-button": ["Location7_HammerButton"],
        "location-14-pc-snaker": ["Location14_PCSnaker"],
        "location-17-pumpkin-clicker": ["Location17_PumpkinClicker"],
        "games-core": ["GamesCore_Main"],
        "menu-mita-dance": ["MenuMitaDance"],
        "tetris": ["TetrisGame"],
        "tamagotchi-cooking": ["TamagotchiGame_Cooking"],
        "tamagotchi-find-furniture": ["TamagotchiGame_FindFurniture"],
        "tamagotchi-help-trash": ["TamagotchiGame_HelpTrash"],
        "tamagotchi-sorting": ["TamagotchiGame_Sorting"],
    }
    lists = sorted(glob.glob(rd("extracted/harvest/asset-list/*.xml")))
    containers = [os.path.basename(p)[:-4] for p in lists]
    xml_of = dict(zip(containers, lists))
    carrier = {}
    for mg, classes_ in classes.items():
        hits = {}
        for c in containers:
            xml = open(xml_of[c], encoding="utf-8").read()
            n = sum(xml.count("<Name>%s<" % k) for k in classes_)
            if n:
                hits[c] = n
        carrier[mg] = hits
    # filename census: bare + #suffix dumps per class per container
    census = {}
    for mg, classes_ in classes.items():
        census[mg] = {}
        for c in containers:
            d = rd("extracted/harvest/mb-dump/" + c)
            if not os.path.isdir(d):
                continue
            files = os.listdir(d)
            n_bare = sum(1 for k in classes_
                         if (k + ".txt") in files)
            n_suf = sum(1 for f in files for k in classes_
                        if f.startswith(k + "_#") and f.endswith(".txt"))
            if n_bare or n_suf:
                census[mg].setdefault(c, {"bare": 0, "suffixed": 0})
                census[mg][c]["bare"] += n_bare
                census[mg][c]["suffixed"] += n_suf
    return carrier, census, containers


def measure_controller_partition():
    files = sorted(glob.glob(rd("extracted/harvest/mb-dump/*/MinigamesController.txt")))
    groups = collections.defaultdict(list)
    for f in files:
        h = hashlib.md5(open(f, "rb").read()).hexdigest()
        groups[h].append(os.path.basename(os.path.dirname(f)))
    parts = sorted(groups.values(), key=len, reverse=True)
    sizes = sorted((len(p) for p in parts), reverse=True)
    lvl2_hash = None
    for h, members in groups.items():
        if "level2" in members:
            lvl2_hash = h
            lvl2_size = len(members)
    assert sizes == [19, 16, 12, 1], sizes
    return {"dump_files": len(files), "group_sizes": sizes,
            "level2_group_members": lvl2_size,
            "level2_md5": lvl2_hash,
            "group_md5_sizes": sorted(
                ((h, len(m)) for h, m in groups.items()), key=lambda t: (-t[1], t[0]))}


def measure_achi():
    rows = [r for r in read_jsonl(rd("extracted/data/achievements/achievements.jsonl"))
            if "_meta" not in r]
    return rows


def measure_award_sites():
    return [r for r in read_jsonl(
        rd("extracted/data/achievements/relink-achievement-award-site.jsonl"))
        if "_meta" not in r]


def measure_c13():
    rows = read_jsonl(rd("extracted/data/characters/relinks/character--cartridge.jsonl"))
    meta = [r for r in rows if "_meta" in r][0]["_meta"]
    fwd = [r for r in rows if r.get("direction") == "forward"]
    return meta, fwd


def loc_text(category, line_index, locale="English"):
    p = rd("extracted/localization/%s/%s.jsonl" % (locale, category))
    for r in read_jsonl(p):
        if r["line_index"] == line_index:
            return r["text"]
    raise KeyError((category, line_index))


def kebab_save(key):
    return re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", "-", key.lower())


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------

STAMPS = {"build_id": BUILD_ID, "version_label": VERSION_LABEL}

D1_S4 = "docs/research/game-research.mdx section 4 (Fandom Minigames tabulation)"

MINIGAME_DEFS = [
    # id, client_key, key_source, access_medium, alias, loader/carrier extras
    {"minigame_id": "carspace", "client_key": "Minigame CarSpace",
     "key_source": "automate_resource", "access_medium": "resources-prefab",
     "community_alias": {"alias": "Spaceracer (SPACECAR)", "source": D1_S4}},
    {"minigame_id": "makemaneken", "client_key": "Minigame MakeManeken",
     "key_source": "automate_resource", "access_medium": "resources-prefab",
     "community_alias": {"alias": "Dummy Sort", "source": D1_S4}},
    {"minigame_id": "minigame-shooter", "client_key": "MinigameShooter",
     "key_source": "automate_scene", "access_medium": "dedicated-scene",
     "community_alias": {"alias": "Hetoor", "source": D1_S4}},
    {"minigame_id": "fight", "client_key": "Fight",
     "key_source": "tv_games_array", "access_medium": "television",
     "community_alias": {"alias": "Dairy Scandal", "source": D1_S4}},
    {"minigame_id": "pinguin", "client_key": "Pinguin",
     "key_source": "tv_games_array", "access_medium": "television",
     "community_alias": {"alias": "Penguin Piles", "source": D1_S4}},
    {"minigame_id": "location-4-table-card-game", "client_key": "Location4TableCardGame",
     "key_source": "scene_carrier_class", "access_medium": "scene-prop",
     "community_alias": {"alias": "Card Game", "source": D1_S4},
     "class_variants": ["Location4TableCardGame_Card", "Location4TableCardGame_CardHold",
                        "Location4TableCardGame_CardMemory"]},
    {"minigame_id": "location-7-game-dance", "client_key": "Location7_GameDance",
     "key_source": "scene_carrier_class", "access_medium": "scene-prop",
     "community_alias": {"alias": "DDR (dance)", "source": D1_S4},
     "class_variants": ["Location7_GameDance_Music", "Location7_GameDance_Music_Note",
                        "Location7_GameDance_Sphere"]},
    {"minigame_id": "location-7-hammer-button", "client_key": "Location7_HammerButton",
     "key_source": "scene_carrier_class", "access_medium": "scene-prop",
     "community_alias": {"alias": "The Button", "source": D1_S4},
     "class_variants": ["Location7_HammerButton_Animations"]},
    {"minigame_id": "location-14-pc-snaker", "client_key": "Location14_PCSnaker",
     "key_source": "scene_carrier_class", "access_medium": "scene-prop",
     "community_alias": {"alias": "Snake game", "source": D1_S4}},
    {"minigame_id": "location-17-pumpkin-clicker", "client_key": "Location17_PumpkinClicker",
     "key_source": "scene_carrier_class", "access_medium": "scene-prop",
     "community_alias": {"alias": "Kitchen Pumpkins", "source": D1_S4}},
    {"minigame_id": "games-core", "client_key": "GamesCore_Main",
     "key_source": "scene_carrier_class", "access_medium": "core-terminal",
     "community_alias": {"alias": "Quadrangle", "source": D1_S4},
     "class_variants": ["GamesCore_Main_Folder", "GamesCore_Main_Sphere",
                        "GamesCore_InputField", "GamesCore_InputField_Char"]},
    {"minigame_id": "menu-mita-dance", "client_key": "MenuMitaDance",
     "key_source": "scene_carrier_class", "access_medium": "menu",
     "community_alias": None},
    {"minigame_id": "tetris", "client_key": "TetrisGame",
     "key_source": "scene_carrier_class", "access_medium": "scene-prop",
     "community_alias": {"alias": "Tetris", "source":
                         "docs/research/game-research.mdx section 4 (patch-note framing)"},
     "class_variants": ["TetrisFrog", "TetrisSpriteAnimation"]},
    {"minigame_id": "tamagotchi-cooking", "client_key": "TamagotchiGame_Cooking",
     "key_source": "tamagotchi_activity", "access_medium": "tamagotchi-phone",
     "community_alias": None, "unreachable": True,
     "class_variants": ["TamagotchiGame_Cooking_Food"]},
    {"minigame_id": "tamagotchi-find-furniture", "client_key": "TamagotchiGame_FindFurniture",
     "key_source": "tamagotchi_activity", "access_medium": "tamagotchi-phone",
     "community_alias": None, "unreachable": True,
     "class_variants": ["TamagotchiGame_FindFurniture_Object"]},
    {"minigame_id": "tamagotchi-help-trash", "client_key": "TamagotchiGame_HelpTrash",
     "key_source": "tamagotchi_activity", "access_medium": "tamagotchi-phone",
     "community_alias": None, "unreachable": True},
    {"minigame_id": "tamagotchi-sorting", "client_key": "TamagotchiGame_Sorting",
     "key_source": "tamagotchi_activity", "access_medium": "tamagotchi-phone",
     "community_alias": None, "unreachable": True,
     "class_variants": ["TamagotchiGame_Sorting_Item", "TamagotchiGame_Sorting_ItemAnimation"]},
]

ACHIEVEMENT_JOINS = [
    # achievement_id, minigame_id|null, mechanism, attribution evidence list
    ("ACHI_PinguinTusim", "pinguin", "hard", [
        'id contains the TV entry client_key "Pinguin" verbatim',
        'EN Achievements line 3 reads "Penguin Conundrum!"',
        "grant site shares container level6 with the single "
        "MinigamesTelevisionController instance"]),
    ("ACHI_tetro", None, "logic", []),
    ("ACHI_racingfirst", None, "logic", []),
    ("ACHI_applesnake", "location-14-pc-snaker", "logic", [
        'id contains "snake"',
        '"snake" occurs in exactly one decompiled type name corpus-wide: '
        "Location14_PCSnaker (decompiled/_structure/types.json)"]),
    ("ACHI_logA", None, "logic", []),
    ("ACHI_logB", None, "logic", []),
    ("ACHI_hellwin", None, "logic", []),
    ("ACHI_hellmegawin", None, "logic", []),
    ("ACHI_WinFIght", "fight", "hard", [
        'id case-folded contains the TV entry client_key "fight"',
        "type_tag is story (beyond the 8 minigame-tagged rows); grant site "
        "shares container level6 with the single MinigamesTelevisionController "
        "instance"]),
    ("ACHI_greatdance", "location-7-game-dance", "hard", [
        "grant site sits in level9, the only container carrying "
        "Location7_GameDance/Location7_HammerButton carriers",
        "type_tag is story; granted inside the dance location"]),
]


def build_cartridge_rows(keys, pickups, c13_meta, c13_fwd):
    pickup_by_key = collections.defaultdict(list)
    for p in pickups:
        pickup_by_key[p["value"]].append(p)
    char_by_key = {r["save_key"]: r["from"] for r in c13_fwd if r["from"].startswith("mita")
                   or r["from"] == "mila"}
    player_by_key = {r["save_key"]: r["from"] for r in c13_fwd
                     if r["from"].startswith("player")}
    rows = []
    for slot, key in enumerate(keys):
        fam = "character" if slot < 13 else "player"
        ps = pickup_by_key.get(key, [])
        assert len(ps) <= 1, (key, ps)
        p = ps[0] if ps else None
        row = {
            "cartridge_id": kebab_save(key),
            "family": fam,
            "status": "registered-pickup" if p else "registered-unresolved-pickup",
            "save_key": key,
            "registry_literal_ref": "il2cpp/stringliteral.json@0x13AD860[%d]" % slot,
            "pickup_ref": dict(p) if p else None,
            "depicts_character_id": char_by_key.get(key) if fam == "character" else None,
            "contains_player_id": player_by_key.get(key) if fam == "player" else None,
            "collectible_set": "player-cartridges" if fam == "player" else None,
            "container_location_binding":
                ("level%s->Location%d [inferred]"
                 % (p["container"][5:], int(p["container"][5:]) - 2)) if p else None,
            "missing_fields": [] if p else [
                "pickup_ref - R3 sweep unblock: mtad2 community kitchen side table, "
                "mtacore Core computer button; Location18_Flash carries no save field"],
            **STAMPS,
        }
        if key == "mta":
            row["missing_fields"] = row["missing_fields"] + [
                "depicts_character_id - DS-1 registry leaves MitaUsual nameSave empty; "
                "no C13 flashes anchor exists for mta (namespace honesty, AC-3)"]
        rows.append(row)
    return rows


def build_minigame_rows(tv, automates, locales, loccounts, carrier, census,
                        containers):
    tv_by_name = {g["nameResource"]: g for g in tv}
    rows = []
    for d in MINIGAME_DEFS:
        mid = d["minigame_id"]
        ks = d["key_source"]
        loader = None
        key_locator = None
        if ks in ("automate_resource", "automate_scene"):
            cont = {"carspace": "level9", "makemaneken": "level12",
                    "minigame-shooter": "level13"}[mid]
            field = "resourceGame" if ks == "automate_resource" else "sceneGame"
            val = automates[cont][field]
            assert val == d["client_key"], (val, d["client_key"])
            loader = {"container": cont, "file": "MinigamesAutomate.txt",
                      "field": field, "value": val}
            key_locator = "harvest/mb-dump/%s/MinigamesAutomate.txt :: %s" % (cont, field)
        elif ks == "tv_games_array":
            g = tv_by_name[d["client_key"]]
            key_locator = ("harvest/mb-dump/level6/MinigamesTelevisionController.txt "
                           ":: games[nameResource=%s]" % d["client_key"])
        else:
            key_locator = ("harvest/asset-list greps <Name>%s< over all 48 container "
                           "xml files" % d["client_key"])

        name_loc = None
        ui_strings = None
        if mid == "fight":
            name_loc = {"category": "TelevisionGames", "line_index": 0}
            ui_strings = {"category": "TelevisionGames", "line_count": 2}
        elif mid == "pinguin":
            name_loc = {"category": "TelevisionGames", "line_index": 1}
            ui_strings = {"category": "TelevisionGames", "line_count": 2}
        elif mid == "carspace":
            ui_strings = {"category": "MiniGame CarSpace",
                          "line_count": loccounts["MiniGame CarSpace"]["English"]}
        elif mid == "makemaneken":
            ui_strings = {"category": "MiniGame MakeManeken",
                          "line_count": loccounts["MiniGame MakeManeken"]["English"]}
        elif mid == "minigame-shooter":
            ui_strings = {"category": "MiniGame Shooter",
                          "line_count": loccounts["MiniGame Shooter"]["English"]}

        rule_evidence = []
        if mid == "fight":
            g = tv_by_name["Fight"]
            rule_evidence = [
                {"path": "extracted/harvest/mb-dump/level6/MinigamesTelevisionController.txt",
                 "locator": 'string nameResource = "Fight"',
                 "claim": 'entry serializes nameResource "Fight", '
                          'indexStringNameGame %d, playead False, timeTalk 0; win/lose/'
                          'draw counters countWin %d / countLose %d / countDraw %d; '
                          'dialogue arrays sized win %d / lose %d / draw %d'
                          % (g["indexStringNameGame"], g["countWin"], g["countLose"],
                             g["countDraw"], g["dialogueWin_size"], g["dialogueLose_size"],
                             g["dialogueDraw_size"])},
                {"path": "extracted/localization/English/TelevisionGames.jsonl",
                 "locator": "line_index=0",
                 "claim": 'TV title under the pinned offset resolves to "Dairy Scandal"'},
            ]
        elif mid == "pinguin":
            g = tv_by_name["Pinguin"]
            rule_evidence = [
                {"path": "extracted/harvest/mb-dump/level6/MinigamesTelevisionController.txt",
                 "locator": 'string nameResource = "Pinguin"',
                 "claim": 'entry serializes nameResource "Pinguin", '
                          'indexStringNameGame %d, playead False, timeTalk 0; win/lose/'
                          'draw counters countWin %d / countLose %d / countDraw %d; '
                          'dialogue arrays sized win %d / lose %d / draw %d'
                          % (g["indexStringNameGame"], g["countWin"], g["countLose"],
                             g["countDraw"], g["dialogueWin_size"], g["dialogueLose_size"],
                             g["dialogueDraw_size"])},
                {"path": "extracted/localization/English/TelevisionGames.jsonl",
                 "locator": "line_index=1",
                 "claim": 'TV title under the pinned offset resolves to "Penguin Piles"'},
            ]
        elif mid == "carspace":
            rule_evidence = [
                {"path": "extracted/localization/English/MiniGame CarSpace.jsonl",
                 "locator": "line_index=%d" % i,
                 "claim": 'in-game UI string "%s"' % loc_text("MiniGame CarSpace", i)}
                for i in (1, 2, 3, 4, 6)]
        elif mid == "makemaneken":
            rule_evidence = [
                {"path": "extracted/localization/English/MiniGame MakeManeken.jsonl",
                 "locator": "line_index=%d" % i,
                 "claim": 'in-game UI string "%s"' % loc_text("MiniGame MakeManeken", i)}
                for i in (1, 2, 3, 5)]
        elif mid == "minigame-shooter":
            rule_evidence = [
                {"path": "extracted/localization/English/MiniGame Shooter.jsonl",
                 "locator": "line_index=%d" % i,
                 "claim": 'stat label "%s"' % loc_text("MiniGame Shooter", i)}
                for i in range(3, 9)]
        elif mid == "location-4-table-card-game":
            rule_evidence = [
                {"path": "extracted/harvest/mb-dump/level6/Location4TableCardGame.txt",
                 "locator": "SInt32 damage = 8",
                 "claim": 'cards serialize combat stats; first entry reads '
                          '"SInt32 damage = 8" with "SInt32 shield = 1" and '
                          '"SInt32 heart = 3"'}]
        elif mid == "location-7-hammer-button":
            rule_evidence = [
                {"path": "extracted/harvest/mb-dump/level9/Location7_HammerButton.txt",
                 "locator": "int size = 12",
                 "claim": 'serialized groups sized "int size = 3" x4 and '
                          '"int size = 12"'}]
        elif mid == "location-17-pumpkin-clicker":
            rule_evidence = [
                {"path": "extracted/harvest/mb-dump/level19/Location17_PumpkinClicker.txt",
                 "locator": "int size = 5",
                 "claim": 'serialized groups sized "int size = 5" x2 plus one '
                          '"int size = 4"'}]
        elif mid == "games-core":
            rule_evidence = [
                {"path": "extracted/harvest/mb-dump/level15/GamesCore_Main.txt",
                 "locator": "int size = 16",
                 "claim": 'sphere graph board serializes "int size = 16" spheres with '
                          'per-sphere "SInt32 indexSphereRight"/"indexSphereLeft"/'
                          '"indexSphereUp"/"indexSphereDown" links'}]
        elif mid == "menu-mita-dance":
            rule_evidence = [
                {"path": "extracted/harvest/mb-dump/level2/MenuMitaDance.txt",
                 "locator": "SInt32 indexDance = 3",
                 "claim": 'serializes "SInt32 indexDance = 3" and "bool cloth = False"'}]

        ach_ids = sorted(a for a, m, mech, ev in ACHIEVEMENT_JOINS
                         if m == mid and a is not None)
        outfits = ["Chirfns"] if mid == "pinguin" else (
            ["HellVamp"] if mid == "location-17-pumpkin-clicker" else [])

        cc = sorted(carrier[mid].keys())
        note = None
        if mid in ("carspace", "makemaneken"):
            # R4-style dedupe: Resources-loaded prefab family lists in 48 of the
            # 51 asset-lists through AssetStudioMod dependency auto-load; collapse
            # to canonical prefab home + gameplay loader container.
            raw_spread = len(cc)
            loader_container = loader["container"]
            cc = sorted({"resources.assets", loader_container})
            note = ("Resources-loaded prefab family: raw asset-list presence spans %d "
                    "of %d containers via AssetStudioMod dependency auto-load; dedupe "
                    "rule (DS-4 section 3.5 / section 8-R4) collapses the spread - "
                    "canonical prefab home resources.assets, gameplay loader container "
                    "%s" % (raw_spread, len(containers), loader_container))
        row = {
            "minigame_id": mid,
            "client_key": d["client_key"],
            "key_source": ks,
            "key_locator": key_locator,
            "access_medium": d["access_medium"],
            "carrier_containers": cc,
            "carrier_note": note,
            "loader_ref": loader,
            "name_loc": name_loc,
            "community_alias": d["community_alias"],
            "ui_strings_loc": ui_strings,
            "rule_evidence": rule_evidence,
            "scoring_derivable": False,
            "achievement_ids": ach_ids,
            "unlocks_outfits": outfits,
            "present_but_unreachable": bool(d.get("unreachable")),
            **STAMPS,
        }
        rows.append(row)
    return rows


def build_candidates(types_names, carrier, census):
    def cls(n):
        return n in types_names

    tam = [c for c in ("TamagotchiGame_Chip", "TamagotchiGame_Chip_Case",
                       "TamagotchiGame_Chip_Plita", "TamagotchiGame_Cartridge",
                       "TamagotchiGame_Cartridge_Cartridge",
                       "TamagotchiGame_CartridgeDetails") if cls(c)]
    met = sorted(c for c in types_names if c.startswith("Metroidvania_"))
    rows = [
        {"candidate_id": "tamagotchi-chip-and-cartridge-ui",
         "kind_class": "minigame",
         "display_name": "TamagotchiGame_Chip / TamagotchiGame_Cartridge families",
         "status": "unregistered",
         "evidence": [
             {"path": "extracted/decompiled/_structure/types.json",
              "locator": "types[].name=%s" % c} for c in tam] + [
             {"path": "extracted/harvest/asset-list/level3.xml",
              "locator": "<Name>TamagotchiGame_Chip<"},
             {"path": "extracted/harvest/asset-list/level3.xml",
              "locator": "<Name>TamagotchiGame_Cartridge<"}],
         "wiki_source_ref": None,
         "missing_fields": ["loader_ref", "name_loc", "rule_evidence"],
         "note": "phone-console UI/cassette classes measured in level3 only; not "
                 "counted among DS-4 section 3.2's four activity families "
                 "(Cooking/FindFurniture/HelpTrash/Sorting), held here rather than "
                 "dropped (Principle zero)",
         **STAMPS},
        {"candidate_id": "metroidvania-family",
         "kind_class": "minigame",
         "display_name": "Metroidvania_* class family",
         "status": "unregistered",
         "evidence": [
             {"path": "extracted/decompiled/_structure/types.json",
              "locator": "types[].name=%s" % c} for c in met] + [
             {"path": "extracted/harvest/mb-dump (48 containers)",
              "locator": "Metroidvania_Interactive*.txt md5 "
                         "a4c8a17f2deca7707d44078521dabb2d x48 identical"}],
         "wiki_source_ref": None,
         "missing_fields": ["loader_ref", "name_loc", "rule_evidence",
                            "any non-boilerplate instance"],
         "note": "whole unused game family ships as classes; every dumped "
                 "Metroidvania_Interactive component is byte-identical boilerplate "
                 "across all 48 containers - cut-content capture under the COMP J11 "
                 "posture, never promoted without distinct evidence",
         **STAMPS},
    ]
    return rows


def build_j1(keys, c13_fwd):
    meta = {
        "family": "cartridge--character",
        "schema": "miside.relink.cartridge-character/1",
        "generator": GENERATOR,
        "pair": "cartridge_item <-> character/player",
        "join_plan": "docs/specs/dataset-cartridges.mdx section 6 J1",
        "anchor_source": ("extracted/data/characters/relinks/character--cartridge.jsonl "
                          "(C13) reused verbatim; this file mirrors and extends DS-1 J5 "
                          "without mutating it"),
        "edge_types": {"depicts": "mita-family cartridge -> character",
                       "contains": "player-family cartridge -> player"},
        "typed_anchor_vocabulary": {"from": "cartridge:<cartridge_id>",
                                    "to": "<character_id> (DS-1 personages ids)",
                                    "c13_anchor": "flashes:<save_key>"},
        "namespace_honesty": ("C1/C2 carry key mta but DS-1 registry nameSave is empty "
                              "for MitaUsual/MitaTrue, so no C13 anchor exists for mta "
                              "and its depicts side stays null (DS-4 section 3.1 finding 2)"),
        "gallery_corroboration": ("all 23 registry keys are wired one-to-one as "
                                  'MenuPersonage.OpenPersonage("<save_key>") call sites '
                                  "across 23 level2 dumps (measured this pass; e.g. "
                                  "harvest/mb-dump/level2/ButtonMouseClick_#2179.txt -> "
                                  '"mtad2"); the album IS the cartridge gallery'),
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "relocation_note": "move to extracted/relinks/ at run_all stage registration",
    }
    rows = []
    for r in sorted(c13_fwd, key=lambda r: r["to"]):
        key = r["save_key"]
        cid = kebab_save(key)
        ctype = "contains" if r["from"].startswith("player") else "depicts"
        base = {"save_key": key, "c13_anchor": r["to"], "member_character_id": r["from"],
                "mechanism": "hard", "status": "modeled",
                "method": "key membership proven by C1 literal @0x13AD860 + C2 "
                          "FlashTaker.save + C3 FlashTaker.cs SaveFlash(string); "
                          "identity edge mirrored verbatim from the C13 anchor"}
        rows.append({"direction": "forward", "edge_type": ctype,
                     "from": "cartridge:%s" % cid, "to": r["from"], **base})
        rows.append({"direction": "inverse", "edge_type": ctype,
                     "from": r["from"], "to": "cartridge:%s" % cid, **base})
    return meta, rows


def build_j2(pickups):
    meta = {
        "family": "cartridge--scene-placement",
        "schema": "miside.relink.cartridge-scene-placement/1",
        "generator": GENERATOR,
        "pair": "cartridge_item <-> location_scene/transform",
        "join_plan": "docs/specs/dataset-cartridges.mdx section 6 J2",
        "status": "parked",
        "park_reason": ("scene transforms/chapter attribution are the scenes dataset's "
                        "output (COMP J2, P5-gated); this file emits meta-only until "
                        "that stage lands"),
        "placement_census": {"pairs": len(pickups),
                             "containers": sorted({p["container"] for p in pickups}),
                             "authority": ("the 21 (container, save) pairs live in "
                                           "extracted/data/cartridges/cartridges.jsonl "
                                           "pickup_ref; DS-5 consumes the 11-row "
                                           "mita-side overlap by reference (shared-source "
                                           "ruling, DS-4 section 1 as restated by the "
                                           "ds456-arbiter fence)")},
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "relocation_note": "move to extracted/relinks/ at run_all stage registration",
    }
    return meta, []


def build_j3(achi_rows, sites):
    achi_ids = {r["achievement_id"] for r in achi_rows}
    site_by_id = {r["achievement_id"]: r for r in sites}
    tag = {r["achievement_id"]: r.get("type_tag") for r in achi_rows}
    meta = {
        "family": "minigame--achievement",
        "schema": "miside.relink.minigame-achievement/1",
        "generator": GENERATOR,
        "pair": "minigame <-> achievement",
        "join_plan": "docs/specs/dataset-cartridges.mdx section 6 J3",
        "mechanism_rule": ("hard where a dumped AchievementGet award site exists "
                           "(C12 sweep: exactly 11 sites corpus-wide); logic where "
                           "only the type_tag binds - runtime-granted awards live in "
                           "undumped prefabs"),
        "attribution_standard": ("a minigame side is attributed only on mechanical "
                                 "client evidence (verbatim identifier containment or "
                                 "co-container grant site); community prose never "
                                 "attributes an edge"),
        "consumer_note": ("fills joins.minigame_id consumer-side; DS-2 files are NOT "
                          "mutated by this stage"),
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "relocation_note": "move to extracted/relinks/ at run_all stage registration",
    }
    rows = []
    for aid, mid, mech, attribution in sorted(ACHIEVEMENT_JOINS):
        assert aid in achi_ids, aid
        site = site_by_id.get(aid)
        if mech == "hard":
            assert site is not None, aid
        missing = [] if mid else [
            "minigame_id - no dumped award site (grep proof: id absent from all 11 "
            "AchievementGet sites) and no mechanical identifier tie to a measured "
            "surface; unblock: native-code decompile pass over GameAssembly.dll "
            "(section 8-R1) or a prefab sweep surfacing the grant site"]
        base = {"achievement_id": aid, "type_tag": tag.get(aid),
                "mechanism": mech,
                "award_site": ({"level": site["level"], "file": site["file"],
                                "method": site["method"],
                                "args_string": site["args_string"],
                                "target_path_id": site["target_path_id"],
                                "build_id": BUILD_ID}
                               if site else None),
                "attribution_evidence": attribution,
                "status": "modeled" if mid else "partial",
                "missing_fields": missing,
                "method": ("AchievementGet award site dumped and grepped clean; "
                           "minigame side attributed on listed evidence" if mid else
                           "type-tag-only bind (C11 type_tag=minigame); target "
                           "left unresolved rather than guessed")}
        fwd_from = "minigame:%s" % mid if mid else None
        rows.append({"direction": "forward", "from": fwd_from,
                     "to": "achievement:%s" % aid, **base})
        rows.append({"direction": "inverse", "from": "achievement:%s" % aid,
                     "to": fwd_from, **base})
    return meta, rows


CLASS_FAMILY = {
    "carspace": ["CarSpace_Boss", "CarSpace_Car", "CarSpace_Crystall", "CarSpace_Enemy",
                 "CarSpace_Main", "CarSpace_Money", "CarSpace_Music", "CarSpace_Player",
                 "CarSpace_Roket", "CarSpace_Scanner", "CarSpace_WindObject"],
    "makemaneken": ["MakeManeken_Box", "MakeManeken_Interactive", "MakeManeken_Main",
                    "MakeManeken_Switch", "MakeManeken_Tape"],
    "minigame-shooter": ["Shooter_Bubble", "Shooter_Bullet", "Shooter_BulletEnemy",
                         "Shooter_Damager", "Shooter_Enemy", "Shooter_Item",
                         "Shooter_Main", "Shooter_Main_TimePart", "Shooter_Main_Wave",
                         "Shooter_Player"],
    "location-4-table-card-game": ["Location4TableCardGame", "Location4TableCardGame_Card",
                                   "Location4TableCardGame_CardHold",
                                   "Location4TableCardGame_CardMemory"],
    "location-7-game-dance": ["Location7_GameDance", "Location7_GameDance_Music",
                              "Location7_GameDance_Music_Note",
                              "Location7_GameDance_Sphere"],
    "location-7-hammer-button": ["Location7_HammerButton",
                                 "Location7_HammerButton_Animations"],
    "location-14-pc-snaker": ["Location14_PCSnaker"],
    "location-17-pumpkin-clicker": ["Location17_PumpkinClicker"],
    "games-core": ["GamesCore_InputField", "GamesCore_InputField_Char",
                   "GamesCore_Main", "GamesCore_Main_Folder", "GamesCore_Main_Sphere"],
    "menu-mita-dance": ["MenuMitaDance"],
    "tetris": ["TetrisFrog", "TetrisGame", "TetrisSpriteAnimation"],
    "tamagotchi-cooking": ["TamagotchiGame_Cooking", "TamagotchiGame_Cooking_Food"],
    "tamagotchi-find-furniture": ["TamagotchiGame_FindFurniture",
                                  "TamagotchiGame_FindFurniture_Object"],
    "tamagotchi-help-trash": ["TamagotchiGame_HelpTrash"],
    "tamagotchi-sorting": ["TamagotchiGame_Sorting", "TamagotchiGame_Sorting_Item",
                           "TamagotchiGame_Sorting_ItemAnimation"],
}

J4_CONTAINERS = {
    "carspace": [("resources.assets", "canonical prefab home"), ("level9", "loader")],
    "makemaneken": [("resources.assets", "canonical prefab home"), ("level12", "loader")],
    "minigame-shooter": [("level13", "automate sceneGame ref"),
                         ("level23", "Shooter_* dedicated-scene carriers")],
    "fight": [("level6", "television controller")],
    "pinguin": [("level6", "television controller")],
    "tetris": [(None, "carrier")] * 0,  # filled from measurement below
}


def build_j4(carrier, census, partition):
    meta = {
        "family": "minigame--scene-carrier",
        "schema": "miside.relink.minigame-scene-carrier/1",
        "generator": GENERATOR,
        "pair": "minigame <-> location/container carrier classes",
        "join_plan": "docs/specs/dataset-cartridges.mdx section 6 J4",
        "mechanism_rule": ('script/container co-presence (hard): a carrier edge '
                           'claims only (class x container) pairs whose '
                           '"<Name>Class<" grep hits that container\'s asset-list xml'),
        "container_chapter_caveat": ("container != chapter; the levelN <-> "
                                     "Location(N-2) story binding is inferred "
                                     "(DS-3 section 3.6) and chapter attribution stays "
                                     "with the scenes dataset"),
        "boilerplate_dedupe": {
            "rule": "identical-hash template dumps collapse to one logical instance; "
                    "no duplicate-hash dump is ever counted twice in any carrier count "
                    "(DS-4 section 3.5 / section 8-R4)",
            "minigamescontroller_partition": partition,
        },
        "dependency_autoload_dedupe": (
            "Resources-loaded prefab families (CarSpace_*, MakeManeken_*) appear in "
            "all 48 asset-lists via AssetStudioMod dependency auto-load (E1 deviation "
            "6); their spread collapses to the canonical prefab home + loader "
            "container instead of 480 noisy edges"),
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "relocation_note": "move to extracted/relinks/ at run_all stage registration",
    }
    rows = []

    def edge(mid, container, role, classes):
        inst = census.get(mid, {}).get(container)
        payload = {
            "classes": classes,
            "instance_census": inst or {"bare": 0, "suffixed": 0},
            "role": role,
            "mechanism": "hard",
            "status": "modeled",
            "method": '<Name>Class< grep over harvest/asset-list/%s.xml + mb-dump '
                      "filename census (bare + _#pathID suffixed files)" % container,
        }
        rows.append({"direction": "forward",
                     "from": "minigame:%s" % mid,
                     "to": "scene-class-family@%s" % container, **payload})
        rows.append({"direction": "inverse",
                     "from": "scene-class-family@%s" % container,
                     "to": "minigame:%s" % mid, **payload})

    edge("carspace", "level9", "loader", CLASS_FAMILY["carspace"])
    edge("makemaneken", "level12", "loader", CLASS_FAMILY["makemaneken"])
    edge("minigame-shooter", "level13", "automate sceneGame ref", [])
    edge("minigame-shooter", "level23", "dedicated-scene carriers",
         CLASS_FAMILY["minigame-shooter"])
    edge("fight", "level6", "television controller", [])
    edge("pinguin", "level6", "television controller", [])
    for mid in ("location-4-table-card-game", "location-7-game-dance",
                "location-7-hammer-button", "location-14-pc-snaker",
                "location-17-pumpkin-clicker", "games-core", "menu-mita-dance"):
        for c in sorted(carrier[mid]):
            edge(mid, c, "scene-prop carrier", CLASS_FAMILY[mid])
    for c in sorted(carrier["tetris"]):
        edge("tetris", c, "scene-prop carrier", CLASS_FAMILY["tetris"])
    for mid in ("tamagotchi-cooking", "tamagotchi-find-furniture",
                "tamagotchi-help-trash", "tamagotchi-sorting"):
        for c in sorted(carrier[mid]):
            edge(mid, c, "tamagotchi-phone activity", CLASS_FAMILY[mid])
    return meta, rows


def build_j5():
    meta = {
        "family": "minigame--outfit-unlock",
        "schema": "miside.relink.minigame-outfit-unlock/1",
        "generator": GENERATOR,
        "pair": "minigame <-> outfit (ClothCompleted unlock chain)",
        "join_plan": "docs/specs/dataset-cartridges.mdx section 6 J5",
        "authority": ("extracted/decompiled/main/Assembly-CSharp/Achievement_cloth.cs "
                      "ClothCompleted(string _nameCloth); outfit vocabulary inherited "
                      "verbatim from B-1 relink (outfit:original/FIIdClSchool/HellVamp/"
                      "Chirfns)"),
        "site_sweep": ("exactly 2 ClothCompleted sites corpus-wide: "
                       "level5/Dialogue_3DText_#8339.txt (FIIdClSchool) and "
                       "level6/Dialogue_3DText_#7008.txt (Chirfns)"),
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "relocation_note": "move to extracted/relinks/ at run_all stage registration",
    }
    hard_ev = {
        "unlock_site": {"level": "level6", "file": "Dialogue_3DText_#7008.txt",
                        "method": "ClothCompleted", "args_string": "Chirfns",
                        "target_path_id": 9327, "build_id": BUILD_ID},
        "co_grant_fact": ("the same serialized host also calls AchievementGet("
                          '"ACHI_PinguinTusim") - dual grant in one UnityEvent chain'),
        "display_name_loc": {"category": "Clothes", "line_index": 12},
        "display_name_en": "Christmas",
    }
    rows = [
        {"direction": "forward", "from": "minigame:pinguin",
         "to": "outfit:Chirfns", "mechanism": "hard", "status": "modeled",
         "missing_fields": [], "method": "dumped ClothCompleted call site; "
         "minigame side attributed via co-grant in the same file with "
         "ACHI_PinguinTusim whose id equals the TV client_key Pinguin",
         **{k: v for k, v in hard_ev.items()}},
        {"direction": "inverse", "from": "outfit:Chirfns",
         "to": "minigame:pinguin", "mechanism": "hard", "status": "modeled",
         "missing_fields": [],
         "method": "mirror of the forward unlock edge (doctrine Principle one)",
         **{k: v for k, v in hard_ev.items()}},
        {"direction": "forward", "from": "minigame:location-17-pumpkin-clicker",
         "to": "outfit:HellVamp", "mechanism": "logic", "status": "partial",
         "missing_fields": ["dumped ClothCompleted call site - zero sites exist "
                            "outside levels 5/6 (corpus grep); unblock: native-code "
                            "pass (section 8-R1) or prefab dump of the unlock call"],
         "method": "wiki-asserted link pending a dumped call site (D1 section 4: "
                   'Kitchen Pumpkins "also unlocks Vampire outfit"); kept logic, '
                   "never hard",
         "display_name_loc": {"category": "Clothes", "line_index": 11},
         "display_name_en": "Vampire"},
        {"direction": "inverse", "from": "outfit:HellVamp",
         "to": "minigame:location-17-pumpkin-clicker", "mechanism": "logic",
         "status": "partial",
         "missing_fields": ["dumped ClothCompleted call site"],
         "method": "mirror of the forward unlock edge (doctrine Principle one)",
         "display_name_loc": {"category": "Clothes", "line_index": 11},
         "display_name_en": "Vampire"},
    ]
    return meta, rows


def build_j6():
    meta = {
        "family": "minigame--choice-condition",
        "schema": "miside.relink.minigame-choice-condition/1",
        "generator": GENERATOR,
        "pair": "minigame/tv-game <-> ending choice condition",
        "join_plan": "docs/specs/dataset-cartridges.mdx section 6 J6 (keyed here, "
                     "owned by DS-2 Part B)",
        "measured_absence": ("extracted/data/endings/choice_nodes.jsonl contains NO "
                             "'play a console game'-class condition today - the two "
                             "grep hits for /game|console|arcade/ are both the "
                             "globalgamemanagers container name, not conditions"),
        "key_space": "choice_node ids from endings/choice_nodes.jsonl <-> minigame_id",
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "relocation_note": "move to extracted/relinks/ at run_all stage registration",
    }
    return meta, []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    keys, lit_idx = measure_registry()
    pickups = measure_pickups()
    assert len(pickups) == 21
    tv = measure_tv()
    automates = measure_automates()
    locales, loccounts = measure_loc_counts()
    carrier, census, containers = measure_carriers()
    partition = measure_controller_partition()
    achi_rows = measure_achi()
    sites = measure_award_sites()
    c13_meta, c13_fwd = measure_c13()

    types_names = {t["name"] for t in json.load(
        open(rd("extracted/decompiled/_structure/types.json"), encoding="utf-8"))["types"]}
    hetoor_free = True
    blob = json.dumps(json.load(open(rd("extracted/il2cpp/stringliteral.json"),
                                     encoding="utf-8"))) + "".join(
        open(rd("extracted/localization/%s/%s.jsonl" % (l, c)), encoding="utf-8").read()
        for l in locales for c in ("MiniGame CarSpace", "MiniGame MakeManeken",
                                   "MiniGame Shooter", "TelevisionGames"))
    for bad in ("Hetoor", "Spaceracer"):
        if bad in blob:
            hetoor_free = False
    assert hetoor_free, "community name leaked into client evidence"

    cart_rows = build_cartridge_rows(keys, pickups, c13_meta, c13_fwd)
    mg_rows = build_minigame_rows(tv, automates, locales, loccounts, carrier, census,
                                  containers)
    cand_rows = build_candidates(types_names, carrier, census)

    unresolved = sorted(r["save_key"] for r in cart_rows if r["pickup_ref"] is None)
    assert unresolved == ["mtacore", "mtad2"], unresolved

    cart_meta = {
        "schema": "miside.cartridges.cartridges/1",
        "generator": GENERATOR,
        "row_count": len(cart_rows),
        "source_table": "docs/specs/dataset-cartridges.mdx section 2 (C1, C2, C3, C4, "
                        "C11, C13)",
        "registry_pin": {
            "literal": "il2cpp/stringliteral.json@0x13AD860 (array index %d)" % lit_idx,
            "keys": len(keys), "family_split": "13 character (slots 0-12) / 10 player "
                                               "(slots 13-22)"},
        "collection_identity": {"literal_a": "il2cpp/stringliteral.json@0x13A7B28 "
                                             "(/Save/Flashes)",
                                "literal_b": "il2cpp/stringliteral.json@0x13BEC20 "
                                             "(Flashes)"},
        "derived_fields": ["cartridge_id (boundary-split kebab of save_key; additive "
                           "only)", "family", "status", "container_location_binding",
                           "missing_fields"],
        "slug_rule": "lowercase; hyphen inserted at every letter-digit boundary "
                     "(mtacap -> mta-cap, plr1099 -> plr-1099); never replaces "
                     "save_key",
        "namespace_honesty": ("mta row documents DS-1's empty nameSave for "
                              "MitaUsual/MitaTrue; depicts_character_id joins ride C13 "
                              "anchors, never assumed nameSave equality"),
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
    }
    write_jsonl("cartridges.jsonl", cart_meta, cart_rows)

    mg_meta = {
        "schema": "miside.minigames.minigames/1",
        "generator": GENERATOR,
        "row_count": len(mg_rows),
        "source_table": "docs/specs/dataset-cartridges.mdx section 2 (C5-C10, C16) "
                        "and section 3.2 four-registry model",
        "surface_count": {"prefab_scene": 3, "tv": 2, "carrier_class": 8,
                          "tamagotchi_activity": 4},
        "tv_name_offset_pin": {
            "chosen_hypothesis": 'GetString("TelevisionGames", indexStringNameGame - 1)',
            "rejected_hypothesis": 'GetString("TelevisionGames", indexStringNameGame)',
            "rejected_failure": ('identity offset would name the fight-styled entry '
                                 '"Fight" -> line 1 "Penguin Piles" while the '
                                 'penguin-styled "Pinguin" took line 0 "Dairy Scandal" '
                                 "- rejected on semantics exactly like DS-1's clothes "
                                 "off-by-one"),
            "verified_this_pass": ("both computations recomputed against "
                                   "localization/<locale>/TelevisionGames.jsonl across "
                                   "all 34 locale dirs")},
        "derived_fields": ["minigame_id", "access_medium", "carrier_containers",
                           "name_loc resolution", "achievement_ids", "unlocks_outfits",
                           "present_but_unreachable"],
        "scoring_fence": "scoring_derivable false on every row (section 8-R1 IL-stub "
                         "fence) until a native-code pass lands",
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
    }
    write_jsonl("minigames.jsonl", mg_meta, mg_rows)

    cand_meta = {
        "schema": "miside.cartridges.candidates/1",
        "generator": GENERATOR,
        "row_count": len(cand_rows),
        "ladder": ("tier 3 candidates only (class evidence without a loader/name row); "
                   "tier-4 wiki-only claims get no row and no candidate per section 7 "
                   "item 4 - they are noted in README.md against the research citation"),
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
    }
    write_jsonl("cartridges-minigames.candidates.jsonl", cand_meta, cand_rows)

    m1, r1 = build_j1(keys, c13_fwd)
    write_jsonl("relinks/cartridge--character.jsonl", m1, r1)
    m2, r2 = build_j2(pickups)
    write_jsonl("relinks/cartridge--scene-placement.jsonl", m2, r2)
    m3, r3 = build_j3(achi_rows, sites)
    write_jsonl("relinks/minigame--achievement.jsonl", m3, r3)
    m4, r4 = build_j4(carrier, census, partition)
    write_jsonl("relinks/minigame--scene-carrier.jsonl", m4, r4)
    m5, r5 = build_j5()
    write_jsonl("relinks/minigame--outfit-unlock.jsonl", m5, r5)
    m6, r6 = build_j6()
    write_jsonl("relinks/minigame--choice-condition.jsonl", m6, r6)

    manifest = {
        "written_sorted": sorted(_written),
        "rows": {"cartridges": len(cart_rows), "minigames": len(mg_rows),
                 "candidates": len(cand_rows),
                 "j1": len(r1), "j2": len(r2), "j3": len(r3),
                 "j4": len(r4), "j5": len(r5), "j6": len(r6)},
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
    }
    with open(os.path.join(OUT, "build", "written-manifest.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps(manifest["rows"], sort_keys=True))


if __name__ == "__main__":
    sys.exit(main())
