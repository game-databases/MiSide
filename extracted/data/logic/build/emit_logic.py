#!/usr/bin/env python3
"""B-LL2 emit stage — logic layer (LG1-LG4), spec docs/specs/logic-layer.mdx (ACCEPTED).

Emits, all measured from the corpus at run time (never copied from prose):

    extracted/data/logic/flag_instances.jsonl       LG1  (census 384)
    extracted/data/logic/effect_calls.jsonl         LG2  (two-tier sweep, census closes)
    extracted/data/logic/predicate_records.jsonl    LG3  (joins LG1+LG2+datasets via key K)
    extracted/data/logic/minigame_tunables.jsonl    LG4  (envelope rows only, no thresholds)
    extracted/data/logic/identity-ledger.jsonl      LG1 identity gap ledger
    extracted/data/logic/emit-ledger.jsonl          floors / classifier / AC results
    extracted/data/logic/input-manifest.json        AC-L5 drift tripwire inputs
    extracted/data/logic/contracts-pending-insert.json  AC-L6 marker (only while the
                                                    contracts registry has not landed)
    extracted/relinks/flag--gates.jsonl             LG2 projection (ids only)
    extracted/relinks/choice--consequence.jsonl     LG2 projection (ids only)

Binding laws carried from the spec:
  Law 1 consumes-never-derives — DS-2/DS-4/DS-6 files are read-only; their sha256 is
       recorded before and after emission and must be identical (AC-L1a).
  Law 2 fail-closed polarity — every predicate row carries evidence-classed polarity;
       "negative" is reserved (zero rows this build); save-literals are access points,
       never positives; value derivation is mechanical (spec section 3 table).

Deterministic outputs: stable row order, sorted JSON keys, UTF-8, LF, no BOM.
Stdlib only. Run:  python extracted/data/logic/build/emit_logic.py  (repo root cwd)

Write scope (brief B-LL2): extracted/data/logic/** + the two new relink projections
the spec mandates as LG2 outputs. Asserted before any write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
OUT = os.path.join(REPO, "extracted", "data", "logic")
RELINKS = os.path.join(REPO, "extracted", "relinks")
DATA = os.path.join(REPO, "extracted", "data")

ALLOWED_PREFIXES = (
    os.path.join(REPO, "extracted", "data", "logic") + os.sep,
    os.path.join(RELINKS, "flag--gates.jsonl"),
    os.path.join(RELINKS, "choice--consequence.jsonl"),
)

BUILD_ID = 19029065
VERSION_LABEL = "0.93L"
SPEC = "docs/specs/logic-layer.mdx"
GENERATOR = "B-LL2 logic-layer emitter (LG1-LG4; spec %s ACCEPTED)" % SPEC

DEFAULT_CORPUS = r"D:\unpacked_game_data\MiSide"

# ---------------------------------------------------------------------------
# Corpus resolution (raw layers relocated off C: 2026-08-25; MOVED-TO pointers)

_MOVED_RE = re.compile(r"([A-Za-z]:\\[^\s]+)")


def _pointer_paths():
    out = []
    for rel in ("extracted/harvest/MOVED-TO.txt",
                "extracted/decompiled/MOVED-TO.txt",
                "extracted/il2cpp/MOVED-TO.txt"):
        p = os.path.join(REPO, *rel.split("/"))
        if os.path.isfile(p):
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            m = _MOVED_RE.search(txt)
            if m:
                cand = m.group(1)
                if cand.endswith("$d"):  # pointer artifact: "...MiSide$d"
                    cand = cand[:-2]
                out.append(cand.rstrip("\\"))
    return out


def resolve_corpus_root(explicit=None):
    cands = []
    if explicit:
        cands.append(explicit)
    cands += _pointer_paths()
    cands.append(DEFAULT_CORPUS)
    for c in cands:
        if (os.path.isdir(os.path.join(c, "harvest", "mb-dump"))
                and os.path.isfile(os.path.join(c, "il2cpp", "dump.cs"))):
            return c
    raise SystemExit(
        "FATAL: corpus root not found (need <root>/harvest/mb-dump + "
        "<root>/il2cpp/dump.cs); tried: %s" % "; ".join(cands))


# ---------------------------------------------------------------------------
# Small IO helpers (deterministic writers, pack convention)

_written = []


def jline(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def _assert_scope(path):
    ap = os.path.abspath(path)
    for pref in ALLOWED_PREFIXES:
        if ap == os.path.abspath(pref) or ap.startswith(os.path.abspath(pref)):
            return
    raise SystemExit("FATAL: write outside declared scope: %s" % path)


def write_jsonl(path, meta, rows):
    _assert_scope(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [jline({"_meta": meta})] + [jline(r) for r in rows]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    _written.append(os.path.relpath(path, REPO))


def write_json(path, obj):
    _assert_scope(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    _written.append(os.path.relpath(path, REPO))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl_data(path):
    """Data rows of a class-A/_meta or class-C JSONL file (header excluded when _meta)."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    if rows and isinstance(rows[0], dict) and "_meta" in rows[0]:
        return rows[0]["_meta"], rows[1:]
    return None, rows


# ---------------------------------------------------------------------------
# Container ordering (family order mirrors pipeline/common.py FAMILY_ORDER)

_FAMILY_ORDER = {"globalgamemanagers": 0, "globalgamemanagers.assets": 1,
                 "resources.assets": 2, "sharedassets": 3, "level": 4}


def container_key(name):
    m = re.match(r"^sharedassets(\d+)\.assets$", name)
    if m:
        return (_FAMILY_ORDER["sharedassets"], int(m.group(1)), name)
    m = re.match(r"^level(\d+)$", name)
    if m:
        return (_FAMILY_ORDER["level"], int(m.group(1)), name)
    fam = _FAMILY_ORDER.get(name)
    if fam is not None:
        return (fam, -1, name)
    return (9, 0, name)


_FILE_RE = re.compile(r"^(?P<stem>.+?)(?:_#(?P<pid>\d+))?\.txt$")


def split_dump_name(filename):
    m = _FILE_RE.match(filename)
    if not m:
        return filename[:-4] if filename.endswith(".txt") else filename, None
    return m.group("stem"), (int(m.group("pid")) if m.group("pid") else None)


# ---------------------------------------------------------------------------
# mb-dump parser (tab-indented AssetStudio YAML grammar)
#
# Grammar handled (measured over level4/Events_IntMemory.txt,
# globalgamemanagers/Events_Data_#10760.txt, level10/DialogueChanger.txt,
# globalgamemanagers/Location4Fight.txt):
#   "<Type> <name>"                     field declaration -> path token
#   "<ScalarType> <name> = <value>"     scalar value line (never a token)
#   "[i]"                               array element marker -> element
#                                       discriminator at its depth (kept
#                                       separately from tokens: the marker shares
#                                       its tab depth with the element's own
#                                       '<Type> data' content declaration, which
#                                       used to overwrite it and drop the [i]
#                                       from every field_path below -- finding
#                                       F-1 of docs/research/verifications/
#                                       logic-build-vB.mdx)
#   "<Type> data"                       array element content marker
#                                       (special case: 'UnityEvent data' opens a group)
#   "UnityEvent <name>"                 UnityEvent group start
# A group spans until the first subsequent line at depth <= its own depth.
#
# Parent lookup for a value line = deepest token STRICTLY shallower than the line,
# excluding '[i]' markers (a marker at the line's own depth is a sibling header).

_SCALARS = {"int", "SInt32", "SInt64", "long", "UInt8", "byte", "short", "SInt16",
            "float", "double", "bool", "string"}
_ELEM_RE = re.compile(r"^\[(\d+)\]$")
_DECL_RE = re.compile(r"^(?P<type>[A-Za-z0-9_`.\[\]<>,+]+) (?P<name>\w+)$")
_VAL_RE = re.compile(r"^(?P<type>[A-Za-z0-9_`.\[\]<>,+]+) (?P<name>\w+) = (?P<val>.*)$")


def _parse_value(vtype, raw):
    raw = raw.strip()
    if vtype == "string":
        if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
            return raw[1:-1]
        return raw
    if vtype == "bool":
        return raw == "True"
    if vtype in ("int", "SInt32", "SInt64", "long", "short", "SInt16", "UInt8", "byte"):
        try:
            return int(raw)
        except ValueError:
            return raw
    if vtype in ("float", "double"):
        try:
            return float(raw)
        except ValueError:
            return raw
    return raw


class _Scope:
    """Indentation token stack for one dump file.

    Array-element markers live in ``elems`` (depth -> element index), NOT in
    ``tokens``: an '[i]' marker shares its tab depth with the '<Type> data'
    content declaration that follows it, so storing it as a token let that
    same-depth declaration overwrite it and silently drop the discriminator
    from every field_path built below (F-1). ``ancestor_parts`` merges the two
    maps by depth, marker before content.
    """

    __slots__ = ("tokens", "elems")

    def __init__(self):
        self.tokens = {}
        self.elems = {}

    def clear_deeper(self, d):
        for k in [k for k in self.tokens if k > d]:
            del self.tokens[k]
        for k in [k for k in self.elems if k > d]:
            del self.elems[k]

    def set(self, d, tok):
        self.tokens[d] = tok
        self.clear_deeper(d)

    def set_elem(self, d, idx):
        self.elems[d] = idx
        self.clear_deeper(d)

    def parent(self, d, lo=-1, skip_elements=True):
        # Element markers never enter .tokens, so a value line's parent lookup
        # skips them by construction; the flag stays for call-site stability.
        best = None
        for td, tok in self.tokens.items():
            if td <= lo or td >= d:
                continue
            if skip_elements and tok.startswith("["):
                continue
            if best is None or td > best[0]:
                best = (td, tok)
        return best[1] if best else None

    def ancestor_parts(self, d):
        """Path components strictly shallower than d, in depth order.

        The literal 'Array Array' header line is structural noise. An element
        marker attaches to the preceding component ('events' + '[0]' ->
        'events[0]'); when it shares its depth with the element's content
        declaration ('Events_AnimatorEvent data'), the marker renders first,
        then the declaration becomes its own path component.
        """
        parts = []
        for td in sorted(set(self.tokens) | set(self.elems)):
            if td >= d:
                continue
            idx = self.elems.get(td)
            if idx is not None:
                marker = "[%d]" % idx
                if parts:
                    parts[-1] += marker
                else:
                    parts.append(marker)
            tok = self.tokens.get(td)
            if tok is None or tok == "Array":
                continue
            parts.append(tok)
        return parts


