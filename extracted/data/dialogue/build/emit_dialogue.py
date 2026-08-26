#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DS-3 dialogue-graph emitter (MiSide, buildId 19029065).

Implements docs/specs/dataset-dialogue.mdx exactly:
  node kinds §3.1 · node record §3.2 · edge kinds §3.3 · binding rule §3.6
  (union-of-carriers, line_index = indexString − 1 at every use) ·
  outputs §7 · ACs D1–D9.

Parked here pending PIPE §3 stage-tree adoption (arbiter residue (a) picked
the `extracted/data/dialogue/` family name; brief B-3 pins the path).

Inputs (all read-only):
  extracted/harvest/mb-dump/<container>/*.txt   typed MonoBehaviour dumps (fields)
  RAW MiSideFull_Data/globalgamemanagers.assets MonoScript class table (identity)
  RAW MiSideFull_Data/levelN                    true component PathIDs + GO pids
                                                (identity only — raw header parse,
                                                no typetree needed)
  extracted/localization/<locale>/<category>.jsonl
  extracted/localization/_ledger/encoding-residue.jsonl

Outputs (byte-deterministic, D9): see OUT_FILES below.
"""
import csv
import io
import json
import os
import re
import struct
import sys
from collections import defaultdict

PACK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
EXTRACTED = os.path.join(PACK, "extracted")
MB = os.path.join(EXTRACTED, "harvest", "mb-dump")
LOC = os.path.join(EXTRACTED, "localization")
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RAW_DATA = r"A:\SteamLibrary\steamapps\common\MiSide\MiSideFull_Data"

BUILD = 19029065                       # E1/DAQ pin; every record stamps it (D8)

# ---- code authorities (extracted/decompiled/main/Assembly-CSharp/) ----------
THEMES = ["Mita", "MitaOld", "MitaNew", "Player", "ChibiMita", "MitaKnow",
          "Creepy", "LittleMita", "White", "Limping", "MitaDark", "MitaDream",
          "MitaGlasses", "MitaFon"]            # Dialogue_3DText.Dialogue3DTheme
EMOTIONS = ["none", "off", "smile", "angry", "quest", "smileteeth", "sad",
            "smilestrange", "shy", "smileobvi", "smiletonque", "smilecringe",
            "sleep", "halfsleep", "surprise", "emptiness", "deactiveEmotion",
            "suspicion", "trytoque", "discontent", "ajar", "catchQuest",
            "arrogance", "surpriseo"]          # EmotionType.cs (declaration order)
L14_SPEAKERS = ["player", "mita"]              # Location14_Dialogue.Loc14WhioSpeak
STYLES = ["normal", "horror"]                  # DialogueChanger.TypeSyleQuestDialogue

# The five enums D6 fences as null:"pending-curation" (brief + spec §9.3).
PENDING = {"MitaKnow", "MitaFon", "White", "Creepy", "MitaDream"}
# Provisional slugs for the nine unambiguous themes (alignment with DS-1
# curation lands later; status field says so on every row).
SLUGS = {
    "Mita": ("mita_variant", "mita"),
    "MitaOld": ("mita_variant", "mita-old"),
    "MitaNew": ("mita_variant", "mita-new"),
    "Player": ("player_character", "player"),
    "ChibiMita": ("player_character", "chibi-player"),
    "LittleMita": ("mita_variant", "little-mita"),
    "Limping": ("player_character", "limping-person"),
    "MitaDark": ("mita_variant", "mita-dark"),
    "MitaGlasses": ("mita_variant", "mita-glasses"),
}
DISPLAY_ANCHOR = {"Mita": {"names_line": 0}, "Player": {"names_line": 1}}

NODE_CLASSES = {
    "Dialogue_3DText": "ambient_line",
    "DialogueChanger": "quest_box",
    "Location14_Dialogue": "branch_group",
    "Location18_Dialogue": "grouped_scene_dialogue",
    "Tamagotchi_Dialogue_Mob": "pet_dialogue",
    "Location21_DialogueRandom": "random_router",
}

LOCALES = sorted(d for d in os.listdir(LOC)
                 if os.path.isdir(os.path.join(LOC, d)) and d != "_ledger")

LD_CATS = ["LocationDialogue Location%d" % i for i in list(range(1, 16)) + list(range(17, 21))]
LEVELS = ["level%d" % n for n in range(0, 24)]
BIND = {("level%d" % n): ("LocationDialogue Location%d" % (n - 2))
        for n in range(3, 23) if n not in (18,)}


def jdump(path, obj):
    """Byte-deterministic JSON write (sorted where free, LF, no BOM)."""
    data = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)


def jl(path, rows):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# dump-text parser (AssetStudioMod typed tree: tab-indented)
# ---------------------------------------------------------------------------

class Node(object):
    __slots__ = ("line", "kids")

    def __init__(self, line):
        self.line = line
        self.kids = []

    @property
    def scalar(self):
        return " = " in self.line

    @property
    def value(self):
        return self.line.rsplit(" = ", 1)[1]

    @property
    def name(self):
        head = self.line.split(" = ", 1)[0]
        return head.split()[1] if len(head.split()) > 1 else head.split()[0]

    def child(self, name):
        for k in self.kids:
            if k.name == name and not k.line.endswith("]"):
                return k
        return None

    def items(self):
        """Array items of an `X[] name` node → list[Node] (each `... data`).

        AssetStudioMod writes items one indent PAST `int size = N`:
            X[] name / Array Array / int size = N / [i] / TypeName data
        """
        holder = self
        has_items_here = any(k.line.endswith("]") for k in self.kids)
        if not has_items_here:
            for k in self.kids:
                if k.scalar and k.name == "size":
                    holder = k
                    break
        out, cur = [], False
        for k in holder.kids:
            if k.line.endswith("]"):
                cur = True
                continue
            if cur and not k.line.endswith("]"):
                out.append(k)
        return out


def parse_dump(text):
    root, stack = None, []
    for raw in text.split("\n"):
        if not raw.strip():
            continue
        depth = len(raw) - len(raw.lstrip("\t"))
        n = Node(raw.strip())
        if depth == 0:
            root = n
            stack = [n]
            continue
        while len(stack) <= depth:
            stack.append(stack[-1])
        parent = stack[depth - 1]
        parent.kids.append(n)
        stack[depth:] = [n]
    return root


def scalar_str(v):
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    return v


def ptr(node):
    """PPtr subtree → {'file_id': int, 'path_id': int}."""
    fid = node.child("m_FileID")
    pid = node.child("m_PathID")
    return {"file_id": int(fid.value), "path_id": int(pid.value)}


def calls(event_node):
    """UnityEvent node → list of persistent-call dicts (verbatim, typed)."""
    grp = event_node.child("m_PersistentCalls")
    lst = grp.child("m_Calls") if grp else None
    out = []
    if lst is None:
        return out
    for it in lst.items():
        tgt = it.child("m_Target")
        args = it.child("m_Arguments")
        obj_arg = args.child("m_ObjectArgument") if args else None
        out.append({
            "target_ptr": ptr(tgt) if tgt is not None else None,
            "target_type": scalar_str(it.child("m_TargetAssemblyTypeName").value),
            "method": scalar_str(it.child("m_MethodName").value),
            "mode": int(it.child("m_Mode").value),
            "call_state": int(it.child("m_CallState").value),
            "args": {
                "object_ptr": ptr(obj_arg) if obj_arg is not None else None,
                "int": int(args.child("m_IntArgument").value),
                "float": float(args.child("m_FloatArgument").value),
                "string": scalar_str(args.child("m_StringArgument").value),
                "bool": args.child("m_BoolArgument").value == "True",
            },
        })
    return out


# ---------------------------------------------------------------------------
# identity pass: true component PathIDs from the scene files themselves
# ---------------------------------------------------------------------------

def parse_mb_header(data):
    off = 0
    _fid, = struct.unpack_from("<i", data, off); off += 4
    gpid, = struct.unpack_from("<q", data, off); off += 8
    off += 4                                     # m_Enabled u8 + pad
    sfid, = struct.unpack_from("<i", data, off); off += 4
    spid, = struct.unpack_from("<q", data, off); off += 8
    nlen, = struct.unpack_from("<i", data, off); off += 4
    name = data[off:off + nlen].decode("utf-8", "replace")
    return gpid, sfid, spid, name


def script_table(path):
    import UnityPy
    env = UnityPy.load(path)
    table = {}
    for obj in env.objects:
        if obj.type.name == "MonoScript":
            try:
                table[obj.path_id] = obj.read_typetree().get("m_ClassName", "?")
            except Exception:
                pass
    return table


def container_identities(path, scripts):
    """→ ({class_name: [(true_pid, go_pid)]}, {pid: obj_type}, go→[(cls,pid)])"""
    import UnityPy
    env = UnityPy.load(path)
    exts = [os.path.basename(getattr(e, "path_name", getattr(e, "path", "")))
            for e in env.file.externals]
    by_class = defaultdict(list)
    obj_types = {}
    comps_on_go = defaultdict(list)
    for obj in env.objects:
        obj_types[obj.path_id] = obj.type.name
        if obj.type.name != "MonoBehaviour":
            continue
        gpid, sfid, spid, _ = parse_mb_header(obj.get_raw_data())
        cls = scripts.get(spid) if (sfid > 0 and sfid - 1 < len(exts)
                                    and exts[sfid - 1] == "globalgamemanagers.assets") else None
        cls = cls or "?external%d" % sfid
        by_class[cls].append((obj.path_id, gpid))
        comps_on_go[gpid].append((cls, obj.path_id))
    return by_class, obj_types, comps_on_go


# ---------------------------------------------------------------------------
# loc layer
# ---------------------------------------------------------------------------

def cat_rows(locale, category):
    """[(line_index:int, text:str)] split-based; None when category absent."""
    p = os.path.join(LOC, locale, category + ".jsonl")
    if not os.path.exists(p):
        return None
    rows = []
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows.append((r["line_index"], r["text"]))
    return rows


def cat_count(en_rows_cache, category):
    if category not in en_rows_cache:
        en_rows_cache[category] = cat_rows("English", category)
    rows = en_rows_cache[category]
    return len(rows) if rows is not None else -1


# ===========================================================================
# main build
# ===========================================================================

def main():
    log = lambda *a: print(*a, file=sys.stderr)
    ledgers = {
        "dangling": [],       # D5
        "range": [],          # D2 violations / span-rule rows
        "identity": [],       # dump-file ↔ true-pathID reconciliation rows
        "notes": [],
    }
    en_cache = {}
    os.makedirs(os.path.join(OUT, "graphs"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "_ledger"), exist_ok=True)

    scripts = script_table(os.path.join(RAW_DATA, "globalgamemanagers.assets"))
    log("MonoScript table: %d classes" % len(scripts))

    nodes = []                 # dicts (node records §3.2 + kind payload)
    edges = []                 # dicts §7 edges.jsonl
    per_level = defaultdict(lambda: {"nodes": [], "amb_by_go": {}, "by_true_pid": {},
                                     "go_multi": defaultdict(list)})

    all_comp_class = defaultdict(dict)   # level -> {true_pid: class} (every MB)
    go_census = {}                       # level -> {"all_go": set, "comps_on_go": dict}

    for level in LEVELS:
        ldir = os.path.join(MB, level)
        if not os.path.isdir(ldir):
            continue
        idents, obj_types, comps_on_go = container_identities(
            os.path.join(RAW_DATA, level), scripts)
        go_census[level] = {"obj_types": obj_types, "comps_on_go": comps_on_go}

        # index identity rows per class for matching + resolution maps
        ident_by_go = defaultdict(list)     # (class, go_pid) -> [true_pid]
        ident_by_pid = {}                   # true_pid -> (class, go_pid)
        for cls, rowsx in idents.items():
            for tp, gp in rowsx:
                ident_by_go[(cls, gp)].append(tp)
                ident_by_pid[tp] = (cls, gp)
        for tp, (cls, _gp) in sorted(ident_by_pid.items()):
            all_comp_class[level][tp] = cls

        files = sorted(f for f in os.listdir(ldir))
        dumps = []
        for fname in files:
            m = re.match(r"^(.*)_#\d+\.txt$", fname)
            if m:
                dumps.append((fname, m.group(1)))

        matched_by_cls = defaultdict(set)   # cls -> {true_pid} matched so far
        for fname, cls in list(dumps):
            if cls not in NODE_CLASSES:
                continue
            with io.open(os.path.join(ldir, fname), encoding="utf-8") as fh:
                root = parse_dump(fh.read())
            go_pid = ptr(root.child("m_GameObject"))["path_id"]
            cands = ident_by_go.get((cls, go_pid), [])
            if len(cands) == 1:
                true_pid = cands[0]
            elif not cands:
                ledgers["identity"].append({
                    "level": level, "dump": fname, "issue": "no-identity-match",
                    "go_path_id": go_pid})
                continue
            else:
                ledgers["identity"].append({
                    "level": level, "dump": fname, "issue": "ambiguous-identity",
                    "go_path_id": go_pid, "candidates": cands})
                continue
            matched_by_cls[cls].add(true_pid)
            emit_node(nodes, edges, per_level[level], level, cls, true_pid,
                      go_pid, root, ledgers, en_cache)

        # plain-named instances: AssetStudioMod gives the FIRST dump of a
        # class in a container the bare `<Class>.txt` name (suffix _#toolId
        # only on collision), so exactly one true PathID per class stays
        # unmatched after the numbered files — that is the plain instance.
        for cls in sorted(NODE_CLASSES):
            present = sorted({tp for tp, _ in idents.get(cls, [])})
            if not present or cls == "Location21_DialogueRandom":
                continue   # zero-instance kinds emit nothing; measured absence
            rest = [tp for tp in present if tp not in matched_by_cls[cls]]
            if len(rest) != 1:
                continue   # no bare-named dump for this class here (or drift)
            true_pid = rest[0]
            go_pid = ident_by_pid[true_pid][1]
            ppath = os.path.join(ldir, cls + ".txt")
            if not os.path.exists(ppath):
                ledgers["identity"].append({
                    "level": level, "class": cls,
                    "issue": "unmatched-identity-without-bare-dump",
                    "true_path_id": true_pid})
                continue
            with io.open(ppath, encoding="utf-8") as fh:
                root = parse_dump(fh.read())
            got_go = ptr(root.child("m_GameObject"))["path_id"]
            if got_go != go_pid:
                ledgers["identity"].append({
                    "level": level, "class": cls,
                    "issue": "go-mismatch-bare-file",
                    "expected_go": go_pid, "dump_go": got_go})
                continue
            ledgers["identity"].append({
                "level": level, "class": cls, "issue": "bare-named-instance",
                "true_path_id": true_pid, "go_path_id": go_pid,
                "method": "elimination over matched numbered dumps"})
            emit_node(nodes, edges, per_level[level], level, cls, true_pid,
                      go_pid, root, ledgers, en_cache)

    # ------------------------------------------------------------------
    # second pass: resolve PPtr edges now that all nodes exist
    # ------------------------------------------------------------------
    resolve_edges(nodes, edges, per_level, ledgers, all_comp_class, go_census)

    # ------------------------------------------------------------------
    # text refs: line_index = index − 1 everywhere (§3.6 contract), range
    # checks against GetCountString(category) (AC D2), union-span rows (§3.6)
    # ------------------------------------------------------------------
    validate_ranges(nodes, ledgers, en_cache)

    # ------------------------------------------------------------------
    # condition hints (§3.5) — EN pivot comments attached to next content row
    # ------------------------------------------------------------------
    hint_stats = attach_hints(nodes, ledgers, en_cache)

    # ------------------------------------------------------------------
    # speakers.json (D6)
    # ------------------------------------------------------------------
    emit_speakers()

    # availability.csv (D3) + per-locale parity ledger + residue links (D4)
    parity_stats = emit_availability(en_cache)
    residue_nodes = emit_residue_links(nodes)

    # graphs/<level>.json
    entry_term = {}
    for level in sorted(per_level):
        st = per_level[level]
        ids = sorted(n["id"] for n in nodes if n["level"] == level)
        inbound = set()
        for e in edges:
            if e["kind"] in ("next", "choice", "branch_left", "branch_right") \
               and e.get("dst") and e["dst"].split(":")[0] == level:
                inbound.add(e["dst"])
        entries = sorted(i for i in ids if i not in inbound)
        boxes = sorted(n["id"] for n in nodes
                       if n["level"] == level and n["kind"] == "quest_box")
        terminals = sorted(n["id"] for n in nodes if n["level"] == level
                           and n["kind"] == "ambient_line"
                           and (n.get("_next_null") is True))
        g = {
            "build": BUILD,
            "level": level,
            "location_category": BIND.get(level),
            "nodes": ids,
            "entry_points_interaction": boxes,
            "entry_points_graph": [e for e in entries if e not in set(boxes)],
            "terminals_next_null": terminals,
            "edge_count": sum(1 for e in edges
                              if (e.get("src") or "").split(":")[0] == level),
            "dangling_edge_rows": sum(1 for r in ledgers["dangling"]
                                      if r["src"].split(":")[0] == level),
        }
        os.makedirs(os.path.join(OUT, "graphs"), exist_ok=True)
        jdump(os.path.join(OUT, "graphs", "%s.json" % level), g)
        entry_term[level] = g

    # core outputs (§7) ------------------------------------------------------
    os.makedirs(OUT, exist_ok=True)
    nodes.sort(key=lambda n: (n["level"], n["kind"], n["source"]["path_id"]
                              if n["source"]["path_id"] is not None else -1))
    clean_nodes = []
    for n in nodes:
        r = {k: v for k, v in n.items() if not k.startswith("_")}
        clean_nodes.append(r)
    jl(os.path.join(OUT, "nodes.jsonl"), clean_nodes)
    edges.sort(key=lambda e: (e["kind"], str(e.get("src")), str(e.get("dst")),
                              str(e.get("slot")), int(e.get("call_index", 0))))
    jl(os.path.join(OUT, "edges.jsonl"), edges)

    # ledgers -----------------------------------------------------------------
    os.makedirs(os.path.join(OUT, "_ledger"), exist_ok=True)
    jl(os.path.join(OUT, "_ledger", "dangling-edges.jsonl"), sorted(
        ledgers["dangling"],
        key=lambda r: (str(r.get("src")), str(r.get("slot")),
                       int(r.get("call_index", 0)), str(r.get("kind")))))
    jl(os.path.join(OUT, "_ledger", "range-check.jsonl"), ledgers["range"])
    jl(os.path.join(OUT, "_ledger", "identity-reconciliation.jsonl"), ledgers["identity"])

    kind_counts = defaultdict(int)
    for n in nodes:
        kind_counts[n["kind"]] += 1
    edge_counts = defaultdict(int)
    for e in edges:
        edge_counts[e["kind"]] += 1
    meta = {
        "build": BUILD,
        "spec": "docs/specs/dataset-dialogue.mdx",
        "emitter": "extracted/data/dialogue/build/emit_dialogue.py",
        "nodes_total": len(nodes),
        "nodes_by_kind": dict(sorted(kind_counts.items())),
        "edges_total": len(edges),
        "edges_by_kind": dict(sorted(edge_counts.items())),
        "levels_with_graph": sorted(per_level),
        "hint_stats": hint_stats,
        "ledger_rows": {k: len(v) for k, v in ledgers.items()},
        "residue_nodes": residue_nodes,
        "locale_count": len(LOCALES),
        "locale_parity": parity_stats,
        "binding_rule": "levelN -> LocationDialogue Location(N-2); validated "
                        "per level in _ledger/range-check.jsonl",
        "off_by_one_contract": "line_index = game_index - 1 at EVERY use "
                               "(indexString, stringFile, indexFile, index)",
    }
    jdump(os.path.join(OUT, "_ledger", "build-meta.json"), meta)
    log(json.dumps(meta, indent=1)[:2000])


# ---------------------------------------------------------------------------
# node emission
# ---------------------------------------------------------------------------

def base_record(level, kind, cls, true_pid, go_pid):
    return {
        "id": "%s:%s#%d" % (level, cls, true_pid),
        "kind": kind,
        "level": level,
        "location": BIND.get(level),
        "chapter": None,
        "speaker": None,
        "text_ref": None,
        "emotion": None,
        "style": None,
        "voice_present": None,
        "condition_hints": [],
        "build": BUILD,
        "source": {"container": level, "class": cls,
                   "path_id": true_pid, "gameobject_path_id": go_pid},
    }


def emit_node(nodes, edges, lstate, level, cls, true_pid, go_pid, root,
              ledgers, en_cache):
    kind = NODE_CLASSES[cls]

    if kind == "ambient_line":
        rec = base_record(level, kind, cls, true_pid, go_pid)
        idx = int(root.child("indexString").value)
        theme_i = int(root.child("themeDialogue").value)
        es = int(root.child("emotionStart").value)
        ef = int(root.child("emotionFinish").value)
        rec["speaker"] = theme_speaker(THEMES[theme_i] if 0 <= theme_i < len(THEMES)
                                       else "?theme%d" % theme_i)
        rec["text_ref"] = {"category": BIND.get(level), "line_index": idx - 1,
                           "game_index": idx}
        rec["emotion"] = {"start": EMOTIONS[es] if 0 <= es < len(EMOTIONS) else "?%d" % es,
                          "finish": EMOTIONS[ef] if 0 <= ef < len(EMOTIONS) else "?%d" % ef}
        nt = root.child("nextText")
        np_ = ptr(nt) if nt is not None else {"file_id": 0, "path_id": 0}
        rec["_next_ptr"] = np_
        rec["_next_null"] = np_["path_id"] == 0
        ev = {}
        for slot in ("eventFinish", "eventFinishPrint", "eventDontVoice"):
            c = calls(root.child(slot))
            if c:
                ev[slot] = c
                for i, call in enumerate(c):
                    edges.append({
                        "kind": "on_finish_action", "src": rec["id"],
                        "dst": None, "slot": slot, "call_index": i,
                        "call": call, "resolved_to": None})
        rec["events_with_calls"] = sorted(ev)
        nodes.append(rec)
        lstate["amb_by_go"][go_pid] = rec["id"]
        return

    if kind == "quest_box":
        rec = base_record(level, kind, cls, true_pid, go_pid)
        fq = root.child("fileQuest")
        rec["file_quest"] = scalar_str(fq.value)
        style_i = int(root.child("style").value)
        rec["style"] = STYLES[style_i] if 0 <= style_i < len(STYLES) else "?%d" % style_i
        btns = root.child("buttons")
        cases = btns.items() if btns is not None else []
        case_ids = []
        for ci, cs in enumerate(cases):
            cid = "%s/case/%d" % (rec["id"], ci)
            case_ids.append(cid)
            sfi = int(cs.child("stringFile").value)
            flags = {f: (cs.child(f).value == "True")
                     for f in ("closeClick", "oneTime", "exitButton", "isClose",
                               "oneTimeUse")}
            icon = cs.child("iconButton")
            crec = {
                "id": cid, "kind": "choice_case", "level": level,
                "location": BIND.get(level), "chapter": None,
                "speaker": None, "emotion": None, "style": None,
                "voice_present": None, "condition_hints": [], "build": BUILD,
                "parent_node": rec["id"], "case_index": ci,
                "label_ref": {"category": rec["file_quest"],
                              "line_index": sfi - 1, "game_index": sfi},
                "flags": flags,
                "icon_button_ptr": ptr(icon) if icon is not None else None,
                "text_ref": None,
                "source": {"container": level, "class": "DialogueChangerCase",
                           "path_id": true_pid, "gameobject_path_id": go_pid,
                           "embedded_index": ci},
            }
            nodes.append(crec)
            edges.append({"kind": "choice", "src": rec["id"], "dst": cid,
                          "slot": "buttons[%d]" % ci, "call_index": 0,
                          "label_ref": crec["label_ref"]})
            ec = cs.child("eventClick")
            for i, call in enumerate(calls(ec)):
                edges.append({"kind": "on_finish_action", "src": cid,
                              "dst": None, "slot": "eventClick",
                              "call_index": i, "call": call,
                              "resolved_to": None})
        rec["case_ids"] = case_ids
        for slot in ("eventStart", "eventClose", "eventExit", "eventLastStop",
                     "eventAgainFarAway"):
            for i, call in enumerate(calls(root.child(slot))):
                edges.append({"kind": "on_finish_action", "src": rec["id"],
                              "dst": None, "slot": slot, "call_index": i,
                              "call": call, "resolved_to": None})
        nodes.append(rec)
        return

    if kind == "branch_group":
        rec = base_record(level, kind, cls, true_pid, go_pid)
        dlg = root.child("dialogue")
        entries = []
        for gi, g in enumerate(dlg.items() if dlg is not None else []):
            spk = int(g.child("speaker").value)
            txts = g.child("text")
            for ti, t in enumerate(txts.items() if txts is not None else []):
                idx = int(t.child("indexFile").value)
                eid = "%s/text/%d/%d" % (rec["id"], gi, ti)
                entries.append({
                    "entry_id": eid, "group_index": gi, "text_index": ti,
                    "speaker_enum": L14_SPEAKERS[spk] if 0 <= spk < len(L14_SPEAKERS) else "?%d" % spk,
                    "text_ref": {"category": BIND.get(level),
                                 "line_index": idx - 1, "game_index": idx},
                })
                for i, call in enumerate(calls(t.child("eventFinishText"))):
                    edges.append({"kind": "on_finish_action",
                                  "src": rec["id"], "dst": None,
                                  "slot": "dialogue[%d].text[%d].eventFinishText" % (gi, ti),
                                  "call_index": i, "call": call,
                                  "resolved_to": None,
                                  "anchor_entry": eid})
        rec["entries"] = entries
        rec["speaker"] = None
        fork_targets = {}
        for side in ("Right", "Left"):
            fn = root.child("indexFile%s" % side)
            if fn is not None:
                fork_targets["branch_%s" % side.lower()] = {
                    "game_index": int(fn.value), "line_index": int(fn.value) - 1}
            for i, call in enumerate(calls(root.child("event%s" % side))):
                edges.append({"kind": "on_finish_action", "src": rec["id"],
                              "dst": None, "slot": "event%s" % side,
                              "call_index": i, "call": call,
                              "resolved_to": None})
        for i, call in enumerate(calls(root.child("eventFinish"))):
            edges.append({"kind": "on_finish_action", "src": rec["id"],
                          "dst": None, "slot": "eventFinish",
                          "call_index": i, "call": call, "resolved_to": None})
        rec["_forks"] = fork_targets
        mn = root.child("main")
        rec["main_ptr"] = ptr(mn) if mn is not None else None
        nodes.append(rec)
        return

    if kind == "grouped_scene_dialogue":
        rec = base_record(level, kind, cls, true_pid, go_pid)
        dlgs = root.child("dialogues")
        groups = []
        for gi, g in enumerate(dlgs.items() if dlgs is not None else []):
            pers = g.child("personageSpeak")
            iss = g.child("indexStrings")
            lines = []
            for li, ix in enumerate(iss.items() if iss is not None else []):
                idx = int(ix.child("index").value)
                lid = "%s/line/%d/%d" % (rec["id"], gi, li)
                lines.append({
                    "line_id": lid, "group_index": gi, "line_index_in_group": li,
                    "text_ref": {"category": BIND.get(level),
                                 "line_index": idx - 1, "game_index": idx},
                })
                for slotname in ("eventStart", "eventFinishPrint"):
                    for i, call in enumerate(calls(ix.child(slotname))):
                        edges.append({
                            "kind": "on_finish_action", "src": rec["id"],
                            "dst": None,
                            "slot": "dialogues[%d].indexStrings[%d].%s" % (gi, li, slotname),
                            "call_index": i, "call": call,
                            "resolved_to": None, "anchor_entry": lid})
            groups.append({
                "group_index": gi,
                "personage_ptr": ptr(pers) if pers is not None else None,
                "lines": lines,
            })
        rec["groups"] = groups
        nd = root.child("nextDialogue")
        rec["_next_component_ptr"] = ptr(nd) if nd is not None else None
        for i, call in enumerate(calls(root.child("eventStop"))):
            edges.append({"kind": "on_finish_action", "src": rec["id"],
                          "dst": None, "slot": "eventStop",
                          "call_index": i, "call": call, "resolved_to": None})
        nodes.append(rec)
        return

    if kind == "pet_dialogue":
        rec = base_record(level, kind, cls, true_pid, go_pid)
        df = root.child("dialogueFile")
        ns = root.child("nameString")
        rec["dialogue_file_declared"] = scalar_str(df.value) if df is not None else ""
        rec["name_string_declared"] = int(ns.value) if ns is not None else 0
        cp = root.child("copyPerson")
        rec["copy_person_ptr"] = ptr(cp) if cp is not None else None
        dl = root.child("dialogue")
        lines = []
        for di, d in enumerate(dl.items() if dl is not None else []):
            idx = int(d.child("indexString").value)
            did = "%s/pet-line/%d" % (rec["id"], di)
            anim_p = d.child("animationPlay")
            anim_i = d.child("animationIdle")
            lines.append({
                "line_id": did, "dialogue_index": di,
                "text_ref": {"category": BIND.get(level),
                             "line_index": idx - 1, "game_index": idx},
                "emotion_declared": scalar_str(d.child("emotion").value)
                if d.child("emotion") is not None else "",
                "body_ik_active": d.child("bodyIKActive").value == "True",
                "animation_play_ptr": ptr(anim_p) if anim_p is not None else None,
                "animation_idle_ptr": ptr(anim_i) if anim_i is not None else None,
            })
            for i, call in enumerate(calls(d.child("eventStart"))):
                edges.append({"kind": "on_finish_action", "src": rec["id"],
                              "dst": None,
                              "slot": "dialogue[%d].eventStart" % di,
                              "call_index": i, "call": call,
                              "resolved_to": None, "anchor_entry": did})
        rec["pet_lines"] = lines
        rec["speaker"] = None
        nd = root.child("nextDialogue")
        rec["_next_component_ptr"] = ptr(nd) if nd is not None else None
        for i, call in enumerate(calls(root.child("eventStop"))):
            edges.append({"kind": "on_finish_action", "src": rec["id"],
                          "dst": None, "slot": "eventStop",
                          "call_index": i, "call": call, "resolved_to": None})
        nodes.append(rec)
        return

    if kind == "random_router":
        rec = base_record(level, kind, cls, true_pid, go_pid)
        dl = root.child("dialogues")
        rec["fanout_ptrs"] = [ptr(g) for g in (dl.items() if dl is not None else [])]
        rec["destroy_after"] = root.child("destroyAfter").value == "True"
        for t in rec["fanout_ptrs"]:
            edges.append({"kind": "random_fanout", "src": rec["id"],
                          "dst": None, "slot": "dialogues",
                          "target_ptr": t, "weight": None,
                          "resolved_to": None})
        nodes.append(rec)
        return


def iter_text_refs(n):
    """Every (category, line_index, game_index) ref a node carries."""
    if n["kind"] == "ambient_line":
        if n.get("text_ref"):
            yield n["text_ref"]
    elif n["kind"] == "choice_case":
        if n.get("label_ref"):
            yield n["label_ref"]
    elif n["kind"] == "branch_group":
        for e in n["entries"]:
            yield e["text_ref"]
    elif n["kind"] == "grouped_scene_dialogue":
        for g in n["groups"]:
            for ln in g["lines"]:
                yield ln["text_ref"]
    elif n["kind"] == "pet_dialogue":
        for ln in n["pet_lines"]:
            yield ln["text_ref"]


def theme_speaker(theme):
    ent = SLUGS.get(theme)
    speaker = {
        "theme": theme,
        "display": {"en": theme},
    }
    if ent:
        speaker["entity"] = {"kind": ent[0], "slug": ent[1],
                             "status": "provisional-pending-ds1"}
    else:
        speaker["entity"] = {"kind": None, "slug": None,
                             "status": "pending-curation"}
    if theme in DISPLAY_ANCHOR:
        speaker["display"]["names_anchor"] = DISPLAY_ANCHOR[theme]["names_line"]
    return speaker


# ---------------------------------------------------------------------------
# edge resolution (second pass)
# ---------------------------------------------------------------------------

def resolve_edges(nodes, edges, per_level, ledgers, all_comp_class, go_census):
    amb_by_go = {lv: st["amb_by_go"] for lv, st in per_level.items()}
    node_by_id = {n["id"]: n for n in nodes}
    # union-of-carriers index map (§3.6): every node kind's text rows indexed
    # by (level, game_index) — branch forks resolve against ALL carriers
    carrier_by_game_index = defaultdict(list)
    for n in nodes:
        if n["kind"] == "ambient_line" and n.get("text_ref"):
            carrier_by_game_index[(n["level"], n["text_ref"]["game_index"])].append(n["id"])
        elif n["kind"] == "branch_group":
            for e in n["entries"]:
                carrier_by_game_index[(n["level"], e["text_ref"]["game_index"])].append(n["id"])
        elif n["kind"] == "grouped_scene_dialogue":
            for g in n["groups"]:
                for ln in g["lines"]:
                    carrier_by_game_index[(n["level"], ln["text_ref"]["game_index"])].append(n["id"])
        elif n["kind"] == "pet_dialogue":
            for ln in n["pet_lines"]:
                carrier_by_game_index[(n["level"], ln["text_ref"]["game_index"])].append(n["id"])

    def resolve_go(lv, p):
        if p["path_id"] == 0:
            return {"status": "null"}
        if p["file_id"] != 0:
            return {"status": "cross-container", "ptr": p}
        hits = amb_by_go.get(lv, {}).get(p["path_id"])
        if hits:
            return {"status": "resolved", "dst": hits}
        return {"status": "unresolved-in-level", "ptr": p}

    def resolve_component(lv, p):
        if p["path_id"] == 0:
            return {"status": "null"}
        if p["file_id"] != 0:
            return {"status": "cross-container", "ptr": p}
        for n in nodes:
            if n["level"] == lv and n["source"]["path_id"] == p["path_id"]:
                return {"status": "resolved", "dst": n["id"]}
        return {"status": "unresolved-in-level", "ptr": p}

    for n in nodes:
        lv = n["level"]
        if n["kind"] == "ambient_line":
            r = resolve_go(lv, n.pop("_next_ptr"))
            n["next_resolved"] = r["status"]
            if r["status"] == "resolved":
                edges.append({"kind": "next", "src": n["id"], "dst": r["dst"],
                              "slot": "nextText", "call_index": 0})
            elif r["status"] != "null":
                hosted = sorted(c for c, _ in
                                go_census.get(lv, {}).get("comps_on_go", {})
                                .get(r.get("ptr", {}).get("path_id"), []))
                ledgers["dangling"].append({
                    "src": n["id"], "kind": "next", "slot": "nextText",
                    "reason": r["status"], "ptr": r.get("ptr"),
                    "target_gameobject_hosts": hosted})
        elif n["kind"] in ("grouped_scene_dialogue", "pet_dialogue"):
            r = resolve_component(lv, n.pop("_next_component_ptr"))
            n["next_resolved"] = r["status"]
            if r["status"] == "resolved":
                edges.append({"kind": "next", "src": n["id"], "dst": r["dst"],
                              "slot": "nextDialogue", "call_index": 0})
            elif r["status"] != "null":
                ledgers["dangling"].append({
                    "src": n["id"], "kind": "next", "slot": "nextDialogue",
                    "reason": r["status"], "ptr": r.get("ptr")})
        elif n["kind"] == "branch_group":
            forks = n.pop("_forks")
            n["forks"] = {}
            for side, fx in sorted(forks.items()):
                gi = fx["game_index"]
                if gi == 0:
                    n["forks"][side] = {"status": "unwired"}
                    continue   # serialized 0 = no fork on this side
                targets = sorted(set(carrier_by_game_index.get((lv, gi), [])))
                label_ref = {"category": BIND.get(lv),
                             "line_index": gi - 1, "game_index": gi}
                # §3.3: branch_left/right are keyed on LOC LINE INDICES — the
                # fork renders that row whether or not a node component also
                # carries it. dst = the unique carrier node when one exists.
                if len(targets) == 1:
                    n["forks"][side] = {"status": "resolved", "dst": targets[0]}
                    edges.append({"kind": side, "src": n["id"],
                                  "dst": targets[0],
                                  "slot": "indexFile%s" % side.split("_")[1].capitalize(),
                                  "call_index": 0, "label_ref": label_ref})
                else:
                    n["forks"][side] = ({
                        "status": "text-keyed-no-node-carrier",
                        "game_index": gi} if not targets else
                        {"status": "ambiguous", "game_index": gi,
                         "candidates": len(targets)})
                    edges.append({"kind": side, "src": n["id"], "dst": None,
                                  "slot": "indexFile%s" % side.split("_")[1].capitalize(),
                                  "call_index": 0, "label_ref": label_ref,
                                  "resolution": n["forks"][side]["status"]})
                    if targets:
                        ledgers["dangling"].append({
                            "src": n["id"], "kind": side,
                            "slot": "indexFile%s" % side.split("_")[1],
                            "reason": "ambiguous-carriers",
                            "game_index": gi, "candidates": targets})

    # action-call target resolution — every in-container object is known from
    # the identity + GameObject census, so targets classify exactly:
    #   dialogue node id | component:<Class> (non-node carrier) |
    #   gameobject:<pid> (SetActive-style GO targets) |
    #   out-of-census-scope (cross-file) | null-target
    comp_class = {lv: dict(m) for lv, m in all_comp_class.items()}
    resolved_ct = 0
    for e in edges:
        if e["kind"] not in ("on_finish_action",):
            continue
        tp = e["call"]["target_ptr"]
        lv = e["src"].split(":")[0]
        if tp["path_id"] == 0:
            e["resolved_to"] = "null-target"
            continue
        if tp["file_id"] != 0:
            e["resolved_to"] = "out-of-census-scope"
            continue
        cls = comp_class.get(lv, {}).get(tp["path_id"])
        if cls is not None:
            cand = "%s:%s#%d" % (lv, cls, tp["path_id"])
            if cand in node_by_id:
                e["dst"] = cand
                e["resolved_to"] = cand
                resolved_ct += 1
            else:
                e["resolved_to"] = "component:%s" % cls
            continue
        if tp["path_id"] in go_census.get(lv, {}).get("obj_types", {}):
            tname = go_census[lv]["obj_types"][tp["path_id"]]
            if tname == "GameObject":
                e["resolved_to"] = "gameobject:%d" % tp["path_id"]
            else:
                e["resolved_to"] = "component:%s#%d" % (tname, tp["path_id"])
            continue
        e["resolved_to"] = "unresolved-path-id"
        ledgers["dangling"].append({
            "src": e["src"], "kind": e["kind"], "slot": e["slot"],
            "call_index": e["call_index"], "reason": "target-not-in-container",
            "ptr": tp})
    return resolved_ct


# ---------------------------------------------------------------------------
# range validation + span rule (§3.6, AC D2)
# ---------------------------------------------------------------------------

def validate_ranges(nodes, ledgers, en_cache):
    span = defaultdict(lambda: [None, None])   # level -> [min,max] over union
    carriers = defaultdict(lambda: defaultdict(int))  # level -> carrier kind -> n
    for n in nodes:
        refs = []
        if n["kind"] == "ambient_line":
            refs = [("ambient_line.indexString", n["text_ref"])]
        elif n["kind"] == "quest_box":
            pass
        elif n["kind"] == "choice_case":
            refs = [("DialogueChangerCase.stringFile", n["label_ref"])]
        elif n["kind"] == "branch_group":
            refs += [("Loc14_DialogueText.indexFile", e["text_ref"]) for e in n["entries"]]
            for side, fx in sorted(n.get("forks", {}).items()):
                if fx.get("game_index"):   # 0 = unwired, not a range subject
                    refs.append(("Location14_Dialogue.indexFile%s" % side.split("_")[1],
                                 {"category": BIND.get(n["level"]), "line_index": fx["game_index"] - 1,
                                  "game_index": fx["game_index"]}))
        elif n["kind"] == "grouped_scene_dialogue":
            refs = [("Location18_Dialogue_DialogueIndex.index",
                     ln["text_ref"]) for g in n["groups"] for ln in g["lines"]]
        elif n["kind"] == "pet_dialogue":
            refs = [("Tamagotchi_Dialogue_Events.indexString", ln["text_ref"])
                    for ln in n["pet_lines"]]
        elif n["kind"] == "random_router":
            refs = []
        for carrier, ref in refs:
            cat = ref["category"]
            if not cat:
                ledgers["range"].append({
                    "node": n["id"], "carrier": carrier, "issue": "no-bound-category",
                    "ref": ref})
                continue
            cnt = cat_count(en_cache, cat)
            li = ref["line_index"]
            ok = 0 <= li < cnt
            if not ok:
                ledgers["range"].append({
                    "node": n["id"], "carrier": carrier, "issue": "out-of-range",
                    "category": cat, "line_index": li,
                    "game_index": ref.get("game_index"), "count": cnt})
            else:
                lo, hi = span[n["level"]]
                span[n["level"]] = [min(x for x in (lo, li) if x is not None),
                                    max(x for x in (hi, li) if x is not None)]
                carriers[n["level"]][carrier.split(".")[0]] += 1
    # quest-box label categories ride their own fileQuest categories — record
    for lvl in sorted(span):
        cat = BIND.get(lvl)
        cnt = cat_count(en_cache, cat)
        lo, hi = span[lvl]
        span_ok = (hi == cnt - 1)
        ledgers["range"].append({
            "level": lvl, "bound_category": cat, "count": cnt,
            "union_min_line_index": lo, "union_max_line_index": hi,
            "span_rule_max_equals_count_minus_1": span_ok,
            "carriers": dict(sorted(carriers[lvl].items())),
            "rule_status": "validated" if span_ok else "VIOLATION-LEDGERED"})


# ---------------------------------------------------------------------------
# condition hints (§3.5 / AC D7)
# ---------------------------------------------------------------------------

def attach_hints(nodes, ledgers, en_cache):
    """§3.5 / AC D7. Every EN author comment attaches to EVERY node whose
    text_ref carries its target row (next non-blank non-comment row of the
    category, previous-row fallback) — never one attachment per node.
    A comment whose target row no component serializes is NOT dropped: it
    lands in unattached_rows with the reason. Reconciliation invariant,
    asserted in-code:

        comments shipped into condition_hints + comments_unattachable
            == en_comment_rows_total
    """
    texts, target_of = {}, {}          # (cat, ci) -> text / -> (cat, nxt)|None
    total_comments = 0
    for cat in LD_CATS:
        rows = cat_rows("English", cat)
        if rows is None:
            continue
        by_idx = dict(rows)
        comment_idxs = sorted(i for i, t in by_idx.items()
                              if t.startswith("//"))
        total_comments += len(comment_idxs)
        for ci in comment_idxs:
            nxt = None
            for j in sorted(by_idx):
                if j > ci and not by_idx[j].startswith("//") and by_idx[j] != "":
                    nxt = j
                    break
            if nxt is None:
                for j in sorted(by_idx, reverse=True):
                    if j < ci and not by_idx[j].startswith("//") and by_idx[j] != "":
                        nxt = j
                        break
            target_of[(cat, ci)] = (cat, nxt)   # nxt None = no content row
            texts[(cat, ci)] = by_idx[ci]

    carried = set()                    # (cat, line_index) rows nodes carry
    for n in nodes:
        for ref in iter_text_refs(n):
            if ref and ref.get("category"):
                carried.add((ref["category"], ref["line_index"]))
    hints_by_target = defaultdict(list)
    for (cat, ci), tgt in sorted(target_of.items()):
        if tgt[1] is not None:
            hints_by_target[tgt].append((cat, ci))

    shipped, items, applied = set(), 0, 0
    for n in nodes:
        got = {}
        for ref in iter_text_refs(n):   # ALL refs — no early break
            for key in hints_by_target.get(
                    (ref.get("category"), ref.get("line_index")), ()):
                got[key] = True
        if got:
            keys = sorted(got)
            n["condition_hints"] = [
                {"lang": "en", "line_index": k[1], "text": texts[k]}
                for k in keys]
            shipped.update(keys)
            items += len(keys)
            applied += 1

    unattached = []
    for (cat, ci), tgt in sorted(target_of.items()):
        if tgt[1] is None:
            unattached.append({"category": cat, "comment_line_index": ci,
                               "reason": "no-content-row-in-category"})
        elif tgt not in carried:
            unattached.append({"category": cat, "comment_line_index": ci,
                               "target_line_index": tgt[1],
                               "reason": "target-row-not-carried-by-any-node"})
    if len(shipped) + len(unattached) != total_comments:
        raise SystemExit(
            "D7 invariant broken: %d comments shipped into condition_hints "
            "+ %d unattached != %d source comment rows"
            % (len(shipped), len(unattached), total_comments))
    stats = {
        "en_comment_rows_total": total_comments,
        "comments_attached_to_a_content_row": len(shipped),
        "comments_emitted_into_condition_hints": len(shipped),
        "hint_items_emitted": items,
        "comments_unattachable": len(unattached),
        "unattached_rows": unattached,
        "nodes_carrying_hints": applied,
        "reconciliation_invariant": (
            "comments_emitted_into_condition_hints (%d) + comments_"
            "unattachable (%d) == en_comment_rows_total (%d)"
            % (len(shipped), len(unattached), total_comments)),
        "note": "every hint-bearing ref of a node attaches (no early break); "
                "comments attach to the next non-blank non-comment row of "
                "their category (previous row as fallback); verbatim EN, "
                "lang-tagged, never rendered as speech (D7); comments whose "
                "target row no component serializes stay explicit in "
                "unattached_rows, never dropped",
    }
    if unattached:
        ledgers["notes"].append({"kind": "unattached-condition-hints",
                                 "rows": unattached})
    return stats


# ---------------------------------------------------------------------------
# speakers.json / availability.csv / residue-links.jsonl
# ---------------------------------------------------------------------------

def emit_speakers():
    rows = []
    for t in THEMES:
        ent = SLUGS.get(t)
        rows.append({
            "theme": t,
            "enum_index": THEMES.index(t),
            "carrier": "Dialogue_3DText.themeDialogue (Dialogue3DTheme)",
            "display_en": t,
            "names_anchor": DISPLAY_ANCHOR.get(t, {}).get("names_line"),
            "entity": ({"kind": ent[0], "slug": ent[1],
                        "status": "provisional-pending-ds1"} if ent else
                       {"kind": None, "slug": None,
                        "status": "pending-curation"}),
        })
    doc = {
        "build": BUILD,
        "contract": "docs/contracts/dataset-dialogue.mdx",
        "curated_mapping": rows,
        "personage_carriers": [
            {"carrier": "Location14_Dialogue.Loc14WhioSpeak",
             "values": L14_SPEAKERS,
             "entity_note": "player|mita spoken-side of branch groups"},
            {"carrier": "Location18_Personage PPtr",
             "values": "per-group PPtr; personage entities land with DS-1 "
                       "character curation; raw path_ids preserved on nodes"},
            {"carrier": "Names category (47 EN lines)",
             "pool": "extracted/localization/English/Names.jsonl"},
        ],
        "pending_curation_enums": sorted(PENDING),
        "policy": "the five ambiguous enums stay slug-null pending-curation "
                  "(D6); display ships as the verbatim enum value",
    }
    jdump(os.path.join(OUT, "speakers.json"), doc)


def emit_availability(en_cache):
    """Per (bucket, locale) cells + the measured per-locale parity ledger.

    Spec §2.1 claimed exact positional parity across locales; measurement
    REFUTES it for 4 locales (tail deltas) — deltas ship as data here and
    in _ledger/locale-parity.jsonl, never silently assumed."""
    os.makedirs(OUT, exist_ok=True)
    rows = []
    parity = []
    buckets = LD_CATS + ["LocationDialogue Location16"]
    pivots = {c: cat_count(en_cache, c) for c in LD_CATS}
    for locale in LOCALES:
        for cat in buckets:
            p = os.path.join(LOC, locale, cat + ".jsonl")
            present = os.path.exists(p)
            size = os.path.getsize(p) if present else -1
            n = -1
            if present:
                with io.open(p, encoding="utf-8") as f:
                    n = sum(1 for line in f if line.strip())
            pivot = pivots.get(cat, -1)
            contentless = present and size == 0
            if contentless:
                cell = "contentless"
            elif present and n > 0:
                cell = "present"
            else:
                cell = "filler"
            delta = None
            if cat in pivots and present and pivot >= 0 and not contentless:
                delta = n - pivot
                if delta != 0:
                    parity.append({"locale": locale, "category": cat,
                                   "pivot_lines": pivot, "locale_lines": n,
                                   "delta": delta,
                                   "kind": "surplus-tail" if delta > 0
                                   else "shortfall-tail-filler"})
            rows.append({"bucket": cat, "locale": locale,
                         "classification": cell, "line_count": n,
                         "pivot_line_count": pivot, "tail_delta": delta,
                         "file_bytes": size})
    rows.sort(key=lambda r: (r["bucket"], r["locale"]))
    parity.sort(key=lambda r: (r["locale"], r["category"]))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["bucket", "locale", "classification",
                                        "line_count", "pivot_line_count",
                                        "tail_delta", "file_bytes"],
                       lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    with io.open(os.path.join(OUT, "availability.csv"), "w", encoding="utf-8",
                 newline="") as f:
        f.write(buf.getvalue())
    jl(os.path.join(OUT, "_ledger", "locale-parity.jsonl"), parity)
    return {"locales_with_tail_deltas": len({r["locale"] for r in parity}),
            "delta_rows": len(parity),
            "detail": [{"locale": r["locale"], "category": r["category"],
                        "delta": r["delta"]} for r in parity]}


def emit_residue_links(nodes):
    ledger_path = os.path.join(LOC, "_ledger", "encoding-residue.jsonl")
    res = [json.loads(l) for l in io.open(ledger_path, encoding="utf-8")]
    ld12 = [r for r in res if r["category"] == "LocationDialogue Location12"]
    fffd_locales = sorted(r["locale"] for r in ld12
                          if (r.get("segments_marked_fffd") or 0) > 0)
    recovered = sorted({r["codec"] for r in ld12 if r.get("codec")})
    touched = []
    for n in nodes:
        refs = []
        if n["kind"] == "ambient_line":
            refs = [n["text_ref"]]
        elif n["kind"] == "branch_group":
            refs = [e["text_ref"] for e in n["entries"]]
        elif n["kind"] == "grouped_scene_dialogue":
            refs = [ln["text_ref"] for g in n["groups"] for ln in g["lines"]]
        elif n["kind"] == "pet_dialogue":
            refs = [ln["text_ref"] for ln in n["pet_lines"]]
        for ref in refs:
            if ref["category"] == "LocationDialogue Location12" and ref["line_index"] == 58:
                touched.append(n["id"])
                break
    rows = [{
        "node_id": nid,
        "category": "LocationDialogue Location12",
        "line_index": 58,
        "locales_marked_fffd": fffd_locales,
        "codec_recovered": recovered,
        "residue_ids": sorted(r["id"] for r in ld12),
    } for nid in sorted(touched)]
    jl(os.path.join(OUT, "residue-links.jsonl"), rows)
    return len(rows)


if __name__ == "__main__":
    main()
