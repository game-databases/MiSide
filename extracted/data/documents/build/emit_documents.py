#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DS-5 documents & lore-collectibles emitter (MiSide, buildId 19029065).

Implements docs/specs/dataset-documents.mdx exactly:
  profile_documents x14 (§4.2) · world_documents 160 notes under the §7-R4
  dedupe rule + 5 BlackRoom paper parts + 1 novella surface (§4.3) ·
  books x8 derived per locale (§4.4) · relinks §4.5 (J2/J3/J4/J5/J6) ·
  README honesty ledger feed (§8 AC-10).

Placement authority: DS-4 (dataset-cartridges.mdx §1 shared-source ruling).
This stage consumes the 11-row Mita-side `(save_key, container)` subset BY
REFERENCE from `extracted/data/cartridges-minigames/cartridges.jsonl` when it
exists; until that emission lands it reads the same primary corpus census and
flags `placement_source` honestly. It never emits standalone placement rows.

Identity pass mirrors B-3's precedent (build-log deviation 3): AssetStudioMod
dump-filename `_#N` suffixes are NOT PathIDs; true component PathIDs come from
a raw-header parse of the installed scene files (read-only; MonoScript table
from globalgamemanagers.assets). Dump filenames stay on rows as locators.

Parked here pending PIPE §3 stage-tree adoption (B-1/B-2/B-3 residue (a)).
Inputs are read-only; outputs byte-deterministic (fixed key order, sorted
arrays, LF, no BOM).
"""
import hashlib
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


def _resolve_art():
    """extracted/art may be triaged off the corpus drive (C: disk-full); the
    MOVED-TO.txt pointer is the mechanized fallback, never a hardcoded guess."""
    repo = os.path.join(EXTRACTED, "art", "localization-art")
    if os.path.isdir(repo):
        return repo
    ptr = os.path.join(EXTRACTED, "art", "MOVED-TO.txt")
    if os.path.exists(ptr):
        with io.open(ptr, encoding="utf-8") as f:
            m = re.search(r"->\s*(.+?)\s*$", f.readline())
        if m:
            base = m.group(1).strip()
            for cand in (os.path.join(base, "localization-art"), base):
                if os.path.isdir(cand):
                    return cand
    sys.exit("art layer not found: neither %s nor a readable MOVED-TO.txt" % repo)


ART = _resolve_art()
RAW_DATA = r"A:\SteamLibrary\steamapps\common\MiSide\MiSideFull_Data"
PERSONAGES = os.path.join(EXTRACTED, "data", "characters", "personages.jsonl")
CARTRIDGES_CANDIDATES = [
    os.path.join(EXTRACTED, "data", "cartridges", "cartridges.jsonl"),
    os.path.join(EXTRACTED, "data", "cartridges-minigames", "cartridges.jsonl"),
]
CONTRACT_ACH = os.path.join(PACK, "contracts", "dataset-achievements.mdx")

BUILD = "19029065"
VERSION_LABEL = "0.93L"
GENERATOR = ("B-5 dataset-builder curation pass (run_all stage registration "
             "pending; docs/specs/dataset-documents.mdx)")

LOCALES = sorted(d for d in os.listdir(LOC)
                 if os.path.isdir(os.path.join(LOC, d)) and d != "_ledger")
LEVELS = ["level%d" % n for n in range(0, 24)]

BOOK_TEXTURES = [                      # (subtree, stem, book_id, consumer_scene)
    ("Location House", "Books0", "books-0", "Location House"),
    ("Location House", "Books1", "books-1", "Location House"),
    ("Location House", "Books2", "books-2", "Location House"),
    ("Location House", "Books4", "books-4", "Location House"),
    ("Location19", "Book 1", "book-1", "Location19"),
    ("Location19", "Book 2", "book-2", "Location19"),
    ("Location19", "Book 3", "book-3", "Location19"),
    ("Location19", "Book 4", "book-4", "Location19"),
]

FALSIFIER = (
    "if the P5 scene parse or a future native decompile surfaces a second "
    "serialized profile registry (a profile screen object, a second save-key "
    "family), the emit pass forks `profile_document` away from cartridge "
    "identity and ledger both shapes - never silently merge")


# ---------------------------------------------------------------------------
# stale-log defense (PIPE §3, spec §8 AC-9)
# ---------------------------------------------------------------------------

def compare_defaults(defaults, detect):
    """Pure pin comparison -> list of mismatch tuples (empty == consistent)."""
    checks = [
        ("buildId", defaults.get("buildId"), detect.get("build_id")),
        ("versionLabel", defaults.get("versionLabel"),
         (detect.get("version_label") or "").replace("VERSION ", "")),
        ("unity", defaults.get("unity"), (detect.get("flavor") or {}).get("unity_version")),
        ("metadataVersion", str(defaults.get("metadataVersion")),
         str((detect.get("flavor") or {}).get("metadata_version"))),
    ]
    return [(k, a, b) for k, a, b in checks if str(a) != str(b)]


def stale_log_guard():
    log_p = os.path.join(EXTRACTED, "EXTRACTION-LOG.md")
    det_p = os.path.join(EXTRACTED, "census", "detect.json")
    with io.open(log_p, encoding="utf-8") as f:
        m = re.search(r"```json pipeline-defaults\n(.*?)```", f.read(), re.S)
    if not m:
        sys.exit("stale-log refusal: EXTRACTION-LOG.md has no pipeline-defaults block")
    defaults = json.loads(m.group(1))
    detect = json.load(io.open(det_p, encoding="utf-8"))
    bad = compare_defaults(defaults, detect)
    if bad:
        sys.exit("stale-log refusal: EXTRACTION-LOG pipeline-defaults disagree with "
                 "census/detect.json: %r" % (bad,))
    return defaults


# ---------------------------------------------------------------------------
# typed-dump text parser (AssetStudioMod tab-indented tree; B-3 method)
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
        parts = head.split()
        return parts[1] if len(parts) > 1 else parts[0]

    def child(self, name):
        for k in self.kids:
            if k.name == name and not k.line.endswith("]"):
                return k
        return None

    def items(self):
        """Array items of an `X[] name` node -> list[Node].

        AssetStudioMod writes items one indent PAST `int size = N`; each item
        node's line is e.g. `PersistentCall data` and its fields are children.
        """
        holder = self
        if not any(k.line.endswith("]") for k in self.kids):
            for k in self.kids:
                if k.scalar and k.name == "size":
                    holder = k
                    break
        out, cur = [], False
        for k in holder.kids:
            if k.line.endswith("]"):
                cur = True
                continue
            if cur:
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
        stack[depth - 1].kids.append(n)
        stack[depth:] = [n]
    return root


def scalar_str(v):
    return v[1:-1] if v.startswith('"') and v.endswith('"') else v


def ptr(node):
    if node is None:
        return None
    fid = node.child("m_FileID")
    pid = node.child("m_PathID")
    if fid is None or pid is None:
        return None
    return {"file_id": int(fid.value), "path_id": int(pid.value)}


def event_calls(ue_node):
    """UnityEvent node -> list of serialized PersistentCall dicts."""
    grp = ue_node.child("m_PersistentCalls")
    lst = grp.child("m_Calls") if grp else None
    out = []
    if lst is None:
        return out
    for it in lst.items():
        tgt = ptr(it.child("m_Target"))
        tan = it.child("m_TargetAssemblyTypeName")
        mn = it.child("m_MethodName")
        out.append({
            "method": scalar_str(mn.value) if mn is not None else None,
            "target_type": (scalar_str(tan.value).split(",")[0]
                            if tan is not None else None),
            "target_ptr": tgt,
        })
    return out


# ---------------------------------------------------------------------------
# identity pass: true component PathIDs from the scene files (read-only)
# ---------------------------------------------------------------------------

def parse_mb_header(data):
    off = 0
    _fid, = struct.unpack_from("<i", data, off); off += 4
    gpid, = struct.unpack_from("<q", data, off); off += 8
    off += 4                                     # m_Enabled u8 + pad
    sfid, = struct.unpack_from("<i", data, off); off += 4
    spid, = struct.unpack_from("<q", data, off); off += 8
    return gpid, sfid, spid


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
    """-> ({class_name: [(true_pid, go_pid)]}, {go_pid: set(class_name)})"""
    import UnityPy
    env = UnityPy.load(path)
    exts = [os.path.basename(getattr(e, "path_name", getattr(e, "path", "")))
            for e in env.file.externals]
    by_class = defaultdict(list)
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        gpid, sfid, spid = parse_mb_header(obj.get_raw_data())
        cls = scripts.get(spid) if (sfid > 0 and sfid - 1 < len(exts)
                                    and exts[sfid - 1] == "globalgamemanagers.assets") \
            else None
        cls = cls or "?external%d" % sfid
        by_class[cls].append((obj.path_id, gpid))
    return by_class


def read_dump(ldir, fname):
    with io.open(os.path.join(ldir, fname), encoding="utf-8",
                 errors="replace") as fh:
        return parse_dump(fh.read())


def dump_go(root):
    gon = root.child("m_GameObject")
    return ptr(gon)["path_id"] if gon is not None else -1


def match_dumps(level, want_classes, local_idents, union, ledgers):
    """Match typed dumps of want_classes to true component PathIDs.

    Resolution order per dump (spec §7-R4 posture: level-scene ownership wins):
      1. the level's own raw identities (unique (class, GO) candidate);
      2. bare-named elimination inside the level;
      3. corpus-wide union fallback over all containers (AssetStudioMod
         dependency auto-load re-lists shared-prefab objects — including
         resources.assets prefabs — inside many level dump folders, so ONE
         underlying component legitimately backs rows in several levels;
         claims are tracked PER LEVEL only).

    -> {(class, dump_file): {"go", "true_pid", "root", "serialized_container"}}
    """
    ldir = os.path.join(MB, level)
    used = set()                                  # (container, true_pid) this level claimed
    local_by_go = defaultdict(list)
    local_by_pid = {}
    for cls, rows in local_idents.items():
        for tp, gp in rows:
            local_by_go[(cls, gp)].append(tp)
            local_by_pid[tp] = gp

    def bind(cls, go_pid, fname):
        cands = [tp for tp in local_by_go.get((cls, go_pid), [])
                 if (level, tp) not in used]
        if len(cands) == 1:
            return (level, cands[0]), "level-scene"
        seen, pool = set(), []
        for c, tp in union.get((cls, go_pid), []):
            if (c, tp) in used:
                continue
            if (c, tp) not in seen:
                seen.add((c, tp))
                pool.append((c, tp))
        if len(pool) == 1:
            return pool[0], "dependency-auto-load"
        if len(pool) > 1:
            pool.sort(key=lambda t: (t[0].startswith("level"), natkey(t[0]), t[1]))
            ledgers["identity"].append({
                "level": level, "dump": fname, "issue": "prefab-duplicate-candidates",
                "candidates": ["%s#%d" % (c, tp) for c, tp in pool]})
            return pool[0], "dependency-auto-load"
        return (None, None), "unresolved"

    matched_local = defaultdict(set)
    out = {}
    files = sorted(f for f in os.listdir(ldir) if f.endswith(".txt"))
    for fname in files:
        m = re.match(r"^(.*)_#\d+\.txt$", fname)
        if not (m and m.group(1) in want_classes):
            continue
        cls = m.group(1)
        root = read_dump(ldir, fname)
        go_pid = dump_go(root)
        (cont, tp), how = bind(cls, go_pid, fname)
        if tp is not None:
            used.add((cont, tp))
            matched_local[cls].add(tp)
        else:
            ledgers["identity"].append({
                "level": level, "dump": fname, "issue": "no-identity-match",
                "go_path_id": go_pid})
        out[(cls, fname)] = {"go": go_pid, "true_pid": tp, "root": root,
                             "serialized_container": cont, "how": how}

    # bare-named instance: exactly one local identity left unmatched per class
    for cls in sorted(want_classes):
        ppath = os.path.join(ldir, cls + ".txt")
        if not os.path.exists(ppath) or (cls, cls + ".txt") in out:
            continue
        present = sorted({tp for tp, _gp in local_idents.get(cls, [])})
        rest = [tp for tp in present
                if tp not in matched_local[cls] and (level, tp) not in used]
        if len(rest) == 1:
            true_pid = rest[0]
            root = read_dump(ldir, cls + ".txt")
            got_go = dump_go(root)
            go_pid = local_by_pid[true_pid]
            if got_go != go_pid:
                ledgers["identity"].append({"level": level,
                                            "dump": cls + ".txt",
                                            "issue": "go-mismatch-bare-file",
                                            "expected_go": go_pid,
                                            "dump_go": got_go})
                true_pid = None
            else:
                ledgers["identity"].append({
                    "level": level, "dump": cls + ".txt",
                    "issue": "bare-named-instance", "true_path_id": true_pid,
                    "go_path_id": go_pid,
                    "method": "elimination over matched numbered dumps"})
            used.add((level, true_pid))
            out[(cls, cls + ".txt")] = {"go": got_go, "true_pid": true_pid,
                                        "root": root,
                                        "serialized_container": level,
                                        "how": "level-scene"}
            continue
        if not os.path.exists(ppath):
            continue
        # bare dump with no local identity left — try the union fallback
        root = read_dump(ldir, cls + ".txt")
        go_pid = dump_go(root)
        (cont, tp), _how = bind(cls, go_pid, cls + ".txt")
        if tp is None:
            ledgers["identity"].append({"level": level, "dump": cls + ".txt",
                                        "issue": "bare-file-unresolvable",
                                        "unmatched_local_identities": len(rest),
                                        "go_path_id": go_pid})
            out[(cls, cls + ".txt")] = {"go": go_pid, "true_pid": None,
                                        "root": root,
                                        "serialized_container": None,
                                        "how": "unresolved"}
        else:
            used.add((cont, tp))
            out[(cls, cls + ".txt")] = {"go": go_pid, "true_pid": tp,
                                        "root": root,
                                        "serialized_container": cont,
                                        "how": "dependency-auto-load"}
    return out


COMPANION_CLASSES = ("Events_Data", "Time_Events", "Button", "Image")


def companion_scan(level, note_gos, ledgers):
    """Sibling-component payloads for note GameObjects, joined by the GO PPtr
    in each dump header alone (engine/UI classes need no true PathID here).

    -> {"wiring_by_go": {go: [(cls, rec)]}, "images_by_go": {go: [(fn, rec)]}}
    """
    ldir = os.path.join(MB, level)
    wiring_by_go = defaultdict(list)
    images_by_go = defaultdict(list)
    pat = re.compile(r"^(%s)(?:_#\d+)?\.txt$" % "|".join(COMPANION_CLASSES))
    for fname in sorted(os.listdir(ldir)):
        m = pat.match(fname)
        if not m:
            continue
        cls = m.group(1)
        root = read_dump(ldir, fname)
        go = dump_go(root)
        if go not in note_gos:
            continue
        if cls == "Image":
            images_by_go[go].append((fname, {"root": root}))
        else:
            wiring_by_go[go].append((cls, {"root": root}))
    return wiring_by_go, images_by_go


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def cat(locale, category):
    p = os.path.join(LOC, locale, category + ".jsonl")
    if not os.path.exists(p):
        return None
    rows = {}
    with io.open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            rows[r["line_index"]] = r["text"]
    return rows


def jl_write(path, rows):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")) + "\n")


def natkey(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


# ---------------------------------------------------------------------------
# corpus censuses
# ---------------------------------------------------------------------------

def flashtaker_census():
    """[(save_key, container, dump_rel)] over all FlashTaker dumps."""
    out = []
    for d in sorted(os.listdir(MB)):
        dd = os.path.join(MB, d)
        for fn in sorted(os.listdir(dd)):
            if not fn.startswith("FlashTaker"):
                continue
            with io.open(os.path.join(dd, fn), encoding="utf-8",
                         errors="replace") as fh:
                t = fh.read()
            m = re.search(r'string save = "(.*?)"', t)
            if m:
                out.append((m.group(1), d, d + "/" + fn))
    return sorted(out)


def note_filename_census():
    """{level: count} of Unity_Note* dumps in level containers (>0 only)."""
    counts = {}
    for lv in LEVELS:
        ld = os.path.join(MB, lv)
        if os.path.isdir(ld):
            n = sum(1 for f in os.listdir(ld) if f.startswith("Unity_Note"))
            if n:
                counts[lv] = n
    return counts


def magnet_census():
    magnets = finish = 0
    for d in sorted(os.listdir(MB)):
        dd = os.path.join(MB, d)
        for fn in os.listdir(dd):
            if fn.startswith("Transform_MagnetFinish"):
                finish += 1
            elif fn.startswith("Transform_Magnet"):
                magnets += 1
    return magnets, finish


def registry_parse(ledgers):
    """Parse level2/MenuPersonage.txt resourceMita[14] (element semantics:
    array item nodes ARE the `PersonageResource data` lines)."""
    p = os.path.join(MB, "level2", "MenuPersonage.txt")
    with io.open(p, encoding="utf-8", errors="replace") as fh:
        root = parse_dump(fh.read())
    arr = root.child("resourceMita")
    rows = []
    for i, data in enumerate(arr.items()):
        rows.append({
            "index": i,
            "lore_line": int(data.child("indexDescriptionStringFile").value),
            "menu_line": int(data.child("indexNameStringFile").value),
            "resource_path": scalar_str(data.child("resourcePath").value),
            "name_save": scalar_str(data.child("nameSave").value),
        })
    ledgers["notes"].append({"fact": "registry resourceMita size", "value": len(rows)})
    return rows


def character_map():
    """resource_path -> character_id from the built DS-1 emission (join authority)."""
    out = {}
    with io.open(PERSONAGES, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("kind") == "mita":
                out[r["resource_path"]] = r["character_id"]
    return out


def consume_ds4_placements():
    """BY REFERENCE consumption of DS-4's pickup census when its emission exists."""
    src = next((p for p in CARTRIDGES_CANDIDATES if os.path.exists(p)), None)
    if src:
        pairs = {}
        with io.open(src, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if "save_key" not in r:
                    continue
                pr = r.get("pickup_ref")
                if pr:
                    pairs[r["save_key"]] = {"container": pr.get("container"),
                                            "file": pr.get("file")}
        return pairs, "ds4-emission:" + os.path.relpath(src, PACK).replace("\\", "/")
    return None, None


# ---------------------------------------------------------------------------
# profile rows
# ---------------------------------------------------------------------------

def build_profile_rows(registry, chars, ds4_pairs, measured_pairs, placement_source,
                       identity_by_key, ledgers):
    rows = []
    shared_lines = defaultdict(int)
    for r in registry:
        shared_lines[r["menu_line"]] += 1
    en_menu = cat("English", "Menu") or {}

    for r in registry:
        cid = chars.get(r["resource_path"])
        i = r["index"]
        # Row 0's pickup namespace value is the MEASURED `mta` (spec §3 finding 2).
        eff_key = "mta" if i == 0 else r["name_save"]
        pickup = None
        if eff_key:
            hits = [p for p in measured_pairs if p[0] == eff_key]
            pickup = hits[0] if len(hits) == 1 else None
            if eff_key in ds4_pairs and pickup is not None:
                src_container = (ds4_pairs[eff_key] or {}).get("container")
                if src_container and pickup[1] != src_container:
                    ledgers["reconcile_divergence"].append({
                        "save_key": eff_key, "ds4_container": src_container,
                        "corpus_container": pickup[1]})
                    pickup = (pickup[0], src_container, pickup[2])

        if i in (6, 9):
            mechanism, placement = "script_granted", None
        elif i == 13:
            mechanism, placement = "story_granted", None
        else:
            mechanism = "placed"
            if pickup is None:
                ledgers["reconcile_divergence"].append({
                    "save_key": eff_key, "issue": "placed-without-census-pair"})
                placement = None
            else:
                ident = identity_by_key.get(eff_key)
                placement = {"carrier_class": "FlashTaker",
                             "component_path_id": ident["true_pid"] if ident else None,
                             "container": pickup[1]}
                if not ident or ident["true_pid"] is None:
                    ledgers["identity"].append({
                        "save_key": eff_key,
                        "issue": "flash-taker-true-pid-unresolved",
                        "dump": pickup[2]})

        flash_key = "mta" if i == 0 else (r["name_save"] or None)
        evidence = []
        if placement and placement.get("component_path_id") is not None:
            evidence.append("%s#%d" % (placement["container"],
                                       placement["component_path_id"]))
        if i == 9:
            evidence.append("CoreSoft.jsonl#line_index=37")

        rows.append({
            "achievement_sets": ["mita-profiles"],
            "build_id": BUILD,
            "chapter": None,
            "document_id": "%s-profile" % cid,
            "evidence": evidence,
            "family": "profile",
            "flash_save_key": flash_key,
            "lore_loc": {"category": "Personages", "line_index": r["lore_line"]},
            "name_en": en_menu.get(r["menu_line"]),
            "name_is_shared": shared_lines[r["menu_line"]] > 1,
            "name_loc": {"category": "Menu", "line_index": r["menu_line"]},
            "placement": placement,
            "placement_mechanism": mechanism,
            "registry_ref": "level2#resourceMita[%d]" % i,
            "subject_character_id": cid,
            "version_label": VERSION_LABEL,
        })
    return rows


# ---------------------------------------------------------------------------
# world rows
# ---------------------------------------------------------------------------

def companion_wiring(companions):
    """Serialized persistent calls from sibling components on a note GO."""
    wiring = []
    for cls, rec in companions:
        root = rec["root"]
        if cls == "Events_Data":
            arr = root.child("_event")
            if arr is not None:
                for idx, ue in enumerate(arr.items()):
                    for c in event_calls(ue):
                        wiring.append(dict(c, trigger="Events_Data._event[%d]" % idx))
        elif cls == "Time_Events":
            arr = root.child("EventsOnTime")
            if arr is not None:
                for idx, item in enumerate(arr.items()):
                    tnode = item.child("time")
                    raw_time = tnode.value if tnode is not None else "?"
                    ue = item.child("_event")
                    for c in event_calls(ue):
                        wiring.append(dict(
                            c, trigger="Time_Events.EventsOnTime[%d]@%s"
                                       % (idx, raw_time)))
        elif cls == "Button":
            oc = root.child("m_OnClick")
            if oc is not None:
                for c in event_calls(oc):
                    wiring.append(dict(c, trigger="Button.onClick"))
    return wiring


def sprite_on_note(image_recs, ledgers, level, note_go):
    chosen, extras = None, []
    for _fname, rec in image_recs:
        sp = ptr(rec["root"].child("m_Sprite"))
        if sp is None or sp["path_id"] == 0:
            continue
        if chosen is None:
            chosen = sp
        else:
            extras.append(sp)
    if extras:
        ledgers["sprite_extras"].append({"level": level, "go": note_go,
                                         "extra_sprites": extras})
    return chosen


def build_world_rows(identity_matches, companions_by_level, ledgers):
    rows = []
    note_counts = note_filename_census()

    for lv in LEVELS:
        if lv not in note_counts:
            continue
        matches = identity_matches.get(lv, {})
        note_recs = [(fn, rec) for (cls, fn), rec in matches.items()
                     if cls == "Unity_Note"]
        note_gos = {rec["go"] for _fn, rec in note_recs}
        wiring_by_go, images_by_go = companions_by_level.get(lv, ({}, {}))
        comps_on_go = wiring_by_go

        for fn, rec in sorted(note_recs,
                              key=lambda t: (t[1]["true_pid"] is None,
                                             t[1]["true_pid"] or 0, natkey(t[0]))):
            go = rec["go"]
            wiring = companion_wiring(sorted(comps_on_go.get(go, []),
                                             key=lambda t: t[0]))
            wiring.sort(key=lambda w: (w["trigger"], natkey(w["method"] or ""),
                                       w["target_type"] or "",
                                       (w["target_ptr"] or {}).get("path_id", 0)))
            spr = sprite_on_note(sorted(images_by_go.get(go, [])),
                                 ledgers, lv, go)
            tp = rec["true_pid"]
            doc_id = "note-%s-%s" % (lv, tp if tp is not None
                                     else "unk-" + re.sub(r"[^A-Za-z0-9]", "", fn))
            rows.append({
                "actor_refs": [],
                "build_id": BUILD,
                "carrier": {"container": lv,
                            "dump_file": fn,
                            "mb_class": "Unity_Note",
                            "path_id": tp,
                            "serialized_container": rec["serialized_container"]},
                "document_id": doc_id,
                "event_wiring": wiring,
                "family": "note",
                "puzzle_index": None,
                "scene_ref": {"container": lv, "gameobject_path_id": go},
                "sprite_ptr": spr,
                "text_loc": None,
                "text_mechanism": "unresolved",
                "version_label": VERSION_LABEL,
            })

    # --- paper parts (level13) ----------------------------------------------
    pp = sorted(((fn, rec) for (cls, fn), rec
                 in identity_matches.get("level13", {}).items()
                 if cls == "Location11_PaperPart"),
                key=lambda t: int(t[1]["root"].child("indexPuzle").value)
                if t[1]["root"].child("indexPuzle") else 99)
    for fn, rec in pp:
        root = rec["root"]
        idx_n = root.child("indexPuzle")
        idx = int(idx_n.value) if idx_n is not None else None
        rows.append({
            "actor_refs": [],
            "build_id": BUILD,
            "carrier": {"container": "level13",
                        "dump_file": fn,
                        "mb_class": "Location11_PaperPart",
                        "path_id": rec["true_pid"],
                        "serialized_container": rec["serialized_container"]},
            "document_id": "paperpart-level13-%s" % idx,
            "event_wiring": [],
            "family": "paper_part",
            "puzzle_index": idx,
            "scene_ref": {"container": "level13", "gameobject_path_id": rec["go"]},
            "scr_main": ptr(root.child("scrMain")),
            "sprite_ptr": None,
            "text_loc": None,
            "text_mechanism": "unresolved",
            "version_label": VERSION_LABEL,
        })

    # --- novella surface (level20) -------------------------------------------
    nv = [(fn, rec) for (cls, fn), rec in identity_matches.get("level20", {}).items()
          if cls == "Location18_Novella"]
    assert len(nv) == 1, "expected exactly one Location18_Novella dump, got %d" % len(nv)
    fn, rec = nv[0]
    root = rec["root"]
    pg = root.child("personages")
    actor_ptrs = [ptr(it) for it in pg.items()] if pg is not None else []
    name_by_pid = {}
    for (cls2, _f2), rec2 in identity_matches.get("level20", {}).items():
        if cls2 != "Location18_Personage" or rec2["true_pid"] is None:
            continue
        npn = rec2["root"].child("namePersonage")
        if npn is not None:
            name_by_pid[rec2["true_pid"]] = int(npn.value)
    actors = [{"name_personage": name_by_pid.get(a["path_id"]),
               "path_id": a["path_id"]} for a in actor_ptrs if a is not None]
    wiring = []
    for ev_name in ("pauseStart", "pauseStop"):
        ue = root.child(ev_name)
        if ue is not None:
            for c in event_calls(ue):
                wiring.append(dict(c, trigger=ev_name))
    wiring.sort(key=lambda w: (w["trigger"], natkey(w["method"] or "")))
    audio_keys = ("audioMain", "audio1", "audio2", "audio3", "audio4", "audio5",
                  "audioNext", "audioReady")
    rows.append({
        "actor_refs": actors,
        "audio_source_refs": sorted(ptr(root.child(k))["path_id"]
                                    for k in audio_keys if root.child(k) is not None),
        "build_id": BUILD,
        "carrier": {"container": "level20",
                    "dump_file": fn,
                    "mb_class": "Location18_Novella",
                    "path_id": rec["true_pid"],
                    "serialized_container": rec["serialized_container"]},
        "document_id": "novella-location18",
        "event_wiring": wiring,
        "family": "novella_surface",
        "puzzle_index": None,
        "scene_ref": {"container": "level20", "gameobject_path_id": rec["go"]},
        "sprite_ptr": None,
        "text_loc": None,
        "text_mechanism": "unresolved",
        "version_label": VERSION_LABEL,
    })
    return rows, note_counts


def build_book_rows(ledgers):
    rows = []
    for sub, stem, book_id, scene in BOOK_TEXTURES:
        per_locale, missing = {}, []
        for lc in LOCALES:
            ok = os.path.exists(os.path.join(ART, lc, "Textures", sub,
                                             stem + ".webp"))
            per_locale[lc] = ok
            if not ok:
                missing.append(lc)
        if missing:
            ledgers["books_missing"].append({"book_id": book_id,
                                             "locales": sorted(missing)})
        rows.append({
            "art_per_locale": per_locale,
            "art_per_locale_available_count": sum(1 for v in per_locale.values() if v),
            "book_id": book_id,
            "build_id": BUILD,
            "consumer_scene": scene,
            "dressing_only": False,
            "locales_missing": sorted(missing),
            "texture_rel": "Textures/%s/%s.webp" % (sub, stem),
            "version_label": VERSION_LABEL,
        })
    return rows


# ---------------------------------------------------------------------------
# relinks
# ---------------------------------------------------------------------------

def rel_meta(fam, cnt, extra=None):
    base = {"schema": "miside.documents.relinks.%s/1" % fam,
            "generator": GENERATOR, "build_id": BUILD,
            "version_label": VERSION_LABEL, "row_count": cnt,
            "parking": "extracted/data/documents/relinks/ (moves to "
                       "extracted/relinks/ at PIPE emit-stage registration; "
                       "DS-1 relocation precedent)"}
    base.update(extra or {})
    return base


def edge(from_, to, mech, method, status, kind="forward", call=None):
    return {"call": call, "from": from_, "kind": kind, "mechanism": mech,
            "method": method, "status": status, "to": to}


def relink_character(profile_rows):
    meth = ("subject_character_id == DS-1 personages.character_id "
            "(extracted/data/characters/personages.jsonl); flash_save_key "
            "cross-checked against registry save_key (row 0 measured namespace "
            "divergence 'mta' documented)")
    rows = [rel_meta("document--character", 2 * len(profile_rows))]
    for r in profile_rows:
        f = "profile_document:%s" % r["document_id"]
        t = "character:%s" % r["subject_character_id"]
        rows.append(edge(f, t, "hard", meth, "modeled"))
        rows.append(edge(t, f, "hard", meth, "modeled", "inverse"))
    return rows


def relink_achievement(profile_rows):
    meth = ('achievement_sets ["mita-profiles"] == contracts/'
            'dataset-achievements.mdx collectible_set id 13 (ACHI_mitastory); '
            'counting predicate unverified-behavior (code body empty)')
    rows = [rel_meta("document--achievement", 2 * len(profile_rows))]
    for r in profile_rows:
        f = "profile_document:%s" % r["document_id"]
        t = "achievement:ACHI_mitastory"
        rows.append(edge(f, t, "hard", meth, "modeled"))
        rows.append(edge(t, f, "hard", meth, "modeled", "inverse"))
    return rows


def relink_scene_membership(profile_rows, world_rows, placement_source_note):
    fwd = []
    for r in world_rows:
        meth = ("mb-dump filename census + dedupe rule spec §7-R4 "
                "(level-scene ownership wins)" if r["family"] == "note"
                else "typed dump in container")
        fwd.append(("%s:%s" % (r["family"], r["document_id"]),
                    "container:%s" % r["carrier"]["container"], meth))
    for r in profile_rows:
        if r["placement"]:
            fwd.append(("profile_document:%s" % r["document_id"],
                        "container:%s" % r["placement"]["container"],
                        "placement consumed BY REFERENCE from DS-4 AC-2 census "
                        "(single placement authority)%s" % placement_source_note))
    rows = [rel_meta("document--scene-membership", 2 * len(fwd),
                     {"note": "prefab-shared duplicates collapse under spec "
                              "§7-R4; the 98 non-level copies are accounted in "
                              "world_documents _meta.dedupe"})]
    for f, t, meth in fwd:
        rows.append(edge(f, t, "hard", meth, "modeled"))
    for f, t, meth in fwd:
        rows.append(edge(t, f, "hard", meth, "modeled", "inverse"))
    return rows


def relink_event_wiring(world_rows):
    fwd = []
    for r in world_rows:
        for w in r["event_wiring"]:
            tp = w.get("target_ptr") or {}
            pid = tp.get("path_id")
            t = "target:%s#%s:%s" % (r["carrier"]["container"],
                                     "null" if pid is None else pid,
                                     w["target_type"])
            fwd.append(("%s:%s" % (r["family"], r["document_id"]), t,
                        "serialized UnityEvent persistent call (%s)" % w["trigger"],
                        w["method"]))
    rows = [rel_meta("document--event-wiring", 2 * len(fwd))]
    for f, t, meth, m in fwd:
        rows.append(edge(f, t, "hard", meth, "modeled", call=m))
    for f, t, meth, m in fwd:
        rows.append(edge(t, f, "hard", meth, "modeled", "inverse", m))
    return rows


def relink_minigame(world_rows, magnet_count):
    fwd = []
    for r in world_rows:
        if r["family"] == "paper_part":
            scr = r.get("scr_main") or {}
            fwd.append(("paper_part:%s" % r["document_id"],
                        "controller:level13#%s:Location11_BlackRoom"
                        % scr.get("path_id"),
                        "scrMain PPtr (hard)",
                        "serialized controller reference, indexPuzle=%s"
                        % r["puzzle_index"]))
    fwd.append(("choice_flag:Takemagnetfridge (owner: DS-2 Part B §B.1)",
                "prop_family:Transform_Magnet (%d instances + "
                "Transform_MagnetFinish)" % magnet_count,
                "inferred",
                "census-only boundary edge (spec §2.6/§5-J6); magnets owned by "
                "the endings dataset; this file exists so the relink matrix "
                "has the pair"))
    rows = [rel_meta("document--minigame", 2 * len(fwd))]
    for f, t, mech, meth in fwd:
        rows.append(edge(f, t, mech, meth, mech))
    for f, t, mech, meth in fwd:
        rows.append(edge(t, f, mech, meth, mech, "inverse"))
    return rows


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------

README_TEMPLATE = """# Documents & lore collectibles — dataset (DS-5 build B-5)

Contract: [`contracts/dataset-documents.mdx`](../../../contracts/dataset-documents.mdx)
· Spec: [`docs/specs/dataset-documents.mdx`](../../../docs/specs/dataset-documents.mdx)
(arbiter-approved, [ds456-arbiter](../../../docs/research/verifications/ds456-arbiter.mdx))
· Build pins: buildId **{build}**, version **{ver}** (EXTRACTION-LOG
pipeline-defaults == census/detect.json verified at emit; stale-log refusal armed).

| File | Rows |
|---|---|
| `profile_documents.jsonl` | {prof} (11 placed · 2 script-granted · 1 story-granted) |
| `world_documents.jsonl` | {world} ({notes} notes + 5 paper parts + 1 novella surface) |
| `books.jsonl` | 8 localized readable-book textures |
| `relinks/document--character.jsonl` | {rel_char} edges (fwd+inv) |
| `relinks/document--achievement.jsonl` | {rel_ach} edges (fwd+inv) |
| `relinks/document--scene-membership.jsonl` | {rel_scene} edges (fwd+inv) |
| `relinks/document--event-wiring.jsonl` | {rel_ev} edges (fwd+inv) |
| `relinks/document--minigame.jsonl` | {rel_mg} edges (fwd+inv, incl. magnet census edge) |

Relinks are PARKED here (write scope) and move to `extracted/relinks/` at the
PIPE emit-stage registration commit — DS-1 relocation precedent
(`extracted/data/characters/README.md`).

## Honesty ledger feed (missingdata.md input; spec §8 AC-10)

- **Note content carriers unresolved (R1)** — all {notes} `note` rows carry
  `text_mechanism: "unresolved"`, `text_loc: null`. The component serializes
  zero fields ([Unity_Note.cs](../../../extracted/decompiled/main/Assembly-CSharp/Unity_Note.cs));
  no loc category, no scene Text payload (negative findings below); the
  baked-texture hypothesis stays unproven until the R5 sprite index exists.
  Notes render as placed interactables with their serialized event wiring —
  never with invented prose.
- **Script-granted profiles** — `mita-2-d` (row 6, `mtad2`) and `mita-core`
  (row 9, `mtacore`) carry `placement: null`,
  `placement_mechanism: "script_granted"`. Evidence: `CoreSoft.jsonl#line_index=37`
  = "Get Flash Drive" for the Core computer grant (row 9);
  `level2/ButtonMouseClick_#2179.txt` passing `"mtad2"` (DS-4 §3.1 finding 4)
  for row 6.
- **Story-granted profile** — `mita-true` (row 13) is keyless in BOTH
  namespaces (registry `nameSave` empty; no FlashTaker anywhere):
  `flash_save_key: null`, `name_is_shared: true` (Menu line 83 reused with
  row 0).
- **`chapter` is null on all 14 rows** (R3) — fills only from the P5
  level↔chapter map; community chapter attributions never enter rows.
- **R5 raw-pointer state** — `sprite_ptr` values are raw `{{file_id, path_id}}`
  PPtrs; naming waits on the sprite-pathID→export-name index (72,115 exported
  sprites). `books.jsonl` scene bindings stay at subtree-name level
  (`consumer_scene`), never asserted to a parsed scene.

## Placement authority (consume-by-reference)

Per [DS-4 §1](../../../docs/specs/dataset-cartridges.mdx) shared-source ruling,
this dataset is NOT a placement authority: the 11 placed rows'
`(save_key, container)` pairs consume **by reference** to DS-4 AC-2's pickup
census (11-row Mita-side subset; the 10 player-side pickups are DS-4's alone).
Emit-time state: {placement_source}.
Reconciliation against `cartridges.jsonl` is wired into
`selfcheck_documents.py` and runs mechanically whenever that emission exists;
divergence settles toward DS-4's census, never a silent second derivation.

## Negative findings re-proven this pass (spec §8 AC-5)

1. **ComicBook is not readable content** — the only `ComicBook` class is a
   Colorful post-processing image effect
   ([Colorful/ComicBook.cs](../../../extracted/decompiled/main/Assembly-CSharp/Colorful/ComicBook.cs));
   dumps re-counted this pass: exactly one per scene file in **21 containers**.
2. **No loc category carries note/paper/profile text** — English ships **65**
   categories; none matches notes/documents/profiles; `Translation.jsonl`
   holds exactly **1 record, `"-"`**. Re-walked x34 at emit: `Personages` =
   26 records in every locale.
3. **In-scene `Text` payloads are not documents** — re-scan of all 18,117
   `Text*` dumps found exactly **49** `m_Text` literals longer than 60 chars,
   all dev/UI strings. Zero TextMeshPro components exist in any dump.

## R2 unification adjudication — executed, not assumed (spec §8 AC-6)

Searched for a second profile registry: (a) `MenuPersonage` typed dumps across
all 51 containers — exactly ONE instance (`level2/MenuPersonage.txt`);
(b) decompiled Assembly-CSharp classes touching `nameSave` /
`indexDescriptionStringFile` / `resourceMita` — only `Menu`, `MenuPersonage`,
`PersonageResource`; (c) all `*Personage*` / `*Profile*` classes —
`Location18_Personage` (novella actor presentation), `Menu_CasePersonage`
(UI button), `MenuPersonage`, `PersonageResource`; (d) il2cpp string literals —
`/Save/Flashes` is the only flash collection path. **Outcome: no second
serialized profile registry found; unification stands.** Falsifier, verbatim
from spec §2.2: {falsifier}

## Measured divergences found while building (finer measurement, no contradiction)

1. **Book art parity is NOT total x34.** Spec §2.3 recorded "8/8 x34";
   re-walking `art/localization-art/*/Textures/` this pass measures **32 x 8/8**
   and **ChineseSimplified + ChineseTraditional 4/8** — both zh locales lack
   the four `Textures/Location19/Book {{1,2,3,4}}.webp` pages entirely (their
   whole localized subset is 16 files). `books.jsonl` derives availability
   from the filesystem (never asserts), so the cells already say this; the zh
   cells render the declared explicit-filler state for those four pages.
2. **Novella AudioSources: 8, not the 7 sketched in spec §2.4** — serialized
   refs `audioMain, audio1..audio5, audioNext, audioReady` (stored verbatim in
   the row's `audio_source_refs`).
3. **Non-level note copies group by content hash into groups sized
   [{md5_groups}]** across 25 non-level containers; under the pinned §7-R4
   field-signature rule they are **1 shared-prefab group** (Unity_Note
   serializes no payload field beyond the MonoBehaviour base, so every copy's
   signature is empty). Both numbers live in `world_documents.jsonl`
   `_meta.dedupe`.

## Interpretation decisions (documented deviations, no spec violations)

1. **`subject_character_id` uses the BUILT DS-1 slugs** (e.g. `mita-usual`,
   `mita-short-hairs`) — spec §3's draft column predates B-1's emission; J2
   names the built emission the join authority. Multiset equality per AC-1 is
   on `(resource_path, lore_line, name_line)`, which matches the registry
   byte-for-byte.
2. **`carrier.path_id` = TRUE serialized component PathID** resolved by the
   B-3-method raw-header identity pass (AssetStudioMod `_#N` dump suffixes are
   tool ordinals, not PathIDs — build-log B-3 finding 1). Dump filenames ride
   along as `carrier.dump_file` so every row greps clean to its evidence;
   `scene_ref.gameobject_path_id` is verbatim from the dump text.
3. **Row 0 `flash_save_key` = `"mta"`** — the measured FlashTaker namespace
   value; the registry's empty `nameSave` fact stands documented right beside
   it (AC-1 single divergence).
4. **`event_wiring` row shape** — `{{trigger, method, target_type, target_ptr}}`;
   the spec triple `{{method, target_type, target_method}}` maps onto it:
   `method` = serialized `m_MethodName` (the target method),
   `target_type` = serialized assembly type short name; `trigger` adds the
   owning serialized field (`Events_Data._event[i]`,
   `Time_Events.EventsOnTime[j]@<time>`, `Button.onClick`,
   `pauseStart`/`pauseStop`).
5. **`scr_main` additive field** on paper-part rows — the serialized scrMain
   PPtr is J6's join payload; keeping it on the row makes the relink edge
   reproducible without re-opening the dump.
6. **Emitter/checker parked at `data/documents/build/`** — register in the
   PIPE stage tree at adoption, ordered after DS-4's stage per arbiter fence
   (recorded in the build-log handoff).
7. **Relinks parked in `relinks/` subdir** — move to `extracted/relinks/` in
   the registration commit (handoff below).

## Regeneration

```
python extracted/data/documents/build/emit_documents.py      # emit (stale-log guarded)
python extracted/data/documents/build/selfcheck_documents.py # AC scoreboard + rerun diff
```

Two consecutive emits are byte-identical (AC-9); the selfcheck proves it by
re-emitting into a temp dir and diffing bytes.

The book-art walk resolves `extracted/art/localization-art/` first; if that
subtree is triaged off the corpus drive, the emitter follows
`extracted/art/MOVED-TO.txt` mechanically (2026-08-25 C:-disk-full triage
relocated it to `D:\\unpacked_game_data\\MiSide\\art-export\\`).
"""


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def build(out_dir):
    global MAGNET_COUNT
    stale_log_guard()
    ledgers = {"identity": [], "notes": [], "sprite_extras": [],
               "reconcile_divergence": [], "books_missing": []}
    os.makedirs(os.path.join(out_dir, "relinks"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "build"), exist_ok=True)

    # ---- corpus censuses ----------------------------------------------------
    measured = flashtaker_census()
    ds4_pairs, ds4_src = consume_ds4_placements()
    if ds4_pairs is None:
        ds4_pairs = {k: {"container": c, "file": f} for k, c, f in measured}
        placement_source = ("corpus census (DS-4 emission not yet on disk at "
                            "build time); reconcile-vs-cartridges.jsonl armed "
                            "in selfcheck")
    else:
        placement_source = ds4_src

    registry = registry_parse(ledgers)
    chars = character_map()
    assert len(registry) == 14, "registry resourceMita must hold 14 entries"

    # ---- identity pass ------------------------------------------------------
    scripts = script_table(os.path.join(RAW_DATA, "globalgamemanagers.assets"))
    WANT = {"Unity_Note", "FlashTaker", "Location11_PaperPart",
            "Location18_Novella", "Location18_Personage"}
    raw_containers = []
    for cont in sorted(os.listdir(MB)):
        if cont == "globalgamemanagers":          # engine config file, no MBs
            continue
        if os.path.exists(os.path.join(RAW_DATA, cont)):
            raw_containers.append(cont)
    union = defaultdict(list)                     # (cls, go_pid) -> [(container, pid)]
    for cont in raw_containers:
        idents = container_identities(os.path.join(RAW_DATA, cont), scripts)
        for cls in WANT:
            for tp, gp in idents.get(cls, []):
                union[(cls, gp)].append((cont, tp))
    identity_matches = {}
    identity_by_key = {}
    for lv in LEVELS:
        ldir = os.path.join(MB, lv)
        if not os.path.isdir(ldir):
            continue
        local = {c: [] for c in WANT}
        if os.path.exists(os.path.join(RAW_DATA, lv)):
            local = container_identities(os.path.join(RAW_DATA, lv), scripts)
        matches = match_dumps(lv, WANT, local, union, ledgers)
        identity_matches[lv] = matches
        for (cls, _fn), rec in matches.items():
            if cls == "FlashTaker":
                sv = rec["root"].child("save")
                key = scalar_str(sv.value) if sv is not None else None
                if key:
                    identity_by_key[key] = rec

    magnet_count, magnet_finish = magnet_census()
    MAGNET_COUNT = magnet_count

    # ---- rows ---------------------------------------------------------------
    profile_rows = build_profile_rows(registry, chars, ds4_pairs, measured,
                                      placement_source, identity_by_key, ledgers)
    companions_by_level = {}
    for lv in note_filename_census():
        matches = identity_matches.get(lv, {})
        note_gos = {rec["go"] for (cls, _fn), rec in matches.items()
                    if cls == "Unity_Note"}
        companions_by_level[lv] = companion_scan(lv, note_gos, ledgers)
    world_rows, note_counts = build_world_rows(identity_matches,
                                               companions_by_level, ledgers)
    book_rows = build_book_rows(ledgers)

    # ---- profile meta --------------------------------------------------------
    prof_meta = {
        "schema": "miside.documents.profile_documents/1",
        "generator": GENERATOR,
        "source_table": "docs/specs/dataset-documents.mdx §2.2/§3 (registry read "
                        "verbatim from harvest/mb-dump/level2/MenuPersonage.txt)",
        "schema_doc": "contracts/dataset-documents.mdx",
        "build_id": BUILD, "version_label": VERSION_LABEL,
        "row_count": len(profile_rows),
        "ordering": "registry order resourceMita[0..13]",
        "derived_fields": ["document_id", "name_en", "name_is_shared",
                           "evidence", "achievement_sets"],
        "dedupe_rule_applied": "none needed (registry rows; §7-R4 applies to notes)",
        "placement_authority": "DS-4 dataset-cartridges.mdx §1 shared-source "
                               "ruling; consumed BY REFERENCE (11-row Mita-side "
                               "subset)",
        "placement_source": placement_source,
        "chapter_policy": "null until the P5 level↔chapter map lands (spec §7-R3)",
    }
    nonlevel, sig_nonlevel = {}, defaultdict(list)
    for d in sorted(os.listdir(MB)):
        if d.startswith("level"):
            continue
        fs = [f for f in os.listdir(os.path.join(MB, d)) if f.startswith("Unity_Note")]
        if fs:
            nonlevel[d] = len(fs)
            for fn in fs:
                with io.open(os.path.join(MB, d, fn), encoding="utf-8",
                             errors="replace") as fh:
                    body = fh.read()
                sig_nonlevel[hashlib.md5(body.encode("utf-8")).hexdigest()].append((d, fn))
    # ---- meta ---------------------------------------------------------------
    under = defaultdict(list)
    for r in world_rows:
        if r["family"] != "note":
            continue
        c = r["carrier"]["serialized_container"]
        under[(c, r["carrier"]["path_id"])].append(r["carrier"]["container"])
    shared_components = [
        {"backing_levels": sorted(v), "container": k[0], "path_id": k[1],
         "rows": len(v)}
        for k, v in sorted(under.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        if len(v) > 1]
    world_meta = {
        "schema": "miside.documents.world_documents/1",
        "generator": GENERATOR,
        "source_table": "docs/specs/dataset-documents.mdx §2.1/§2.4/§2.5 (typed "
                        "dumps + raw-header identity pass)",
        "schema_doc": "contracts/dataset-documents.mdx",
        "build_id": BUILD, "version_label": VERSION_LABEL,
        "row_count": len(world_rows),
        "ordering": "family note<paper_part<novella_surface; notes by "
                    "(container, true_path_id, dump_file)",
        "derived_fields": ["document_id", "event_wiring.trigger",
                           "carrier.serialized_container"],
        "dedupe": {
            "rule": "spec §7-R4: level-scene ownership wins; non-level copies "
                    "counted once per unique (mb_class, field-signature)",
            "level_owned_note_rows": sum(note_counts.values()),
            "per_container_census": dict(sorted(note_counts.items())),
            "non_level_dump_copies": sum(nonlevel.values()),
            "non_level_containers": dict(sorted(nonlevel.items())),
            "field_signature_groups": 1,
            "field_signature_basis": "Unity_Note serializes zero payload fields "
                                     "beyond the MonoBehaviour base — every "
                                     "copy's signature is empty",
            "raw_md5_groups_non_level": sorted(
                (len(v) for v in sig_nonlevel.values()), reverse=True),
            "underlying_components": {
                "distinct_serialized_note_components": len(under),
                "level_scene_serialized_rows": sum(
                    1 for r in world_rows if r["family"] == "note"
                    and str(r["carrier"]["serialized_container"]).startswith("level")),
                "dependency_prefab_backed_rows": sum(s["rows"]
                                                     for s in shared_components),
                "shared_components": shared_components,
                "note": "AssetStudioMod dependency auto-load re-lists "
                        "Resources-loaded note prefabs inside many level dump "
                        "folders; each row keeps its level-owned census slot "
                        "(ruling §7-R4) while carrier.serialized_container "
                        "records where the component physically serializes",
            },
        },
        "content_carrier_state": "text_mechanism unresolved on every note (R1); "
                                 "unblock = R5 sprite index + P5 hierarchy + "
                                 "native decompile",
    }
    books_meta = {
        "schema": "miside.documents.books/1",
        "generator": GENERATOR,
        "source_table": "docs/specs/dataset-documents.mdx §2.3/§4.4 (availability "
                        "computed by walking art/localization-art/<locale>/Textures/)",
        "schema_doc": "contracts/dataset-documents.mdx",
        "build_id": BUILD, "version_label": VERSION_LABEL,
        "row_count": len(book_rows),
        "derived_fields": ["book_id", "art_per_locale",
                           "art_per_locale_available_count", "locales_missing"],
        "dressing_note": "shelf-prop sprites (Magazines/LivingRoomBookScaff/"
                         "Bedroom Books...) stay ART-layer catalogue rows; "
                         "excluded here",
        "divergence_finding": "zh-Hans/zh-Hant ship 4/8 book textures "
                              "(Location19 pages absent) — see README divergence 1",
    }

    # ---- write ---------------------------------------------------------------
    jl_write(os.path.join(out_dir, "profile_documents.jsonl"),
             [prof_meta] + profile_rows)
    jl_write(os.path.join(out_dir, "world_documents.jsonl"),
             [world_meta] + world_rows)
    jl_write(os.path.join(out_dir, "books.jsonl"), [books_meta] + book_rows)

    rel_char = relink_character(profile_rows)
    rel_ach = relink_achievement(profile_rows)
    rel_scene = relink_scene_membership(profile_rows, world_rows,
                                        " (source state: %s)" % placement_source)
    rel_ev = relink_event_wiring(world_rows)
    rel_mg = relink_minigame(world_rows, magnet_count)
    jl_write(os.path.join(out_dir, "relinks", "document--character.jsonl"), rel_char)
    jl_write(os.path.join(out_dir, "relinks", "document--achievement.jsonl"), rel_ach)
    jl_write(os.path.join(out_dir, "relinks", "document--scene-membership.jsonl"), rel_scene)
    jl_write(os.path.join(out_dir, "relinks", "document--event-wiring.jsonl"), rel_ev)
    jl_write(os.path.join(out_dir, "relinks", "document--minigame.jsonl"), rel_mg)

    counts = {
        "build": BUILD, "ver": VERSION_LABEL,
        "prof": len(profile_rows), "world": len(world_rows),
        "notes": sum(1 for r in world_rows if r["family"] == "note"),
        "rel_char": len(rel_char) - 1, "rel_ach": len(rel_ach) - 1,
        "rel_scene": len(rel_scene) - 1, "rel_ev": len(rel_ev) - 1,
        "rel_mg": len(rel_mg) - 1,
        "md5_groups": ", ".join(str(x) for x
                                in world_meta["dedupe"]["raw_md5_groups_non_level"]),
        "placement_source": placement_source,
        "falsifier": FALSIFIER,
    }
    with io.open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8",
                 newline="\n") as f:
        f.write(README_TEMPLATE.format(**counts))

    stats = {
        "book_rows": len(book_rows),
        "books_ledger": ledgers["books_missing"],
        "identity_issue_count": len(ledgers["identity"]),
        "magnet_finish": magnet_finish,
        "magnets": magnet_count,
        "note_rows": counts["notes"],
        "paper_parts": sum(1 for r in world_rows if r["family"] == "paper_part"),
        "novella_rows": sum(1 for r in world_rows if r["family"] == "novella_surface"),
        "placement_divergences": len(ledgers["reconcile_divergence"]),
        "profile_rows": len(profile_rows),
        "sprites_named": sum(1 for r in world_rows if r.get("sprite_ptr")),
        "wired_calls": sum(len(r["event_wiring"]) for r in world_rows),
        "world_rows": len(world_rows),
    }
    with io.open(os.path.join(out_dir, "build", "emit-stats.json"), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(stats, indent=1, sort_keys=True) + "\n")
    return stats


MAGNET_COUNT = 0

if __name__ == "__main__":
    out = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    print(json.dumps(build(out), indent=1, sort_keys=True))