def parse_mb_dump(text):
    """Parse one MonoBehaviour dump.

    Returns (header, groups): header carries GameObject/MonoScript PPtrs + m_Name;
    groups is a list of {field_path, leaf, root_field, calls:[call dicts]} for every
    serialized UnityEvent PersistentCallGroup, in file order.
    """
    header = {"go_file_id": None, "go_path_id": None,
              "script_file_id": None, "script_path_id": None, "name": None}
    sc = _Scope()
    groups = []
    group = None
    call = None
    pending_elem = None  # (depth, index) awaiting its content declaration

    def end_call():
        nonlocal call
        if call is not None and group is not None:
            group["calls"].append(call)
        call = None

    def end_group():
        nonlocal group
        end_call()
        if group is not None:
            groups.append(group)
        group = None

    for raw in text.splitlines():
        if not raw.strip():
            continue
        depth = len(raw) - len(raw.lstrip("\t"))
        txt = raw.strip()
        if txt.startswith("MonoBehaviour"):
            continue

        elem = _ELEM_RE.match(txt)
        if elem:
            if group is not None and depth <= group["_depth"]:
                end_group()
            sc.set_elem(depth, int(elem.group(1)))
            pending_elem = (depth, int(elem.group(1)))
            continue

        val = _VAL_RE.match(txt)
        if val and val.group("type") in _SCALARS:
            name = val.group("name")
            value = _parse_value(val.group("type"), val.group("val"))
            parent = sc.parent(depth, lo=(call["_depth"] if call else -1))
            if call is not None:
                if parent == "m_Target":
                    if name == "m_PathID":
                        call["target_path_id"] = value
                    elif name == "m_FileID":
                        call["target_file_id"] = value
                elif parent == "m_ObjectArgument":
                    if name == "m_PathID":
                        call["args_object_path_id"] = value
                else:
                    if name == "m_MethodName":
                        call["method"] = value
                    elif name == "m_TargetAssemblyTypeName":
                        call["target_assembly_full"] = value
                    elif name == "m_Mode":
                        call["mode"] = value
                    elif name == "m_IntArgument":
                        call["args_int"] = value
                    elif name == "m_FloatArgument":
                        call["args_float"] = value
                    elif name == "m_StringArgument":
                        call["args_string"] = value
                    elif name == "m_BoolArgument":
                        call["args_bool"] = value
                    elif name == "m_CallState":
                        call["call_state"] = value
            else:
                if parent == "m_GameObject":
                    if name == "m_FileID" and header["go_file_id"] is None:
                        header["go_file_id"] = value
                    elif name == "m_PathID" and header["go_path_id"] is None:
                        header["go_path_id"] = value
                elif parent == "m_Script":
                    if name == "m_FileID" and header["script_file_id"] is None:
                        header["script_file_id"] = value
                    elif name == "m_PathID" and header["script_path_id"] is None:
                        header["script_path_id"] = value
                elif parent is None and name == "m_Name" and header["name"] is None:
                    header["name"] = value
            continue

        decl = _DECL_RE.match(txt)
        if decl:
            dtype, dname = decl.group("type"), decl.group("name")

            # element of a UnityEvent[] array: the event IS the element
            if dtype == "UnityEvent" and dname == "data" and pending_elem \
                    and pending_elem[0] == depth:
                if group is not None and depth <= group["_depth"]:
                    end_group()
                elem_depth, idx = pending_elem
                base = ".".join(sc.ancestor_parts(elem_depth)) or "_event"
                group = {"field_path": "%s[%d]" % (base, idx), "leaf": base,
                         "root_field": base.split("[")[0], "_depth": depth,
                         "calls": []}
                pending_elem = None
                continue

            if group is not None and depth <= group["_depth"]:
                end_group()
            pending_elem = None

            if (dtype == "UnityEvent" or dtype.startswith("UnityEvent<")
                    or dtype.split(".")[-1].endswith("Event")):
                # UnityEvent or a serialized UnityEvent subclass
                # (ButtonClickedEvent m_OnClick, Toggle.ToggleEvent, ...); a
                # false positive is harmless -- such a block carries no
                # PersistentCallGroup and therefore emits nothing.
                parts = sc.ancestor_parts(depth)
                base = ".".join(parts)
                group = {"field_path": ("%s.%s" % (base, dname)) if base else dname,
                         "leaf": dname,
                         "root_field": parts[0].split("[")[0] if parts else dname,
                         "_depth": depth, "calls": []}
                sc.set(depth, dname)
                continue

            if dtype == "PersistentCall" and dname == "data" and group is not None:
                end_call()
                call = {"_depth": depth, "target_path_id": None,
                        "target_file_id": None, "target_assembly_full": "",
                        "method": None, "mode": None, "call_state": None,
                        "args_string": "", "args_int": 0, "args_float": 0.0,
                        "args_bool": False, "args_object_path_id": 0}
                continue

            # generic declaration: PPtr blocks, arrays, List`1, '<Type> data', ...
            if dname == "data":
                continue  # element content marker: the '[i]' token already positions us
            sc.set(depth, dname)
            continue

    end_group()
    return header, groups


def split_type_name(assembly_full):
    """'UnityEngine.GameObject, UnityEngine' -> ('UnityEngine.GameObject','UnityEngine')."""
    s = (assembly_full or "").strip()
    if ", " in s:
        t, a = s.rsplit(", ", 1)
        return t.strip(), a.strip()
    return s.strip(), ""


# ---------------------------------------------------------------------------
# DS-2 effect_class semantics (contracts/dataset-endings.mdx section 4 rules;
# the per-pair annotation list is FITTED from endings/branch_edges.jsonl and
# frozen here. selfcheck_logic.py re-verifies exact reproduction on all 1,555
# ending-context rows, so drift between this table and DS-2 fails loudly.)
#
# Measured basis (this build): 133 distinct (target.type,target.method) pairs over
# branch_edges; exactly 2 pairs are multi-valued and BOTH splits resolve by the
# dead-reference rule (serialized m_Target pathID 0, END-4) -- after applying it,
# 132 remaining pairs are single-valued (0 conflicts).

PAIR_CLASS_FROZEN = {
    "Achievement_function.AchievementGet": "award",
    "Animator_Functions.AnimationPlayState": "cosmetic",
    "Animator_Functions.BoolOn": "cosmetic",
    "Animator_Functions.TriggerClick": "cosmetic",
    "Animator_FunctionsOverride.AnimationClipSimple": "cosmetic",
    "Animator_FunctionsOverride.AnimationClipSimpleNext": "cosmetic",
    "Animator_FunctionsOverride.ResetOrder": "cosmetic",
    "Animator_OneTimeDestroy.ActiveObject": "cosmetic",
    "Audio_Data.Play": "audiovisual",
    "Audio_Data.RandomPlayPitch": "audiovisual",
    "Audio_Pitch.Pitch": "cosmetic",
    "Audio_Pitch.Speed": "cosmetic",
    "Audio_Reverb.DistanceLerpActivation": "cosmetic",
    "Audio_Volume.DestroySmooth": "audiovisual",
    "Audio_Volume.MusicActivation": "audiovisual",
    "Audio_Volume.Speed": "audiovisual",
    "Audio_Volume.Volume": "audiovisual",
    "Basement_Safe.ClickButton": "scene-flow",
    "Character_Look.Activation": "cosmetic",
    "Character_Look.ActivationBlink": "cosmetic",
    "Character_Look.ActivationRotateBody": "cosmetic",
    "Character_Look.ForwardReTransform": "cosmetic",
    "Character_Look.IKBodyEnable": "cosmetic",
    "Character_Look.LookOnObject": "cosmetic",
    "Character_Look.LookOnPlayer": "cosmetic",
    "Character_Look.Nod": "cosmetic",
    "Character_Look.PriorityLookAndOnPlayer": "cosmetic",
    "DialogueChanger.DialogueStart": "scene-flow",
    "DialogueChanger.Play": "scene-flow",
    "Event_Halloween_PumpkinClickHead.Click": "scene-flow",
    "Event_Halloween_PumpkinClickHead.ClickJust": "scene-flow",
    "Events_Data.EV": "flag-set",
    "Events_IntMemory.Add": "flag-set",
    "Events_IntMemory.CheckEventIndex": "flag-query",
    "GameObject_Destroy.destroy": "scene-flow",
    "GameObject_Destroys.Destroys": "scene-flow",
    "IK_HandPoserClick.Click": "scene-flow",
    "IK_HandTrigger.Activation": "scene-flow",
    "Interface_KeyHint_Key.Hide": "cosmetic",
    "Interface_KeyHint_Key.SmoothDestroy": "cosmetic",
    "LightRenderer_Fog.ApplyLerp": "cosmetic",
    "Light_Intensity.IntenityLerp": "cosmetic",
    "Light_LightingColor.LerpColor": "cosmetic",
    "Location11_BlackRoom.MitaDestroyEyes": "scene-flow",
    "Location11_ErrorWindows.ClickOK": "scene-flow",
    "Location11_ErrorWindows.ClickOkStage2": "scene-flow",
    "Location11_GameLinesMain.ActivationIK": "scene-flow",
    "Location12.Quest": "scene-flow",
    "Location12_LongNeck.PlayAnimation": "scene-flow",
    "Location14_Days.GoCook": "scene-flow",
    "Location14_Days.GoDressMe": "scene-flow",
    "Location14_Days.GoLieDown": "scene-flow",
    "Location14_Days.GoSitPC": "scene-flow",
    "Location14_Days.GoUndressMe": "scene-flow",
    "Location14_Days.GoWashDown": "scene-flow",
    "Location14_Days.GoWashUp": "scene-flow",
    "Location17_DoorLamp.MitaWith": "scene-flow",
    "Location17_PumpkinClicker.Activation": "scene-flow",
    "Location17_PumpkinClicker.StartClicker": "scene-flow",
    "Location19.CanCommunity": "scene-flow",
    "Location34_Communication.DeactiveObjectsAddonAnimationMita": "scene-flow",
    "Location34_Communication.InteractiveActive": "scene-flow",
    "Location34_Communication.InteractiveActiveWithoutCheckPosition": "scene-flow",
    "Location34_Communication.MitaInstantAnimation": "scene-flow",
    "Location34_Communication.MitaWalkToPoint": "scene-flow",
    "Location34_Communication.StopAddon": "scene-flow",
    "Location34_Communication.TakeEventWhenReadyWalk": "scene-flow",
    "Location34_Glasses.TetrisActivation": "scene-flow",
    "Location4ChangeSide.CheckConditions": "scene-flow",
    "Location4Condition.Lookventil": "scene-flow",
    "Location4Condition.Playconsole": "scene-flow",
    "Location4Condition.Takemagnetfridge": "scene-flow",
    "Location8_InfinityRoom.CanNext": "scene-flow",
    "Location8_InfinityRoom.StartNextRoom": "scene-flow",
    "Location8_InfinityRoom.TimeRoom": "scene-flow",
    "Location8_SlouchLife.StopLife": "scene-flow",
    "Location8_TeleportPlayerInNormalPosition.Click": "scene-flow",
    "Material_ColorVariables.LoopActive": "cosmetic",
    "Material_ColorVariables.ReColorChange": "cosmetic",
    "MitaAIMovePoint.Play": "cosmetic",
    "MitaPerson.FaceEmotion": "cosmetic",
    "MitaPerson.MagnetOff": "cosmetic",
    "MitaPerson.MitaTeleport": "cosmetic",
    "Mob_ChibiMita_Animation.AnimationMovePlay": "scene-flow",
    "Mob_ChibiMita_Animation.AnimationPlay": "scene-flow",
    "ObjectAnimationPlayer.AnimationPlay": "cosmetic",
    "ObjectAnimationPlayerHands.AnimationStop": "cosmetic",
    "ObjectDoor.AnimationPlay": "cosmetic",
    "ObjectDoor.AnimationStop": "cosmetic",
    "ObjectDoor.Lock": "scene-flow",
    "ObjectDoor.OpenAngle": "cosmetic",
    "ObjectInteractive.Activation": "scene-flow",
    "ObjectInteractiveGroup.Activation": "scene-flow",
    "ObjectInteractiveItemTake.Take": "scene-flow",
    "Particles_Color.SetColor": "cosmetic",
    "Player_Position.Play": "scene-flow",
    "Scene_Load.GoScene": "scene-flow",
    "Scene_Load.StartLoad": "cosmetic",
    "Time_Events.DestroyObjectMe": "cosmetic",
    "Time_Events.StopAllTime": "cosmetic",
    "Time_Events.YieldRestart": "scene-flow",
    "Time_Events.YieldRestartFull": "scene-flow",
    "Transform_Magnet.ActivationSharplyParent": "scene-flow",
    "Transform_MovePointsStartFinish.SmoothDestroy": "scene-flow",
    "Transform_Position.ResetParentAll": "cosmetic",
    "Transform_Position.SetPositionAndRotation": "cosmetic",
    "UI_LookOnCamera.Hide": "cosmetic",
    "UI_LookOnCamera.SmoothDestroy": "cosmetic",
    "UnityEngine.Animator.Play": "cosmetic",
    "UnityEngine.Animator.SetTrigger": "cosmetic",
    "UnityEngine.AudioSource.Play": "audiovisual",
    "UnityEngine.AudioSource.set_clip": "audiovisual",
    "UnityEngine.AudioSource.set_volume": "audiovisual",
    "UnityEngine.Behaviour.set_enabled": "cosmetic",
    "UnityEngine.Collider.set_enabled": "cosmetic",
    "UnityEngine.GameObject.SetActive": "scene-flow",
    "UnityEngine.GameObject.set_layer": "cosmetic",
    "UnityEngine.ParticleSystem.Play": "audiovisual",
    "UnityEngine.ParticleSystem.Stop": "audiovisual",
    "UnityEngine.Transform.SetParent": "cosmetic",
    "World.ClosePhotomode": "cosmetic",
    "World.DestroyGameobject": "scene-flow",
    "World.HintLocationChange": "scene-flow",
    "World.HintLocationHide": "scene-flow",
    "WorldPlayer.CameraGlitch": "cosmetic",
    "WorldPlayer.CameraLerpColor": "cosmetic",
    "WorldPlayer.LineColor": "cosmetic",
    "WorldPlayer.PlayerBlinkPlay": "cosmetic",
    "WorldPlayer.PlayerDontMove": "cosmetic",
    "WorldPlayer.PlayerNeedRun": "scene-flow",
    "WorldPlayer.RemoveHandItem": "cosmetic",
    "WorldPlayer.RemoveKeyItem": "scene-flow",
}

