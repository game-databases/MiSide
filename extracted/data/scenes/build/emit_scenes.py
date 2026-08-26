#!/usr/bin/env python3
"""DS-6 scenes dataset emitter — builder B-6 (2026-08-25; M0 rerun 2026-08-26).

Emits extracted/data/scenes/{scenes,scene-links,poi,spawn-tables,markers}.jsonl
plus poi-kinds.json, README.md and parked relinks/ per
docs/specs/dataset-scenes.mdx (post-F-DS6, ds6-vA PASS). The markers.jsonl
projection is M0 of docs/specs/map-viewer.mdx §3: entity-backed rows over the
landed owning datasets (DS-4 cartridges, DS-5 profile documents,
minigame--scene-carrier edges), the two-list family ledger (A-MV1 F-1) and
the PIPE S9 disposition accounting for the pptr-unresolved positions.

Deterministic by construction: no wall-clock, fixed orderings, floats carried
verbatim as they print in the MB dumps (class Raw). Run twice -> byte-identical.

Harvest root: extracted/harvest/ is the default; when the corpus lives
elsewhere (C:-pressure move of 2026-08-25), set MISIDE_HARVEST_ROOT to the
directory holding mb-dump/ + asset-list/.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PACK = Path(__file__).resolve().parents[4]
HARVEST = Path(os.environ.get("MISIDE_HARVEST_ROOT")
               or (PACK / "extracted/harvest"))
MB = HARVEST / "mb-dump"
ASL_DIR = HARVEST / "asset-list"
LOC = PACK / "extracted/localization"
OUT = PACK / "extracted/data/scenes"
RELINKS = OUT / "relinks"

BUILD_ID = None
VERSION_LABEL = None


def load_pins():
    global BUILD_ID, VERSION_LABEL
    txt = (PACK / "extracted/EXTRACTION-LOG.md").read_text(encoding="utf-8")
    m = re.search(r'"buildId":\s*"([^"]+)"', txt)
    n = re.search(r'"versionLabel":\s*"([^"]+)"', txt)
    if not (m and n):
        sys.exit("pipeline-defaults pins not found in EXTRACTION-LOG.md")
    BUILD_ID, VERSION_LABEL = m.group(1), n.group(1)


# ---------------------------------------------------------------- dump parser
class Node:
    __slots__ = ("key", "val", "kids")

    def __init__(self, key, val=None):
        self.key = key
        self.val = val
        self.kids = []


ARRAY_HEADER_KEYS = ("Array Array", "int size")


def parse_dump(path):
    root = Node("__root__")
    stack = [(-1, root)]
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            s = line.strip()
            if " = " in s:
                k, v = s.split(" = ", 1)
            else:
                k, v = s, None
            node = Node(k, v)
            # array header lines ("Array Array" / "int size") never become
            # parents: this dump style writes [i] markers one level deeper
            # than the header, directly under the array field
            while stack and (
                indent <= stack[-1][0]
                or stack[-1][1].key in ARRAY_HEADER_KEYS
            ):
                stack.pop()
            stack[-1][1].kids.append(node)
            if node.key not in ARRAY_HEADER_KEYS:
                stack.append((indent, node))
    assert len(root.kids) == 1 and root.kids[0].key == "MonoBehaviour Base"
    return root.kids[0]


def kid(n, name):
    """First child whose field name matches (type prefix tolerated)."""
    for c in n.kids:
        if c.key == name or c.key.split()[-1] == name:
            return c
    return None


def has(n, name):
    return kid(n, name) is not None


def val(n, name):
    c = kid(n, name)
    return None if c is None else c.val


def intval(n, name):
    return int(val(n, name))


def boolval(n, name):
    return val(n, name) == "True"


def strval(n, name):
    v = val(n, name)
    if v is None:
        return None
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
        return v[1:-1]
    return v


def rawvec(n, name, dims=3):
    c = kid(n, name)
    if c is None:
        return None
    axes = ("x", "y", "z")[:dims]
    out = []
    for a in axes:
        t = val(c, a)
        if t is None:
            return None
        out.append(Raw(t))
    return out


def pptr(n, name):
    c = kid(n, name)
    if c is None:
        return None
    fid = val(c, "m_FileID")
    pid = val(c, "m_PathID")
    return {"file_id": int(fid), "path_id": int(pid)}


def arr_elems(n, name):
    """Elements of an array field: the node following each [i] marker."""
    c = kid(n, name)
    if c is None:
        return []
    elems = []
    take_next = False
    for k in c.kids:
        if k.key.startswith("["):
            take_next = True
            continue
        if take_next:
            elems.append(k)
            take_next = False
    size = kid(c, "size")
    if size is not None:
        assert len(elems) == int(size.val), f"{name}: {len(elems)} != {size.val}"
    return elems


class Raw(str):
    """Numeric token preserved byte-for-byte from the source dump."""


# ------------------------------------------------------------- serialization
def jdump(o):
    if isinstance(o, Raw):
        return str(o)
    if o is None:
        return "null"
    if o is True:
        return "true"
    if o is False:
        return "false"
    if isinstance(o, int):
        return str(o)
    if isinstance(o, float):  # defensive; corpus numbers are always Raw
        return repr(o)
    if isinstance(o, str):
        return json.dumps(o, ensure_ascii=False)
    if isinstance(o, dict):
        body = ",".join(jdump(k) + ":" + jdump(v) for k, v in o.items())
        return "{" + body + "}"
    if isinstance(o, list):
        return "[" + ",".join(jdump(v) for v in o) + "]"
    raise TypeError(type(o))


def write_jsonl(path, meta, rows):
    lines = [jdump(meta)] + [jdump(r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_json(path, obj):
    path.write_text(jdump(obj) + "\n", encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ ASL index
def asl_index(container):
    xml = (ASL_DIR / f"{container}.xml").read_text(encoding="utf-8")
    idx = {}
    for block in xml.split("<Asset>")[1:]:
        block = block.split("</Asset>")[0]
        if '<Type id="114">MonoBehaviour</Type>' not in block:
            continue
        nm = re.search(r"<Name>([^<]*)</Name>", block)
        pid = re.search(r"<PathID>(\d+)</PathID>", block)
        if nm and pid:
            idx.setdefault(nm.group(1), []).append(int(pid.group(1)))
    return idx


def resolve_path_ids(container, stem, suffixed_pids, asl):
    candidates = sorted(asl.get(stem, []))
    remaining = [p for p in candidates if p not in set(suffixed_pids)]
    assert len(remaining) >= 1, f"{container}:{stem}: no unclaimed ASL pathID"
    return candidates, remaining[0]


def container_files(container):
    d = MB / container
    return {p.name[:-4]: p for p in d.glob("*.txt")}


def dumps_for(container, stem):
    """[(dump_key, path)] where dump_key keeps the _#pid suffix grammar."""
    files = container_files(container)
    exact = stem in files
    pat = re.compile(re.escape(stem) + r"_#(\d+)$")
    suffixed = {int(m.group(1)): files[f"{stem}_#{m.group(1)}"]
                for m in (pat.match(f) for f in files) if m}
    asl = get_asl(container)
    if not exact and not suffixed:
        assert not asl.get(stem), \
            f"{container}:{stem}: ASL has instances but no dump files"
        return []
    _, first_pid = resolve_path_ids(container, stem, sorted(suffixed), asl)
    out = [(stem, files[stem], first_pid)] if exact else []
    for pid in sorted(suffixed):
        out.append((f"{stem}_#{pid}", suffixed[pid], pid))
    assert len(out) == len(asl.get(stem, [])), \
        f"{container}:{stem}: file census {len(out)} != ASL {len(asl.get(stem, []))}"
    return out


ASL_CACHE = {}


def get_asl(container):
    if container not in ASL_CACHE:
        ASL_CACHE[container] = asl_index(container)
    return ASL_CACHE[container]


# ------------------------------------------------------------------ containers
LEVELS = [f"level{i}" for i in range(24)]
CONTAINER_RANK = {c: i for i, c in enumerate(
    LEVELS + ["globalgamemanagers", "globalgamemanagers.assets",
              "resources.assets"]
    + [f"sharedassets{i}.assets" for i in range(24)])}


def loc_dirs():
    return sorted(p.name for p in LOC.iterdir()
                  if p.is_dir() and not p.name.startswith("_"))


def read_category(locale_dir, category):
    p = LOC / locale_dir / f"{category}.jsonl"
    if not p.exists():
        return None
    rows = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rows[int(r["line_index"])] = r["text"]
    return rows


# ------------------------------------------------------------------ extraction
def extract_world(container, path, pid):
    n = parse_dump(path)
    screens = []
    scr = kid(n, "positionsHintScreen")
    if scr is not None:
        for el in arr_elems(n, "positionsHintScreen"):
            screens.append({"x": Raw(val(el, "x")), "y": Raw(val(el, "y"))})
    pos = rawvec(n, "positionSpawn", 3)
    rot = rawvec(n, "rotationSpawn", 2)
    return {
        "name_location": strval(n, "nameLocation"),
        "position_spawn": pos,
        "rotation_spawn": rot,
        "show_hint": boolval(n, "showHint"),
        "index_hint": intval(n, "indexHint"),
        "hint_screens": screens,
        "go_path_id": pptr(n, "m_GameObject")["path_id"],
        "path_id": pid,
    }