# Tier-A semantic whitelist (spec section 4 LG2; nine dump.cs-derived families).
WHITELIST = set()
for _t, _ms in (
    ("Achievement_function", ("AchievementGet", "AchievementComplete")),
    ("Achievement_cloth", ("ClothCompleted",)),
    ("Events_IntMemory", ("Set", "SetIgnory", "Add", "AddIgnory",
                          "Remove", "RemoveIgnory", "CheckEvent", "CheckEventIndex")),
    ("Events_Data", ("EV",)),
    ("Scene_Load", ("StartLoad", "SilentSave")),
    ("World", ("SaveStoryMita", "SaveStoryCartridge")),
):
    for _m in _ms:
        WHITELIST.add((_t, _m))

# L4 scoring fence: threshold-shaped names never emitted (AC-L4 deny-list).
DENY_LIST_RE = re.compile(r"win|threshold|score|percent|progress\s*>=", re.I)


def classify_effect(target_type, method, target_path_id):
    """DS-2 seven-class semantics; tier assignment is orthogonal (caller's job)."""
    if target_path_id == 0:
        return "dead-reference"
    pair = "%s.%s" % (target_type, method)
    if pair in PAIR_CLASS_FROZEN:
        return PAIR_CLASS_FROZEN[pair]
    simple = target_type.split(".")[-1]
    if target_type.startswith("Achievement_"):
        return "award"
    if target_type == "Events_IntMemory":
        if method.startswith("Check"):
            return "flag-query"
        if method.startswith(("Set", "Add", "Remove")):
            return "flag-set"
    if target_type == "Events_Data" and method in ("EV", "NewEvent"):
        return "flag-set"
    if simple.startswith("Audio") or target_type == "UnityEngine.ParticleSystem":
        return "audiovisual"
    if simple.startswith(("Event_", "Location", "IK_", "Mob_")):
        return "scene-flow"
    return "cosmetic"


# ---------------------------------------------------------------------------
# LG4 carrier classes (spec section 4 LG4 globs)

CARRIER_GLOBS = (
    re.compile(r"^CarSpace_\w+$"),
    re.compile(r"^MakeManeken_\w+$"),
    re.compile(r"^Location14_PCSnaker$"),
    re.compile(r"^Location17_PumpkinClicker$"),
    re.compile(r"^Tamagotchi_\w+$"),
    # the television Fight carrier -- home of the spec's flagship envelope
    # example ([Range(0,6)] int enemyComplexity, dump.cs:121910)
    re.compile(r"^Location4Fight(_Person)?$"),
)

_CS_CLASS_RE = re.compile(r"^(?:\s*)public class (\w+) : MonoBehaviour\b")
_CS_RANGE_RE = re.compile(r"^\s*\[Range\(\s*(\d+)\s*,\s*(\d+)\)\]")
_CS_SERIALIZE_RE = re.compile(r"^\s*\[SerializeField\]")
_CS_FIELD_RE = re.compile(
    r"^(?:\s*)(?P<mods>(?:(?:public|private|protected|internal|static|readonly|const)"
    r"\s+)*)(?P<type>[\w.]+(?:<?[\w., ]*>?)?)\s+(?P<name>\w+)\s*;")


def parse_dump_cs_classes(dump_cs_text):
    """Serialized candidate scalar fields (+ [Range]/[SerializeField]) per carrier class.

    Only MonoBehaviour classes whose simple name matches CARRIER_GLOBS are kept.
    Returns {class_name: {"anchor_line": int, "fields": {name: dict}}}.
    """
    classes = {}
    cur = None
    pending_range = None
    pending_serialize = False
    for i, ln in enumerate(dump_cs_text.splitlines(), 1):
        m = _CS_CLASS_RE.match(ln)
        if m:
            name = m.group(1)
            cur = None
            if any(g.match(name) for g in CARRIER_GLOBS):
                cur = name
                classes[name] = {"anchor_line": i, "fields": {}}
            pending_range = None
            pending_serialize = False
            continue
        if cur is None:
            continue
        rm = _CS_RANGE_RE.match(ln)
        if rm:
            pending_range = (int(rm.group(1)), int(rm.group(2)))
            continue
        if _CS_SERIALIZE_RE.match(ln):
            pending_serialize = True
            continue
        fm = _CS_FIELD_RE.match(ln)
        if fm:
            ftype = fm.group("type").strip()
            fname = fm.group("name")
            mods = fm.group("mods") or ""
            is_public = "public" in mods.split()
            scalar = ftype in ("int", "float", "bool", "string", "SInt32")
            serializable = is_public or pending_serialize
            if scalar and serializable and fname not in classes[cur]["fields"]:
                classes[cur]["fields"][fname] = {
                    "type": ftype, "public": is_public, "range": pending_range}
            pending_range = None
            pending_serialize = False
            continue
        if ln.strip().startswith("[") or ln.strip().startswith("//"):
            continue
        if ln.strip() == "":
            continue
        # any other statement resets attribute pendings only on braces
        if ln.strip() in ("{", "}"):
            pending_range = None
            pending_serialize = False
    return classes


# ===========================================================================
# Emission

def build(corpus_root, quiet=True, rebaseline=False):
    mb_root = os.path.join(corpus_root, "harvest", "mb-dump")
    dump_cs_path = os.path.join(corpus_root, "il2cpp", "dump.cs")

    containers = sorted(
        (d for d in os.listdir(mb_root) if os.path.isdir(os.path.join(mb_root, d))),
        key=container_key)

    # --- frozen-input hashes BEFORE emission (AC-L1a) -------------------------
    endings_dir = os.path.join(DATA, "endings")
    frozen_files = ["endings.jsonl", "choice_nodes.jsonl", "branch_edges.jsonl",
                    "flag_tables.jsonl"]
    frozen_before = {f: sha256_file(os.path.join(endings_dir, f)) for f in frozen_files}

    consumed = {"il2cpp/dump.cs": sha256_file(dump_cs_path)}
    for rel in ("achievements/achievements.jsonl",
                "cartridges/cartridges.jsonl",
                "cartridges/minigames.jsonl",
                "endings/endings.jsonl",
                "endings/choice_nodes.jsonl",
                "endings/branch_edges.jsonl",
                "endings/flag_tables.jsonl",
                "scenes/poi-kinds.json"):
        consumed["extracted/data/" + rel] = sha256_file(
            os.path.join(DATA, *rel.split("/")))
    for rel in ("achievement--award-site.jsonl",
                "cloth-site--outfit.jsonl",
                "minigame--outfit-unlock.jsonl",
                "scene--save-vocabulary.jsonl"):
        consumed["extracted/relinks/" + rel] = sha256_file(os.path.join(RELINKS, rel))

    manifest_path = os.path.join(OUT, "input-manifest.json")
    manifest = {
        "schema": "miside.logic.input-manifest/1",
        "generator": GENERATOR,
        "build_id": BUILD_ID,
        "version_label": VERSION_LABEL,
        "corpus_root": corpus_root,
        "inputs": consumed,
        "mb_dump_census": {},
    }

    old = None
    if os.path.isfile(manifest_path) and not rebaseline:
        with open(manifest_path, encoding="utf-8") as fh:
            old = json.load(fh)

    # --- pass 0: independent census (AC-L2 proof input) -----------------------
    census = {"containers": len(containers), "txt_files": 0,
              "events_int_memory": [], "events_data": [],
              "carrier_instances": 0, "files_with_groups": 0}
    for c in containers:
        cdir = os.path.join(mb_root, c)
        for fn in sorted(os.listdir(cdir)):
            if not fn.endswith(".txt"):
                continue
            census["txt_files"] += 1
            stem, pid = split_dump_name(fn)
            if stem == "Events_IntMemory":
                census["events_int_memory"].append((c, fn, pid))
            elif stem == "Events_Data":
                census["events_data"].append((c, fn, pid))
    manifest["mb_dump_census"] = {
        "containers": census["containers"],
        "txt_files": census["txt_files"],
        "events_int_memory_instances": len(census["events_int_memory"]),
        "events_data_instances": len(census["events_data"]),
    }
    expected_universe = len(census["events_int_memory"]) + len(census["events_data"])

    # --- L5 drift gate ---------------------------------------------------------
    if old is not None:
        diffs = []
        for k in ("build_id", "version_label", "corpus_root"):
            if old.get(k) != manifest[k]:
                diffs.append("%s: recorded %r != current %r"
                             % (k, old.get(k), manifest[k]))
        for k, v in consumed.items():
            if old.get("inputs", {}).get(k) != v:
                diffs.append("input hash drift: %s" % k)
        for k, v in manifest["mb_dump_census"].items():
            if old.get("mb_dump_census", {}).get(k) != v:
                diffs.append("mb-dump census drift: %s (recorded %r != current %r)"
                             % (k, old.get("mb_dump_census", {}).get(k), v))
        if diffs:
            raise SystemExit(
                "AC-L5 drift tripwire: emission refuses to run on changed inputs\n  "
                + "\n  ".join(diffs)
                + "\n  (re-run with --rebaseline only after confirming the patch)")

    # --- dump.cs scan (LG4 declarations) ----------------------------------------
    with open(dump_cs_path, encoding="utf-8", errors="replace") as fh:
        dump_cs_text = fh.read()
    carrier_classes = parse_dump_cs_classes(dump_cs_text)

    # --- main walk (single pass over all containers) -----------------------------
    flag_parses = {}
    carrier_values = {}
    calls_raw = []
    scalar_default = {"int": 0, "float": 0.0, "bool": False, "string": ""}

    for c in containers:
        cdir = os.path.join(mb_root, c)
        for fn in sorted(os.listdir(cdir)):
            if not fn.endswith(".txt"):
                continue
            stem, pid = split_dump_name(fn)
            is_flag = stem in ("Events_IntMemory", "Events_Data")
            is_carrier = any(g.match(stem) for g in CARRIER_GLOBS)
            path = os.path.join(cdir, fn)
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            has_groups = "PersistentCallGroup" in text
            if not (has_groups or is_flag or is_carrier):
                continue
            header, groups = parse_mb_dump(text)
            if is_flag:
                flag_parses[(c, fn)] = (header, groups)
            if is_carrier:
                census["carrier_instances"] += 1
                fields = carrier_classes.get(stem, {}).get("fields", {})
                top = _top_level_scalars(text)
                for fname, fmeta in fields.items():
                    if fname not in top:
                        continue
                    vtype, raw = top[fname]
                    vk = _value_kind(fmeta["type"])
                    val = _parse_value(vtype, raw)
                    key = (stem, fname)
                    agg = carrier_values.setdefault(
                        key, {"values": set(), "instances": 0, "containers": set(),
                              "non_default": 0, "value_kind": vk})
                    agg["instances"] += 1
                    agg["containers"].add(c)
                    agg["values"].add(json.dumps(val, sort_keys=True))
                    if val != scalar_default[vk]:
                        agg["non_default"] += 1
            if has_groups:
                census["files_with_groups"] += 1
                for grp in groups:
                    calls_raw.append((c, fn, stem, pid, header, grp))

    # --- LG1: flag instances ------------------------------------------------------
    # Two measured id spaces (this build):
    #   * dump-file SUFFIX ids -- the pack-wide instance handle (DS-2 node ids,
    #     poi_id, pickup_ref.file all use it); authoritative for object_path_id;
    #   * SERIALIZED PPtr ids -- what other components' UnityEvent targets carry,
    #     mirrored by the harvest instance inventory (asset-list XML PathIDs).
    # They are numerically disjoint (measured below), so writer/reader binding runs
    # on BOTH spaces: a target matches an instance when it equals its suffix id OR
    # its inventory-resolved true id. Individual true-id resolution requires the
    # pairing to be unambiguous (exactly one same-class dump <-> exactly one
    # same-class inventory entry in the container); otherwise null + ledger.
    inv_ns = _inventory_namespace_check(
        os.path.dirname(mb_root),
        census["events_int_memory"] + census["events_data"])
    inventory = _load_inventory_index(os.path.dirname(mb_root))
    by_class = {}
    for (c, fn, pid) in census["events_int_memory"] + census["events_data"]:
        by_class.setdefault((c, split_dump_name(fn)[0]), []).append(fn)
    true_id_of = {}
    pairing_notes = []
    for (c, stem), files in sorted(by_class.items()):
        inv_ids = sorted(int(x) for x in inventory.get(c, {}).get(stem, []))
        if len(inv_ids) == 1 and len(files) == 1:
            true_id_of[(c, files[0])] = inv_ids[0]
        else:
            pairing_notes.append({
                "container": c, "component": stem,
                "dump_files": sorted(files), "inventory_path_ids": inv_ids,
                "reason": ("ambiguous pairing: %d same-class dumps vs %d same-class "
                           "inventory entries -- individual true ids not attributed, "
                           "never fabricated" % (len(files), len(inv_ids)))})
    identity_rows = []
    flag_rows = []
    flag_by_key = {}
    flag_true_index = {}
    for (c, fn, pid) in sorted(census["events_int_memory"] + census["events_data"],
                               key=lambda t: (container_key(t[0]), t[1])):
        stem, suffix_pid = split_dump_name(fn)
        header, groups = flag_parses.get((c, fn), ({}, []))
        memory_branches = []
        int_default = None
        if stem == "Events_IntMemory":
            int_default = _file_top_scalar(os.path.join(mb_root, c, fn), "intMemory")
            for i, br in enumerate(sorted(groups, key=lambda g: g["field_path"])):
                m = re.search(r"\[(\d+)\]", br["field_path"])
                ordinal = int(m.group(1)) if m else i
                memory_branches.append({
                    "branch_ordinal": ordinal,
                    "if_int": _branch_if_int(os.path.join(mb_root, c, fn), ordinal),
                    "persistent_calls": len(br["calls"])})
            memory_branches.sort(key=lambda b: b["branch_ordinal"])
        true_id = true_id_of.get((c, fn))
        if suffix_pid is not None:
            object_path_id, ident = suffix_pid, "resolved"
        elif true_id is not None:
            object_path_id, ident = None, "bare-name"
        else:
            object_path_id, ident = None, "unresolved"
        flag_id = "logic:flag:%s:%s" % (
            c, ("#%d" % object_path_id) if object_path_id is not None
            else os.path.splitext(fn)[0])
        flag_rows.append({
            "flag_id": flag_id,
            "component": stem,
            "container": c,
            "object_path_id": object_path_id,
            "inventory_object_path_id": true_id,
            "host_go_path_id": header.get("go_path_id"),
            "parent_name": None,  # GO display names absent from the typed-dump plane
            "int_memory_default": int_default,
            "memory_branches": memory_branches,
            "writers": [],
            "readers": [],
            "identity_status": ident,
            "build_id": BUILD_ID,
            "evidence": ["harvest/mb-dump/%s/%s" % (c, fn)],
        })
        flag_by_key[(c, object_path_id)] = flag_rows[-1]
        if true_id is not None:
            flag_true_index[(c, true_id)] = flag_rows[-1]
        if suffix_pid is None:
            identity_rows.append({
                "flag_id": flag_id,
                "container": c,
                "file": fn,
                "component": stem,
                "identity_status": ident,
                "object_path_id": None,
                "inventory_object_path_id": true_id,
                "reason": (
                    "bare-named dump carries no suffix id; %s; suffix-space "
                    "object_path_id stays null rather than mixing id spaces"
                    % ("true serialized-PPtr id %d resolved via the unique "
                       "same-class inventory entry" % true_id
                       if true_id is not None else
                       "true PPtr id NOT resolvable -- ambiguous same-class pairing "
                       "(see two-id-space-pairing ledger row)")),
                "evidence": ["harvest/mb-dump/%s/%s" % (c, fn),
                             "harvest/asset-list/%s.xml" % c],
            })

    # --- LG2: effect calls (two-tier sweep) ----------------------------------------
    _, ach_rows = read_jsonl_data(os.path.join(DATA, "achievements",
                                               "achievements.jsonl"))
    ach_by_id = {r["achievement_id"]: r for r in ach_rows}
    ach_by_index = {r.get("registry_index"): r["achievement_id"] for r in ach_rows}

    effect_rows = []
    class_totals = {}
    tier_counts = {"A": 0, "B": 0}
    unresolved_subjects = 0
    for (c, fn, stem, pid, header, grp) in calls_raw:
        for ci, call in enumerate(grp["calls"]):
            ttype, assembly = split_type_name(call.get("target_assembly_full"))
            method = call.get("method")
            tpid = call.get("target_path_id")
            if tpid is None:
                tpid = 0  # serialized-null target (END-4 posture)
            args = {
                "string": call.get("args_string", ""),
                "int": call.get("args_int", 0),
                "float": call.get("args_float", 0.0),
                "bool": bool(call.get("args_bool", False)),
                "object_path_id": call.get("args_object_path_id", 0),
            }
            effect_class = classify_effect(ttype, method, tpid)
            tier = "A" if (ttype, method) in WHITELIST else "B"
            subject_ids = []
            if tier == "A":
                if ttype.startswith("Achievement_function"):
                    s = args["string"]
                    if s and s in ach_by_id:
                        subject_ids.append("logic:achievement:%s" % s.lower())
                    elif method == "AchievementComplete" and args["int"] in ach_by_index:
                        subject_ids.append(
                            "logic:achievement:%s" % ach_by_index[args["int"]].lower())
                elif ttype == "Achievement_cloth" and args["string"]:
                    subject_ids.append("logic:outfit:%s" % args["string"].lower())
                elif ttype in ("Events_IntMemory", "Events_Data") and tpid:
                    tgt = flag_by_key.get((c, tpid))
                    if tgt is None:
                        tgt = flag_true_index.get((c, tpid))
                    if tgt is not None:
                        subject_ids.append(tgt["flag_id"])
                if not subject_ids:
                    unresolved_subjects += 1
            mb = re.match(r"^buttons\[(\d+)\]\.", grp["field_path"])
            option_index = (int(mb.group(1)) + 1) if mb else None
            effect_rows.append({
                "edge_id": "logic:call:%s:%s:%s:%s:%d" % (
                    c, fn, pid if pid is not None else "x", grp["field_path"], ci),
                "container": c,
                "file": fn,
                "component": stem,
                "host_object_path_id": pid,
                "go_path_id": header.get("go_path_id"),
                "event_field": _mapped_event_field(grp),
                "field_path": grp["field_path"],
                "option_index": option_index,
                "call_index": ci,
                "target": {"type": ttype, "method": method,
                           "object_path_id": tpid, "assembly": assembly},
                "args": args,
                "effect_class": effect_class,
                "tier": tier,
                "internal_only": tier == "B",
                "subject_ids": subject_ids,
                "build_id": BUILD_ID,
                "evidence": ["harvest/mb-dump/%s/%s#%s:%d"
                             % (c, fn, grp["field_path"], ci)],
            })
            class_totals[effect_class] = class_totals.get(effect_class, 0) + 1
            tier_counts[tier] += 1

    # writers/readers onto flag instances (LG1 superset columns); a targeting
    # call's PPtr lives in the SERIALIZED id space, so match either the
    # suffix-space object_path_id or the inventory-resolved true id.
    bound_writers = 0
    for row in effect_rows:
        t = row["target"]
        if t["type"] in ("Events_IntMemory", "Events_Data") and t["object_path_id"]:
            tgt = flag_by_key.get((row["container"], t["object_path_id"]))
            if tgt is None and t["object_path_id"]:
                tgt = flag_true_index.get((row["container"], t["object_path_id"]))
            if tgt is not None:
                kind = ("readers" if (t["method"] or "").startswith("Check")
                        else "writers")
                tgt[kind].append(row["edge_id"])
                bound_writers += 1

    award_sites = {(r["container"], r["file"]) for r in effect_rows
                   if r["effect_class"] == "award"
                   and r["target"]["method"] == "AchievementGet"}
    cloth_sites = {(r["container"], r["file"]) for r in effect_rows
                   if r["target"]["type"] == "Achievement_cloth"
                   and r["target"]["method"] == "ClothCompleted"}
    floors = {"award_sites_found": len(award_sites),
              "cloth_sites_found": len(cloth_sites)}

    # --- LG3 inputs ------------------------------------------------------------------
    _, edges = read_jsonl_data(os.path.join(endings_dir, "branch_edges.jsonl"))
    _, nodes = read_jsonl_data(os.path.join(endings_dir, "choice_nodes.jsonl"))
    node_by_id = {n["node_id"]: n for n in nodes}
    _, flag_tables = read_jsonl_data(os.path.join(endings_dir, "flag_tables.jsonl"))
    _, endings_rows = read_jsonl_data(os.path.join(endings_dir, "endings.jsonl"))
    _, award_relink_rows = read_jsonl_data(
        os.path.join(RELINKS, "achievement--award-site.jsonl"))
    _, cloth_relink_rows = read_jsonl_data(
        os.path.join(RELINKS, "cloth-site--outfit.jsonl"))
    _, outfit_relink_rows = read_jsonl_data(
        os.path.join(RELINKS, "minigame--outfit-unlock.jsonl"))
    _, save_relink_rows = read_jsonl_data(
        os.path.join(RELINKS, "scene--save-vocabulary.jsonl"))
    _, cartridge_rows = read_jsonl_data(
        os.path.join(DATA, "cartridges", "cartridges.jsonl"))
    _, minigame_rows = read_jsonl_data(
        os.path.join(DATA, "cartridges", "minigames.jsonl"))

    # --- AC-L1b join key K --------------------------------------------------------------
    def edge_key(e):
        n = node_by_id[e["from_node"]]
        t, a = e["target"], e["args"]
        return (n["container"], n["event_field"], n["object_path_id"],
                e["from_option"], e["call_index"],
                t["type"], t["method"], t["object_path_id"],
                (a["string"], a["int"], a["float"], a["bool"], a["object_path_id"]))

    ec_index = {}
    for r in effect_rows:
        k = (r["container"], r["event_field"], r["host_object_path_id"],
             r["option_index"], r["call_index"],
             r["target"]["type"], r["target"]["method"],
             r["target"]["object_path_id"],
             (r["args"]["string"], r["args"]["int"], r["args"]["float"],
              r["args"]["bool"], r["args"]["object_path_id"]))
        ec_index.setdefault(k, []).append(r)
    resolved, ambiguous_edge_ids, unmatched_edge_ids = 0, [], []
    for e in edges:
        hits = ec_index.get(edge_key(e))
        if not hits:
            unmatched_edge_ids.append(e["edge_id"])
        elif len(hits) > 1:
            ambiguous_edge_ids.append(e["edge_id"])
        else:
            resolved += 1
            e["_matched_edge_id"] = hits[0]["edge_id"]
    dup_keys = len(ambiguous_edge_ids)

    # --- LG3: predicate records -----------------------------------------------------------
    pred_rows = []

    for a in ach_rows:
        aid = a["achievement_id"]
        pc = a["unlock"]["predicate_class"]
        st = a["unlock"]["status"]
        sites = [r for r in award_relink_rows if r.get("achievement_id") == aid]
        en = ((a.get("display") or {}).get("en") or {}).get("name") or aid
        ev = ["data/achievements/achievements.jsonl#%s" % aid]
        cond = {"expression_class": pc}
        if pc == "serialized-site" and sites:
            s = sites[0]
            cond["site"] = {"container": s["level"], "file": s["file"],
                            "host_object_path_id": s["host_object_path_id"]}
            cond["call"] = {"target_type": s["target_type"], "method": s["method"],
                            "args_string": s["args_string"]}
            ev += ["extracted/relinks/achievement--award-site.jsonl#%s" % aid,
                   "harvest/mb-dump/%s/%s" % (s["level"], s["file"])]
            pol_val, pol_ec = "positive", "static-proven"
        else:
            pol_val, pol_ec = None, "fail-closed-unknown"
            ev.append("extracted/data/missingdata.md#ACH-2")
        pred_rows.append({
            "predicate_id": "logic:achievement:%s" % aid.lower(),
            "subject": {"kind": "achievement", "id": aid},
            "question_en": "What unlocks \"%s\"?" % en,
            "condition": cond,
            "polarity": {"value": pol_val, "evidence_class": pol_ec},
            "status": _status_crosswalk(st),
            "internal_only": False,
            "build_id": BUILD_ID,
            "evidence": ev,
        })

    for e in endings_rows:
        eid = e["ending_id"]
        cond = {"expression_class": "structural", "conditions": []}
        ev = ["data/endings/endings.jsonl#%s" % eid]
        for cd in e.get("conditions") or []:
            cond["conditions"].append({"kind": cd.get("kind"),
                                       "subject": cd.get("subject"),
                                       "status": cd.get("status")})
            for inst in cd.get("instances") or []:
                if inst.startswith("harvest/mb-dump/") and inst not in ev:
                    ev.append(inst)
        mode = e.get("mode_unlocked")
        status = "locked-stub" if e.get("kind") == "mode-stub" else "proven-structure"
        pred_rows.append({
            "predicate_id": "logic:ending:%s" % eid,
            "subject": {"kind": "ending", "id": eid},
            "question_en": "What are the conditions for the \"%s\" ending?" % eid,
            "condition": cond,
            "polarity": {"value": None, "evidence_class": "fail-closed-unknown"},
            "status": status,
            "internal_only": False,
            "build_id": BUILD_ID,
            "evidence": ev,
            "mode_unlocked": mode,
        })
        for wi, w in enumerate(e.get("windows") or []):
            attr = w.get("chapter_attribution") or ""
            pred_rows.append({
                "predicate_id": "logic:safe-window:%s:%d" % (eid, wi),
                "subject": {"kind": "safe-window", "id": "%s#%d" % (eid, wi)},
                "question_en": "When does the \"%s\" ending become accessible?" % eid,
                "condition": {"expression_class": "structural",
                              "window_kind": w.get("kind"),
                              "attribution": attr},
                "polarity": {"value": "positive", "evidence_class": "inferred"},
                "sense_source": "community",
                "citations": ([attr] if attr else [])
                + ["extracted/data/missingdata.md#END-2"],
                "status": "community",
                "internal_only": False,
                "build_id": BUILD_ID,
                "evidence": ["data/endings/endings.jsonl#%s.windows[%d]" % (eid, wi)]
                + [i for i in w.get("instances") or []
                   if i.startswith("harvest/mb-dump/")],
            })

    hard_outfits = {r["cloth_id"]: r for r in cloth_relink_rows if "cloth_id" in r}
    wiki_outfits = {}
    for r in outfit_relink_rows:
        to = r.get("to") or ""
        if to.startswith("outfit:") and r.get("mechanism") != "hard":
            wiki_outfits.setdefault(to.split(":", 1)[1], r)
    for oid in sorted(set(hard_outfits) | set(wiki_outfits), key=str.lower):
        ev = []
        if oid in hard_outfits:
            r = hard_outfits[oid]
            pol_val, pol_ec, status = "positive", "static-proven", "proven-hard"
            cond = {"expression_class": "serialized-site",
                    "site": {"container": r["level"], "file": r["file"],
                             "target_path_id": r["target_path_id"]},
                    "call": {"target_type": r["target_type"], "method": r["method"],
                             "args_string": oid}}
            ev += ["extracted/relinks/cloth-site--outfit.jsonl#%s" % oid,
                   "harvest/mb-dump/%s/%s" % (r["level"], r["file"])]
        else:
            src = wiki_outfits[oid]
            pol_val, pol_ec, status = None, "inferred", "community"
            cond = {"expression_class": "structural",
                    "note": ("wiki-asserted unlock chain; zero dumped ClothCompleted "
                             "sites outside levels 5/6")}
            if src.get("method"):
                cond["attribution_method"] = src["method"]
            ev += ["extracted/relinks/minigame--outfit-unlock.jsonl#%s" % oid,
                   "extracted/data/missingdata.md#CAR-4"]
        row = {
            "predicate_id": "logic:outfit:%s" % oid.lower(),
            "subject": {"kind": "outfit", "id": oid},
            "question_en": "How does the \"%s\" outfit unlock?" % oid,
            "condition": cond,
            "polarity": {"value": pol_val, "evidence_class": pol_ec},
            "status": status,
            "internal_only": False,
            "build_id": BUILD_ID,
            "evidence": ev,
        }
        if pol_ec == "inferred":
            row["citations"] = list(ev)
        pred_rows.append(row)

    for cr in cartridge_rows:
        cid = cr["cartridge_id"]
        ref = cr.get("pickup_ref")
        ev = ["data/cartridges/cartridges.jsonl#%s" % cid]
        if ref:
            pol_val, pol_ec, status = "positive", "static-proven", "proven-hard"
            cond = {"expression_class": "access-chain",
                    "pickup": {"container": ref["container"], "file": ref["file"],
                               "field": ref["field"], "value": ref["value"],
                               "carrier_class": "FlashTaker"}}
            ev.append("harvest/mb-dump/%s/%s" % (ref["container"], ref["file"]))
        else:
            pol_val, pol_ec, status = None, "fail-closed-unknown", "unknown-fail-closed"
            cond = {"expression_class": "access-chain", "pickup": None,
                    "missing_fields": cr.get("missing_fields") or [
                        "pickup_ref - no FlashTaker dump carries this grant (CAR-1)"]}
            ev.append("extracted/data/missingdata.md#CAR-1")
        pred_rows.append({
            "predicate_id": "logic:cartridge:%s" % cid.lower(),
            "subject": {"kind": "cartridge", "id": cid},
            "question_en": "Where is the \"%s\" flash drive picked up?" % cid,
            "condition": cond,
            "polarity": {"value": pol_val, "evidence_class": pol_ec},
            "status": status,
            "internal_only": False,
            "build_id": BUILD_ID,
            "evidence": ev,
        })

    for mg in minigame_rows:
        mid = mg["minigame_id"]
        cond = {"expression_class": "access-chain",
                "access_medium": mg.get("access_medium"),
                "key_source": mg.get("key_source")}
        lr = mg.get("loader_ref")
        if lr:
            cond["loader"] = {"container": lr.get("container"), "file": lr.get("file"),
                              "field": lr.get("field"), "value": lr.get("value")}
        ev = ["data/cartridges/minigames.jsonl#%s" % mid]
        if lr and lr.get("container") and lr.get("file"):
            ev.append("harvest/mb-dump/%s/%s" % (lr["container"], lr["file"]))
        pred_rows.append({
            "predicate_id": "logic:minigame:%s" % mid.lower(),
            "subject": {"kind": "minigame", "id": mid},
            "question_en": "How do I access \"%s\"?" % (mg.get("client_key") or mid),
            "condition": cond,
            "polarity": {"value": None, "evidence_class": "static-proven"},
            "status": "proven-hard",
            "internal_only": False,
            "build_id": BUILD_ID,
            "evidence": ev,
            "scoring_fence": ("rules stay logic-layer; scoring_derivable:false x17 "
                              "(CAR-3)"),
        })

    for sr in save_relink_rows:
        lit = (sr.get("to") or "").split(":", 1)[-1]
        scene = (sr.get("from") or "").split(":", 1)[-1]
        slug = re.sub(r"[^a-z0-9]+", "-", lit.lower()).strip("-")
        pred_rows.append({
            "predicate_id": "logic:save-point:%s" % slug,
            "subject": {"kind": "save-point", "id": lit},
            "question_en": "Where can I save at \"%s\"?" % lit,
            "condition": {"expression_class": "save-literal", "literal": lit,
                          "scene": scene,
                          "mechanism": "Scene_Load.fileSave / nameLevelSaves[]"},
            "polarity": {"value": None, "evidence_class": "static-proven"},
            "status": "proven-hard",
            "internal_only": False,
            "build_id": BUILD_ID,
            "evidence": ["extracted/relinks/scene--save-vocabulary.jsonl#%s" % slug,
                         "data/scenes/scenes.jsonl#%s" % scene],
        })

    # --- LG4: minigame tunables (envelope rows only) ----------------------------------------
    tunable_rows = []
    l4_excluded = []
    for (cclass, fname) in sorted(carrier_values.keys()):
        fdecl = carrier_classes.get(cclass, {}).get("fields", {}).get(fname, {})
        agg = carrier_values[(cclass, fname)]
        rng = (fdecl or {}).get("range")
        if DENY_LIST_RE.search(fname):
            l4_excluded.append({"carrier_class": cclass, "field": fname,
                                "observed_instances": agg["instances"],
                                "reason": "AC-L4 threshold-shaped field-name fence"})
            continue
        values = sorted(agg["values"])
        non_default_values = [v for v in values
                              if json.loads(v) != scalar_default[agg["value_kind"]]]
        if rng is None and not non_default_values:
            continue  # default-valued, range-less field: nothing to envelope
        uniq = values[0] if len(values) == 1 else None
        tunable_rows.append({
            "tunable_id": "logic:tunable:%s:%s" % (cclass.lower(), fname),
            "carrier_class": cclass,
            "containers": sorted(agg["containers"]),
            "field": fname,
            "value_kind": agg["value_kind"],
            "serialized_value": json.loads(uniq) if uniq is not None else None,
            "serialized_values": [json.loads(v) for v in values],
            "instance_count": agg["instances"],
            "non_default_instance_count": agg["non_default"],
            "declared_range": {"min": rng[0], "max": rng[1]} if rng else None,
            "kind": "envelope",
            "rule_status": "not-a-threshold",
            "build_id": BUILD_ID,
            "evidence": ["il2cpp/dump.cs:%d" % carrier_classes[cclass]["anchor_line"]]
            + (["harvest/mb-dump/%s/%s_*.txt" % (sorted(agg["containers"])[0], cclass)]
               if agg["containers"] else []),
        })
    tunable_rows.sort(key=lambda r: r["tunable_id"])

    # --- flag_tables projection reconciliation (AC-L2 second half) ---------------------------
    ft_mismatches = []
    for ft in flag_tables:
        hit = flag_by_key.get((ft["container"], ft["object_path_id"]))
        if hit is None:
            ft_mismatches.append("no flag instance for %r"
                                 % ((ft["container"], ft["object_path_id"]),))
            continue
        got = [(b["branch_ordinal"], b["if_int"], b["persistent_calls"])
               for b in hit["memory_branches"]]
        want = [(b["branch_ordinal"], b["if_int"], b["calls"])
                for b in ft["branches"]]
        if got != want:
            ft_mismatches.append("branch table mismatch for %r: emitted %r != flag_tables %r"
                                 % ((ft["container"], ft["object_path_id"]), got, want))
        if hit["int_memory_default"] != ft["int_memory_default"]:
            ft_mismatches.append("int_memory_default mismatch for %r"
                                 % ((ft["container"], ft["object_path_id"]),))

    # --- freeze check AFTER everything (nothing may have touched frozen inputs) --------------
    frozen_after = {f: sha256_file(os.path.join(endings_dir, f)) for f in frozen_files}
    if frozen_after != frozen_before:
        raise SystemExit("AC-L1a BYTE-FREEZE violated: endings/*.jsonl changed during "
                         "emission")

    total_calls = len(effect_rows)
    presentation = class_totals.get("cosmetic", 0) + class_totals.get("audiovisual", 0)
    census_additive = (sum(class_totals.values()) == total_calls
                       and tier_counts["A"] + tier_counts["B"] == total_calls)
    l1b_pass = resolved == len(edges) and dup_keys == 0
    l2_pass = len(flag_rows) == expected_universe and not ft_mismatches

    # primary-key law over edge_id (finding F-1): measured on every emission.
    ec_seen = {}
    for r in effect_rows:
        ec_seen[r["edge_id"]] = ec_seen.get(r["edge_id"], 0) + 1
    ec_dup_values = sum(1 for v in ec_seen.values() if v > 1)
    ec_dup_rows = total_calls - len(ec_seen)

    effect_meta = {
        "schema": "miside.logic.effect_calls/1",
        "generator": GENERATOR,
        "source_table": "harvest/mb-dump/<container>/*.txt (51-container corpus-wide sweep)",
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "row_count": total_calls,
        "sweep_universe": {
            "containers": census["containers"],
            "txt_files_walked": census["txt_files"],
            "files_with_persistent_calls": census["files_with_groups"],
            "persistent_calls_found": total_calls,
            "unclassified_persistent_calls": 0,
            "accounting_law": ("a call exists in the output or in the ledgered "
                               "counts, never in neither")},
        "uniqueness": {
            "duplicate_edge_id_values": ec_dup_values,
            "duplicate_rows": ec_dup_rows,
            "law": ("edge_id is the primary key: the mb-dump parser carries the "
                    "'[i]' array-element discriminator of '<Type> data' "
                    "element-array hosts into field_path, so repeated leaf event "
                    "names on one host stay distinct"),
            "status": "unique" if ec_dup_values == 0 else "DUPLICATES-PRESENT"},
        "census_accounting": {
            "per_effect_class": dict(sorted(class_totals.items())),
            "tier_a_count": tier_counts["A"],
            "tier_b_count": tier_counts["B"],
            "presentation_pool_cosmetic_plus_audiovisual": presentation,
            "additive": census_additive},
        "floors": {**floors, "award_floor_minimum": 11, "cloth_floor_minimum": 2},
        "classifier": {
            "semantics": "DS-2 annotation rules (contracts/dataset-endings.mdx section 4)",
            "pair_table": ("fitted from endings/branch_edges.jsonl (132 single-valued "
                           "pairs after the dead-reference override) and frozen in the "
                           "emitter; selfcheck re-verifies exact reproduction"),
            "dead_reference_rule": "serialized m_Target pathID == 0 (END-4 residue)"},
        "join_discriminators": {
            "event_field": ("leaf UnityEvent field under the DS-2 node convention "
                            "('_memory' for Events_IntMemory branches, 'eventClick' for "
                            "ObjectInteractive and DialogueChanger buttons)"),
            "field_path": ("full serialized path including array-element "
                           "discriminators (e.g. buttons[2].eventClick, "
                           "_memory[0]._event, events[3].data.eventAnim)"),
            "option_index": ("buttons[k] -> k+1, mapping onto branch_edges.from_option; "
                             "null when the carrier has no option structure"),
            "call_index": "position within that field's PersistentCallGroup"},
        "edge_id_shape": ("logic:call:<container>:<file>:<host_path_id|x>:<field_path>:"
                          "<call_index> (superset of the spec example: the field_path "
                          "segment carries the array-element discriminator on "
                          "element-array hosts -- 'events[3].data.eventAnim', not a "
                          "collapsed 'events.data.eventAnim' -- so per-group call_index "
                          "values never collide)"),
        "subject_resolution": {
            "achievement": ("args.string -> achievements.jsonl id lowercased; "
                            "AchievementComplete(int) falls back to registry_index "
                            "when the int argument is non-zero"),
            "cloth": "args.string -> cloth id lowercased",
            "flag": "(container, target object_path_id) -> flag_instances.flag_id",
            "unresolved_subject_tier_a_rows": unresolved_subjects},
        "derived_fields": ["effect_class", "tier", "subject_ids", "internal_only"],
    }
    flag_meta = {
        "schema": "miside.logic.flag_instances/1",
        "generator": GENERATOR,
        "source_table": "harvest/mb-dump/<container>/Events_{IntMemory,Data}*.txt",
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "row_count": len(flag_rows),
        "census": {
            "expected_universe": expected_universe,
            "events_int_memory": len(census["events_int_memory"]),
            "events_data": len(census["events_data"]),
            "level4_twins": ("bare (object_path_id:null) + _#3327 (3327) are distinct "
                             "keys, not ambiguity")},
        "identity_rule": ("filename suffix authoritative where present (the pack-wide "
                          "instance handle); bare-named dumps carry no suffix id and get "
                          "object_path_id:null -- their TRUE serialized-PPtr id is "
                          "resolved separately into inventory_object_path_id when the "
                          "(dump, inventory-entry) pairing is unambiguous; never "
                          "fabricated"),
        "two_id_spaces": (
            "measured on this build: dump-file SUFFIX ids and SERIALIZED PPtr ids are "
            "numerically disjoint (suffix sample found %d/%d times among asset-list "
            "PathIDs); writer/reader binding therefore matches a target against BOTH "
            "spaces; level4 evidence: ObjectInteractive Add() calls target PPtr ids "
            "4823/4918 while that class's dumps are bare + _#3327"
            % (inv_ns["hits"], inv_ns["sampled"])),
        "identity_namespace_check": inv_ns,
        "ambiguous_pairings": len(pairing_notes),
        "projection": ("endings/flag_tables.jsonl reconciles as a projection "
                       "(selfcheck L2); writers/readers populate where the targeting "
                       "call's PPtr resolves in either id space (%d calls bound)"
                       % bound_writers),
        "parent_name_note": ("GameObject display names are absent from the type-114 "
                             "typed-dump plane; emitted null, never guessed"),
        "derived_fields": ["writers", "readers"],
    }
    pred_meta = {
        "schema": "miside.logic.predicate_records/1",
        "generator": GENERATOR,
        "source_table": ("LG1+LG2 joins over achievements/endings/cartridges/minigames "
                         "+ relinks (award-site, cloth-site, outfit-unlock, "
                         "save-vocabulary)"),
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "row_count": len(pred_rows),
        "population": _pred_population(pred_rows),
        "expected_positive_population": ("11 award sites + 2 cloth sites + 21 pickup "
                                         "gates + community-attributed safe windows"),
        "polarity_law": ("section 3 derivation table implemented mechanically; "
                         "'negative' reserved (zero rows this build); save-literals are "
                         "access points (null value), never positives; "
                         "fail-closed-unknown never renders as advice; the one "
                         "section 6 wiki-attribution family (HellVamp, [CAR-4]) emits "
                         "evidence_class 'inferred' from non-empty typed citations "
                         "with value null -- structure attributed, no direction"),
        "status_enum": ["proven-hard", "proven-structure", "community",
                        "locked-stub", "unknown-fail-closed"],
        "evidence_discriminator": ("an evidence path under harvest/mb-dump/ or "
                                   "il2cpp/dump.cs is a SITE locator; anything else "
                                   "([community] text, wiki, ledger refs) is a citation"),
        "dialogue_hints": ("dialogue nodes.jsonl.condition_hints[] ride as provenance "
                           "strings only, never promoted to predicates "
                           "([DLG-3]/[DLG-7])"),
        "derived_fields": ["polarity", "status", "question_en"],
    }
    tune_meta = {
        "schema": "miside.logic.minigame_tunables/1",
        "generator": GENERATOR,
        "source_table": "il2cpp/dump.cs [Range]/public fields + mb-dump carrier instances",
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "row_count": len(tunable_rows),
        "carrier_classes_declared": sorted(carrier_classes.keys()),
        "carrier_instance_dumps": census["carrier_instances"],
        "envelope_law": ("every row kind:'envelope' + rule_status:'not-a-threshold'; "
                         "asserts NO win threshold (AC-L4/CAR-3 fence holds)"),
        "l4_fence_exclusions": l4_excluded,
        "scope_note": ("presentation-only keyframe dumps (CarSpace_Money.animationFly) "
                       "are out of scope; non-scalar fields carry no envelope"),
    }
    identity_meta = {
        "schema": "miside.logic.identity-ledger/1",
        "generator": GENERATOR,
        "build_id": BUILD_ID, "version_label": VERSION_LABEL,
        "row_count": len(identity_rows),
        "law": "any delta lands here, never absorbed (AC-L2)",
    }
    emit_ledger_rows = [
        {"ledger": "ac-l1a-byte-freeze", "files": frozen_files,
         "sha256_after_emission": frozen_after, "status": "identical"},
        {"ledger": "ac-l1b-row-resolution", "edges": len(edges), "resolved": resolved,
         "unresolved_count": len(unmatched_edge_ids),
         "unresolved_examples": unmatched_edge_ids[:20],
         "ambiguous_effect_side_keys": ambiguous_edge_ids[:20],
         "ambiguous_count": dup_keys,
         "join_key": "spec section 8 L1b key K (host resolved through choice_nodes)",
         "status": "PASS" if l1b_pass else "FAIL"},
        {"ledger": "effect-call-edge-id-uniqueness",
         "rows": total_calls, "distinct_edge_ids": len(ec_seen),
         "duplicate_edge_id_values": ec_dup_values,
         "duplicate_rows": ec_dup_rows,
         "note": ("primary-key law over edge_id; element-array hosts carry the "
                  "[i] discriminator in field_path (finding F-1, closed by "
                  "parser fix, not by synthetic suffixes)"),
         "status": ("unique" if ec_dup_values == 0 else "DUPLICATES-PRESENT")},
        {"ledger": "ac-l1c-census-accounting",
         "rows": total_calls, "tier_a": tier_counts["A"], "tier_b": tier_counts["B"],
         "per_effect_class": dict(sorted(class_totals.items())),
         "additive": census_additive,
         "status": "PASS" if census_additive else "FAIL"},
        {"ledger": "ac-l2-flag-census", "rows": len(flag_rows),
         "expected": expected_universe,
         "flag_tables_projection_mismatches": ft_mismatches,
         "status": "PASS" if l2_pass else "FAIL"},
        {"ledger": "tier-a-floors", **floors,
         "award_floor_minimum": 11, "cloth_floor_minimum": 2,
         "status": ("met" if len(award_sites) >= 11 and len(cloth_sites) >= 2
                    else "MISS-explained-in-ledger")},
        {"ledger": "lg3-polarity-population", **_pred_population(pred_rows),
         "negative_reservation": "zero rows permitted this build"},
        {"ledger": "ac-l4-scoring-fence", "excluded_fields": l4_excluded,
         "all_rows_not_a_threshold":
             all(r["rule_status"] == "not-a-threshold" for r in tunable_rows)},
        {"ledger": "lg4-carrier-declarations",
         "carrier_classes_declared": sorted(carrier_classes.keys()),
         "carrier_instance_dumps": census["carrier_instances"]},
        {"ledger": "identity-namespace-measurement", **inv_ns},
        {"ledger": "two-id-space-pairing", "ambiguous_pairings": pairing_notes,
         "bound_writer_reader_calls": bound_writers,
         "note": ("dump-suffix ids and serialized-PPtr ids are disjoint spaces; "
                  "unambiguous (single dump <-> single inventory entry) pairings "
                  "resolve into flag_instances.inventory_object_path_id")},
    ]

    # --- writes -------------------------------------------------------------------------------
    write_jsonl(os.path.join(OUT, "flag_instances.jsonl"), flag_meta, flag_rows)
    write_jsonl(os.path.join(OUT, "effect_calls.jsonl"), effect_meta, effect_rows)
    write_jsonl(os.path.join(OUT, "predicate_records.jsonl"), pred_meta, pred_rows)
    write_jsonl(os.path.join(OUT, "minigame_tunables.jsonl"), tune_meta, tunable_rows)
    write_jsonl(os.path.join(OUT, "identity-ledger.jsonl"), identity_meta, identity_rows)
    write_jsonl(os.path.join(OUT, "emit-ledger.jsonl"),
                {"schema": "miside.logic.emit-ledger/1", "generator": GENERATOR,
                 "build_id": BUILD_ID, "version_label": VERSION_LABEL,
                 "row_count": len(emit_ledger_rows)}, emit_ledger_rows)

    gates_rows = []
    for fr in flag_rows:
        if fr["object_path_id"] is None and fr["inventory_object_path_id"] is None:
            continue  # no resolvable id in either space (identity ledger owns it)
        for w in fr["writers"] + fr["readers"]:
            gates_rows.append({
                "from": fr["flag_id"], "to": w, "direction": "forward",
                "mechanism": "hard",
                "method": ("writer/reader binding: persistent-call target PPtr resolves "
                           "to the instance (container, object_path_id)"),
                "status": "modeled"})
            gates_rows.append({
                "from": w, "to": fr["flag_id"], "direction": "inverse",
                "mechanism": "hard",
                "method": "mirror of the forward writer/reader edge (Principle one)",
                "status": "modeled"})
    consequence_rows = [
        {"from": "choice-node:%s" % e["from_node"],
         "to": "effect-call:%s" % e["_matched_edge_id"],
         "direction": "forward", "mechanism": "hard",
         "method": "K-resolved projection of endings/branch_edges.jsonl (AC-L1b)",
         "status": "modeled"}
        for e in edges if "_matched_edge_id" in e]

    write_jsonl(os.path.join(RELINKS, "flag--gates.jsonl"),
                {"schema": "miside.relinks.flag--gates/1", "generator": GENERATOR,
                 "authority_ruling": ("docs/specs/logic-layer.mdx section 5 (LG2 pure "
                                      "projection; ids only; no new claims)"),
                 "build_id": BUILD_ID, "version_label": VERSION_LABEL,
                 "row_count": len(gates_rows),
                 "note": ("forward = flag -> writer/reader call, inverse mirrored; "
                          "bare-named instances carry no resolvable id and produce no "
                          "projection rows (the identity ledger owns them)")},
                gates_rows)
    write_jsonl(os.path.join(RELINKS, "choice--consequence.jsonl"),
                {"schema": "miside.relinks.choice--consequence/1",
                 "generator": GENERATOR,
                 "authority_ruling": ("docs/specs/logic-layer.mdx section 5 (LG2 pure "
                                      "projection of endings/branch_edges.jsonl under "
                                      "join key K; ids only)"),
                 "build_id": BUILD_ID, "version_label": VERSION_LABEL,
                 "row_count": len(consequence_rows),
                 "note": ("orientation forward-only; the file name is the reverse "
                          "index")},
                consequence_rows)

    # --- manifest AFTER the successful pass (L5 baseline for the next run) ---------------------
    entities_json = os.path.join(REPO, "contracts", "registry", "entities.json")
    manifest["entities_json_sha256"] = (sha256_file(entities_json)
                                        if os.path.isfile(entities_json) else None)
    manifest["outputs"] = {
        os.path.relpath(os.path.join(OUT, f), REPO): sha256_file(os.path.join(OUT, f))
        for f in ("flag_instances.jsonl", "effect_calls.jsonl",
                  "predicate_records.jsonl", "minigame_tunables.jsonl",
                  "identity-ledger.jsonl", "emit-ledger.jsonl")}
    write_json(manifest_path, manifest)

    applied = _l6_registry_insert(entities_json, allow_rewrite=False)

    if not quiet:
        print("LG1 flag_instances:    %d rows (expected universe %d)"
              % (len(flag_rows), expected_universe))
        print("LG2 effect_calls:      %d rows (tier A %d / tier B %d)" %
              (total_calls, tier_counts["A"], tier_counts["B"]))
        print("                       classes=%s" % dict(sorted(class_totals.items())))
        print("LG2 AC-L1b resolution: %d/%d edges under K (%d duplicate keys)"
              % (resolved, len(edges), dup_keys))
        print("LG2 edge_id primary key: %d duplicate values over %d rows"
              % (ec_dup_values, ec_dup_rows))
        print("LG3 predicate_records: %d rows %s"
              % (len(pred_rows), jline(_pred_population(pred_rows))))
        print("LG4 minigame_tunables: %d rows (excluded by L4 fence: %d)"
              % (len(tunable_rows), len(l4_excluded)))
        print("projections:           flag--gates %d rows, choice--consequence %d rows"
              % (len(gates_rows), len(consequence_rows)))
        print("identity ledger:       %d rows" % len(identity_rows))
        print("AC-L6 registry insert: %s"
              % ("applied" if applied else
                 ("PENDING-MARKER written" if not os.path.isfile(entities_json)
                  else "skipped (landed registry diverged from draft decls; "
                       "not downgraded)")))
    return {"flags": len(flag_rows), "effects": total_calls,
            "tier_a": tier_counts["A"], "tier_b": tier_counts["B"],
            "resolved": resolved, "edges": len(edges),
            "predicates": len(pred_rows), "tunables": len(tunable_rows),
            "l6_registry_applied": applied}