def extract_scene_load(container, path, pid):
    n = parse_dump(path)
    def _unquote(v):
        if v is not None and len(v) >= 2 and v[0] == '"' and v[-1] == '"':
            return v[1:-1]
        return v

    saves = [_unquote(e.val) for e in arr_elems(n, "nameLevelSaves")]
    return {
        "name_scene_load": strval(n, "nameSceneLoad"),
        "name_scene_unload": strval(n, "nameSceneUnload"),
        "name_scene_continue": strval(n, "nameSceneContinue"),
        "string_file_name_part": intval(n, "stringFileNamePart"),
        "file_save": strval(n, "fileSave"),
        "name_level_saves": saves,
        "go_path_id": pptr(n, "m_GameObject")["path_id"],
        "path_id": pid,
    }


def poi_common(container, dump_key, cls, pid, kind, location_id, joins,
               position):
    return {
        "poi_id": f"{container}:{dump_key}",
        "class": cls,
        "kind": kind,
        "level": container,
        "location_id": location_id,
        "position": position,
        "joins": joins,
        "build_id": BUILD_ID,
        "_pid": pid,  # stripped before serialization
    }


POS_NONE = {"source": "none", "space": "unknown", "x": None, "y": None,
            "z": None}


def pos_inline(vec, space):
    return {"source": "inline", "space": space,
            "x": vec[0], "y": vec[1], "z": vec[2]}


def pos_pptr(target, space="unknown"):
    return {"source": "pptr-unresolved", "space": space, "x": None, "y": None,
            "z": None, "target": target}


def target_of(pp, kind):
    t = {"kind": kind, "path_id": pp["path_id"]}
    if pp["file_id"]:
        t["file_id"] = pp["file_id"]
    return t


def calls_summary(node, event_field):
    ev = kid(node, event_field)
    if ev is None:
        return []
    out = []
    grp = kid(ev, "m_PersistentCalls")
    calls_node = grp if grp is not None else ev
    for el in arr_elems(calls_node, "m_Calls"):
        asm = strval(el, "m_TargetAssemblyTypeName") or ""
        meth = strval(el, "m_MethodName") or ""
        mode = intval(el, "m_Mode")
        out.append({"target": asm.split(",")[0], "method": meth,
                    "mode": mode})
    return out