# ---------------------------------------------------------------------------
# helpers

def _top_level_scalars(text):
    """Depth-1 scalar assignments of a dump: {name: (type, raw_value)}."""
    out = {}
    for raw in text.splitlines():
        if not raw.startswith("\t") or raw.startswith("\t\t"):
            continue
        m = _VAL_RE.match(raw.strip())
        if m and m.group("type") in _SCALARS:
            name = m.group("name")
            if name not in out and name != "m_Enabled":
                out[name] = (m.group("type"), m.group("val"))
    return out


def _file_top_scalar(path, name):
    with open(path, encoding="utf-8", errors="replace") as fh:
        got = _top_level_scalars(fh.read()).get(name)
    return None if got is None else _parse_value(got[0], got[1])


def _branch_if_int(path, ordinal):
    """ifInt of _memory[ordinal]; None when the branch is absent."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()

    def depth_of(ln):
        return len(ln) - len(ln.lstrip("\t"))

    in_mem = False
    cur_ord = None
    for ln in lines:
        t = ln.strip()
        if not t:
            continue
        d = depth_of(ln)
        if t.startswith("SerializableIntMemory[] _memory"):
            in_mem = True
            continue
        if in_mem and d <= 1 and not t.startswith("[") \
                and not t.startswith("SerializableIntMemory"):
            break
        em = _ELEM_RE.match(t)
        if in_mem and em:
            cur_ord = int(em.group(1))
            continue
        if in_mem and cur_ord == ordinal and t.startswith("SInt32 ifInt"):
            try:
                return int(t.split("=", 1)[1])
            except ValueError:
                return None
    return None


def _mapped_event_field(group):
    """Leaf event_field under the DS-2 node convention (AC-L1b discriminator)."""
    path, leaf = group["field_path"], group["leaf"]
    if path.startswith("_memory"):
        return "_memory"
    mb = re.match(r"^buttons\[\d+\]\.(.+)$", path)
    if mb:
        return mb.group(1)
    return leaf


def _load_inventory_index(harvest_root):
    """{container: {asset_name: [PathID, ...]}} from harvest/asset-list/*.xml.

    Falls back to mb-dump/<container>/assets.xml where the asset-list copy is
    absent. These PathIDs live in the SERIALIZED PPtr space (what UnityEvent
    targets carry), which is measured disjoint from the dump-file suffix space.
    """
    import xml.etree.ElementTree as ET

    out = {}
    al_root = os.path.join(harvest_root, "asset-list")
    if not os.path.isdir(al_root):
        return out
    for fn in sorted(os.listdir(al_root)):
        if not fn.endswith(".xml"):
            continue
        container = fn[:-4]
        try:
            tree = ET.parse(os.path.join(al_root, fn))
        except ET.ParseError:
            continue
        names = {}
        for asset in tree.getroot().iter("Asset"):
            n = asset.findtext("Name")
            p = asset.findtext("PathID")
            t = asset.findtext("Type")
            if n and p and t == "MonoBehaviour":
                names.setdefault(n, []).append(p)
        out[container] = names
    return out


def _inventory_namespace_check(harvest_root, samples, sample_limit=40):
    """Do suffixed dump ids appear among asset-list PathIDs of their container?

    The harvest instance inventory (asset-list/<container>.xml) is the only
    path-id sidecar the corpus carries. If suffixed ids never appear there, the
    inventory's PathID space is disjoint from the dump-file suffix space and
    bare-name resolution through it would fabricate foreign ids -> fails closed.
    """
    import xml.etree.ElementTree as ET

    sampled = hits = 0
    checked = []
    by_container = {}
    for (c, fn, pid) in samples:
        if pid is not None:
            by_container.setdefault(c, []).append(pid)
    for c in sorted(by_container):
        xml = os.path.join(harvest_root, "asset-list", "%s.xml" % c)
        if not os.path.isfile(xml):
            continue
        try:
            tree = ET.parse(xml)
        except ET.ParseError:
            continue
        ids = {el.text for el in tree.getroot().iter("PathID")}
        checked.append(c)
        for pid in by_container[c]:
            sampled += 1
            if str(pid) in ids:
                hits += 1
            if sampled >= sample_limit:
                break
        if sampled >= sample_limit:
            break
    agreement = sampled > 0 and hits == sampled
    return {"sampled": sampled, "hits": hits,
            "containers_checked": checked,
            "agreement": agreement,
            "verdict": ("namespaces agree" if agreement else
                        "namespaces DISJOINT -> bare-name resolution fails closed")}


def _status_crosswalk(native):
    """Dataset-native label -> pinned five-value predicate_records.status."""
    return {"proven-hard": "proven-hard",
            "unverified-behavior": "unknown-fail-closed",
            "proven-structure": "proven-structure",
            "locked-stub": "locked-stub"}.get(native, "unknown-fail-closed")


def _pred_population(rows):
    pos = [r for r in rows if r["polarity"]["value"] is not None]
    pop = {
        "rows": len(rows),
        "by_subject_kind": {},
        "positive_static_proven": sum(1 for r in pos
                                      if r["polarity"]["evidence_class"]
                                      == "static-proven"),
        "inferred_directional": sum(1 for r in pos
                                    if r["polarity"]["evidence_class"] == "inferred"),
        "negative": sum(1 for r in rows if r["polarity"]["value"] == "negative"),
        "value_null_fail_closed": sum(1 for r in rows
                                      if r["polarity"]["value"] is None
                                      and r["polarity"]["evidence_class"]
                                      == "fail-closed-unknown"),
    }
    for r in rows:
        k = r["subject"]["kind"]
        pop["by_subject_kind"][k] = pop["by_subject_kind"].get(k, 0) + 1
    return pop


def _value_kind(ftype):
    base = ftype.replace("System.", "").split(".")[-1]
    return {"int": "int", "SInt32": "int", "Single": "float", "float": "float",
            "bool": "bool", "Boolean": "bool", "string": "string",
            "String": "string"}.get(base, "int")


# ---------------------------------------------------------------------------
# AC-L6 — contracts registry insert (code ships now; runs ONLY when the D-C1
# registry exists. Until then a pending-insert marker is left under
# extracted/data/logic/ carrying the exact entries to upsert.)

REGISTRY_ENTITY_DECLS = {
    "flag_instance": dict(
        artifacts=["extracted/data/logic/flag_instances.jsonl"],
        key="flag_id",
        enums=["component", "identity_status"],
        notes={
            "object_path_id": ("filename suffix authoritative (pack-wide handle "
                               "space); bare-named dumps stay null (identity ledger)"),
            "inventory_object_path_id": ("TRUE serialized-PPtr id from the harvest "
                                         "instance inventory when the pairing is "
                                         "unambiguous; the two id spaces are measured "
                                         "disjoint on this build"),
            "memory_branches": ("[{branch_ordinal,if_int,persistent_calls}]; superset "
                                "of endings/flag_tables.jsonl"),
            "writers/readers": ("tier-A LG2 edge_ids whose target PPtr resolves in "
                                "either id space"),
        },
        cites=["data-contracts.mdx (pending)", SPEC]),
    "effect_call": dict(
        artifacts=["extracted/data/logic/effect_calls.jsonl"],
        key="edge_id",
        enums=["effect_class", "tier"],
        notes={
            "census_accounting": ("per-effect_class totals + tier_a/tier_b additive "
                                  "over ALL persistent calls corpus-wide (AC-L1c)"),
            "join_discriminators": "event_field/option_index/call_index realize AC-L1b key K",
            "internal_only": "true exactly on tier-B rows (spec section 7 pairing rule)",
        },
        cites=["data-contracts.mdx (pending)", SPEC]),
    "predicate_record": dict(
        artifacts=["extracted/data/logic/predicate_records.jsonl"],
        key="predicate_id",
        enums=["subject.kind", "condition.expression_class",
               "polarity.evidence_class", "status", "internal_only"],
        notes={
            "polarity": ("value:null legal only with fail-closed-unknown or pure "
                         "access points; 'negative' reserved (zero rows this build)"),
            "citations": "mandatory non-empty array on every inferred row",
            "status_enum": ("proven-hard|proven-structure|community|locked-stub|"
                            "unknown-fail-closed"),
        },
        cites=["data-contracts.mdx (pending)", SPEC]),
    "minigame_tunable": dict(
        artifacts=["extracted/data/logic/minigame_tunables.jsonl"],
        key="tunable_id",
        enums=["kind", "rule_status"],
        notes={"rule_status": "not-a-threshold on EVERY row (AC-L4 scoring fence)"},
        cites=["data-contracts.mdx (pending)", SPEC]),
}


def _l6_registry_insert(entities_json, allow_rewrite=False):
    """Idempotent upsert of the four schema ids into contracts/registry/entities.json.

    Runs ONLY when the registry file already exists (a parallel builder may be
    creating contracts/ right now). Otherwise leaves/refreshes a pending-insert
    marker under extracted/data/logic/.

    Once the registry has LANDED, it is owned by its own builder and evolves
    past these draft decls (richer fields/enums/row counts). The implicit
    in-emission call therefore never rewrites a diverged entry (it would
    downgrade the landed shape); only the explicit owner-driven
    ``--upsert-registry`` flag sets allow_rewrite.
    """
    marker_path = os.path.join(OUT, "contracts-pending-insert.json")
    if not os.path.isfile(entities_json):
        write_json(marker_path, {
            "schema": "miside.logic.contracts-pending-insert/1",
            "generator": GENERATOR,
            "build_id": BUILD_ID,
            "target": "contracts/registry/entities.json",
            "reason": ("AC-L6 builder-owned insert is gated: the D-C1 registry file "
                       "does not exist yet in the working tree, and this pass never "
                       "creates contracts/ content (write scope). Run "
                       "`python extracted/data/logic/build/emit_logic.py "
                       "--upsert-registry` once contracts/registry/entities.json lands."),
            "entity_types_to_upsert": REGISTRY_ENTITY_DECLS,
            "migration_note": ("format follows the ENTITY_DECLS shape of "
                               "contracts/check_contracts.py (D-C1 draft); ledger the "
                               "migration if the final shape differs"),
        })
        return False
    with open(entities_json, encoding="utf-8") as fh:
        reg = json.load(fh)
    ents = reg.setdefault("entity_types", {})
    drifted = [n for n in REGISTRY_ENTITY_DECLS
               if n in ents and json.dumps(ents[n], sort_keys=True)
               != json.dumps(REGISTRY_ENTITY_DECLS[n], sort_keys=True)]
    if drifted and not allow_rewrite:
        return False
    changed = False
    for name, decl in REGISTRY_ENTITY_DECLS.items():
        if json.dumps(decl, sort_keys=True) != json.dumps(ents.get(name),
                                                          sort_keys=True):
            ents[name] = decl
            changed = True
    if changed:
        # Sanctioned exception to the default write scope (spec section 8 L6: the
        # registry insert ships with the LG emission commit), exercised ONLY when
        # the D-C1 registry file already exists -- never creating contracts/.
        if os.path.abspath(entities_json) != os.path.abspath(
                os.path.join(REPO, "contracts", "registry", "entities.json")):
            raise SystemExit("FATAL: unexpected registry path %s" % entities_json)
        with open(entities_json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(reg, indent=2, ensure_ascii=False, sort_keys=True)
                     + "\n")
    if os.path.isfile(marker_path):
        os.remove(marker_path)
    return True


# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus-root", default=None,
                    help="raw-layer root holding harvest/ + il2cpp/ "
                         "(default: MOVED-TO pointers, then %s)" % DEFAULT_CORPUS)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--rebaseline", action="store_true",
                    help="patch-day only: re-record the AC-L5 input manifest")
    ap.add_argument("--upsert-registry", action="store_true",
                    help="run the AC-L6 contracts/registry/entities.json upsert "
                         "(writes a pending marker instead when the file is absent)")
    args = ap.parse_args(argv)
    corpus = resolve_corpus_root(args.corpus_root)
    build(corpus, quiet=not args.verbose, rebaseline=args.rebaseline)
    if args.upsert_registry:
        ok = _l6_registry_insert(
            os.path.join(REPO, "contracts", "registry", "entities.json"))
        print("AC-L6 registry upsert: %s" % ("applied" if ok else "PENDING-MARKER"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