def main():
    load_pins()
    OUT.mkdir(parents=True, exist_ok=True)
    RELINKS.mkdir(parents=True, exist_ok=True)

    # ---------------- census over level containers (dedupe rule §2.7)
    level_dump_census = {}
    whole_census = {}
    for cont in CONTAINER_RANK:
        names = [p.name[:-4] for p in (MB / cont).glob("*.txt")]
        whole_census[cont] = names
        if cont in LEVELS:
            level_dump_census[cont] = names

    def class_instances(names, stem):
        return [x for x in names
                if x == stem or x.startswith(stem + "_#")]

    dedupe_classes = ["MitaKiller", "ObjectInteractive", "Trigger_Event",
                      "Transform_Position", "Interface_KeyHint_Key"]

    # ---------------- World registry
    world_rows = {}
    for lv in LEVELS:
        got = dumps_for(lv, "World")
        if got:
            (_, path, pid), = got
            world_rows[lv] = extract_world(lv, path, pid)

    def role_of(lv):
        i = int(lv[5:])
        if 3 <= i <= 22:
            return "story"
        return {0: "boot", 1: "title", 2: "menu", 23: "unbound"}[i]

    menu_en = read_category("English", "Menu")

    # scene_load per level
    sl_rows = {}
    for lv in LEVELS:
        got = dumps_for(lv, "Scene_Load")
        if got:
            (_, path, pid), = got
            sl_rows[lv] = extract_scene_load(lv, path, pid)

    # objective hint pools: EN pivot, else the first locale that carries
    # the category (FR-only extras are contentless-in-EN, never missing —
    # DS3 §4 classification)
    hint_categories = {}
    for lv in LEVELS:
        w = world_rows.get(lv)
        if not w or not w["name_location"]:
            continue
        cat = f'LocationHint {w["name_location"]}'
        carrier = None
        en = read_category("English", cat)
        if en is not None:
            carrier = "English"
        else:
            for d in loc_dirs():
                m = read_category(d, cat)
                if m is not None:
                    carrier, pool = d, m
                    break
        if carrier == "English":
            hint_categories[lv] = (cat, sorted(en), "English")
        elif carrier is not None and pool:
            hint_categories[lv] = (cat, sorted(pool), carrier)
        # carrier found but zero records (0-byte shell) -> contentless
        # everywhere; recorded in README, never fabricated as pointers

    quest_cats_en = {}
    for w in world_rows.values():
        nl = w["name_location"]
        if nl and read_category("English", nl) is not None:
            quest_cats_en[nl] = True

    scene_rows = []
    for lv in LEVELS:
        role = role_of(lv)
        w = world_rows.get(lv)
        sl = sl_rows.get(lv)
        loc = w["name_location"] if w else None
        hints = []
        hints_text = []
        hints_locale = None
        if lv in hint_categories:
            cat, idxs, carrier = hint_categories[lv]
            pool_en = read_category("English", cat)
            hints = [{"category": cat, "line_index": i} for i in idxs]
            hints_text = [pool_en[i] for i in idxs] \
                if pool_en is not None else []
            hints_locale = carrier
        quest = [loc] if (loc and loc in quest_cats_en) else []
        chapter_loc = None
        chapter_en = None
        part = sl["string_file_name_part"] if sl else 0
        if part:
            chapter_loc = {"category": "Menu", "line_index": part}
            chapter_en = menu_en.get(part)
            assert chapter_en is not None and chapter_en != "", \
                f"{lv}: Menu line {part} unresolved"
        row = {
            "scene_id": lv,
            "role": role,
            "location_id": loc,
            "display_name_loc": None,
            "objective_hints": hints,
            "objective_hints_text_en": hints_text,
            "objective_hints_source_locale": hints_locale,
            "quest_text_categories": quest,
            "spawn": None,
            "hint_screens": [],
            "sub_scenes_loaded": [],
            "sub_scenes_unloaded": [],
            "sub_scenes_continued": [],
            "chapter_name_loc": chapter_loc,
            "chapter_name_en": chapter_en,
            "provenance": None,
            "build_id": BUILD_ID,
            "version_label": VERSION_LABEL,
        }
        if w:
            assert role == "story", f"unexpected World on non-story {lv}"
            row["spawn"] = {
                "x": w["position_spawn"][0], "y": w["position_spawn"][1],
                "z": w["position_spawn"][2],
                "rot_x": w["rotation_spawn"][0],
                "rot_y": w["rotation_spawn"][1],
                "source": "inline", "space": "world-assumed",
            }
            row["hint_screens"] = w["hint_screens"]
            row["provenance"] = {"component": "World", "container": lv,
                                 "path_id": w["path_id"]}
        if sl:
            row["sub_scenes_loaded"] = ([sl["name_scene_load"]]
                                        if sl["name_scene_load"] else [])
            row["sub_scenes_unloaded"] = ([sl["name_scene_unload"]]
                                          if sl["name_scene_unload"] else [])
            row["sub_scenes_continued"] = ([sl["name_scene_continue"]]
                                           if sl["name_scene_continue"] else [])
        scene_rows.append(row)

    # ---------------- scene-links
    link_rows = []
    loaded_names = set()
    for lv in LEVELS:
        sl = sl_rows.get(lv)
        if not sl:
            continue
        loaded_names.add(sl["name_scene_load"])
    dangling = []
    chapter_links = 0
    for lv in LEVELS:
        sl = sl_rows.get(lv)
        if not sl:
            continue

        def edge(kind, name):
            ok = name in loaded_names
            if not ok:
                dangling.append((lv, kind, name))
            return {
                "from_level": lv,
                "edge_kind": kind,
                "to_sub_scene": name,
                "via_component": "Scene_Load",
                "path_id": sl["path_id"],
                "mechanism": "hard",
                "resolves": ok,
            }

        if sl["name_scene_load"]:
            link_rows.append(edge("loads", sl["name_scene_load"]))
        if sl["name_scene_unload"]:
            link_rows.append(edge("unloads", sl["name_scene_unload"]))
        if sl["name_scene_continue"]:
            link_rows.append(edge("continues", sl["name_scene_continue"]))
        if sl["string_file_name_part"]:
            link_rows.append({
                "from_level": lv,
                "edge_kind": "chapter_name",
                "to_sub_scene": None,
                "chapter_name_loc": {"category": "Menu",
                                     "line_index": sl["string_file_name_part"]},
                "via_component": "Scene_Load.stringFileNamePart",
                "path_id": sl["path_id"],
                "mechanism": "hard",
                "note": "Menu line_index is the client's own chapter "
                        "sequence; wiki numbering diverges (spec §2.4)",
            })
            chapter_links += 1
    level18_note = {
        "from_level": "level18",
        "edge_kind": "ledger",
        "to_sub_scene": None,
        "note": "level18 ships no Scene_Load component (measured absence, "
                "ASL+mb-dump both zero); lattice edges stay absent, never "
                "synthesized (spec S3)",
        "via_component": None,
        "path_id": None,
        "mechanism": "hard",
    }
    link_rows.append(level18_note)

    # ---------------- POIs
    poi_rows = []
    spawn_tables = []

    story_loc = {lv: world_rows[lv]["name_location"] for lv in LEVELS
                 if lv in world_rows}

    # FlashTaker cartridges (placement authority stays DS-4; join keys only)
    ft_saves = []
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "FlashTaker"):
            n = parse_dump(path)
            save = strval(n, "save")
            take = pptr(n, "objectTake")
            ft_saves.append((lv, save))
            joins = {"save_key": save,
                     "placement_authority": "extracted/data/cartridges/"
                                            "cartridges.jsonl (DS-4; consumed "
                                            "by reference, never re-derived)"}
            if take and take["path_id"]:
                position = pos_pptr(target_of(take, "GameObject"))
                joins["pickup_object_path_id"] = take["path_id"]
            else:
                position = dict(POS_NONE)
                joins["pickup_object_path_id"] = (
                    take["path_id"] if take else None)
            poi_rows.append(poi_common(lv, key, "FlashTaker", pid, "cartridge",
                                       story_loc.get(lv), joins, position))

    # TamagotchiGame pet cartridges (distinct in-fiction kind)
    for lv in LEVELS:
        for stem, fam in (("TamagotchiGame_Cartridge", "tamagotchi-game"),
                          ("TamagotchiGame_Cartridge_Cartridge",
                           "tamagotchi-pet-cartridge")):
            for key, path, pid in dumps_for(lv, stem):
                n = parse_dump(path)
                joins = {"cartridge_family": fam}
                poi_rows.append(poi_common(lv, key, stem, pid, "cartridge",
                                           story_loc.get(lv), joins,
                                           dict(POS_NONE)))

    # monster / anomaly carriers
    monster_classes = [
        "MitaKiller", "MitaFreak Enter", "Mob_Maneken",
        "Location10_MitaInShadow", "Mob_Cockroach", "Mob_ChibiMita",
        "QuadLiner_Enemy", "Shooter_Enemy",
    ]
    for cls in monster_classes:
        for lv in LEVELS:
            for key, path, pid in dumps_for(lv, cls):
                poi_rows.append(poi_common(lv, key, cls, pid, "monster",
                                           story_loc.get(lv), {},
                                           dict(POS_NONE)))
    # LightRenderer_Fog — anomaly CANDIDATE only (J6: identity unproven)
    fog_count = 0
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "LightRenderer_Fog"):
            poi_rows.append(poi_common(
                lv, key, "LightRenderer_Fog", pid, "other", story_loc.get(lv),
                {"curation": "fog-anomaly-candidate-unproven"}, dict(POS_NONE)))
            fog_count += 1

    # interactables
    oi_calls = 0
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "ObjectInteractive"):
            n = parse_dump(path)
            calls = calls_summary(n, "eventClick")
            oi_calls += len(calls)
            poi_rows.append(poi_common(
                lv, key, "ObjectInteractive", pid, "interactable",
                story_loc.get(lv), {"event_click_calls": calls},
                dict(POS_NONE)))

    # travel / portals
    tt_targets = []
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "Trigger_Teleport"):
            n = parse_dump(path)
            tgt = pptr(n, "targetTeleport")
            tt_targets.append((lv, tgt))
            poi_rows.append(poi_common(
                lv, key, "Trigger_Teleport", pid, "travel_gate",
                story_loc.get(lv), {},
                pos_pptr(target_of(tgt, "Transform"))))
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "Player_Teleport"):
            n = parse_dump(path)
            pos = rawvec(n, "position", 3)
            joins = {"position_add": boolval(n, "positionAdd"),
                     "use_rotation": boolval(n, "useRotation"),
                     "rotation": Raw(val(n, "rotation")),
                     "rotation_add": boolval(n, "rotationAdd"),
                     "use_rotation_head": boolval(n, "useRotationHead"),
                     "rotation_head": Raw(val(n, "rotationHead"))}
            # inline floats exist but their frame is unproven (IL-stub bodies)
            poi_rows.append(poi_common(
                lv, key, "Player_Teleport", pid, "travel_gate",
                story_loc.get(lv), joins, pos_inline(pos, "unknown")))
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "Scene_Load"):
            n = parse_dump(path)
            joins = {"scene_load": sl_rows[lv]["name_scene_load"],
                     "file_save": sl_rows[lv]["file_save"]}
            poi_rows.append(poi_common(lv, key, "Scene_Load", pid,
                                       "travel_gate", story_loc.get(lv),
                                       joins, dict(POS_NONE)))

    # AI move points
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "MitaAIMovePoint"):
            n = parse_dump(path)
            tm = pptr(n, "targetMove")
            mita = pptr(n, "mita")
            joins = {"mita_person_path_id": mita["path_id"] if mita else None}
            position = (pos_pptr(target_of(tm, "Transform"))
                        if tm and tm["path_id"] else dict(POS_NONE))
            poi_rows.append(poi_common(lv, key, "MitaAIMovePoint", pid,
                                       "move_point", story_loc.get(lv),
                                       joins, position))

    # proximity triggers
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "Trigger_DistanceCircle"):
            n = parse_dump(path)
            tgt = pptr(n, "target")
            joins = {"radius": Raw(val(n, "radius")),
                     "event_enter_calls": len(calls_summary(n, "eventEnter")),
                     "event_exit_calls": len(calls_summary(n, "eventExit"))}
            position = (pos_pptr(target_of(tgt, "Transform"))
                        if tgt and tgt["path_id"] else dict(POS_NONE))
            poi_rows.append(poi_common(lv, key, "Trigger_DistanceCircle", pid,
                                       "interactable", story_loc.get(lv),
                                       joins, position))

    # spawn events + spawn tables
    ecr_enum = {0: "halloween", 1: "christmas", 2: "none"}  # DEC enum order
    ecr_count = 0
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "Event_CreateResource"):
            n = parse_dump(path)
            day = intval(n, "eventDay")
            entries = []
            for el in arr_elems(n, "create"):
                parent = pptr(el, "parent")
                # element nodes ARE the PPtr ("PPtr<GameObject> data")
                refs = [{"file_id": int(val(pe, "m_FileID")),
                         "path_id": int(val(pe, "m_PathID"))}
                        for pe in arr_elems(el, "prefabCreate")]
                pt = {"kind": "Transform", "path_id": parent["path_id"]}
                if parent["file_id"]:
                    pt["file_id"] = parent["file_id"]
                entries.append({
                    "parent_target": pt,
                    "prefab_refs": [{"file_id": r["file_id"],
                                     "path_id": r["path_id"]} for r in refs],
                    "prefab_count": len(refs),
                })

            def arr_size(name):
                c = kid(kid(n, name), "size") if has(n, name) else None
                return int(c.val) if c is not None else None

            row = {
                "spawn_table_id": f"{lv}:{key}",
                "level": lv,
                "event_day": day,
                "event_day_label": ecr_enum[day],
                "destroy_after_create": boolval(n, "destroyObjectAfterCreate"),
                "entries": entries,
                "meshes_count": arr_size("meshes"),
                "materials_count": arr_size("materials"),
                "textures_count": arr_size("textures"),
                "destroy_objects_count": arr_size("destroyObjects"),
                "status": "unresolved-target",
                "build_id": BUILD_ID,
            }
            spawn_tables.append(row)
            ecr_count += 1
            poi_rows.append(poi_common(
                lv, key, "Event_CreateResource", pid, "spawn_event",
                story_loc.get(lv),
                {"spawn_table_id": row["spawn_table_id"]}, dict(POS_NONE)))

    # minigame access carriers
    mg_count = 0
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "MinigamesController"):
            n = parse_dump(path)
            joins = {"is_scene": boolval(n, "isScene")}
            wo = pptr(n, "worldObject")
            if wo and wo["path_id"]:
                joins["world_object_path_id"] = wo["path_id"]
            poi_rows.append(poi_common(lv, key, "MinigamesController", pid,
                                       "minigame_access", story_loc.get(lv),
                                       joins, dict(POS_NONE)))
            mg_count += 1

    # Basement_Safe furniture
    safe_count = 0
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "Basement_Safe"):
            n = parse_dump(path)
            buttons = kid(n, "buttons")
            size = int(kid(buttons, "size").val) if buttons is not None else 0
            er = len(calls_summary(n, "eventRight"))
            poi_rows.append(poi_common(
                lv, key, "Basement_Safe", pid, "safe", story_loc.get(lv),
                {"buttons": size, "event_right_calls": er}, dict(POS_NONE)))
            safe_count += 1

    # Transform_Position point sets (inline, parent-local where myParent!=0)
    tp_points_total = 0
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "Transform_Position"):
            n = parse_dump(path)
            parent = pptr(n, "myParent")
            points = []
            for el in arr_elems(n, "positions"):
                p = rawvec(el, "position", 3)
                r = rawvec(el, "rotation", 3)
                points.append({"x": p[0], "y": p[1], "z": p[2],
                               "rx": r[0], "ry": r[1], "rz": r[2]})
            tp_points_total += len(points)
            space = "parent-local" if (parent and parent["path_id"]) \
                else "unknown"
            if points:
                position = {"source": "inline", "space": space, "x": None,
                            "y": None, "z": None, "points": points}
            else:
                # instance serializes no points at all - nothing inline
                position = {"source": "none", "space": space, "x": None,
                            "y": None, "z": None}
            if parent and parent["path_id"] and position["source"] == "inline":
                position["target"] = target_of(parent, "Transform")
            poi_rows.append(poi_common(lv, key, "Transform_Position", pid,
                                       "move_point", story_loc.get(lv), {},
                                       position))

    # ObjectItem hand/face offsets (never map-projected)
    for lv in LEVELS:
        for key, path, pid in dumps_for(lv, "ObjectItem"):
            n = parse_dump(path)
            face = rawvec(n, "positionFace", 3)
            rotf = rawvec(n, "rotationFace", 3)
            hand = rawvec(n, "positionItemInHand", 3)
            joins = {"rotation_face": rotf, "item_in_hand_offset": hand}
            poi_rows.append(poi_common(lv, key, "ObjectItem", pid, "other",
                                       story_loc.get(lv), joins,
                                       pos_inline(face,
                                                  "object-local-offset")))

    # ordering: (container rank, class rank, poi_id)
    class_order = {c: i for i, c in enumerate(sorted({r["class"] for r in
                                                      poi_rows}))}
    poi_rows.sort(key=lambda r: (CONTAINER_RANK[r["level"]],
                                 class_order[r["class"]], r["poi_id"]))
    for r in poi_rows:
        del r["_pid"]

    # ---------------- poi-kinds curated rulings
    kinds_doc = {
        "_meta": {
            "schema": "miside.scenes.poi-kinds/1",
            "generator": "B-6 dataset-builder curation pass",
            "rule": "one ruling per class; marker_eligible=false rows are"
                    " excluded from marker projection (spec §3.3)",
            "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        },
        "classes": [
            {"class": "Basement_Safe", "kind": "safe", "marker_eligible": True,
             "note": "scene furniture; window percentages stay logic-layer"},
            {"class": "Event_CreateResource", "kind": "spawn_event",
             "marker_eligible": True,
             "note": "day/holiday-gated creation; table rows live in"
                     " spawn-tables.jsonl"},
            {"class": "FlashTaker", "kind": "cartridge",
             "marker_eligible": True,
             "note": "pickup carrier; placement authority DS-4 by reference"},
            {"class": "TamagotchiGame_Cartridge", "kind": "cartridge",
             "marker_eligible": True,
             "note": "in-fiction phone-space pet cartridges - distinct kind"
                     " from flash drives (AC S5)"},
            {"class": "TamagotchiGame_Cartridge_Cartridge", "kind":
             "cartridge", "marker_eligible": True,
             "note": "pet-cartridge subclass stem"},
            {"class": "Interface_KeyHint_Key", "kind": "interactable",
             "marker_eligible": False,
             "note": "enumerated NEXT TIER (382 level instances measured);"
                     " UI hint chips, not places"},
            {"class": "LightRenderer_Fog", "kind": "other",
             "marker_eligible": False,
             "note": "Fog-anomaly candidacy unproven (J6); never emitted as"
                     " a monster"},
            {"class": "Location10_MitaInShadow", "kind": "monster",
             "marker_eligible": True, "note": ""},
            {"class": "MakeManeken_Interaction", "kind": "interactable",
             "marker_eligible": False,
             "note": "dummy family enumerated next tier (~276 corpus-wide);"
                     " exact per-level sweep pending"},
            {"class": "MinigamesController", "kind": "minigame_access",
             "marker_eligible": True,
             "note": "access-location side of J7 hard; rules stay logic-layer"},
            {"class": "Mob_ChibiMita", "kind": "monster",
             "marker_eligible": True, "note": ""},
            {"class": "Mob_Cockroach", "kind": "monster",
             "marker_eligible": True, "note": ""},
            {"class": "Mob_Maneken", "kind": "monster",
             "marker_eligible": True, "note": ""},
            {"class": "MitaAIMovePoint", "kind": "move_point",
             "marker_eligible": True, "note": "targetMove PPtr unresolved"},
            {"class": "MitaFreak Enter", "kind": "monster",
             "marker_eligible": True, "note": ""},
            {"class": "MitaKiller", "kind": "monster",
             "marker_eligible": True,
             "note": "chase system switches on mid-game (absent levels 3-7,"
                     " 18)"},
            {"class": "ObjectInteractive", "kind": "interactable",
             "marker_eligible": True, "note": "eventClick call groups kept"},
            {"class": "ObjectItem", "kind": "other",
             "marker_eligible": False,
             "note": "hand/face offsets - NEVER map-projected (spec §3.3)"},
            {"class": "Player_Teleport", "kind": "travel_gate",
             "marker_eligible": True,
             "note": "inline destination floats, frame unproven (IL-stub)"
                     " - space unknown"},
            {"class": "QuadLiner_Enemy", "kind": "monster",
             "marker_eligible": True, "note": ""},
            {"class": "Scene_Load", "kind": "travel_gate",
             "marker_eligible": True,
             "note": "additive sub-scene gate; lattice owned by"
                     " scene-links.jsonl"},
            {"class": "Shooter_Enemy", "kind": "monster",
             "marker_eligible": True, "note": "all four in unbound level23"},
            {"class": "Transform_Position", "kind": "move_point",
             "marker_eligible": True,
             "note": "point sets; parent-relative where myParent!=0"},
            {"class": "Trigger_DistanceCircle", "kind": "interactable",
             "marker_eligible": True, "note": "proximity trigger"},
            {"class": "Trigger_Teleport", "kind": "travel_gate",
             "marker_eligible": True,
             "note": "portal chamber (all 14 in level9)"},
        ],
    }

    # ---------------- markers v1 (M0 projection rerun; map-viewer §3)
    # Owning datasets, consumed BY REFERENCE (never re-derived). Only
    # entities confirmed by these emitted files may carry a marker row.
    def read_owned(rel, id_field):
        out = []
        for line in (PACK / rel).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "_meta" in r:
                continue
            if "schema" in r and id_field not in r:
                continue  # flat header shape (DS-5 documents family)
            out.append(r)
        return out

    cart_rows = read_owned("extracted/data/cartridges/cartridges.jsonl",
                           "cartridge_id")
    prof_rows = read_owned("extracted/data/documents/profile_documents.jsonl",
                           "document_id")
    mini_rows = read_owned("extracted/data/cartridges/minigames.jsonl",
                           "minigame_id")
    mg_edges = read_owned("extracted/relinks/minigame--scene-carrier.jsonl",
                          "from")
    doc_edges = read_owned("extracted/relinks/document--scene-membership.jsonl",
                           "from")

    ROUTED_SEGMENT = {"cartridges": "cartridges", "profiles": "lore/profiles",
                      "minigames": "minigames"}
    loc_of_scene = {r["scene_id"]: r["location_id"] for r in scene_rows}

    def layer_of(container):
        # scene display layer: World.nameLocation when the scene binds one,
        # else the scene id itself (menu/boot/title/unbound bind none)
        return f"location-scenes/{loc_of_scene.get(container) or container}"

    def dump_key_of(poi_id):
        return poi_id.split(":", 1)[1]

    def instance_census(cls, container):
        """bare/suffixed/total recount of one class's instances in one
        container, from the emitted per-instance poi pool."""
        rows = [r for r in poi_rows
                if r["class"] == cls and r["level"] == container]
        bare = sum(1 for r in rows
                   if not re.search(r"_#\d+$", dump_key_of(r["poi_id"])))
        census = {"bare": bare, "suffixed": len(rows) - bare,
                  "total": len(rows)}
        assert census["total"] >= 1, \
            f"instance_census: {cls} has no instance in {container}"
        return census

    marker_rows = []

    # -- cartridge_item: FlashTaker poi rows <-> DS-4 via joins.save_key ----
    cart_by_save = defaultdict(list)
    for c in cart_rows:
        if c.get("save_key"):
            cart_by_save[c["save_key"]].append(c)
    for r in poi_rows:
        if r["class"] != "FlashTaker":
            continue
        save = r["joins"]["save_key"]
        hits = cart_by_save.get(save, [])
        assert len(hits) == 1, \
            f"join audit FAIL: save_key {save!r} -> {len(hits)} DS-4 rows"
        c = hits[0]
        pref = c.get("pickup_ref")
        assert pref and pref.get("container") == r["level"], \
            f"join audit FAIL: {c['cartridge_id']} pickup_ref drift vs " \
            f"{r['poi_id']} ({pref})"
        slug = c["cartridge_id"]
        container = r["level"]
        pos = dict(r["position"])
        # pptr rows name a transform target S9 will resolve; none-source rows
        # serialize no target at all -> honest scene granularity, never a spot
        pos["status"] = ("awaiting-transform-stage"
                         if r["position"]["source"] == "pptr-unresolved"
                         else "scene-granular")
        ek = "cartridges"
        marker_rows.append({
            "marker_id": f"{container}:cartridge:{slug}",
            "poi_id": r["poi_id"],
            "layer": layer_of(container),
            "kind": "cartridge",
            "entity_kind": ek,
            "entity_slug": slug,
            "icon": {"source": None,
                     "fallback_state": "named-explicit-missing"},
            "position": pos,
            "placement": {"mechanism": "hard", "source_join": "save_key",
                          "scene_binding": container},
            "links": {
                "page_url": f"/{ROUTED_SEGMENT[ek]}/{slug}",
                "focus_url": f"/map?focus={ek}:{slug}&scene={container}"},
        })
    cart_markers = len(marker_rows)

    # -- profile_document: DS-5 placement column (scene-granular always) ----
    doc_edge_by_id = {}
    for e in doc_edges:
        frm = e.get("from") or ""
        if e.get("kind") == "forward" and frm.startswith("profile_document:"):
            did = frm.split(":", 1)[1]
            assert did not in doc_edge_by_id, f"duplicate edge for {did}"
            doc_edge_by_id[did] = e
    placed_docs = [d for d in prof_rows if d.get("placement")]
    for d in placed_docs:
        slug = d["document_id"]
        pl = d["placement"]
        container = pl["container"]
        edge = doc_edge_by_id.get(slug)
        assert edge is not None, \
            f"join audit FAIL: no membership edge for {slug}"
        assert edge["to"] == f"container:{container}", \
            f"join audit FAIL: {slug} edge container {edge['to']} != DS-5 " \
            f"placement.container {container}"
        assert pl["carrier_class"] == "FlashTaker", \
            f"{slug}: unexpected carrier_class {pl['carrier_class']}"
        ek = "profiles"
        marker_rows.append({
            "marker_id": f"{container}:profile:{slug}",
            "placement_source": "DS-5",
            "document_id": slug,
            "poi_id": None,
            "layer": layer_of(container),
            "kind": "profile_document",
            "entity_kind": ek,
            "entity_slug": slug,
            "container": container,
            "icon": {"source": None,
                     "fallback_state": "named-explicit-missing"},
            "position": {"x": None, "y": None, "z": None,
                         "status": "scene-granular"},
            "instance_census": instance_census("FlashTaker", container),
            "placement": {"carrier_class": pl["carrier_class"],
                          "component_path_id": pl["component_path_id"],
                          "container": container,
                          "mechanism": edge["mechanism"],
                          "status": edge["status"],
                          "method": edge["method"],
                          "source_join": "DS-5 placement",
                          "scene_binding": container},
            "links": {
                "page_url": f"/{ROUTED_SEGMENT[ek]}/{slug}",
                "focus_url": f"/map?focus={ek}:{slug}&scene={container}"},
        })
    prof_markers = len(marker_rows) - cart_markers

    # -- minigame_access: carrier edges only, scene-granular (OQ-7/F-2) -----
    mg_ids = {m["minigame_id"] for m in mini_rows}
    fwd_edges = [e for e in mg_edges if e.get("direction") == "forward"]
    hosted_by_container = defaultdict(set)
    for e in mg_edges:
        if e.get("direction") != "inverse":
            continue
        frm, to = e.get("from") or "", e.get("to") or ""
        if frm.startswith("scene-class-family@") and to.startswith("minigame:"):
            hosted_by_container[frm.split("@", 1)[1]].add(
                to.split(":", 1)[1])
    seen_pairs = set()
    covered_containers = set()
    for e in fwd_edges:
        assert e["from"].startswith("minigame:") \
            and e["to"].startswith("scene-class-family@"), \
            f"unexpected carrier edge grammar: {e['from']} -> {e['to']}"
        mg = e["from"].split(":", 1)[1]
        container = e["to"].split("@", 1)[1]
        pair = (mg, container)
        assert pair not in seen_pairs, f"duplicate carrier pair {pair}"
        seen_pairs.add(pair)
        covered_containers.add(container)
        assert container in LEVELS, f"carrier container {container} not a level"
        assert e["mechanism"] == "hard", \
            f"carrier edge {pair} mechanism {e['mechanism']}"
        assert mg in mg_ids, \
            f"join audit FAIL: minigame {mg} not in minigames.jsonl ids"
    for container in hosted_by_container:
        fwd_set = {mg for (mg, cc) in seen_pairs if cc == container}
        assert hosted_by_container[container] == fwd_set, \
            f"carrier direction mismatch at {container}"
    for mg, container in sorted(seen_pairs):
        ek = "minigames"
        census = instance_census("MinigamesController", container)
        census["minigames_hosted"] = len(hosted_by_container[container])
        edge = next(e for e in fwd_edges
                    if e["from"] == f"minigame:{mg}"
                    and e["to"] == f"scene-class-family@{container}")
        marker_rows.append({
            "marker_id": f"{container}:minigame:{mg}",
            "placement_source": "minigame--scene-carrier",
            "minigame_id": mg,
            "poi_id": None,
            "layer": layer_of(container),
            "kind": "minigame_access",
            "entity_kind": ek,
            "entity_slug": mg,
            "container": container,
            "icon": {"source": None,
                     "fallback_state": "named-explicit-missing"},
            "position": {"x": None, "y": None, "z": None,
                         "status": "scene-granular"},
            "instance_census": census,
            "placement": {"mechanism": edge["mechanism"],
                          "status": edge["status"],
                          "method": edge["method"],
                          "role": edge.get("role"),
                          "source_join": "minigame--scene-carrier",
                          "scene_binding": container},
            "links": {
                "page_url": f"/{ROUTED_SEGMENT[ek]}/{mg}",
                "focus_url": f"/map?focus={ek}:{mg}&scene={container}"},
        })
    marker_rows.sort(key=lambda r: (
        {"cartridge": 0, "profile_document": 1,
         "minigame_access": 2}[r["kind"]], r["marker_id"]))
    cart_markers = sum(1 for r in marker_rows if r["kind"] == "cartridge")
    prof_markers = sum(1 for r in marker_rows
                       if r["kind"] == "profile_document")
    mg_markers = sum(1 for r in marker_rows if r["kind"] == "minigame_access")

    # -- two-list family ledger (A-MV1 F-1); counts recomputed, never v0 ----
    eligible_kind_of = {c["class"]: c["kind"] for c in kinds_doc["classes"]
                        if c["marker_eligible"]}
    pool = [(r["kind"], r["class"], r["level"]) for r in poi_rows
            if r["class"] in eligible_kind_of]
    for k, c, _ in pool:
        assert k == eligible_kind_of[c], \
            f"kind ruling drift: {c} carries kind {k} != ruled " \
            f"{eligible_kind_of[c]}"
    tally = Counter((k, c) for k, c, _ in pool)

    def fam_count(kinds, classes, include=None):
        n = 0
        for cls in classes:
            for (k, c), _n_kc in tally.items():
                if c != cls or k not in kinds:
                    continue
                by_lvl = Counter(l for (kk, cc, l) in pool
                                 if cc == cls and kk == k)
                if include is not None:
                    n += sum(by_lvl[l] for l in include)
                else:
                    n += sum(by_lvl.values())
        return n

    controller_levels = sorted({l for (k, c, l) in pool
                                if c == "MinigamesController"})
    uncovered_containers = [l for l in controller_levels
                            if l not in covered_containers]

    def deferred(fid, kinds, classes, reason, owner, owning_dataset, unblock):
        return {"family_id": fid, "poi_kinds": kinds, "poi_classes": classes,
                "poi_rows": fam_count(kinds, classes),
                "disposition": "deferred", "reason_code": reason,
                "unblock_owner": owner, "owning_dataset": owning_dataset,
                "unblock": unblock}

    pending_families = [
        {"family_id": "cartridge_item/flash-taker",
         "poi_kinds": ["cartridge"], "poi_classes": ["FlashTaker"],
         "poi_rows": fam_count(["cartridge"], ["FlashTaker"]),
         "disposition": "emitted", "emitted_markers": cart_markers,
         "owning_dataset": "extracted/data/cartridges/cartridges.jsonl",
         "join_key": "joins.save_key",
         "unblock": "emitted this rerun: DS-4 landed; projection re-derives"
                    " from joins.save_key on every pass"},
        deferred("cartridge_item/tamagotchi", ["cartridge"],
                 ["TamagotchiGame_Cartridge",
                  "TamagotchiGame_Cartridge_Cartridge"],
                 "owner-ruling-pending", "DS-4 curator (OQ-8)",
                 "(none - no DS-4 row exists for either class)",
                 "extend DS-4 with tamagotchi rows, re-rule the kind, or "
                 "confirm orphanhood; ships with CAR-8 compromised treatment "
                 "when resolved"),
        deferred("travel_gate/save-point", ["travel_gate"], ["Scene_Load"],
                 "no-entity-dataset", "SCN-1/XC-5",
                 "(SPEC save_point; no entity dataset emitted yet)",
                 "fileSave/nameLevelSaves vocabulary lives in scene-links + "
                 "relinks/scene--save-vocabulary; markers wait for the entity "
                 "owner"),
        deferred("travel_gate/unowned-teleports", ["travel_gate"],
                 ["Trigger_Teleport", "Player_Teleport"],
                 "no-entity-dataset", "SCN-6 tier-2 / scenes J8",
                 "(no travel_gate entity dataset emitted yet)",
                 "teleport targets are PPtr carriers; semantics stay "
                 "logic-layer until the tier-2 enumeration"),
        {"family_id": "minigame_access/carrier-covered",
         "poi_kinds": ["minigame_access"],
         "poi_classes": ["MinigamesController"],
         "level_scope": {"include": sorted(covered_containers)},
         "poi_rows": fam_count(["minigame_access"], ["MinigamesController"],
                               include=sorted(covered_containers)),
         "disposition": "emitted",
         # no emitted_markers here: these rows are relink-sourced
         # (placement-sourced shape), so their count appears exactly once,
         # keyed by source, under placement_families[] below (A-MV1 F-1)
         "emitted_via": "placement_families[]:"
                        "minigame_access/minigame--scene-carrier",
         "scope_rule": "containers holding >=1 forward carrier edge in "
                       "extracted/relinks/minigame--scene-carrier.jsonl",
         "owning_dataset": "extracted/relinks/minigame--scene-carrier.jsonl",
         "unblock": "emitted scene-granular per A-MV1 OQ-7; pin-level"
                    " upgrade waits for PIPE S9 carrier transforms"},
        {"family_id": "minigame_access/no-carrier-edge",
         "poi_kinds": ["minigame_access"],
         "poi_classes": ["MinigamesController"],
         "level_scope": {"include": uncovered_containers},
         "poi_rows": fam_count(["minigame_access"], ["MinigamesController"],
                               include=uncovered_containers),
         "disposition": "deferred", "reason_code": "no-carrier-edge",
         "unblock_owner": "DS-4 J7 follow-up",
         "owning_dataset": "extracted/relinks/minigame--scene-carrier.jsonl",
         "unblock": "these containers sit outside every carrier edge (joins "
                    "carry is_scene:false); J7 follow-up owns the recheck"},
        deferred("move_point", ["move_point"],
                 ["MitaAIMovePoint", "Transform_Position"],
                 "no-entity-dataset", "XC-5",
                 "(no move-point entity dataset emitted yet)",
                 "AI path waypoints have no entity registry to anchor slugs"),
        deferred("spawn_event", ["spawn_event"], ["Event_CreateResource"],
                 "unresolved-target-until-xc3", "XC-3",
                 "extracted/data/scenes/spawn-tables.jsonl (status:"
                 " unresolved-target)",
                 "prefab refs resolve when the XC-3 global pathID index lands"),
        deferred("safe", ["safe"], ["Basement_Safe"],
                 "no-entity-dataset", "XC-5",
                 "(no safe entity dataset emitted yet)",
                 "window percentages stay logic-layer (poi-kinds ruling)"),
        deferred("interactable", ["interactable"],
                 ["ObjectInteractive", "Trigger_DistanceCircle"],
                 "scn6-tier-2", "SCN-6",
                 "(tier-2 trigger/enumeration pass owns these classes)",
                 "next-tier POI enumeration (map-viewer §13 non-goal)"),
        deferred("monster_anomaly", ["monster"],
                 ["Location10_MitaInShadow", "Mob_Cockroach", "Mob_Maneken",
                  "MitaKiller", "MitaFreak Enter", "Shooter_Enemy",
                  "QuadLiner_Enemy", "Mob_ChibiMita"],
                 "no-entity-dataset", "XC-5",
                 "(no monster/anomaly entity dataset emitted yet)",
                 "strict no-orphan wait (A-MV1 OQ-3); counted rows on "
                 "/locations pages give the coverage meanwhile"),
    ]
    placement_families = [
        {"family_id": "profile_document/ds5-placement",
         "source_dataset":
             "extracted/data/documents/profile_documents.jsonl",
         "disposition": "emitted", "emitted_markers": prof_markers,
         "shape": "placement-sourced (map-viewer §3.2(b)): poi_id null, "
                  "scalar container split emitter-side, DS-5 placement "
                  "verbatim, scene-granular always"},
        {"family_id": "minigame_access/minigame--scene-carrier",
         "source_dataset":
             "extracted/relinks/minigame--scene-carrier.jsonl",
         "disposition": "emitted", "emitted_markers": mg_markers,
         "shape": "placement-sourced (map-viewer §3.2(b) per A-MV1 OQ-7): "
                  "one row per (minigame_id, container) carrier pair; "
                  "per-instance anchoring prohibited"},
    ]

    # ledger arithmetic asserted at emit (AC MV-0.4 a/b + disjointness)
    def claimed_by(kind, cls, level):
        hits = []
        for f in pending_families:
            if kind not in f["poi_kinds"] or cls not in f["poi_classes"]:
                continue
            sc = f.get("level_scope")
            if sc and "include" in sc and level not in sc["include"]:
                continue
            hits.append(f["family_id"])
        return hits

    for kind, cls, lvl in pool:
        hits = claimed_by(kind, cls, lvl)
        assert len(hits) == 1, \
            f"ledger partition: {kind}|{cls}@{lvl} claimed by {hits}"
    assert sum(f["poi_rows"] for f in pending_families) == len(pool), \
        "ledger partition sum != eligible recount"

    # -- position dispositions: total over the pptr-unresolved pool --------
    pptr_pool = [r for r in poi_rows
                 if r["position"]["source"] == "pptr-unresolved"]
    pptr_by_class = Counter(r["class"] for r in pptr_pool)
    position_dispositions = {"resolved-by-s9": 0,
                             "deferred:s9-not-run": len(pptr_pool)}
    assert sum(position_dispositions.values()) == len(pptr_pool)

    # -- unplaced confirmed entities (A-MV1 OQ-9: exclusion confirmed) -----
    unplaced = {
        "cartridges": [
            {"entity_kind": "cartridges", "entity_slug": c["cartridge_id"],
             "save_key": c["save_key"], "status": c["status"],
             "reason_code": "registered-unresolved-pickup",
             "note": "DS-4 pickup_ref null - registered without a proven "
                     "container; DOC-5 cited only as the analogous "
                     "cartridge-side undumped-grant row"}
            for c in cart_rows if not c.get("pickup_ref")],
        "profiles": [
            {"entity_kind": "profiles", "entity_slug": d["document_id"],
             "reason_code": d["placement_mechanism"],
             "note": "DS-5 placement_mechanism verbatim; no container "
                     "inference from container_location_binding [inferred] "
                     "(faked-spot law)"}
            for d in prof_rows if not d.get("placement")],
    }
    assert len(unplaced["cartridges"]) == 2 and len(unplaced["profiles"]) == 3
    # ---------------- relinks (parked until stage registration)
    rel_scene_chapter = []
    for r in scene_rows:
        if r["chapter_name_loc"]:
            fwd = {"direction": "forward",
                   "from": f"scene:{r['scene_id']}",
                   "to": f"loc:{r['chapter_name_loc']['category']}"
                         f"[{r['chapter_name_loc']['line_index']}]",
                   "mechanism": "hard",
                   "method": "Scene_Load.stringFileNamePart -> Menu"
                             " line_index (client's own pointer)",
                   "status": "modeled"}
            inv = dict(fwd, direction="inverse")
            rel_scene_chapter += [fwd, inv]
    rel_dialogue = []
    for lv, loc in sorted(story_loc.items()):
        if not loc:
            continue
        cat = f"LocationDialogue {loc}"
        fwd = {"direction": "forward", "from": f"scene:{lv}",
               "to": f"loc:{cat}[0..]", "mechanism": "hard",
               "method": "World.nameLocation -> dialogue category name"
                         " (DS-3 §3.6 upgraded to hard-corroborated)",
               "status": "modeled"}
        rel_dialogue += [fwd, dict(fwd, direction="inverse")]
    rel_hints = []
    for lv, (cat, idxs, carrier) in sorted(hint_categories.items()):
        fwd = {"direction": "forward", "from": f"scene:{lv}",
               "to": f"loc:{cat}[{idxs[0]}..{idxs[-1]}]" if idxs
                     else f"loc:{cat}[empty]",
               "mechanism": "hard",
               "method": "World.nameLocation -> LocationHint category"
                         f" (objective layer; carrier locale {carrier})",
               "status": "modeled"}
        rel_hints += [fwd, dict(fwd, direction="inverse")]
    gk = read_category("English", "LocationHintKey Location General")
    rel_hints.append({
        "direction": "forward", "from": "scene:*",
        "to": f"loc:LocationHintKey Location General[0..{len(gk) - 1}]",
        "mechanism": "hard",
        "method": "Interface_KeyHint_Key instances resolve interaction verbs"
                  " into the shared General pool",
        "status": "partial",
        "missing_fields": ["per-instance resolution waits for trigger-family"
                           " enumeration tier"]})
    # cartridge <-> character (J5) against DS-1 registry on disk
    char_by_save = {}
    with open(PACK / "extracted/data/characters/personages.jsonl",
              encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            r = json.loads(line)
            sk = r.get("save_key") or ""
            if sk:
                char_by_save.setdefault(sk, []).append(r["character_id"])
    rel_cart_char = []
    matched, unmatched = 0, []
    for lv, save in sorted(ft_saves):
        hits = char_by_save.get(save, [])
        edge = {"direction": "forward",
                "from": f"flashes:{save}",
                "to": (f"character:{hits[0]}" if len(hits) == 1 else
                       ("characters:" + "|".join(hits) if hits else None)),
                "mechanism": "hard" if hits else "inferred",
                "method": "FlashTaker.save <-> DS-1 personages.save_key"
                          " string match",
                "status": "modeled" if hits else "partial",
                "placed_in": lv}
        if hits:
            matched += 1
        else:
            unmatched.append(save)
        rel_cart_char.append(edge)
        rel_cart_char.append(dict(edge, direction="inverse"))
    for key in ("mtad2", "mtacore"):
        edge = {"direction": "forward", "from": f"flashes:{key}",
                "to": char_by_save.get(key, [None])[0],
                "mechanism": "inferred",
                "method": "registry key without FlashTaker carrier (granted"
                          " by console command / no pickup instance)",
                "status": "partial",
                "missing_fields": ["pickup_ref"],
                "curation_status": "registered-unresolved-pickup"}
        rel_cart_char.append(edge)
        rel_cart_char.append(dict(edge, direction="inverse"))
    mta_edge = {"direction": "forward", "from": "flashes:mta",
                "to": None, "mechanism": "inferred",
                "method": 'FlashTaker.save="mta" (level17) matches no DS-1'
                          ' gallery save_key',
                "status": "partial",
                "missing_fields": ["character_join"],
                "curation_status": "ruling-required (spec §9-R3)"}
    rel_cart_char.append(mta_edge)
    rel_cart_char.append(dict(mta_edge, direction="inverse"))
    rel_save_vocab = []
    save_vocab = set()
    for lv in LEVELS:
        sl = sl_rows.get(lv)
        if not sl:
            continue
        vals = [sl["file_save"]] + sl["name_level_saves"]
        vals = [v for v in vals if v]
        for v in vals:
            save_vocab.add(v)
            rel_save_vocab.append({
                "direction": "forward", "from": f"scene:{lv}",
                "to": f"save_point:{v}",
                "mechanism": "hard",
                "method": "Scene_Load.fileSave / nameLevelSaves[] verbatim",
                "status": "modeled"})
    lit_path = PACK / "extracted/il2cpp/stringliteral.json"
    if not lit_path.exists():
        # il2cpp/ moved off C: in the 2026-08-25 disk emergency; it sits
        # beside the relocated harvest root (MISIDE_HARVEST_ROOT/..)
        lit_path = HARVEST.parent / "il2cpp" / "stringliteral.json"
    assert lit_path.exists(), f"stringliteral.json not found ({lit_path})"
    lits = {e.get("value") for e in json.loads(
        lit_path.read_text(encoding="utf-8"))
        if isinstance(e, dict) and str(e.get("value", "")).startswith(
            "SaveGame")}
    assert save_vocab == lits, (save_vocab ^ lits)

    def rel_meta(family, pair, extra):
        m = {"family": family, "pair": pair,
             "mechanism_vocabulary": "hard|logic|inferred",
             "status_vocabulary": "modeled|partial|missing",
             "build_id": BUILD_ID, "version_label": VERSION_LABEL}
        m.update(extra)
        m["relocation_note"] = ("parked at extracted/data/scenes/relinks/;"
                                " moves to extracted/relinks/ when the emit"
                                " stage registers (B-1 precedent)")
        return m

    relinks = {
        "scene--chapter.jsonl":
            (rel_meta("scene↔chapter", "scene:level ↔ Menu[line_index]",
                      {"join": "stringFileNamePart"}),
             rel_scene_chapter),
        "scene--dialogue-pool.jsonl":
            (rel_meta("scene↔dialogue-pool",
                      "scene:level ↔ LocationDialogue Category",
                      {"join": "World.nameLocation"}),
             rel_dialogue),
        "scene--objective-hints.jsonl":
            (rel_meta("scene↔objective-hints",
                      "scene:level ↔ LocationHint*/LocationHintKey",
                      {"join": "World.nameLocation"}),
             rel_hints),
        "cartridge--character-placement.jsonl":
            (rel_meta("cartridge↔character-placement",
                      "flashes:<save_key> ↔ character:<id>",
                      {"join": "FlashTaker.save ↔ DS-1 save_key",
                       "matched_pairs": matched,
                       "unmatched_saves": unmatched}),
             rel_cart_char),
        "scene--save-vocabulary.jsonl":
            (rel_meta("scene↔save-vocabulary",
                      "scene:level ↔ save_point:<literal>",
                      {"join": "Scene_Load fileSave/nameLevelSaves",
                       "vocabulary_size": len(save_vocab),
                       "stringliteral_parity": "both-directions-equal"}),
             rel_save_vocab),
    }
    for fname, (meta, rows) in relinks.items():
        write_jsonl(RELINKS / fname, meta, rows)

    # ---------------- meta headers
    scenes_meta = {
        "_meta": {
            "schema": "miside.scenes.registry/1",
            "generator": "B-6 dataset-builder curation pass (run_all stage"
                         " registration pending; docs/specs/"
                         "dataset-scenes.mdx)",
            "source_table": "docs/specs/dataset-scenes.mdx sections 2-3 "
                            "(measured from extracted/harvest/mb-dump/"
                            "level*/World.txt + Scene_Load.txt + "
                            "localization/<locale>/)",
            "schema_doc": "contracts/dataset-scenes.mdx",
            "build_id": BUILD_ID,
            "version_label": VERSION_LABEL,
            "row_count": len(scene_rows),
            "ordering": "level0..level23 numeric",
            "derived_fields": ["objective_hints_text_en",
                               "objective_hints_source_locale (non-English"
                               " carrier for FR-only pools)",
                               "chapter_name_en", "quest_text_categories",
                               "role",
                               "display_name_loc(null until SPEC gap #1"
                               " closes)", "provenance"],
        },
    }
    links_meta = {
        "_meta": {
            "schema": "miside.scene-links.lattice/1",
            "generator": "B-6 dataset-builder curation pass",
            "source_table": "docs/specs/dataset-scenes.mdx §2.3/§3.2",
            "schema_doc": "contracts/dataset-scenes.mdx",
            "build_id": BUILD_ID,
            "version_label": VERSION_LABEL,
            "row_count": len(link_rows),
            "ordering": "level0..level23 then edge_kind loads,unloads,"
                        "continues,chapter_name",
            "derived_fields": ["resolves", "chapter_name rows", "level18"
                               " ledger row"],
        },
    }
    poi_meta = {
        "_meta": {
            "schema": "miside.scenes.poi/1",
            "generator": "B-6 dataset-builder curation pass",
            "source_table": "docs/specs/dataset-scenes.mdx §2.6-§2.7/§3.3",
            "schema_doc": "contracts/dataset-scenes.mdx",
            "build_id": BUILD_ID,
            "version_label": VERSION_LABEL,
            "row_count": len(poi_rows),
            "ordering": "(container rank, class, poi_id)",
            "position_truth_census": {
                "inline": sum(1 for r in poi_rows
                              if r["position"]["source"] == "inline"),
                "pptr-unresolved": sum(1 for r in poi_rows
                                       if r["position"]["source"] ==
                                       "pptr-unresolved"),
                "none": sum(1 for r in poi_rows
                            if r["position"]["source"] == "none"),
            },
            "dedupe_rule": "level-scene ownership wins (spec §2.7): only"
                           " mb-dump/level*/ copies emit; non-level copies"
                           " collapse into this _meta accounting:",
            "dedupe_accounting": {
                c: {"whole_corpus": len(class_instances(
                        [x for names in whole_census.values() for x in
                         names], c)),
                    "level_scenes": len(class_instances(
                        [x for names in level_dump_census.values() for x in
                         names], c))}
                for c in dedupe_classes},
            "derived_fields": ["kind (poi-kinds.json ruling)", "joins.*",
                               "location_id via World.nameLocation"],
        },
    }
    st_meta = {
        "_meta": {
            "schema": "miside.spawn-tables/1",
            "generator": "B-6 dataset-builder curation pass",
            "source_table": "docs/specs/dataset-scenes.mdx §2.7/§3.4",
            "schema_doc": "contracts/dataset-scenes.mdx",
            "build_id": BUILD_ID,
            "version_label": VERSION_LABEL,
            "row_count": len(spawn_tables),
            "ordering": "(level, dump filename)",
            "derived_fields": ["event_day_label (DEC enum order)",
                               "meshes/materials/textures/destroy counts",
                               "status=unresolved-target until global"
                               " pathID index (§9-R4)"],
        },
    }
    markers_meta = {
        "_meta": {
            "schema": "miside.markers.projection/1",
            "generator": "B-6 dataset-builder curation pass (M0 marker"
                         " projection rerun; docs/specs/map-viewer.mdx §3)",
            "source_table": "docs/specs/map-viewer.mdx §3.2/§4.1 (routed"
                            " entity_kind vocabulary supersedes the"
                            " dataset-scenes §3.5 example per A-MV1 OQ-4)",
            "schema_doc": "contracts/dataset-scenes.mdx",
            "build_id": BUILD_ID,
            "version_label": VERSION_LABEL,
            "row_count": len(marker_rows),
            "ordering": "(family block cartridge_item, profile_document,"
                        " minigame_access, then marker_id asc)",
            "no_orphan_rule": "markers exist ONLY for entities confirmed by"
                              " their owning dataset's emitted files; every"
                              " family below is deferred with its unblock -"
                              " none dropped silently",
            "focus_url_contract": "/map?focus=<entity_kind>:<entity_slug>"
                                  "&scene=<scene_id>; routed ENTITY_KINDS"
                                  " keys: cartridges|profiles|minigames"
                                  " (map-viewer §4.1)",
            "layer_contract": "location-scenes/<World.nameLocation> when the"
                             " scene binds a location, else the scene_id"
                             " itself (boot/title/menu/unbound bind none)",
            "pending_families": pending_families,
            "placement_families": placement_families,
            "position_dispositions": position_dispositions,
            "position_dispositions_note":
                f"total over the {len(pptr_pool)} pptr-unresolved poi rows;"
                f" class split: "
                + ", ".join(f"{c} ×{n}" for c, n in sorted(
                    pptr_by_class.items())) +
                "; PIPE S9 scene-transform (dataset-scenes §6) is the named"
                " coordinate unblock and has not run — no coordinates are"
                " fabricated, every row keeps its deferred reason code",
            "unplaced": unplaced,
        },
    }

    # ---------------- README (honesty ledger)
    truth = poi_meta["_meta"]["position_truth_census"]
    by_class = Counter(r["class"] for r in poi_rows)
    class_census = ", ".join(
        f"{cls} ×{n}" for cls, n in sorted(by_class.items(),
                                           key=lambda t: (-t[1], t[0])))
    readme = f"""# scenes — dataset honesty ledger (DS-6)

Emitted by `build/emit_scenes.py` (builder B-6, 2026-08-25) against
[docs/specs/dataset-scenes.mdx](../../../docs/specs/dataset-scenes.mdx)
(post-F-DS6; verifier [ds6-vA](../../../docs/research/verifications/ds6-vA.mdx)
PASS). Build **{BUILD_ID}** / **{VERSION_LABEL}**. Regenerate:
`python extracted/data/scenes/build/emit_scenes.py` (set `MISIDE_HARVEST_ROOT`
when extracted/harvest/ lives elsewhere) — reruns are byte-identical (no
wall-clock inputs; floats carried verbatim from the MB dumps).

## Files

- `scenes.jsonl` — {len(scene_rows)} registry rows ({sum(1 for r in scene_rows if r['role']=='story')} story + boot/title/menu + level23 `unbound`).
- `scene-links.jsonl` — {len(link_rows)} rows: {sum(1 for r in link_rows if r.get('edge_kind')=='loads')} loads / {sum(1 for r in link_rows if r.get('edge_kind')=='unloads')} unloads / {sum(1 for r in link_rows if r.get('edge_kind')=='continues')} continues edges, {chapter_links} chapter pointers, 1 level18 absence ledger row.
- `poi.jsonl` — {len(poi_rows)} placement-bearing instances: {class_census}.
- `spawn-tables.jsonl` — {len(spawn_tables)} Event_CreateResource rows.
- `markers.jsonl` — M0 projection rerun: {len(marker_rows)} entity-backed rows ({cart_markers} cartridge via DS-4 save_key · {prof_markers} profile_document from DS-5 placement · {mg_markers} minigame_access carrier pairs, the latter two families scene-granular with `poi_id:null`); family ledger + S9 dispositions in `_meta`.
- `poi-kinds.json` — curated class→kind rulings.
- `relinks/` — inverted indexes parked until stage registration (B-1 precedent).

## Position truth census

inline {truth['inline']} · pptr-unresolved {truth['pptr-unresolved']} · none {truth['none']}.
`world-assumed` appears ONLY on World.positionSpawn (scenes.jsonl).
Player_Teleport carries inline floats but its frame is unproven (IL-stub
bodies) → `space:"unknown"`. Transform_Position sets are parent-relative
where `myParent ≠ 0`, else `unknown`; S9 calibration will refine both.
ObjectItem face/hand offsets are `object-local-offset` and excluded from
marker projection. The transform stage (PIPE S9) flips pptr-unresolved rows
to inline without schema change.

## Measured corrections to the spec (dumps stay the anchor)

1. **level7 unloads** `"Scene 5 - StartHorror"` — DS-6 §2.3's table shows
   `—`; `mb-dump/level7/Scene_Load.txt` measures the string verbatim. Rows
   follow the dump.
2. **Non-zero chapter pointers = {chapter_links}**, not §5's projected 16.
3. **Event_CreateResource distribution**: levels 3–19 and 21 carry them;
   multiples at 4/5/6 (×2) and 17 (×3); absent from 20 and 22 — §2.7's
   "one per story level ± extra in 4/16/17" was a gloss.
4. **eventDay is holiday-gated**: measured values are only
   halloween (0, ×3) and christmas (1, ×21); DEC enum adds `none` (2,
   unused). "Day-gated" reading corrected.
5. **LocationHint pools: 18 in English, not §5's 19** — and
   `LocationHint Location18` (level20's objective pool) is CONTENTLESS in
   every locale: French ships a 0-byte file, no other locale ships any
   (measured census). Classified per DS3 §4: contentless ≠ missing; no
   pointers are fabricated for level20.
6. Some Transform_Position instances serialize an EMPTY positions array →
   labelled source "none", never inline-with-zero-points.

## Curation rulings

- `flashes:mta` (level17 FlashTaker) matches no DS-1 gallery save_key →
  relink row `curation_status:"ruling-required"` (spec §9-R3); display facts
  ship, no slug invented.
- `mtad2` / `mtacore` ride no FlashTaker (console grant / none) →
  `registered-unresolved-pickup` rows mirroring DS-4's tier ladder.
- `LightRenderer_Fog` ×{fog_count} stays kind `other` with
  `fog-anomaly-candidate-unproven` — J6's identity question is open.
- TamagotchiGame pet cartridges (level3, ×4) are the distinct in-fiction
  kind (AC S5), never merged with flash drives.

## Deferred families (enumerated next tier — never dropped)

Interface_KeyHint_Key ×382 and the MakeManeken_Interaction dummy family
(~276 corpus-wide) are measured but not emitted as POI rows this pass
(UI-hint/dummy carriers; counts pinned here and in poi-kinds.json).
Trigger_Event ×334 (level scenes), ObjectInteractiveItemTake ×11,
Transform_PositionCamera ×30, Transform_Magnet ×191,
Rigidbody_StartVelocity ×27, Transform_MovePointsStartFinish ×7 likewise
await their tier; endings' choice-node dataset already consumes part of
Trigger_Event/ObjectInteractive evidence. Menu-side pickers (MenuLocation
×16, MenuNextLocation ×52) live in level2 and stay out of the physical
carrier set.

## Markers v1 — M0 projection rerun (map-viewer §3)

The no-orphan rule (spec §3.5) still governs: markers exist only for
entities an owning dataset's emitted file confirms. DS-4 (cartridges), DS-5
(profile documents) and the minigame--scene-carrier relink have landed, so
the rerun emits:

- **{cart_markers} `cartridge` rows** — FlashTaker poi rows joined through
  `joins.save_key` to DS-4 `cartridge_id`s (join audited: exactly one DS-4
  row per save_key, pickup_ref.container equal to the poi container).
  19 carry their pptr target with `status:"awaiting-transform-stage"`; the 2
  whose `objectTake` is null serialize no transform at all and stay
  `scene-granular` — never a faked spot.
- **{prof_markers} `profile_document` rows** — placement-sourced shape
  (`placement_source:"DS-5"`, `poi_id:null`, scalar `container` split
  emitter-side out of any compound id, DS-5 `placement` verbatim,
  `instance_census`). Scene-granular always: DS-5 names the carrier
  component, not a resolved transform.
- **{mg_markers} `minigame_access` rows** — placement-sourced carrier pairs
  (`minigame_id` × `container`) over the {len(covered_containers)} covered
  containers, edge `mechanism/status/method` verbatim;
  `instance_census.minigames_hosted` keeps multi-minigame containers from
  reading as one-of-N (level9 hosts 4 minigames over 3 controllers).
  Per-instance controller anchoring is prohibited (A-MV1 OQ-7).

Deferred families stay deferred with reason codes in `_meta`
(`pending_families[]`, Σ poi_rows = {sum(f['poi_rows'] for f in pending_families)} eligible rows):
tamagotchi pet cartridges ×4 (`owner-ruling-pending`), save points ×19 +
unowned teleports ×27 (`no-entity-dataset`), move points ×102,
spawn events ×24 (`unresolved-target-until-xc3`), safes ×2, interactables
×344 (`scn6-tier-2`), monsters ×96, and level1's 3 controllers
(`no-carrier-edge`). Confirmed-but-unplaced entities (`mtad-2`, `mtacore`,
plus the 3 placement-less profiles under their DS-5-declared
`script_granted`/`story_granted` vocabulary) are accounted in
`_meta.unplaced` — no container inference from `[inferred]` bindings.

The {len(pptr_pool)} pptr-unresolved positions all defer as
`deferred:s9-not-run` (`_meta.position_dispositions`): PIPE S9's
scene-transform walk is the coordinate unblock and has not run. Registry v2
(display_label_loc, per-kind counts, artwork-driven status) is written by
the site artifact step additively over v1 fields.

## Non-story levels (evidence classes, Principle zero)

level0 boot: SceneStart, LogoPresent ×24(corpus), ComicBook. level1 title:
SceneLoading_Preloading, ChangeLanguageStart, OptionsGame. level2 menu:
MenuPersonage, MenuLocation ×16, MenuNextLocation ×52, MenuChangeLoadLevel.
level23 `unbound`: MitaKiller, Shooter_Enemy ×4, Achievement_function,
win-animation tracks; no World, no Scene_Load, binds no location (§9-R5).
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8", newline="\n")

    write_jsonl(OUT / "scenes.jsonl", scenes_meta, scene_rows)
    write_jsonl(OUT / "scene-links.jsonl", links_meta, link_rows)
    write_jsonl(OUT / "poi.jsonl", poi_meta, poi_rows)
    write_jsonl(OUT / "spawn-tables.jsonl", st_meta, spawn_tables)
    write_jsonl(OUT / "markers.jsonl", markers_meta, marker_rows)
    write_json(OUT / "poi-kinds.json", kinds_doc)
    summary = {
        "scenes": len(scene_rows),
        "links": len(link_rows),
        "links_chapter": chapter_links,
        "dangling": dangling,
        "poi": len(poi_rows),
        "truth": truth,
        "markers": len(marker_rows),
        "markers_by_kind": {"cartridge": cart_markers,
                            "profile_document": prof_markers,
                            "minigame_access": mg_markers},
        "eligible_pool": len(pool),
        "pptr_disposition": position_dispositions,
        "spawn_tables": len(spawn_tables),
        "ecr_event_days": sorted({r["event_day_label"]
                                  for r in spawn_tables}),
        "transform_position_points": tp_points_total,
        "fog": fog_count,
        "minigame_controllers_level": mg_count,
        "safes": safe_count,
        "objectinteractive_calls": oi_calls,
        "flash_saves": sorted({s for _, s in ft_saves}),
        "cart_char_matched": matched,
        "cart_char_unmatched": unmatched,
        "save_vocab": len(save_vocab),
        "locales": len(loc_dirs()),
    }
    print(json.dumps(summary, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
