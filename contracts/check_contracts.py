#!/usr/bin/env python3
"""check_contracts.py -- generator + verifier for MiSide ``contracts/registry/``.

Contract: docs/specs/data-contracts.mdx (D-C1, ACCEPTED 2026-08-26).
Emits/verifies, all derived from the read surface at runtime (never restated):

    registry/entities.json      section 3 entity-type registry (schemas FROM rows)
    registry/joins.json         section 4 join registry (25 families / 1,159 edges)
    registry/fingerprints.json  section 6 sha256 + row_count + build pins
    registry/availability.json  section 5 locale-availability contract cells
    registry/stub-markers.json  section 7 stub vocabulary <-> missingdata.md map

Design law (section 1): the frontend CONSUMES typed contracts and never derives
data. This tool is its mirror: it derives the registries from
``extracted/data/**`` + ``extracted/relinks/*.jsonl``, byte-compares them with
the committed copies, and runs the acceptance gates C1-C10 that are runnable
offline. Any drift exits non-zero (silent content drift at the same buildId is
a defect, PIPE AC-5 bar).

Usage:
    python contracts/check_contracts.py              # verify (default)
    python contracts/check_contracts.py verify       # regenerate in-memory + compare + gates + self-tests
    python contracts/check_contracts.py generate     # rewrite registry/*.json from disk
    python contracts/check_contracts.py self-test    # offline unit probes only (no writes)
    python contracts/check_contracts.py report       # print measured summary, no writes

Stdlib only; no network, no git, no services.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_PATH = "docs/specs/data-contracts.mdx"
LEDGER_PATH = "extracted/data/missingdata.md"
EXTRACTION_LOG = "extracted/EXTRACTION-LOG.md"
REGISTRY_DIR = os.path.join("contracts", "registry")

ENTITY_FILES = "contracts/registry/entities.json"
JOIN_FILES = "contracts/registry/joins.json"
FINGERPRINT_FILES = "contracts/registry/fingerprints.json"
AVAILABILITY_FILE = "contracts/registry/availability.json"
STUB_FILE = "contracts/registry/stub-markers.json"

# --------------------------------------------------------------------------- #
# tiny IO helpers
# --------------------------------------------------------------------------- #


def rpath(*parts: str) -> str:
    return os.path.join(REPO, *parts)


def read_bytes(rel: str) -> bytes:
    with open(rpath(*rel.split("/")), "rb") as fh:
        return fh.read()


def read_text(rel: str) -> str:
    return read_bytes(rel).decode("utf-8")


def canon_json(obj) -> bytes:
    """Canonical artifact bytes: sorted keys, compact, UTF-8, LF, one trailing newline."""
    return (
        json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def load_jsonl(rel: str) -> list:
    out = []
    with open(rpath(*rel.split("/")), "r", encoding="utf-8", newline="") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_json(rel: str):
    return json.loads(read_text(rel))


# --------------------------------------------------------------------------- #
# build pins (EXTRACTION-LOG.md `pipeline-defaults` block -- stale-log defense)
# --------------------------------------------------------------------------- #


def pipeline_pin() -> dict:
    text = read_text(EXTRACTION_LOG)
    m = re.search(r"```json\s*pipeline-defaults\s*(\{.*?\})\s*```", text, re.S)
    if not m:
        raise SystemExit(f"FATAL: no pipeline-defaults block in {EXTRACTION_LOG}")
    pin = json.loads(m.group(1))
    for key in ("buildId", "versionLabel"):
        if key not in pin:
            raise SystemExit(f"FATAL: pipeline-defaults missing {key}")
    return {"build_id": str(pin["buildId"]), "version_label": str(pin["versionLabel"])}


# --------------------------------------------------------------------------- #
# header classes (spec section 2.2 -- measured, readers dispatch on these)
#   A: {"_meta": {...}} wrapper line, then data rows
#   B: bare descriptor line carrying row_count (no _meta key), then data rows
#   C: headerless -- data rows from line 1
#   S: single-object JSON document (not JSONL)
# --------------------------------------------------------------------------- #

EXPECTED_HEADER_CLASSES = {
    "extracted/data/characters/personages.jsonl": "A",
    "extracted/data/characters/characters.candidates.jsonl": "A",
    "extracted/data/cartridges/cartridges.jsonl": "A",
    "extracted/data/cartridges/minigames.jsonl": "A",
    "extracted/data/cartridges/cartridges-minigames.candidates.jsonl": "A",
    "extracted/data/scenes/scenes.jsonl": "A",
    "extracted/data/scenes/poi.jsonl": "A",
    "extracted/data/scenes/spawn-tables.jsonl": "A",
    "extracted/data/scenes/scene-links.jsonl": "A",
    "extracted/data/scenes/markers.jsonl": "A",
    "extracted/data/documents/world_documents.jsonl": "B",
    "extracted/data/documents/profile_documents.jsonl": "B",
    "extracted/data/documents/books.jsonl": "B",
    "extracted/data/achievements/achievements.jsonl": "C",
    "extracted/data/endings/endings.jsonl": "C",
    "extracted/data/endings/choice_nodes.jsonl": "C",
    "extracted/data/endings/branch_edges.jsonl": "C",
    "extracted/data/endings/flag_tables.jsonl": "C",
    "extracted/data/dialogue/nodes.jsonl": "C",
    "extracted/data/dialogue/edges.jsonl": "C",
    "extracted/data/dialogue/residue-links.jsonl": "C",
    "extracted/relinks/locale_availability.jsonl": "C",
    "extracted/relinks/_assembly-provenance.jsonl": "C",
    # single-object JSON sidecars consumed as typed surfaces (spec sections 2.2/3.7/3.9)
    "extracted/data/dialogue/speakers.json": "S",
    "extracted/data/scenes/poi-kinds.json": "S",
    **{f"extracted/data/dialogue/graphs/level{n}.json": "S" for n in
       (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22)},
    # logic-layer family (docs/specs/logic-layer.mdx section 5): class A _meta-first JSONL;
    # registered here because build_entities consumes them (F-CT2 reconciliation, EXTEND branch)
    "extracted/data/logic/effect_calls.jsonl": "A",
    "extracted/data/logic/flag_instances.jsonl": "A",
    "extracted/data/logic/minigame_tunables.jsonl": "A",
    "extracted/data/logic/predicate_records.jsonl": "A",
    # LG2 logic-relink projections (docs/specs/logic-layer.mdx section 5): class A _meta-first
    # JSONL. F-CT3 KEEP-PINNED ruling (2026-08-26): integrity rides their fingerprints.json
    # entries -- they reach CONSUMED_ARTIFACTS from here, so verify recomputes sha256 +
    # row_count + build stamp like every other consumed artifact. Deliberately NOT JOIN_DECLS
    # families 26/27 (ids-only projections derivable from contract-pinned types; data-contracts.mdx
    # section 4 note) -- registration revisitable if a consumer ever needs join-family semantics.
    "extracted/relinks/flag--gates.jsonl": "A",
    "extracted/relinks/choice--consequence.jsonl": "A",
}

DECLARED_SCHEMA_IDS = {
    "extracted/data/characters/personages.jsonl": "miside.characters.personages/1",
    "extracted/data/characters/characters.candidates.jsonl": "miside.characters.candidates/1",
    "extracted/data/cartridges/cartridges.jsonl": "miside.cartridges.cartridges/1",
    "extracted/data/cartridges/minigames.jsonl": "miside.minigames.minigames/1",
    "extracted/data/cartridges/cartridges-minigames.candidates.jsonl": "miside.cartridges.candidates/1",
    "extracted/data/scenes/scenes.jsonl": "miside.scenes.registry/1",
    "extracted/data/scenes/poi.jsonl": "miside.scenes.poi/1",
    "extracted/data/scenes/spawn-tables.jsonl": "miside.spawn-tables/1",
    "extracted/data/scenes/scene-links.jsonl": "miside.scene-links.lattice/1",
    "extracted/data/scenes/markers.jsonl": "miside.markers.projection/1",
    "extracted/data/documents/world_documents.jsonl": "miside.documents.world_documents/1",
    "extracted/data/documents/profile_documents.jsonl": "miside.documents.profile_documents/1",
    "extracted/data/documents/books.jsonl": "miside.documents.books/1",
    # class-C ids are DECLARED BY THE SPEC (section 2.2), recorded here, never invented into files
    "extracted/data/achievements/achievements.jsonl": "miside.achievements.achievements/1",
    "extracted/data/endings/endings.jsonl": "miside.endings.endings/1",
    "extracted/data/endings/choice_nodes.jsonl": "miside.endings.choice_nodes/1",
    "extracted/data/endings/branch_edges.jsonl": "miside.endings.branch_edges/1",
    "extracted/data/endings/flag_tables.jsonl": "miside.endings.flag_tables/1",
    "extracted/data/dialogue/nodes.jsonl": "miside.dialogue.nodes/1",
    "extracted/data/dialogue/edges.jsonl": "miside.dialogue.edges/1",
    "extracted/data/dialogue/residue-links.jsonl": None,  # single-row sidecar, id not declared
    "extracted/data/dialogue/speakers.json": None,  # single-object sidecar; no schema id on disk or in spec
    "extracted/data/scenes/poi-kinds.json": "miside.scenes.poi-kinds/1",
    **{f"extracted/data/dialogue/graphs/level{n}.json": None for n in
       (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22)},
    # logic-layer schema ids as emitted on disk and pinned by docs/specs/logic-layer.mdx section 5
    "extracted/data/logic/effect_calls.jsonl": "miside.logic.effect_calls/1",
    "extracted/data/logic/flag_instances.jsonl": "miside.logic.flag_instances/1",
    "extracted/data/logic/minigame_tunables.jsonl": "miside.logic.minigame_tunables/1",
    "extracted/data/logic/predicate_records.jsonl": "miside.logic.predicate_records/1",
    # relation-file schema ids as measured on disk (scene--* files ship no schema key)
    **{
        "extracted/relinks/achievement--award-site.jsonl": "miside.relink.achievement-award-site/1",
        "extracted/relinks/achievement--ending.jsonl": "miside.relink.achievement-ending/1",
        "extracted/relinks/cartridge--scene-placement.jsonl": "miside.relink.cartridge-scene-placement/1",
        "extracted/relinks/character--achievement.jsonl": "miside.relink.character-achievement/1",
        "extracted/relinks/character--cartridge.jsonl": "miside.relink.character-cartridge/1",
        "extracted/relinks/character--dialogue-speaker.jsonl": "miside.relink.character-dialogue-speaker/1",
        "extracted/relinks/character--outfit.jsonl": "miside.relink.character-outfit/1",
        "extracted/relinks/character--scene-membership.jsonl": "miside.relink.character-scene/1",
        "extracted/relinks/cloth-site--outfit.jsonl": "miside.relink.cloth-site-outfit/1",
        "extracted/relinks/dialogue-node--encoding-residue.jsonl": "miside.relink.dialogue-node-encoding-residue/1",
        "extracted/relinks/dialogue-speaker-theme--character.jsonl": "miside.relink.dialogue-speaker-theme-character/1",
        "extracted/relinks/document--achievement.jsonl": "miside.documents.relinks.document--achievement/1",
        "extracted/relinks/document--character.jsonl": "miside.documents.relinks.document--character/1",
        "extracted/relinks/document--event-wiring.jsonl": "miside.documents.relinks.document--event-wiring/1",
        "extracted/relinks/document--minigame.jsonl": "miside.documents.relinks.document--minigame/1",
        "extracted/relinks/document--scene-membership.jsonl": "miside.documents.relinks.document--scene-membership/1",
        "extracted/relinks/ending--branch-edge.jsonl": "miside.relink.ending-branch-edge/1",
        "extracted/relinks/minigame--achievement.jsonl": "miside.relink.minigame-achievement/1",
        "extracted/relinks/minigame--choice-condition.jsonl": "miside.relink.minigame-choice-condition/1",
        "extracted/relinks/minigame--outfit-unlock.jsonl": "miside.relink.minigame-outfit-unlock/1",
        "extracted/relinks/minigame--scene-carrier.jsonl": "miside.relink.minigame-scene-carrier/1",
        "extracted/relinks/scene--chapter.jsonl": None,
        "extracted/relinks/scene--dialogue-pool.jsonl": None,
        "extracted/relinks/scene--objective-hints.jsonl": None,
        "extracted/relinks/scene--save-vocabulary.jsonl": None,
    },
}


def split_header(rel: str, cls: str):
    """Return (meta_or_descriptor_dict_or_None, data_rows)."""
    rows = load_jsonl(rel)
    if cls == "A":
        if not rows or "_meta" not in rows[0]:
            raise SystemExit(f"FATAL: {rel} declared class A but first line has no _meta")
        return rows[0]["_meta"], rows[1:]
    if cls == "B":
        if not rows or "row_count" not in rows[0]:
            raise SystemExit(f"FATAL: {rel} declared class B but descriptor lacks row_count")
        return rows[0], rows[1:]
    return None, rows


def measure_header_class(rel: str) -> str:
    """Disk-truth header class for a consumed file."""
    if rel.endswith(".csv"):
        return "CSV"
    raw = read_bytes(rel)
    text = raw.decode("utf-8")
    if not rel.endswith(".jsonl"):
        return "S"
    first = text.split("\n", 1)[0].strip()
    obj = json.loads(first)
    if isinstance(obj, dict) and "_meta" in obj:
        return "A"
    if isinstance(obj, dict) and "row_count" in obj:
        return "B"
    return "C"


def row_count_of(rel: str, cls: str) -> int:
    """Data-unit count used by fingerprints: JSONL data rows; single-object JSON = 1;
    CSV = lines minus header."""
    if cls == "S":
        return 1
    if cls == "CSV":
        return sum(1 for _ in open(rpath(*rel.split("/")), "r", encoding="utf-8")) - 1
    rows = load_jsonl(rel)
    return len(rows) - (1 if cls in ("A", "B") else 0)


# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# JOIN registry declarations (section 4.1 binds text + ownership rulings;
# edge COUNTS are expected values diffed against fresh recounts -- C3)
# --------------------------------------------------------------------------- #

JOIN_DECLS = [
    # stem, binds, expected_edges, direction_handling, anchor_mode, ownership/notes
    ("document--event-wiring", "world_document -> scene event components", 370, "kind-encoded", "endpoints", "documents own document joins (DS-5 J2)"),
    ("document--scene-membership", "world_document -> scene", 354, "kind-encoded", "endpoints", "documents own document joins (DS-5 J2)"),
    ("minigame--scene-carrier", "minigame -> scene-class families", 76, "direction-split", "endpoints", "hard co-presence; 48-dump boilerplate dedupe R4"),
    ("character--achievement", "character -> collectible family", 44, "direction-split", "endpoints", "characters own identity joins (J4, 22 keys)"),
    ("character--cartridge", "character -> save identity", 44, "direction-split", "endpoints", "three-way emission consolidated HERE (J5); mta divergence honest"),
    ("document--achievement", "profile_document -> achievement set", 28, "kind-encoded", "endpoints", "documents own document joins (DS-5 J2)"),
    ("document--character", "profile_document -> subject character", 28, "kind-encoded", "endpoints", "subject_character_id mirror"),
    ("minigame--achievement", "minigame -> award binds UNION type-tag", 20, "direction-split", "endpoints", "3 hard + applesnake logic; J3 null-target partials (ACH-3)"),
    ("scene--dialogue-pool", "scene -> loc dialogue buckets", 40, "direction-split", "endpoints", "hard client pointers"),
    ("scene--objective-hints", "scene -> hint pools", 37, "direction-split", "endpoints", "mirror skew 19/18 is measured"),
    ("scene--save-vocabulary", "scene -> save-point vocab", 19, "forward-only", "endpoints", ""),
    ("scene--chapter", "scene -> chapter-name pointers", 30, "direction-split", "endpoints", ""),
    ("dialogue-speaker-theme--character", "speaker theme -> character", 14, "forward-only", "endpoints", "inferred/curation (DLG-2 alignment); links withheld per Q4"),
    ("character--scene-membership", "character -> scene instances", 12, "direction-split", "endpoints", "fwd 8 / inv 4 + unnamed-instance census (CH-6 counted, never attributed)"),
    ("document--minigame", "world_document -> minigame", 12, "kind-encoded", "endpoints", ""),
    ("achievement--award-site", "achievement -> serialized grant sites", 11, "reverse-index", "id-columns", "hard reverse index"),
    ("character--outfit", "character -> outfit table rows", 4, "forward-only", "endpoints", "Clothes -1 pin in meta"),
    ("minigame--outfit-unlock", "minigame -> ClothCompleted chain", 4, "direction-split", "endpoints", "CAR-4 wiki-only upgrade blocked"),
    ("achievement--ending", "ending -> award achievement", 3, "reverse-index", "id-columns", "hard reverse index"),
    ("cloth-site--outfit", "cloth system -> outfit", 2, "reverse-index", "id-columns", "hard reverse index"),
    ("character--dialogue-speaker", "Names lines 0-2 -> carrier keys", 6, "direction-split", "endpoints", "names only, zero per-line attribution (CH-7 fence)"),
    ("dialogue-node--encoding-residue", "node -> I-3 residue rows", 1, "reverse-index", "id-columns", "hard residue join"),
    ("cartridge--scene-placement", "cartridge -> pickup placement", 0, "meta-only", "meta-only",
     "META-ONLY: authoritative declaration (DS-4 section 1); placements live on cartridges.pickup_ref -- measured absence shipped as data"),
    ("minigame--choice-condition", "minigame -> console choice conditions", 0, "meta-only", "meta-only",
     "META-ONLY: none exist (MA-3)"),
    ("ending--branch-edge", "ending <- branch_edge feeds", 0, "meta-only", "meta-only",
     "META-ONLY: feeds-ending rule matched 0 (MA-8, END-5)"),
]


# DECLARED layer -- what the SPEC fixes and disk cannot tell you:
# schema ids, keys, header classes, closed-enum FIELDS, units/frames, citations.
# Every VALUE (enums, counts, nullability) is measured from the corpus.
# --------------------------------------------------------------------------- #

# entity_type -> declaration
ENTITY_DECLS = {
    "personage": dict(
        artifacts=["extracted/data/characters/personages.jsonl"],
        key="character_id",
        enums=["kind", "status"],
        notes={
            "palette_color1": "float[4] RGBA 0-1, serialized r,g,b,a order; hex = per-channel round(f*255)",
            "palette_color2": "float[4] RGBA 0-1, serialized r,g,b,a order; hex = per-channel round(f*255)",
            "gallery_icon": "PPtr {container,file_id,path_id}; file_id!=0 => external-dependency pointer unresolved today (CH-2)",
            "preview_prefab_key": "verbatim Personages/<Name> string; load-call-site proof pending XC-1 (CH-3)",
            "save_key": '"" allowed (mita-usual, mita-true -- CH-8)',
            "resource_path": '"" allowed (9 player rows)',
            "name_en": "EN convenience copy -- search/API glue, never rendered as non-pivot prose",
        },
        cites=["data-contracts.mdx section 3.1", "contracts/dataset-characters.mdx"],
    ),
    "character_candidate": dict(
        artifacts=["extracted/data/characters/characters.candidates.jsonl"],
        key="candidate_id",
        enums=["kind_class", "status"],
        notes={"evidence": "[] => tier-4 wiki-only, NEVER promoted (CH-9)"},
        cites=["data-contracts.mdx section 3.2", "contracts/dataset-characters.mdx"],
    ),
    "cartridge_candidate": dict(
        artifacts=["extracted/data/cartridges/cartridges-minigames.candidates.jsonl"],
        key="candidate_id",
        enums=["status"],
        notes={},
        cites=["data-contracts.mdx section 3.2", "contracts/dataset-cartridges.mdx"],
    ),
    "cartridge_item": dict(
        artifacts=["extracted/data/cartridges/cartridges.jsonl"],
        key="cartridge_id",
        enums=["family", "status"],
        notes={
            "save_key": "verbatim client identifier; primary (slug additive; letter<->digit hyphen rule)",
            "pickup_ref": "{container,file,field,value}|null; placement authority DS-4 section 1 (CAR-1 null x2)",
            "depicts_character_id": "joins ride C13 anchors only; mta null by namespace-honesty AC-3 (CAR-2)",
            "container_location_binding": "[inferred]-labelled string|null -- label renders with the value or not at all",
        },
        cites=["data-contracts.mdx section 3.3", "contracts/dataset-cartridges.mdx"],
    ),
    "minigame": dict(
        artifacts=["extracted/data/cartridges/minigames.jsonl"],
        key="minigame_id",
        enums=["access_medium", "key_source"],
        notes={
            "name_loc": "pointer|null; only TV rows resolve; CAR-5 absence grep-proven",
            "community_alias": "{alias,source} gloss only, never a key",
            "scoring_derivable": "false x17 -- R1 IL-stub fence; XC-1 unblock",
            "present_but_unreachable": "true x4 -- Peaceful-adjacent lock (CAR-8); visible-locked rendering",
        },
        cites=["data-contracts.mdx section 3.4", "contracts/dataset-cartridges.mdx"],
    ),
    "achievement": dict(
        artifacts=["extracted/data/achievements/achievements.jsonl"],
        key="achievement_id",
        enums=["type_tag", "unlock.predicate_class", "unlock.status", "icon.status", "description.source_role"],
        notes={
            "achievement_id": "= Steam API name, verbatim",
            "display": "map locale->{name,category,line_index}; embedded resolved NAME cells x34 locales (26x34=100%); "
            "deviation scoped to names, NEVER descriptions (Q7)",
            "description": "EN-only Steam capture; XC-11 owner-call hole",
            "icon": "asset_ref stays null while status=pending-export x26 (ACH-1/Q1)",
            "flags": "get_bool_trusted:false x26 -- PERMANENT quarantine, renderer reads neither flag nor derivatives (ACH-5)",
            "unlock": "predicate sites; unverified-behavior renders as community gloss (ACH-2)",
            "joins": "all nullable; chapter_attribution null x26 = XC-2",
            "steam": "ephemeral capture, machine-plane instant; never user-facing freshness",
            "build_id": "INTEGER here (C9: compare stamps canonically as strings)",
        },
        cites=["data-contracts.mdx section 3.5", "contracts/dataset-achievements.mdx"],
    ),
    "ending": dict(
        artifacts=["extracted/data/endings/endings.jsonl"],
        key="ending_id",
        enums=["kind", "award_chain_status", "mode_unlocked.state", "conditions[].status", "windows[].status"],
        notes={
            "mode_unlocked": 'locked-stub cites Menu.jsonl#line_index=130 + dump.cs:206984 (END-1/XC-12)',
            "windows": 'chapter_attribution "[community] ..." labels (END-2 owner-call)',
            "award_chain": "ordered UnityEvent calls",
        },
        cites=["data-contracts.mdx section 3.6", "contracts/dataset-endings.mdx"],
    ),
    "choice_node": dict(
        artifacts=["extracted/data/endings/choice_nodes.jsonl"],
        key="node_id",
        enums=["kind"],
        notes={"active": "null on all rows (measured)"},
        cites=["data-contracts.mdx section 3.6", "contracts/dataset-endings.mdx"],
    ),
    "branch_edge": dict(
        artifacts=["extracted/data/endings/branch_edges.jsonl"],
        key="edge_id",
        enums=["effect_class", "status"],
        notes={
            "feeds_ending": "null x1555 = measured absence MA-8; END-4 dead-reference edges stay dead-reference, never resolved",
        },
        cites=["data-contracts.mdx section 3.6", "contracts/dataset-endings.mdx"],
    ),
    "flag_table": dict(
        artifacts=["extracted/data/endings/flag_tables.jsonl"],
        key="node_id",
        enums=[],
        notes={},
        cites=["data-contracts.mdx section 3.6", "contracts/dataset-endings.mdx"],
    ),
    "dialogue_node": dict(
        artifacts=["extracted/data/dialogue/nodes.jsonl"],
        key="id",
        enums=["kind", "next_resolved"],
        notes={
            "id": "<level>:<Class>#<pathID>",
            "text_ref": "resolve 0-based; line_index = game_index - 1 applied AT EMIT (arithmetic-free resolveLoc, scaffold AC S13)",
            "speaker": "null exactly on the five non-ambient kinds (x129)",
            "next_resolved": "'resolved'/'null'/'unresolved-in-level' on 2745 rows; KEY ABSENT x94 = terminal; "
            "string 'null' = resolved-to-explicit-null (C9 discriminator)",
            "voice_present": "null everywhere (DLG-4, no serialized audio join)",
            "chapter": "null x2839 (DLG-5/XC-2, open question Q3)",
            "build": "INTEGER stamp (C9 canonical comparison)",
        },
        cites=["data-contracts.mdx section 3.7", "contracts/dataset-dialogue.mdx"],
    ),
    "dialogue_edge": dict(
        artifacts=["extracted/data/dialogue/edges.jsonl"],
        key="src+kind+slot+call_index",
        enums=["kind", "resolution"],
        notes={
            "call": "on_finish legs only",
            "resolved_to": "on_finish legs only",
            "anchor_entry": "x142; NO ptr field exists",
            "ledgered_residue": "12 dangling nextText (DLG-6) + 8 unattached hints (DLG-7) + 10 fork slots (DLG-8) -- explicit rows, never dropped",
        },
        cites=["data-contracts.mdx section 3.7", "contracts/dataset-dialogue.mdx"],
    ),
    "encoding_residue": dict(
        artifacts=["extracted/data/dialogue/residue-links.jsonl"],
        key="category+line_index",
        enums=[],
        notes={"residue_ids": "I-3 encoding residue joined onto level14:Dialogue_3DText#5559, per-locale FFFD marking"},
        cites=["data-contracts.mdx sections 2.2/3.7", "contracts/dataset-dialogue.mdx"],
    ),
    "profile_document": dict(
        artifacts=["extracted/data/documents/profile_documents.jsonl"],
        key="document_id",
        enums=["family", "placement_mechanism"],
        notes={
            "subject_character_id": "DS-1 join",
            "placement": "{carrier_class,component_path_id,container}|null x3 (mita-2-d/core/true); authority DS-4 by reference",
            "chapter": "null x14 until XC-2",
            "name_loc/lore_loc": "pointers populated on all 14 rows (DS-5 AC-3)",
        },
        cites=["data-contracts.mdx section 3.8", "contracts/dataset-documents.mdx"],
    ),
    "world_document": dict(
        artifacts=["extracted/data/documents/world_documents.jsonl"],
        key="document_id",
        enums=["family", "text_mechanism"],
        notes={
            "text_mechanism/text_loc": '"unresolved"/null x166 (DOC-1); fill-in-place ruling Q6 -- additive fill rides schema bump',
            "sprite_ptr": "|null; x18 populated, names behind them await XC-4 (DOC-2)",
            "scr_main": "PPtr {file_id,path_id} x5 paperpart-level13-* shared path_id 19195",
        },
        cites=["data-contracts.mdx section 3.8", "contracts/dataset-documents.mdx"],
    ),
    "book": dict(
        artifacts=["extracted/data/documents/books.jsonl"],
        key="book_id",
        enums=[],
        notes={
            "art_per_locale": "map locale->bool; zh-Hans/Hant lack 4 Location19 pages each (DOC-8); 272 cells, 264 true",
            "consumer_scene": "subtree-level ref (DOC-3)",
        },
        cites=["data-contracts.mdx section 3.8", "contracts/dataset-documents.mdx"],
    ),
    "scene": dict(
        artifacts=["extracted/data/scenes/scenes.jsonl"],
        key="scene_id",
        enums=["role"],
        notes={
            "spawn": "World.positionSpawn|null; populated x20 inline&world-assumed -- the ONLY projection-proven cells, SCENE-level never POI",
            "display_name_loc": "null v1 (SCN-8); chapter_name cells x15/null x9 (XC-2)",
            "objective_hints_text_en": "convenience copies -- search/API glue, never rendered as prose on non-pivot pages",
        },
        cites=["data-contracts.mdx section 3.9", "contracts/dataset-scenes.mdx"],
    ),
    "poi": dict(
        artifacts=["extracted/data/scenes/poi.jsonl"],
        key="poi_id",
        enums=["kind", "position.source", "position.space"],
        notes={
            "position": "{source,space,x,y,z} | {source,space,points[]}; points[]{x,y,z,rx,ry,rz}; "
            "serialized Unity transform components; EVERY cell pending-placement, NEVER plotted (XC-3/Q2)",
            "space": "NO fourth value on POI rows; world-assumed occurs only on scene-level spawn; upgrades ride enum bump (Q2 ruled)",
            "class": "23 dump-class values; rulings incl per-class marker_eligible live in poi-kinds.json",
        },
        cites=["data-contracts.mdx section 3.9", "contracts/dataset-scenes.mdx"],
    ),
    "spawn_table": dict(
        artifacts=["extracted/data/scenes/spawn-tables.jsonl"],
        key="spawn_table_id",
        enums=["status"],
        notes={
            "status": '"unresolved-target" x24 mirrors cross-container prefab refs (SCN-7/XC-3)',
            "event_day_label": "DEC enum order -- data, not prose",
            "entries": "prefab_refs file_id>0 = cross-container refs",
        },
        cites=["data-contracts.mdx section 3.9", "contracts/dataset-scenes.mdx"],
    ),
    "scene_link": dict(
        artifacts=["extracted/data/scenes/scene-links.jsonl"],
        key="from_level+to_sub_scene+via_component+path_id+edge_kind",
        enums=["edge_kind"],
        notes={
            "resolves": "bool; key-absent x16 (15 chapter_name rows + the ledger row)",
            "ledger_row": "the level18 row IS the lattice measured-absence ledger row (SCN-10)",
        },
        cites=["data-contracts.mdx section 3.9", "contracts/dataset-scenes.mdx"],
    ),
    "marker": dict(
        artifacts=["extracted/data/scenes/markers.jsonl"],
        key="marker_id",
        enums=["kind", "entity_kind", "icon.fallback_state", "position.source", "position.status",
               "placement.mechanism"],
        notes={
            "row_v2": "XC-5 projection rerun LANDED (map-viewer M0): typed marker rows replaced the v0 "
            "_meta-only posture; shape per map-viewer section 4.1 -- marker_id/poi_id/layer/kind + routed "
            "entity_kind/entity_slug + icon/position/placement/links",
            "icon": 'source null with fallback_state:"named-explicit-missing" on every row this build -- '
            "named explicit-missing state until art lands, never a blank cell",
            "position": 'status "awaiting-transform-stage"|"scene-granular" this build; "projected" arrives '
            "with S9 (projectedCoordinates agreement is map-viewer AC MV-2)",
            "entity_kind": "ROUTED registry segment == ENTITY_KINDS key; the emitter writes final "
            "page_url/focus_url segments so the frontend formats, never maps, vocabularies",
        },
        cites=["data-contracts.mdx section 3.9", "docs/specs/map-viewer.mdx sections 3/4.1"],
    ),
    "speaker_theme": dict(
        artifacts=["extracted/data/dialogue/speakers.json"],
        key="theme",
        enums=["entity.status"],
        notes={
            "curated_mapping": "x14 themes: 9 provisional-pending-ds1 (DLG-2) + 5 pending-curation (DLG-1); "
            "entity links WITHHELD for both statuses until owner rulings (Q4 ruled intentionally open)",
        },
        cites=["data-contracts.mdx section 3.7", "contracts/dataset-dialogue.mdx"],
    ),
    "poi_kind": dict(
        artifacts=["extracted/data/scenes/poi-kinds.json"],
        key="class",
        enums=["kind"],
        notes={"classes": "one ruling per dump class; marker_eligible=false excluded from marker projection (v0: all, pending owners)"},
        cites=["data-contracts.mdx section 3.9", "contracts/dataset-scenes.mdx"],
    ),
    "dialogue_graph": dict(
        artifacts=[f"extracted/data/dialogue/graphs/level{n}.json" for n in
                   (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22)],
        key="level",
        enums=[],
        notes={
            "derived_projection": "per-level node/edge view of dialogue_node/dialogue_edge; no level18 = measured absence SCN-10; "
            "shape owned by the dialogue emitter -- consumers join through nodes/edges, not graphs",
        },
        cites=["data-contracts.mdx sections 2.2/3.7"],
    ),
    "relink_edge": dict(
        artifacts=[f"extracted/relinks/{stem}.jsonl" for stem, *_ in JOIN_DECLS],
        key=None,
        schema_id=None,
        enums=["direction", "kind"],
        notes={
            "from/to": "typed anchors, grammar FAMILY-SPECIFIC (see joins.json anchor_grammar); JSON-null x25 vs "
            "anchor-less x17 edges are DISTINCT empty states (spec section 4.2)",
            "direction": "forward|inverse on character-/minigame-/scene- families + speaker-theme family; document "
            "families encode direction as kind; reverse-index families carry neither",
            "mechanism": "FREE TEXT, not a closed enum {hard x1024, logic x104, inferred x20, 'scrMain PPtr (hard)' x10, absent x1}",
            "status": "FREE TEXT, not a closed enum {modeled x1043, partial x73 (44 with non-empty missing_fields), "
            "provisional-pending-ds1 x9, pending-curation x5, 'scrMain PPtr (hard)' x10, inferred x2, absent x17}",
            "row_count": "= total join edges (1159); per-family counts live in joins.json",
        },
        cites=["data-contracts.mdx section 3.10"],
    ),
    # ---- logic-layer family (docs/specs/logic-layer.mdx, ACCEPTED; emitter B-LL2 LG1-LG4) -----
    # F-CT2 reconciliation EXTEND branch: the logic lane's hand-inserted registry blocks carried
    # clear provenance (spec + input-manifest sha256 pins, all outputs verified against them),
    # so build_entities generates these types from the same rows the emitter pinned.
    "effect_call": dict(
        artifacts=["extracted/data/logic/effect_calls.jsonl"],
        key=None,
        enums=["effect_class", "tier"],
        notes={
            "edge_id": "identifies the serialized call site (logic:call:<container>:<file>:"
            "<host_path_id|x>:<field_path>:<call_index>); DELIBERATELY NOT a unique row key on this "
            "build -- one call can emit several rows (per-effect_class census grain; duplicate groups "
            "measured on disk), so join discipline rides AC-L1b key K (event_field/option_index/"
            "call_index + target + args-tuple), never edge_id uniqueness",
            "tier": "A/B sweep assignment ORTHOGONAL to effect_class -- both axes recorded per row "
            "(LG2/A-LL1-F-1); internal_only:true exactly on tier-B rows, which never surface through LG3",
            "census_accounting": "_meta per-effect_class totals + tier_a/tier_b counts additive over ALL "
            "persistent calls corpus-wide (AC-L1c)",
            "dead-reference": 'serialized m_Target pathID == 0 residue (END-4); index-only forever '
            "(section 7 item 1)",
        },
        cites=["docs/specs/logic-layer.mdx sections 4-LG2/5/7", "docs/specs/logic-layer.mdx AC-L1b/L1c/L2"],
    ),
    "flag_instance": dict(
        artifacts=["extracted/data/logic/flag_instances.jsonl"],
        key="flag_id",
        enums=["component", "identity_status"],
        notes={
            "object_path_id": "filename suffix authoritative where present; bare-named single-instance "
            "dumps resolve identity from the harvest instance inventory or stay null WITH an "
            "identity-ledger row (LG1) -- never fabricated",
            "memory_branches": "[{branch_ordinal,if_int,persistent calls}] -- superset of "
            "endings/flag_tables.jsonl, reconciling as a projection (AC-L2)",
            "writers/readers": "tier-A LG2 edge_ids whose target PPtr resolves ONLY through the SERIALIZED "
            "space (inventory_object_path_id, unique same-class pairing) -- suffix ids never adjudicate "
            "a reference (A-LL2 ruling A; either-id-space fallback deleted, F-LL4)",
            "id_spaces": "serialized component-path-id space vs filename-suffix handle space: "
            "mostly-disjoint -- non-zero numeric coincidence treated as collision (A-LL2 ruling C; "
            "measured 15.23% corpus-wide, Events_* 21.5%) -- suffix ids identify and display rows, "
            "PPtr references resolve exclusively via serialized space under unique pairing; dual-space "
            "hits are ledgered, never resolved",
        },
        cites=["docs/specs/logic-layer.mdx sections 4-LG1/5", "docs/specs/logic-layer.mdx AC-L2"],
    ),
    "minigame_tunable": dict(
        artifacts=["extracted/data/logic/minigame_tunables.jsonl"],
        key="tunable_id",
        enums=["kind", "rule_status"],
        notes={
            "rule_status": '"not-a-threshold" on EVERY row -- the AC-L4 scoring fence stands '
            "(minigames.scoring_derivable:false untouched); envelopes only, win thresholds NOT STATIC",
            "declared_range": "attribute-declared [Range] bounds from dump.cs; serialized_value may be "
            "null when the dump carries the default only",
            "internal_only": "tunables are section-7 internal rows -- envelope-labeled or not surfaced",
        },
        cites=["docs/specs/logic-layer.mdx sections 4-LG4/5/7", "docs/specs/logic-layer.mdx AC-L4"],
    ),
    "predicate_record": dict(
        artifacts=["extracted/data/logic/predicate_records.jsonl"],
        key="predicate_id",
        enums=["subject.kind", "condition.expression_class", "polarity.evidence_class", "status"],
        notes={
            "polarity": "value:null legal only with fail-closed-unknown or pure access points; "
            "'negative' reserved -- zero rows this build (AC-L3 checker recompute)",
            "evidence_discriminator": "a path under harvest/mb-dump/ or il2cpp/dump.cs is a SITE locator; "
            "[community]/wiki/ledger refs are citations -- inferred rows MUST carry non-empty citations",
            "status_enum": "proven-hard|proven-structure|community|locked-stub|unknown-fail-closed",
            "internal_only": "set per join outcome (section 7 item 3), never per class",
        },
        cites=["docs/specs/logic-layer.mdx sections 3/4-LG3/5/6", "docs/specs/logic-layer.mdx AC-L3"],
    ),
}

TOTAL_EDGES_EXPECTED = 1159

# the 25 canonical relation files (class A: _meta anchor line + edge rows)
EXPECTED_HEADER_CLASSES.update(
    {f"extracted/relinks/{stem}.jsonl": "A" for stem, *_ in JOIN_DECLS})

# relation-file schema ids as measured on disk (scene--* ship no schema key)
RELATION_SCHEMA_IDS = {
    stem: DECLARED_SCHEMA_IDS[f"extracted/relinks/{stem}.jsonl"] for stem, *_ in JOIN_DECLS
}

# --------------------------------------------------------------------------- #
# availability declarations (section 5 -- rules pinned by the spec, cells measured)
# --------------------------------------------------------------------------- #

AVAILABILITY_DECLS = {
    "authority": "extracted/relinks/locale_availability.jsonl",
    "locale_key_domain": (
        "client dir name (34 distinct measured, e.g. Portugues-Brasil with accent, Arabic (Egyptian), "
        "Pre-revolutionaryRussian); consumers join through the pinned code-mapping; a ledger locale with "
        "no mapping row fails the build"
    ),
    "rtl": {"dir": "rtl", "locales": ["ar", "ar-EG"]},
    "aliases": [
        {"alias": "ru-x-prerev", "target": "ru", "scope": "chrome-only"},
        {"alias": "ar-EG", "target": "ar", "scope": "chrome-only"},
    ],
    "alias_law": "exactly two aliases exist and both are chrome-only; game text is NEVER aliased; any further alias is a defect",
    "fallback_chain": [
        "resolve the pointer 0-based in locale L's category (arithmetic-free; emit-time offsets already applied)",
        "category absent or cell filler -> render the localized not-yet-translated filler",
        "contentless is NOT missing -- a 0-byte shell renders filler like any unfilled cell",
        "a page is omitted ONLY when the entity has ZERO strings in that locale -- driven solely by ledger membership",
    ],
}

# --------------------------------------------------------------------------- #
# stub vocabulary (section 7) -- markers AS EMITTED + consumer obligations.
# pinned_counts: {carrier_key: expected occurrences} verified against disk.
# --------------------------------------------------------------------------- #

STUB_VOCAB = [
    dict(
        id="missing_fields",
        marker='missing_fields: ["<field> - <reason>", ...]',
        where="cartridges, candidates, partial relink rows",
        obligation="render the named explicit-missing state; never backfill",
        pinned_counts={"relink_partial_rows_nonempty": 44},
    ),
    dict(
        id="registered-unresolved-pickup",
        marker='status:"registered-unresolved-pickup"',
        where="cartridges x2",
        obligation="tier-2 row: no pickup coordinates claimed (CAR-1)",
        pinned_counts={"cartridge_item.status": 2},
    ),
    dict(
        id="pending-export",
        marker='status:"pending-export"',
        where="achievement icon x26",
        obligation="named explicit-missing icon slot; interim official_url may feed OG only (ACH-1/Q1)",
        pinned_counts={"achievement.icon.status": 26},
    ),
    dict(
        id="unverified-behavior",
        marker='unlock.status:"unverified-behavior"',
        where="15/26 predicates (ACH-2), safe windows (END-2)",
        obligation="label as community/unverified gloss; never stated as game fact",
        pinned_counts={"achievement.unlock.status": 15},
    ),
    dict(
        id="get_bool_trusted-false",
        marker='flags.get_bool_trusted:false',
        where="all 26 achievement rows",
        obligation="HARD quarantine -- renderer reads neither the flag nor anything derived from it (ACH-5)",
        pinned_counts={"achievement.flags.get_bool_trusted": 26},
    ),
    dict(
        id="present_but_unreachable",
        marker='present_but_unreachable:true',
        where="minigames x4",
        obligation="visible-locked rendering, never dropped, never speculated (CAR-8)",
        pinned_counts={"minigame.present_but_unreachable": 4},
    ),
    dict(
        id="scoring_derivable-false",
        marker='scoring_derivable:false',
        where="minigames x17",
        obligation="no thresholds rendered; rule_evidence strings only (CAR-3/R1)",
        pinned_counts={"minigame.scoring_derivable_false": 17},
    ),
    dict(
        id="locked-stub",
        marker='kind:"mode-stub" / state:"locked-stub"',
        where="ending peaceful (kind mode-stub x1) + conditions-met carries the same locked-stub "
        "mode_unlocked -- state measures x2 on disk",
        obligation="visible-locked stub with cited evidence (END-1)",
        pinned_counts={"ending.kind_mode_stub": 1, "ending.mode_unlocked.state_locked_stub": 2},
    ),
    dict(
        id="dead-reference",
        marker='effect_class:"dead-reference"',
        where="branch_edges x3",
        obligation="ledgered residue; never silently omitted, never resolved (END-4)",
        pinned_counts={"branch_edge.effect_class": 3},
    ),
    dict(
        id="text_mechanism-unresolved",
        marker='text_mechanism:"unresolved"',
        where="world_documents x166",
        obligation="interactable+wiring surfaces only; zero invented prose (DOC-1)",
        pinned_counts={"world_document.text_mechanism": 166},
    ),
    dict(
        id="pending-curation",
        marker='entity.status:"pending-curation" / "provisional-pending-ds1"',
        where="speakers.json 5 + 9 themes",
        obligation="entity links withheld until slugs are ruled (DLG-1/DLG-2/Q4)",
        pinned_counts={"speaker_theme.pending_curation": 5, "speaker_theme.provisional_pending_ds1": 9},
    ),
    dict(
        id="bracket-labels",
        marker="[inferred] / [community]",
        where="container_location_binding x21, windows.chapter_attribution (END-2); preview_prefab_key carries NO label",
        obligation="the label renders with the value or the value does not render",
        pinned_counts={"cartridge.container_location_binding_inferred": 21},
    ),
    dict(
        id="unverified-columns",
        marker="_meta.unverified_columns / header notes",
        where="class-A/B headers",
        obligation="consumers inherit the caveat; checkers enforce",
        pinned_counts={"personage._meta.unverified_columns": 1},
    ),
]

# missingdata.md coverage map: EVERY ledger ID -> carriers (typed marker ids or documented gaps).
# kind: marker = a STUB_VOCAB/measured-marker id; gap = documented off-corpus surface (evidence path must exist).
LEDGER_COVERAGE = {
    "XC-1": [("gap", None, ["docs/specs/data-contracts.mdx"]), ("marker", "scoring_derivable-false", None),
             ("marker", "unverified-columns", None)],
    "XC-2": [("marker", "chapter-null-columns", None)],
    "XC-3": [("marker", "pptr-unresolved-position", None), ("marker", "unresolved-target-spawn", None)],
    "XC-4": [("gap", None, ["extracted/data/documents/README.md"])],
    "XC-5": [("marker", "marker-projection-v1", None)],
    "XC-6": [("gap", None, ["extracted/relinks/_assembly-provenance.jsonl"])],
    "XC-7": [("gap", None, ["extracted/relinks/_assembly-provenance.jsonl"])],
    "XC-8": [("gap", None, ["extracted/PROOF.md"])],
    "XC-9": [("gap", None, ["extracted/data/missingdata.md"])],
    "XC-10": [("marker", "build-stamps", None)],
    "XC-11": [("marker", "steam-description-en-only", None)],
    "XC-12": [("marker", "locked-stub", None), ("marker", "present_but_unreachable", None)],
    "CH-1": [("gap", None, ["extracted/data/characters/README.md"])],
    "CH-2": [("marker", "unresolved-external-pointer", None)],
    "CH-3": [("marker", "unverified-columns", None)],
    "CH-4": [("gap", None, ["extracted/relinks/character--outfit.jsonl"])],
    "CH-5": [("gap", None, ["extracted/data/characters/README.md"])],
    "CH-6": [("marker", "unnamed-instance-census", None)],
    "CH-7": [("marker", "missing_fields", None)],
    "CH-8": [("marker", "empty-save-key", None)],
    "CH-9": [("marker", "tier4-empty-evidence", None)],
    "ACH-1": [("marker", "pending-export", None)],
    "ACH-2": [("marker", "unverified-behavior", None)],
    "ACH-3": [("marker", "missing_fields", None)],
    "ACH-4": [("marker", "chapter-null-columns", None)],
    "ACH-5": [("marker", "get_bool_trusted-false", None)],
    "ACH-6": [("marker", "inferred-append-only", None)],
    "ACH-7": [("marker", "steam-machine-plane", None)],
    "END-1": [("marker", "locked-stub", None)],
    "END-2": [("marker", "bracket-labels", None), ("marker", "unverified-behavior", None)],
    "END-3": [("marker", "unverified-behavior", None)],
    "END-4": [("marker", "dead-reference", None)],
    "END-5": [("marker", "feeds-ending-null", None)],
    "END-6": [("gap", None, ["extracted/data/endings/emit-ledger.jsonl"])],
    "DLG-1": [("marker", "pending-curation", None)],
    "DLG-2": [("marker", "pending-curation", None)],
    "DLG-3": [("marker", "speaker-null-structural", None)],
    "DLG-4": [("marker", "voice-present-null", None)],
    "DLG-5": [("marker", "chapter-null-columns", None)],
    "DLG-6": [("marker", "dangling-edge-ledger", None)],
    "DLG-7": [("marker", "dangling-edge-ledger", None)],
    "DLG-8": [("marker", "fork-slot-text-keyed", None)],
    "DLG-9": [("marker", "encoding-residue-fffd", None)],
    "DLG-10": [("marker", "locale-parity-ledger", None)],
    "CAR-1": [("marker", "registered-unresolved-pickup", None)],
    "CAR-2": [("marker", "missing_fields", None)],
    "CAR-3": [("marker", "scoring_derivable-false", None)],
    "CAR-4": [("marker", "missing_fields", None)],
    "CAR-5": [("marker", "minigame-name-loc-null", None)],
    "CAR-6": [("gap", None, ["extracted/data/cartridges/README.md"])],
    "CAR-7": [("marker", "tier4-empty-evidence", None)],
    "CAR-8": [("marker", "present_but_unreachable", None)],
    "CAR-9": [("marker", "locale-parity-ledger", None)],
    "DOC-1": [("marker", "text_mechanism-unresolved", None)],
    "DOC-2": [("gap", None, ["extracted/data/documents/README.md"])],
    "DOC-3": [("gap", None, ["extracted/data/documents/README.md"])],
    "DOC-4": [("marker", "chapter-null-columns", None)],
    "DOC-5": [("marker", "missing_fields", None)],
    "DOC-6": [("marker", "unverified-behavior", None)],
    "DOC-7": [("gap", None, ["extracted/data/documents/README.md"])],
    "DOC-8": [("marker", "book-art-per-locale-false", None)],
    "SCN-1": [("marker", "marker-projection-v1", None)],
    "SCN-2": [("marker", "pptr-unresolved-position", None)],
    "SCN-3": [("marker", "curation-ruling-required", None)],
    "SCN-4": [("marker", "registered-unresolved-pickup", None)],
    "SCN-5": [("gap", None, ["extracted/data/scenes/README.md"])],
    "SCN-6": [("gap", None, ["extracted/data/scenes/README.md"])],
    "SCN-7": [("marker", "unresolved-target-spawn", None)],
    "SCN-8": [("marker", "display-name-loc-null", None)],
    "SCN-9": [("marker", "contentless-cell", None)],
    "SCN-10": [("marker", "scene-link-ledger-row", None)],
    "SCN-11": [("marker", "role-unbound-level23", None)],
    "DOCX-1": [("gap", None, ["extracted/data/scenes/README.md"])],
    "DOCX-2": [("gap", None, ["docs/research/build-log.mdx"])],
    "DOCX-3": [("marker", "staging-copies-parked", None)],
    "MA-1": [("gap", None, ["extracted/data/dialogue/_ledger/build-meta.json"])],
    "MA-2": [("marker", "contentless-cell", None)],
    "MA-3": [("marker", "meta-only-family", None)],
    "MA-4": [("gap", None, ["extracted/data/documents/README.md"])],
    "MA-5": [("gap", None, ["extracted/data/documents/README.md"])],
    "MA-6": [("gap", None, ["extracted/data/documents/README.md"])],
    "MA-7": [("gap", None, ["extracted/data/documents/README.md"])],
    "MA-8": [("marker", "feeds-ending-null", None)],
}

MEASURED_MARKERS = {
    # extended markers referenced by LEDGER_COVERAGE beyond the section-7 table;
    # each: (probe key, description, minimum expected occurrences)
    "chapter-null-columns": ("chapter columns null until XC-2 (profiles x14, dialogue x2839, achievements x26)", 100),
    "pptr-unresolved-position": ('poi.position.source:"pptr-unresolved" (SCN-2)', 76),
    "unresolved-target-spawn": ('spawn_table.status:"unresolved-target" (SCN-7)', 24),
    "marker-projection-v1": (
        "markers.jsonl ships typed marker rows keyed by marker_id -- XC-5 projection rerun LANDED "
        "(map-viewer M0 section 4.1; supersedes the v0 _meta-only posture)", 60),
    "build-stamps": ("buildId stamps across artifacts enable drift watch (XC-10)", 1),
    "steam-description-en-only": ("achievement descriptions EN-only official-feed captures (XC-11)", 26),
    "unresolved-external-pointer": ("gallery_icon external pointer file_id 2 / path_id 276 shared by players (CH-2)", 1),
    "unnamed-instance-census": ("character--scene-membership instance censuses counted, never attributed (CH-6)", 1),
    "empty-save-key": ('personage.save_key "" x2 (CH-8)', 2),
    "tier4-empty-evidence": ("candidates with evidence [] -- tier-4 wiki-only, never promoted (CH-9/CAR-7)", 16),
    "feeds-ending-null": ("branch_edge.feeds_ending null x1555 (MA-8/END-5)", 1555),
    "speaker-null-structural": ("dialogue_node.speaker null exactly on the five non-ambient kinds (DLG-3)", 129),
    "voice-present-null": ("dialogue_node.voice_present null everywhere (DLG-4)", 2839),
    "dangling-edge-ledger": ("dialogue _ledger dangling/unattached explicit residue rows (DLG-6/DLG-7)", 12),
    "fork-slot-text-keyed": ('dialogue_edge resolution "text-keyed-no-node-carrier" fork slots (DLG-8)', 10),
    "encoding-residue-fffd": ("residue-links.jsonl I-3 FFFD rows joined onto nodes (DLG-9)", 1),
    "locale-parity-ledger": ("dialogue _ledger locale-parity tail-delta rows (DLG-10/CAR-9)", 4),
    "curation-ruling-required": ("flashes:mta namespace divergence carried in the identity adjudication record (SCN-3)", 1),
    "display-name-loc-null": ("scene.display_name_loc null v1 (SCN-8)", 24),
    "contentless-cell": ("availability contentless cells render filler, never alarm (MA-2/SCN-9)", 9),
    "scene-link-ledger-row": ("scene_links edge_kind ledger row = level18 measured absence (SCN-10)", 1),
    "role-unbound-level23": ('scene role "unbound" on level23 (SCN-11)', 1),
    "book-art-per-locale-false": ("book art_per_locale false cells (DOC-8)", 8),
    "staging-copies-parked": ("_assembly-provenance adjudication excludes DS-6 restatement from canonical tree (DOCX-3)", 1),
    "meta-only-family": ("meta-only relation files ARE the measured answer (MA-3)", 1),
    "minigame-name-loc-null": ("minigame name_loc null outside TV rows (CAR-5)", 15),
    "inferred-append-only": ("achievement registry_index==line_translate [inferred] append-only (ACH-6)", 26),
    "steam-machine-plane": ("steam.captured_at_machine_plane true x26 (ACH-7)", 26),
}


# --------------------------------------------------------------------------- #
# measurement engine
# --------------------------------------------------------------------------- #

TYPE_NAMES = {bool: "boolean", int: "integer", float: "number", str: "string",
              dict: "object", list: "array"}


def jtype(v) -> str:
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    return TYPE_NAMES.get(type(v), "unknown")


def merge_types(types: set) -> str:
    if types == {"integer", "number"} or types == {"number", "integer"}:
        return "number"
    return "|".join(sorted(types)) if types else "unknown"


def get_path(row, dotted: str):
    """Resolve 'a.b' / 'a[].b' paths; returns (found, value)."""
    cur = [row]
    for part in dotted.replace("[]", ".").split("."):
        nxt = []
        for obj in cur:
            if isinstance(obj, dict) and part in obj:
                v = obj[part]
                if isinstance(v, list):
                    nxt.extend(v)
                else:
                    nxt.append(v)
        cur = nxt
        if not cur:
            return False, None
    return True, cur[0] if len(cur) == 1 else cur


def describe_object_field(samples: list, depth: int = 0) -> dict:
    """Sub-shape of an object-valued field (one measured level; maps collapse)."""
    keys: Counter = Counter()
    for s in samples:
        if isinstance(s, dict):
            keys.update(s.keys())
    n = len(samples)
    info: dict = {}
    if not keys:
        return info
    if len(keys) > 12:
        # uniform map (e.g. locale-keyed) -> summarize value shape instead of enumerating keys
        shapes: Counter = Counter()
        for s in samples:
            if isinstance(s, dict):
                inner = tuple(sorted((k, jtype(v)) for k, v in s.items()))
                shapes[inner] += 1
        if len(shapes) == 1:
            shape = next(iter(shapes))
            info["map_value_shape"] = {k: t for k, t in shape}
            info["map_note"] = "uniform keyed map; keys enumerated in data, not restated here"
            return info
    sub = {}
    for k in sorted(keys):
        vals = [s[k] for s in samples if isinstance(s, dict) and k in s and s[k] is not None]
        types = {jtype(v) for v in vals}
        entry: dict = {"type": merge_types(types), "nullable": any(isinstance(s, dict) and (k not in s or s[k] is None) for s in samples)}
        if depth < 1 and types == {"object"}:
            inner = describe_object_field([v for v in vals if isinstance(v, dict)], depth + 1)
            if inner:
                entry["subfields"] = inner
        if depth < 1 and types == {"array"}:
            elems = [e for v in vals for e in (v if isinstance(v, list) else [])]
            if elems and all(isinstance(e, dict) for e in elems):
                ef = describe_object_field(elems, depth + 1)
                if ef:
                    entry["element_fields"] = ef
            elif elems:
                entry["element_type"] = merge_types({jtype(e) for e in elems})
        sub[k] = entry
    info["subfields"] = sub
    return info


def measure_fields(rows: list) -> dict:
    """Complete top-level field inventory measured over ALL rows (C2 full scan)."""
    names: Counter = Counter()
    for r in rows:
        names.update(r.keys())
    fields = {}
    for name in sorted(names):
        present = [r[name] for r in rows if name in r]
        non_null = [v for v in present if v is not None]
        null_rows = sum(1 for v in present if v is None) + sum(1 for r in rows if name not in r)
        types = {jtype(v) for v in non_null}
        entry: dict = {"type": merge_types(types), "nullable": null_rows > 0}
        if null_rows > 0:
            entry["absent_or_null_rows"] = null_rows
        if types == {"object"}:
            shape = describe_object_field(non_null)
            entry.update(shape)
        elif types == {"array"}:
            elems = [e for v in non_null for e in (v if isinstance(v, list) else [])]
            if elems:
                etypes = {jtype(e) for e in elems}
                entry["element_type"] = merge_types(etypes)
                if etypes == {"object"}:
                    ef = describe_object_field(elems)
                    if ef.get("subfields"):
                        entry["element_fields"] = ef["subfields"]
        fields[name] = entry
    return fields


def measure_enums(rows: list, enum_paths: list) -> dict:
    """Measured value sets for declared enum fields (values come from disk only)."""
    enums = {}
    for path in enum_paths:
        values: Counter = Counter()
        for r in rows:
            found, v = get_path(r, path)
            if found and v is not None and not isinstance(v, (dict, list)):
                values[str(v)] += 1
        if values:
            enums[path] = dict(sorted(values.items()))
    return enums


def stamp_keys(rows: list) -> list:
    keys = set()
    for r in rows[:50]:
        for k in ("build_id", "version_label", "build"):
            if k in r:
                keys.add(k)
    return sorted(keys)


def stamp_style(keys: list) -> str:
    ks = set(keys)
    if {"build_id", "version_label"} <= ks:
        return "build_id+version_label"
    if "build_id" in ks:
        return "bare build_id"
    if "build" in ks:
        return "bare build"
    return "none (staleness rides fingerprints)"


# --------------------------------------------------------------------------- #
# registry builders
# --------------------------------------------------------------------------- #


def entity_row_pool(etype: str, decl: dict):
    """ALL data rows of an entity type POOLED across every contributing artifact, in fixed
    declaration order. F1/vB fix: field types, nullability and enum counts are corpus-wide
    measurements over this pool -- never last-artifact-wins merges of per-file inventories.
    Returns (rows, row_total, stamp_styles)."""
    pool: list = []
    row_total = 0
    styles: set = set()
    for rel in decl["artifacts"]:
        cls = EXPECTED_HEADER_CLASSES[rel]
        if cls == "S":
            doc = load_json(rel)
            # curated_mapping / classes arrays are the data planes of single-object sidecars
            arr = doc.get("curated_mapping") if "curated_mapping" in doc else doc.get("classes")
            if arr is None and etype == "dialogue_graph":
                row_total += 1  # one graph document per file; no measurable data plane by design
                continue
            if not isinstance(arr, list):
                raise SystemExit(f"FATAL: {rel}: no data plane array found for {etype}")
            row_total += len(arr)
            pool.extend(arr)
            continue
        _, rows = split_header(rel, cls)
        row_total += len(rows)
        pool.extend(rows)
        styles.add(stamp_style(stamp_keys(rows)))
    return pool, row_total, styles


def build_entities(pin: dict) -> dict:
    entity_types = {}
    for etype, decl in ENTITY_DECLS.items():
        pool, row_total, styles = entity_row_pool(etype, decl)
        # ONE measurement over the pooled rows (F1/vB): multi-artifact types (relink_edge's 25
        # files) now report unioned types/nullability/enum distributions, matching _meta.notation.
        fields = measure_fields(pool)
        enums = measure_enums(pool, decl["enums"])
        # declared annotations layered over measured inventory (never inventing fields)
        for fname, note in decl["notes"].items():
            target = fname.split("/")[0]
            if target in fields:
                fields[target]["note"] = note
        # key uniqueness gate (full scan over every contributing artifact)
        if decl["key"] and row_total:
            keycols = decl["key"].split("+")
            seen: Counter = Counter()
            for rel in decl["artifacts"]:
                cls = EXPECTED_HEADER_CLASSES[rel]
                if cls == "S":
                    doc = load_json(rel)
                    arr = doc.get("curated_mapping") or doc.get("classes") or []
                    rows = arr
                else:
                    _, rows = split_header(rel, cls)
                for r in rows:
                    try:
                        seen[tuple(str(r[c]) for c in keycols)] += 1
                    except KeyError:
                        raise SystemExit(f"FATAL: {etype}: key column missing on a row of {rel}")
            dupes = [k for k, v in seen.items() if v > 1]
            if dupes:
                raise SystemExit(f"FATAL: {etype}: duplicate keys {dupes[:3]}")
        artifacts = decl["artifacts"]
        entry = {
            "artifacts": artifacts,
            "citations": decl["cites"],
            "enums": enums,
            "fields": fields,
            "header_class": EXPECTED_HEADER_CLASSES[artifacts[0]],
            "key": decl["key"],
            "notes": {k: v for k, v in decl["notes"].items()},
            "row_count": row_total,
            "row_stamp_style": "; ".join(sorted(styles)) if styles else "none (staleness rides fingerprints)",
            "schema_id": decl.get("schema_id", DECLARED_SCHEMA_IDS[artifacts[0]]),
        }
        entity_types[etype] = entry
    return {
        "_meta": {
            "consumes_never_derives": "frontend consumes these typed contracts; runtime derivation beyond the "
            "pinned resolution rules is banned (spec section 1)",
            "generated_by": "contracts/check_contracts.py generate",
            "notation": "nullable=true means the field is absent or JSON-null on >=1 measured row POOLED OVER "
            "EVERY contributing artifact of the entity type; absent_or_null_rows counts them corpus-wide; enums "
            "are MEASURED value->count sets pooled over all data rows of all artifacts (never last-file-wins)",
            "spec": SPEC_PATH,
            "build_pin": pin,
        },
        "entity_types": entity_types,
    }


def anchor_form(v: str) -> str:
    return v.split(":", 1)[0] + ":" if ":" in v else "<bare>"


def build_joins(pin: dict) -> dict:
    families = {}
    forms_global: Counter = Counter()
    census = {"anchorless_edges": 0, "edges_with_endpoints": 0, "null_endpoints": 0,
              "string_endpoints": 0, "total_edges": 0}
    for stem, binds, expected, direction_handling, anchor_mode, note in JOIN_DECLS:
        rel = f"extracted/relinks/{stem}.jsonl"
        raw = load_jsonl(rel)
        rows = [r for r in raw if "_meta" not in r]
        head_schema = raw[0]["_meta"].get("schema") if raw and "_meta" in raw[0] else None
        if head_schema != RELATION_SCHEMA_IDS[stem]:
            raise SystemExit(f"FATAL: {stem} schema drift: disk {head_schema!r} != declared {RELATION_SCHEMA_IDS[stem]!r}")
        grammar: dict = {"from": [], "to": []}
        dirs: Counter = Counter()
        kinds: Counter = Counter()
        mech: Counter = Counter()
        stat: Counter = Counter()
        mf_nonempty = 0
        nulls: Counter = Counter()
        fam_strings = 0
        for r in rows:
            d = r.get("direction")
            if d is not None:
                dirs[d] += 1  # families whose rows legitimately lack direction get NO zero-count entry (vB-F5)
            if r.get("kind") is not None:
                kinds[str(r["kind"])] += 1
            if "mechanism" in r:
                mech[str(r["mechanism"])] += 1
            else:
                mech["<absent>"] += 1
            if "status" in r:
                stat[str(r["status"])] += 1
            else:
                stat["<absent>"] += 1
            if r.get("missing_fields"):
                mf_nonempty += 1
            for side in ("from", "to"):
                if side not in r:
                    continue
                v = r[side]
                if v is None:
                    nulls[side] += 1
                    census["null_endpoints"] += 1
                else:
                    form = anchor_form(str(v))
                    forms_global[form] += 1
                    fam_strings += 1
                    if form not in grammar[side]:
                        grammar[side].append(form)
        if anchor_mode == "endpoints":
            census["edges_with_endpoints"] += len(rows)
            census["string_endpoints"] += fam_strings
        else:
            census["anchorless_edges"] += len(rows)
            census["absent_slots"] = census.get("absent_slots", 0) + 2 * len(rows)
        census["total_edges"] += len(rows)
        fam = {
            "anchor_mode": anchor_mode,
            "binds": binds,
            "direction_handling": direction_handling,
            "edge_count_measured": len(rows),
            "edge_count_expected": expected,
            "file": rel,
            "mechanisms": dict(sorted(mech.items())),
            "missing_fields_rows_nonempty": mf_nonempty,
            "notes": note,
            "schema_id": head_schema,
            "statuses": dict(sorted(stat.items())),
        }
        if dirs:
            fam["directions"] = dict(sorted((str(k), v) for k, v in dirs.items()))
        if kinds:
            fam["kinds"] = dict(sorted(kinds.items()))
        if nulls:
            fam["null_anchors"] = dict(sorted(nulls.items()))
        if anchor_mode == "endpoints":
            fam["anchor_grammar"] = {k: sorted(v) for k, v in grammar.items()}
        families[stem] = fam
    if census["total_edges"] != TOTAL_EDGES_EXPECTED:
        raise SystemExit(
            f"FATAL: measured edge total {census['total_edges']} != spec {TOTAL_EDGES_EXPECTED}")
    return {
        "_meta": {
            "cardinality_law": "mirror inverse rows ship in-file for every split-bearing family; character--outfit, "
            "scene--save-vocabulary and dialogue-speaker-theme--character are forward-only; others never mirror; "
            "partial carries non-empty missing_fields on 44 of its 73 rows, the other 29 omit the key "
            "(25 inverse mirrors + 4 unnamed-instance census rows)",
            "consumption_law": "consumers link ONLY through these edges -- an entity page never computes a relation "
            "the tree does not ship (spec section 4.2)",
            "generated_by": "contracts/check_contracts.py generate",
            "read_surface": "extracted/relinks/*.jsonl only; parked data/*/relinks/ copies are staging (DOCX-3/XC-6)",
            "reference_by_reference": "placements stored once at the owner; profiles consume DS-4 by reference (section 4.3)",
            "spec": SPEC_PATH,
            "build_pin": pin,
        },
        "anchor_census": dict(sorted(census.items())) | {"forms": dict(sorted(forms_global.items()))},
        "expected_edge_total": TOTAL_EDGES_EXPECTED,
        "families": families,
    }


def artifact_stamp(rel: str, cls: str, pin: dict):
    """Canonicalized build stamp for a consumed artifact (C9: compared as strings)."""
    if cls in ("A", "B"):
        head, _ = split_header(rel, cls)
        bid = head.get("build_id")
        if bid is not None:
            return str(bid), "header-stamp"
    elif cls == "C":
        rows = load_jsonl(rel)
        if rows:
            for k in ("build_id", "build"):
                if k in rows[0]:
                    return str(rows[0][k]), "row-stamp"
    elif cls == "S":
        doc = load_json(rel)
        for k in ("build_id", "build"):
            if isinstance(doc, dict) and k in doc:
                return str(doc[k]), "document-stamp"
    return pin["build_id"], "pipeline-defaults"


CONSUMED_ARTIFACTS = (
    sorted(EXPECTED_HEADER_CLASSES)
    + [
        "extracted/data/dialogue/speakers.json",
        "extracted/data/scenes/poi-kinds.json",
        "extracted/data/dialogue/availability.csv",
    ]
    + [f"extracted/data/dialogue/graphs/level{n}.json" for n in
       (3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22)]
    + [
        "extracted/data/dialogue/_ledger/ac-scoreboard.json",
        "extracted/data/dialogue/_ledger/build-meta.json",
        "extracted/data/dialogue/_ledger/dangling-edges.jsonl",
        "extracted/data/dialogue/_ledger/identity-reconciliation.jsonl",
        "extracted/data/dialogue/_ledger/locale-parity.jsonl",
        "extracted/data/dialogue/_ledger/range-check.jsonl",
        "extracted/data/achievements/emit-ledger.jsonl",
        "extracted/data/endings/emit-ledger.jsonl",
    ]
    + [f"extracted/relinks/{stem}.jsonl" for stem, *_ in JOIN_DECLS]
)


def build_fingerprints(pin: dict) -> dict:
    artifacts = {}
    for rel in sorted(set(CONSUMED_ARTIFACTS)):
        raw = read_bytes(rel)
        cls = measure_header_class(rel)
        artifacts[rel] = {
            "build_id": None,  # filled below
            "row_count": row_count_of(rel, cls),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        bid, src = artifact_stamp(rel, cls, pin)
        artifacts[rel]["build_id"] = bid
        artifacts[rel]["build_id_source"] = src
    return {
        "_meta": {
            "conventions": {
                "build_id": "canonicalized STRING stamp (C9); sources: header-stamp | row-stamp | document-stamp | pipeline-defaults",
                "row_count": "JSONL data rows (header line excluded per class); single-object JSON = 1 document; CSV = lines-1",
                "sha256": "raw file bytes; recompute on every site build and pipeline emit; mismatch = defect (PIPE AC-5 bar)",
            },
            "generated_by": "contracts/check_contracts.py generate",
            "patch_day": "a new buildId invalidates every fingerprint; rerun re-pins them in the emit-stage commit; "
            "site rebuild fails until re-pinned (spec section 6.4)",
            "spec": SPEC_PATH,
        },
        "artifacts": artifacts,
        "pipeline_pin": pin,
    }


def availability_cells():
    rows = load_jsonl("extracted/relinks/locale_availability.jsonl")
    by_kind: dict = {}
    totals: Counter = Counter()
    locales = set()
    categories = set()
    for r in rows:
        kind = r["kind"]
        locales.add(r["locale"])
        bucket = by_kind.setdefault(kind, {"cells": 0})
        bucket["cells"] += 1
        if kind == "book_page":
            bucket["present_true" if r.get("present") else "present_false"] = bucket.get(
                "present_true" if r.get("present") else "present_false", 0) + 1
        else:
            disp = r["classification"]
            bucket[disp] = bucket.get(disp, 0) + 1
            totals[disp] += 1
            if kind == "category_presence":
                categories.add(r["category"])
    return rows, by_kind, totals, sorted(locales), categories


def build_availability(pin: dict) -> dict:
    rows, by_kind, totals, locales, categories = availability_cells()
    if len(locales) != 34:
        raise SystemExit(f"FATAL: locale domain {len(locales)} != 34 measured")
    return {
        "_meta": {
            "generated_by": "contracts/check_contracts.py generate",
            "regeneration": "regenerated every rerun (localization-architecture section 5.4); reruns byte-identical",
            "row_shapes": "dialogue_bucket rows carry line_count/pivot_line_count/tail_delta/file_bytes (no "
            "record_count); category_presence rows carry record_count (no line fields); book_page rows carry "
            "boolean present instead",
            "spec": SPEC_PATH,
            "unit_tests": "C6 disposition matrix runs inside check_contracts.py --verify",
        },
        "authority": AVAILABILITY_DECLS["authority"],
        "by_kind": {k: dict(sorted(v.items())) for k, v in sorted(by_kind.items())},
        "categories_distinct": len(categories),
        "cells_total": len(rows),
        "disposition_totals_excluding_book_page": dict(sorted(totals.items())),
        "fallback_chain": AVAILABILITY_DECLS["fallback_chain"],
        "aliases": AVAILABILITY_DECLS["aliases"],
        "alias_law": AVAILABILITY_DECLS["alias_law"],
        "locale_key_domain": AVAILABILITY_DECLS["locale_key_domain"],
        "locales": locales,
        "rtl": AVAILABILITY_DECLS["rtl"],
    }


# ---- stub marker occurrence probes ---------------------------------------- #

def probe_carriers() -> dict:
    """Measure every pinned/extended marker occurrence straight from the corpus."""
    p: dict = {}

    def rl(rel):
        return load_jsonl(rel)

    _, pers = split_header("extracted/data/characters/personages.jsonl", "A")
    _, carts = split_header("extracted/data/cartridges/cartridges.jsonl", "A")
    _, mins = split_header("extracted/data/cartridges/minigames.jsonl", "A")
    _, candc = split_header("extracted/data/characters/characters.candidates.jsonl", "A")
    ach = rl("extracted/data/achievements/achievements.jsonl")
    ends = rl("extracted/data/endings/endings.jsonl")
    bedges = rl("extracted/data/endings/branch_edges.jsonl")
    wdocs = split_header("extracted/data/documents/world_documents.jsonl", "B")[1]
    dnodes = rl("extracted/data/dialogue/nodes.jsonl")
    dedges = rl("extracted/data/dialogue/edges.jsonl")
    pois = split_header("extracted/data/scenes/poi.jsonl", "A")[1]
    stables = split_header("extracted/data/scenes/spawn-tables.jsonl", "A")[1]
    slinks = split_header("extracted/data/scenes/scene-links.jsonl", "A")[1]
    books = split_header("extracted/data/documents/books.jsonl", "B")[1]
    spk = load_json("extracted/data/dialogue/speakers.json")["curated_mapping"]

    # section-7 pinned counts
    p["relink_partial_rows_nonempty"] = sum(
        1 for stem, *_ in JOIN_DECLS if not stem.startswith(("cartridge--", "minigame--choice", "ending--"))
        for r in rl(f"extracted/relinks/{stem}.jsonl") if "_meta" not in r and r.get("missing_fields"))
    p["cartridge_item.status"] = sum(1 for r in carts if r.get("status") == "registered-unresolved-pickup")
    p["achievement.icon.status"] = sum(1 for r in ach if (r.get("icon") or {}).get("status") == "pending-export")
    p["achievement.unlock.status"] = sum(1 for r in ach if (r.get("unlock") or {}).get("status") == "unverified-behavior")
    p["achievement.flags.get_bool_trusted"] = sum(1 for r in ach if (r.get("flags") or {}).get("get_bool_trusted") is False)
    p["minigame.present_but_unreachable"] = sum(1 for r in mins if r.get("present_but_unreachable") is True)
    p["minigame.scoring_derivable_false"] = sum(1 for r in mins if r.get("scoring_derivable") is False)
    p["ending.kind_mode_stub"] = sum(1 for r in ends if r.get("kind") == "mode-stub")
    p["ending.mode_unlocked.state_locked_stub"] = sum(
        1 for r in ends if (r.get("mode_unlocked") or {}).get("state") == "locked-stub")
    p["branch_edge.effect_class"] = sum(1 for r in bedges if r.get("effect_class") == "dead-reference")
    p["world_document.text_mechanism"] = sum(1 for r in wdocs if r.get("text_mechanism") == "unresolved")
    p["speaker_theme.pending_curation"] = sum(1 for r in spk if r.get("entity", {}).get("status") == "pending-curation")
    p["speaker_theme.provisional_pending_ds1"] = sum(
        1 for r in spk if r.get("entity", {}).get("status") == "provisional-pending-ds1")
    p["cartridge.container_location_binding_inferred"] = sum(
        1 for r in carts if isinstance(r.get("container_location_binding"), str)
        and "[inferred]" in r["container_location_binding"])
    head_pers, _ = split_header("extracted/data/characters/personages.jsonl", "A")
    p["personage._meta.unverified_columns"] = 1 if head_pers.get("unverified_columns") else 0

    # extended measured markers
    p["chapter_null_columns"] = (
        sum(1 for r in split_header("extracted/data/documents/profile_documents.jsonl", "B")[1] if r.get("chapter") is None)
        + sum(1 for r in dnodes if r.get("chapter") is None)
        + sum(1 for r in ach if (r.get("joins") or {}).get("chapter_attribution") is None))
    p["pptr-unresolved-position_x"] = sum(
        1 for r in pois if isinstance(r.get("position"), dict) and r["position"].get("source") == "pptr-unresolved")
    p["unresolved-target-spawn_x"] = sum(1 for r in stables if r.get("status") == "unresolved-target")
    mk_head, mk_rows = split_header("extracted/data/scenes/markers.jsonl", "A")
    # XC-5 projection rerun LANDED (map-viewer M0): typed marker rows replaced the v0 _meta-only
    # posture -- the marker is now "the projection exists with typed keys", not "it is absent"
    p["marker_projection_v1_x"] = (
        sum(1 for r in mk_rows if isinstance(r.get("marker_id"), str) and r.get("marker_id"))
        if mk_head.get("schema") == "miside.markers.projection/1" else 0)
    p["build_stamps_x"] = 1 if pipeline_pin()["build_id"] else 0
    p["steam_description_en_only_x"] = sum(
        1 for r in ach
        if ((r.get("description") or {}).get("en") or {}).get("source_role") == "official-feed")
    p["unresolved_external_pointer_x"] = sum(
        1 for r in pers if isinstance(r.get("gallery_icon"), dict) and r["gallery_icon"].get("file_id") not in (0, None))
    p["unnamed_instance_census_x"] = sum(
        1 for stem in ("character--scene-membership",) for r in rl(f"extracted/relinks/{stem}.jsonl")
        if "_meta" not in r and r.get("instance_count") is not None)
    p["empty_save_key_x"] = sum(1 for r in pers if r.get("save_key") == "")
    p["tier4_empty_evidence_x"] = sum(1 for r in candc if r.get("evidence") == [])
    p["feeds_ending_null_x"] = sum(1 for r in bedges if r.get("feeds_ending") is None)
    p["speaker_null_structural_x"] = sum(1 for r in dnodes if r.get("speaker") is None)
    p["voice_present_null_x"] = sum(1 for r in dnodes if r.get("voice_present") is None)
    led = rl("extracted/data/dialogue/_ledger/dangling-edges.jsonl")
    p["dangling_edge_ledger_x"] = len(led)
    p["fork_slot_text_keyed_x"] = sum(1 for r in dedges if r.get("resolution") == "text-keyed-no-node-carrier")
    p["encoding_residue_fffd_x"] = len(rl("extracted/data/dialogue/residue-links.jsonl"))
    p["locale_parity_ledger_x"] = len(rl("extracted/data/dialogue/_ledger/locale-parity.jsonl"))
    p["curation_ruling_required_x"] = sum(
        1 for line in read_text("extracted/relinks/_assembly-provenance.jsonl").splitlines()
        if "flashes:mta" in line)
    p["display_name_loc_null_x"] = sum(1 for r in split_header("extracted/data/scenes/scenes.jsonl", "A")[1]
                                       if r.get("display_name_loc") is None)
    _, _, totals, _, _ = availability_cells()
    p["contentless_cell_x"] = totals.get("contentless", 0)
    p["scene_link_ledger_row_x"] = sum(1 for r in slinks if r.get("edge_kind") == "ledger")
    p["role_unbound_level23_x"] = sum(
        1 for r in split_header("extracted/data/scenes/scenes.jsonl", "A")[1] if r.get("role") == "unbound")
    p["book_art_per_locale_false_x"] = sum(
        1 for r in books for v in (r.get("art_per_locale") or {}).values() if v is False)
    prov = rl("extracted/relinks/_assembly-provenance.jsonl")
    p["staging_copies_parked_x"] = sum(1 for r in prov if r.get("record") == "adjudication")
    p["meta_only_family_x"] = sum(1 for stem, *rest in JOIN_DECLS if rest[1] == 0 and stem == "minigame--choice-condition")
    p["minigame_name_loc_null_x"] = sum(1 for r in mins if r.get("name_loc") is None)
    p["inferred_append_only_x"] = sum(1 for r in ach if r.get("registry_index") == r.get("line_translate"))
    p["steam_machine_plane_x"] = sum(
        1 for r in ach if (r.get("steam") or {}).get("captured_at_machine_plane") is True)
    return p


PROBE_KEY_ALIASES = {
    "pptr-unresolved-position": "pptr-unresolved-position_x",
    "unresolved-target-spawn": "unresolved-target-spawn_x",
    "marker-projection-v1": "marker_projection_v1_x",
    "build-stamps": "build_stamps_x",
    "steam-description-en-only": "steam_description_en_only_x",
    "unresolved-external-pointer": "unresolved_external_pointer_x",
    "unnamed-instance-census": "unnamed_instance_census_x",
    "empty-save-key": "empty_save_key_x",
    "tier4-empty-evidence": "tier4_empty_evidence_x",
    "feeds-ending-null": "feeds_ending_null_x",
    "speaker-null-structural": "speaker_null_structural_x",
    "voice-present-null": "voice_present_null_x",
    "dangling-edge-ledger": "dangling_edge_ledger_x",
    "fork-slot-text-keyed": "fork_slot_text_keyed_x",
    "encoding-residue-fffd": "encoding_residue_fffd_x",
    "locale-parity-ledger": "locale_parity_ledger_x",
    "curation-ruling-required": "curation_ruling_required_x",
    "display-name-loc-null": "display_name_loc_null_x",
    "contentless-cell": "contentless_cell_x",
    "scene-link-ledger-row": "scene_link_ledger_row_x",
    "role-unbound-level23": "role_unbound_level23_x",
    "book-art-per-locale-false": "book_art_per_locale_false_x",
    "staging-copies-parked": "staging_copies_parked_x",
    "meta-only-family": "meta_only_family_x",
    "minigame-name-loc-null": "minigame_name_loc_null_x",
    "inferred-append-only": "inferred_append_only_x",
    "steam-machine-plane": "steam_machine_plane_x",
    "chapter-null-columns": "chapter_null_columns",
}


def build_stubs(pin: dict) -> dict:
    probes = probe_carriers()
    vocab_out = []
    failures = []
    for v in STUB_VOCAB:
        measured = {}
        ok = True
        for key, expected in v["pinned_counts"].items():
            got = probes.get(key)
            measured[key] = got
            if got != expected:
                ok = False
        if not ok:
            failures.append((v["id"], measured, v["pinned_counts"]))
        vocab_out.append({
            "consumer_obligation": v["obligation"],
            "id": v["id"],
            "marker": v["marker"],
            "measured": measured,
            "pinned_counts": v["pinned_counts"],
            "where": v["where"],
        })
    if failures:
        raise SystemExit(f"FATAL: stub vocabulary pinned-count drift: {failures}")
    ext = {}
    for mid, (desc, minimum) in sorted(MEASURED_MARKERS.items()):
        got = probes.get(PROBE_KEY_ALIASES.get(mid, mid))
        if got is None or got < minimum:
            raise SystemExit(f"FATAL: measured marker '{mid}' got {got}, expected >= {minimum}")
        ext[mid] = {"description": desc, "occurrences": got}
    ledger_ids = []
    for line in read_text(LEDGER_PATH).splitlines():
        m = re.match(r"\|\s*((?:XC|CH|ACH|END|DLG|CAR|DOC|SCN|DOCX|MA)-\d+)\s*\|", line)
        if m:
            ledger_ids.append(m.group(1))
    coverage = {}
    for lid in ledger_ids:
        if lid not in LEDGER_COVERAGE:
            raise SystemExit(f"FATAL: ledger row {lid} has no coverage entry (C7)")
        carriers = []
        for kind, marker, evidence in LEDGER_COVERAGE[lid]:
            ev = evidence or []
            for e in ev:
                if not os.path.exists(rpath(*e.split("/"))):
                    raise SystemExit(f"FATAL: coverage evidence for {lid} missing on disk: {e}")
            carriers.append({"evidence": ev, "kind": kind, "marker": marker})
        coverage[lid] = {"carriers": carriers}
    orphan_markers = set()
    referenced = {c[1] for entries in LEDGER_COVERAGE.values() for c in entries}
    core = {v["id"] for v in STUB_VOCAB}
    for mid in referenced | core:
        if mid and mid not in core and mid not in ext:
            orphan_markers.add(mid)
    if orphan_markers:
        raise SystemExit(f"FATAL: coverage references undefined markers: {sorted(orphan_markers)}")
    unused_core = sorted(core - referenced)
    return {
        "_meta": {
            "generated_by": "contracts/check_contracts.py generate",
            "rules": [
                "a stub marker MUST cite its missingdata.md ID where one exists; the checker greps both directions",
                "silent empties are banned -- absence is a typed value, never a blank cell",
                "measured-absence rows (MA-1..MA-8) mean nobody re-chases -- the typed markers ARE the data",
            ],
            "spec": SPEC_PATH,
            "build_pin": pin,
        },
        "extended_measured_markers": ext,
        "ledger": {"entries": len(ledger_ids), "ids": ledger_ids, "path": LEDGER_PATH},
        "ledger_coverage": coverage,
        "vocabulary": vocab_out,
        "vocabulary_ids_not_referenced_by_ledger": unused_core,
    }


# --------------------------------------------------------------------------- #
# gates C1-C10
# --------------------------------------------------------------------------- #


class Report:
    def __init__(self):
        self.fails: list = []
        self.warns: list = []
        self.oks: list = []

    def ok(self, msg):
        self.oks.append(msg)

    def warn(self, msg):
        self.warns.append(msg)

    def fail(self, msg):
        self.fails.append(msg)

    def exit_code(self) -> int:
        return 1 if self.fails else 0


def diff_summary(a, b, path="$") -> list:
    """Structural diff (for C8 messaging): list of differing paths."""
    out = []
    if type(a) is not type(b):
        out.append(f"{path}: type {type(a).__name__} -> {type(b).__name__}")
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"{path}.{k}: added")
            elif k not in b:
                out.append(f"{path}.{k}: removed")
            else:
                out.extend(diff_summary(a[k], b[k], f"{path}.{k}"))
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} -> {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(diff_summary(x, y, f"{path}[{i}]"))
    elif a != b:
        out.append(f"{path}: {a!r} -> {b!r}")
    return out


def classify_change(diffs: list) -> str:
    """C8 helper: does a registry diff touch the FIELD SET (=> schema-id bump required)?"""
    typesetish = re.compile(r"\$\.entity_types\.[^.]+: (added|removed)$")
    fieldish = re.compile(r"\$\.entity_types\.[^.]+\.fields\.[^.]+" )
    enumish = re.compile(r"\$\.entity_types\.[^.]+\.enums")
    rowish = re.compile(r"\$\.entity_types\.[^.]+\.row_count")
    if any(typesetish.search(d) for d in diffs):
        return ("ENTITY-TYPE SET CHANGE -- register the type in ENTITY_DECLS and ship checker + regenerated "
                "registries in ONE commit (spec section 6.3; logic-layer AC-L6 pattern)")
    if any(fieldish.search(d) or enumish.search(d) for d in diffs):
        return ("FIELD-SET/ENUM CHANGE -- bump the artifact schema-id version, regenerate entities.json and "
                "update fingerprints.json in ONE commit (spec section 6.3)")
    if any(rowish.search(d) for d in diffs):
        return "ROW-COUNT CHANGE -- regenerate registries; if a dataset changed shape, ride the section 6.3 bump"
    return "VALUE DRIFT"


def gate_registry_file(rep: Report, rel: str, rebuilt: dict, label: str):
    """C1: regenerated byte-identical to committed."""
    if not os.path.exists(rpath(*rel.split("/"))):
        rep.fail(f"C1 {label}: committed file missing ({rel})")
        return
    committed_raw = read_bytes(f"contracts/registry/{label}")
    if canon_json(rebuilt) == committed_raw:
        rep.ok(f"C1 {label}: regenerated byte-identical")
    else:
        try:
            committed = json.loads(committed_raw.decode("utf-8"))
            diffs = diff_summary(committed, rebuilt)
        except Exception as exc:  # noqa: BLE001
            diffs = [f"unparseable committed file: {exc}"]
        rep.fail(f"C1 {label}: regenerated differs from committed ({len(diffs)} deltas; first: {diffs[0] if diffs else '?'})")
        rep.fail(f"C8 {label}: {classify_change(diffs)}")


def committed_registry(label: str):
    """Committed registry artifact parsed, or None when absent/unparseable (existence/parity is
    C1's failure; gates that consume committed state report that fact and move on)."""
    try:
        return json.loads(read_bytes(f"contracts/registry/{label}").decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def nullability_claim_problems(committed_fields: dict, inv: dict) -> list:
    """C2 comparator: COMMITTED per-field claims vs a fresh full-scan measurement.
    Returns human-readable problems; empty list == every checked claim holds over ALL rows."""
    problems = []
    for fname, meas in inv.items():
        claim = committed_fields.get(fname)
        if not isinstance(claim, dict):
            continue  # field-set membership drift is C1/C8 territory
        if bool(claim.get("nullable")) != bool(meas["nullable"]):
            problems.append(f"{fname}: nullable={claim.get('nullable')} committed vs "
                            f"{meas['nullable']} measured")
        c_abs = claim.get("absent_or_null_rows", 0)
        m_abs = meas.get("absent_or_null_rows", 0)
        if c_abs != m_abs:
            problems.append(f"{fname}: absent_or_null_rows={c_abs} committed vs {m_abs} measured")
        if claim.get("type") != meas["type"]:
            problems.append(f"{fname}: type={claim.get('type')!r} committed vs {meas['type']!r} measured")
    return problems


def gate_never_null(rep: Report, committed_entities):
    """C2 half: every nullability/absence/type claim the COMMITTED registry makes about a field is
    re-measured over ALL rows of its artifacts (full scan, no sampling). Real fail path (vB-F2 --
    this gate used to emit oks it could never fail): a stale, hand-edited or regressively
    generated entities.json whose claims contradict the corpus fails HERE on its own, independent
    of C1's byte-compare which would also catch it but without naming the false claims."""
    if committed_entities is None:
        rep.warn("C2 committed entities.json unreadable -- nullability claims unverifiable this run "
                 "(file existence/parity is C1's failure)")
        return
    checked = 0
    problems: list = []
    for etype, decl in ENTITY_DECLS.items():
        committed_fields = ((committed_entities.get("entity_types") or {}).get(etype) or {}).get("fields") or {}
        if not isinstance(committed_fields, dict) or not committed_fields:
            continue
        pool, _, _ = entity_row_pool(etype, decl)
        if not pool:
            continue
        inv = measure_fields(pool)
        checked += sum(1 for f in committed_fields if f in inv)
        problems.extend(f"{etype}.{p}" for p in nullability_claim_problems(committed_fields, inv))
    if problems:
        rep.fail(f"C2 nullability/type claims contradict the corpus on {len(problems)} field claim(s): "
                 f"{problems[:5]}")
    else:
        rep.ok(f"C2 VERIFIED (can fail): {checked} committed field claims re-measured over ALL rows of "
               f"{len(ENTITY_DECLS)} entity types -- nullable flag, absent_or_null_rows and merged type hold")


def gate_joins(rep: Report, joins: dict):
    """C3: recount vs expected table (spec section 4.1 / PROOF section 5.2) + provenance reconcile."""
    bad = [(s, f["edge_count_measured"], f["edge_count_expected"])
           for s, f in joins["families"].items() if f["edge_count_measured"] != f["edge_count_expected"]]
    if bad:
        rep.fail(f"C3 join family recount diverges from spec table: {bad}")
    else:
        rep.ok(f"C3 all 25 families recount == spec table; total {joins['anchor_census']['total_edges']}")
    meta_only = [s for s, f in joins["families"].items() if f["edge_count_measured"] == 0]
    if sorted(meta_only) != ["cartridge--scene-placement", "ending--branch-edge", "minigame--choice-condition"]:
        rep.fail(f"C3 meta-only family set drifted: {sorted(meta_only)}")
    else:
        rep.ok("C3 the three meta-only families carry measured-absence status")
    ac = joins["anchor_census"]
    if ac["total_edges"] != TOTAL_EDGES_EXPECTED or ac["edges_with_endpoints"] != 1142 \
            or ac["string_endpoints"] != 2259 or ac["null_endpoints"] != 25 or ac["anchorless_edges"] != 17:
        rep.fail(f"C3 anchor census drift: {ac}")
    else:
        rep.ok("C3 anchor census == spec section 4.2 (1142 endpoint edges / 2259 strings / 25 nulls / 17 anchor-less)")
    prov_canonical = {r.get("canonical_file") for r in load_jsonl("extracted/relinks/_assembly-provenance.jsonl")}
    missing = [f"extracted/relinks/{s}.jsonl" for s, *_ in JOIN_DECLS
               if f"extracted/relinks/{s}.jsonl" not in prov_canonical]
    if missing:
        rep.fail(f"C3 _assembly-provenance does not consolidate: {missing}")
    else:
        adjudications = [r for r in load_jsonl("extracted/relinks/_assembly-provenance.jsonl")
                         if r.get("record") == "adjudication"]
        if not adjudications:
            rep.fail("C3 _assembly-provenance lacks the DS-6 exclusion adjudication record")
        else:
            rep.ok("C3 _assembly-provenance consolidates all 25 families + records the DS-6 exclusion")


def lint_anchors_against_grammar(stem: str, grammar: dict, rows: list) -> list:
    """Core C4 surface: violations of a FIXED grammar over edge rows. Never derives anything --
    the grammar arrives from the caller (verify: the committed registry; probes: a fixture)."""
    allowed = {side: set(forms) for side, forms in grammar.items()}
    violations = []
    for r in rows:
        for side in ("from", "to"):
            if side not in r:
                continue
            v = r[side]
            if v is None:
                continue
            if anchor_form(str(v)) not in allowed.get(side, set()):
                violations.append(f"{stem}:{side}={v!r}")
    return violations


def gate_anchor_lint(rep: Report, committed_joins):
    """C4: every from/to across all edges parses against its family's grammar as recorded in the
    COMMITTED joins.json -- itself cross-checked against spec censuses by C1/C3. vB-F3 fix:
    linting against a grammar freshly derived FROM THE SAME ROWS auto-admits novel forms before
    linting (a foreign anchor could grow the grammar and pass); derivation (generate-time) and
    lint (verify-time) are now different surfaces."""
    if committed_joins is None:
        rep.fail("C4 committed joins.json unreadable -- no independent grammar to lint against")
        return
    violations: list = []
    checked = 0
    families = 0
    for stem, fam in sorted(committed_joins.get("families", {}).items()):
        if fam.get("anchor_mode") != "endpoints" or "anchor_grammar" not in fam:
            continue
        families += 1
        rows = [r for r in load_jsonl(fam["file"]) if "_meta" not in r]
        for r in rows:
            for side in ("from", "to"):
                if side in r and r[side] is not None:
                    checked += 1
        violations.extend(lint_anchors_against_grammar(stem, fam["anchor_grammar"], rows))
    if violations:
        rep.fail(f"C4 anchor lint violations ({len(violations)}): {violations[:5]}")
    else:
        rep.ok(f"C4 VERIFIED (can fail): all {checked} string endpoints parse against the COMMITTED "
               f"joins.json grammar ({families} endpoint families)")


def gate_fingerprints(rep: Report, fps: dict, pin: dict):
    """C5: recompute sha256 + row_count for every listed artifact."""
    mismatches = []
    for rel, rec in sorted(fps["artifacts"].items()):
        raw = read_bytes(rel)
        sha = hashlib.sha256(raw).hexdigest()
        cls = measure_header_class(rel)
        rc = row_count_of(rel, cls)
        if sha != rec["sha256"] or rc != rec["row_count"]:
            mismatches.append(rel)
        bid, src = artifact_stamp(rel, cls, pin)
        if bid != rec["build_id"]:
            mismatches.append(rel + " (build stamp)")
    if mismatches:
        rep.fail(f"C5 fingerprint drift on {len(mismatches)} artifact(s): {mismatches[:5]}")
    else:
        rep.ok(f"C5 fingerprints recomputed clean over {len(fps['artifacts'])} artifacts")
    stale = [rel for rel, rec in fps["artifacts"].items()
             if rec["build_id_source"] != "pipeline-defaults" and rec["build_id"] != pin["build_id"]]
    if stale:
        rep.warn(f"C5 artifacts stamped at another buildId (patch-day signal): {stale}")


def gate_availability(rep: Report, av: dict):
    """C6 data half: measured cell totals == declared expectations from the accepted spec."""
    bk = av["by_kind"]
    exp = {
        "dialogue_bucket": {"cells": 680, "present": 646, "filler": 33, "contentless": 1},
        "category_presence": {"cells": 1734, "present": 1462, "filler": 264, "contentless": 8},
        "book_page": {"cells": 272, "present_true": 264, "present_false": 8},
    }
    tot = av["disposition_totals_excluding_book_page"]
    if (bk != exp) or tot != {"contentless": 9, "filler": 297, "present": 2108} or av["cells_total"] != 2686:
        rep.fail(f"C6 availability cell drift: by_kind={bk} totals={tot}")
    else:
        rep.ok("C6 availability cells == spec section 5 census (680/1734/272; 2108/297/9)")


# ---- C6/C9 unit semantics -------------------------------------------------- #

def resolve_cell(kind: str, classification) -> str:
    """Section 5 fallback chain, machine form. Returns a consumer action."""
    if kind == "book_page":
        return "render-localized-page" if classification is True else "render-filler-art-state"
    if classification == "present":
        return "render-localized"
    if classification == "filler":
        return "render-filler"
    if classification == "contentless":
        return "render-filler"  # contentless != missing (MA-2 / SCN-9 trap)
    return "fail-unknown-disposition"


def page_membership(cells_for_entity_locale: list) -> str:
    """Page omission law: omitted ONLY when the entity has ZERO ledger membership in the locale."""
    if not cells_for_entity_locale:
        return "omit-page-and-hreflang-and-sitemap"
    return "ship-page"


def canonical_stamp(value) -> str:
    """C9: stamps compare canonically as strings regardless of JSON type."""
    return str(value)


def next_resolved_disposition(row: dict) -> str:
    """C9 discriminator: string-'null' (resolved-to-explicit-null) vs KEY ABSENT (terminal)."""
    if "next_resolved" not in row:
        return "terminal-key-absent"
    v = row["next_resolved"]
    return {"resolved": "resolved", "null": "resolved-to-explicit-null",
            "unresolved-in-level": "unresolved-in-level"}[v]


def gate_unit_semantics(rep: Report):
    # C6 matrix: every (kind, classification) incl. book_page false + contentless trap
    cases = [
        (("dialogue_bucket", "present"), "render-localized"),
        (("dialogue_bucket", "filler"), "render-filler"),
        (("dialogue_bucket", "contentless"), "render-filler"),
        (("category_presence", "present"), "render-localized"),
        (("category_presence", "filler"), "render-filler"),
        (("category_presence", "contentless"), "render-filler"),
        (("book_page", True), "render-localized-page"),
        (("book_page", False), "render-filler-art-state"),
    ]
    for args, want in cases:
        got = resolve_cell(*args)
        if got != want:
            rep.fail(f"C6 resolve_cell{args} = {got}, want {want}")
    # MA-2 / SCN-9 fixtures
    fr16 = {"kind": "dialogue_bucket", "classification": "contentless"}
    fr18 = {"kind": "category_presence", "classification": "contentless"}
    for fix, kind in ((fr16, "dialogue_bucket"), (fr18, "category_presence")):
        if resolve_cell(kind, fix["classification"]) != "render-filler":
            rep.fail(f"C6 contentless trap failed for {fix}")
    if page_membership([]) != "omit-page-and-hreflang-and-sitemap":
        rep.fail("C6 zero-membership locale must omit page + hreflang + sitemap")
    if page_membership([{"classification": "filler"}]) != "ship-page":
        rep.fail("C6 filler-only locale still ships the page (omission only at zero strings)")
    rep.ok("C6 disposition matrix green (8 combos + MA-2/SCN-9 fixtures + omission law)")
    # C9
    if canonical_stamp(19029065) != canonical_stamp("19029065"):
        rep.fail("C9 canonical stamp comparison broken (int vs string)")
    dn = load_jsonl("extracted/data/dialogue/nodes.jsonl")
    counts: Counter = Counter(next_resolved_disposition(r) for r in dn)
    if counts["resolved-to-explicit-null"] != 572 or counts["terminal-key-absent"] != 94 or counts["resolved"] != 2161:
        rep.fail(f"C9 next_resolved discrimination drifted: {dict(counts)}")
    else:
        rep.ok("C9 next_resolved: string-'null' x572 vs key-absent-terminal x94 discriminated over full corpus")


def strip_declared_notes(fields: dict) -> dict:
    """Remove declarative 'note' keys from a fields inventory -- comparisons between a fresh
    measurement and a committed block must be measurement-vs-measurement."""
    out = {}
    for k, v in fields.items():
        if isinstance(v, dict):
            v = {kk: vv for kk, vv in v.items() if kk != "note"}
            for sub in ("subfields", "element_fields"):
                if isinstance(v.get(sub), dict):
                    v[sub] = strip_declared_notes(v[sub])
        out[k] = v
    return out


def gate_selftest_mutations(rep: Report):
    """Negative probes. vB-F4 honesty rule: every green line below has a LIVE fail branch that
    bites through the real compare surface (committed registries / measurement), not a
    self-fulfilling demo -- probes that could not fail were retired or upgraded."""
    rows = split_header("extracted/data/characters/personages.jsonl", "A")[1]
    injected = [dict(rows[0]), ] + [dict(r) for r in rows[1:]]
    injected[0]["__unknown_field__"] = 1
    inv_a = measure_fields(rows)
    inv_b = measure_fields(injected)
    if set(inv_b) == set(inv_a):
        rep.fail("C2 negative probe: unknown-field injection undetected")
    else:
        rep.ok("C2 negative probe: injected unknown field changes the measured inventory (regeneration would differ)")
    # C2 comparator bite (vB-F2): flip a never-null claim the way a bad hand-edit would
    fake_claim = {"nullable": False, "type": inv_a["gallery_icon"]["type"]}
    probs = nullability_claim_problems({"gallery_icon": fake_claim}, inv_a)
    if not probs:
        rep.fail("C2 negative probe: flipped never-null claim undetected by the C2 comparator")
    else:
        rep.ok(f"C2 negative probe: committed nullable=false vs measured nullable=true flagged "
               f"({probs[0]}) -- gate_never_null fail path is live")
    fake_edge = {"from": "cartridge:mta", "to": "scene-class-family@level3"}
    if anchor_form(fake_edge["from"]) in {"<bare>", "scene:", "minigame:", "achievement:", "loc:"}:
        rep.fail("C4 negative probe mis-derived")
    joins_comm = committed_registry("joins.json")
    if joins_comm is None:
        rep.fail("C4 negative probe: committed joins.json unavailable -- lint surface untestable")
    else:
        vio = lint_anchors_against_grammar(
            "minigame--scene-carrier",
            joins_comm["families"]["minigame--scene-carrier"]["anchor_grammar"],
            [fake_edge])
        if not vio:
            rep.fail("C4 negative probe: foreign 'cartridge:' anchor PASSED the committed-grammar lint")
        else:
            rep.ok("C4 negative probe: foreign 'cartridge:' anchor REJECTED by the COMMITTED family "
                   "grammar via the lint surface verify itself uses")
    fps_comm = committed_registry("fingerprints.json")
    ft_rel = "extracted/data/endings/flag_tables.jsonl"
    raw = read_bytes(ft_rel)
    clean_sha = hashlib.sha256(raw).hexdigest()
    tampered_sha = hashlib.sha256(raw[:-2] + b'X\n').hexdigest()
    if fps_comm is None:
        rep.fail("C5 tamper probe: committed fingerprints.json unavailable -- compare surface untestable")
    elif clean_sha != fps_comm["artifacts"][ft_rel]["sha256"]:
        rep.fail("C5 tamper probe: UNTOUCHED artifact disagrees with its committed fingerprint "
                 "(control failed -- corpus moved without regeneration)")
    elif tampered_sha == clean_sha:
        rep.fail("C5 tamper probe: hash collision?!")
    else:
        rep.ok("C5 tamper probe: one flipped byte breaks the sha256 C5 compares against the COMMITTED "
               "fingerprints record (scratch bytes only, corpus untouched)")
    # C1 bite (vB-F4 upgrade of the incremented-int demo): row-level content flows into the
    # measured inventory C1 serializes -- dropping one real row shifts it vs the committed block.
    ent_comm = committed_registry("entities.json")
    inv_full = measure_fields(rows)
    delta_i = next((i for i in range(len(rows))
                    if measure_fields(rows[:i] + rows[i + 1:]) != inv_full), None)
    if delta_i is None:
        rep.fail("C1 mutation probe: no single-row drop changes personage's measured inventory")
    elif ent_comm is not None and inv_full != strip_declared_notes(
            ent_comm["entity_types"]["personage"]["fields"]):
        rep.fail("C1 mutation probe: clean measurement disagrees with committed entities.json personage "
                 "block (control failed -- regenerate before trusting this suite)")
    else:
        rep.ok(f"C1 mutation probe: dropping data row #{delta_i} shifts the measured field inventory "
               f"C1 serializes (regeneration diverges -> exit != 0 path)")


def registry_field_vocabulary(entities: dict) -> set:
    """Every field name at every measured level (fields + subfields + element_fields + map shapes)."""
    vocab = set()

    def walk(fields: dict):
        for fname, entry in fields.items():
            vocab.add(fname)
            if isinstance(entry, dict):
                walk(entry.get("subfields") or {})
                walk(entry.get("element_fields") or {})
                for k in (entry.get("map_value_shape") or {}):
                    vocab.add(k)

    for et in entities["entity_types"].values():
        walk(et.get("fields") or {})
        vocab.update((et.get("enums") or {}).keys())
    return vocab


TYPEISH = re.compile(r"\b(string|int|bool|enum|array|pointer|float|slug|map|list|loc|PPtr|object|json)\b|\[\]", re.I)


def field_table_tokens(mdx_text: str) -> list:
    """(token, typeish) pairs from the FIRST cell of `| Field | ...` tables only.
    Prose, enum values and id examples elsewhere are not field names; a row counts as a
    FIELD declaration only when its second cell carries type vocabulary (carrier/census
    tables reuse the Field header for other vocabularies)."""
    out: list = []
    in_field_table = False
    for line in mdx_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_field_table = False
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and cells[0].startswith("Field"):
            in_field_table = True
            continue
        if in_field_table and cells:
            if set(cells[0]) <= {"-", " ", ":"}:  # separator row
                continue
            typeish = bool(len(cells) > 1 and TYPEISH.search(cells[1]))
            for tok in re.findall(r"`([a-zA-Z][a-zA-Z0-9_.]*(?:/[a-zA-Z0-9_.]+)*)`", cells[0]):
                out.append((tok, typeish))
    return out


def token_in_vocabulary(tok: str, vocabulary: set) -> bool:
    """Match a full token or any slash-part against exact names, dotted leaves,
    or suffix fields emitted as compounds (`sub_scenes_loaded/unloaded/continued`)."""
    parts = tok.split("/")
    for part in parts:
        cands = [part, part.split(".")[-1]]
        for cand in cands:
            if cand in vocabulary:
                return True
            if any(v == cand or v.endswith("_" + cand) for v in vocabulary):
                return True
    return False


def gate_docs_sync(rep: Report, entities: dict):
    """C10: header-class table vs reality (hard) + dataset-contract field-table cross-check."""
    drifted = []
    for rel, cls in sorted(EXPECTED_HEADER_CLASSES.items()):
        actual = measure_header_class(rel)
        if actual != cls:
            drifted.append(f"{rel}: declared {cls} measured {actual}")
    if drifted:
        rep.fail(f"C10 header-class table drifted: {drifted}")
    else:
        rep.ok("C10 header-class table matches reality for every artifact")
    vocabulary = registry_field_vocabulary(entities)
    missing_report = []
    all_mentioned: set = set()
    for name in sorted(os.listdir(rpath("contracts"))):
        if not (name.startswith("dataset-") and name.endswith(".mdx")):
            continue
        text = read_text(f"contracts/{name}")
        pairs = field_table_tokens(text)
        all_mentioned |= {t for t, _ in pairs} | {p for t, _ in pairs for p in t.split("/")}
        for span in re.findall(r"`([a-zA-Z][a-zA-Z0-9_.]*(?:/[a-zA-Z0-9_.]+)*)`", text):
            all_mentioned.add(span)
            all_mentioned.update(span.split("/"))
        miss = sorted({t for t, typeish in pairs if typeish and not token_in_vocabulary(t, vocabulary)})
        if miss:
            missing_report.append((name, miss))
    if missing_report:
        rep.fail(f"C10 dataset-contract field-table names absent from the registry inventories: {missing_report}")
    else:
        rep.ok("C10 every typed field-table name in the seven pinned dataset contracts occurs in the registry inventories")
    extra = sorted(
        f
        for et in entities["entity_types"].values()
        for f in et["fields"]
        if f not in all_mentioned
    )
    if extra:
        rep.warn(
            "C10 registry fields named only by the umbrella spec / relation metas, not in a dataset "
            "contract field table (legal if each carries its bump record): " + ", ".join(extra))


# --------------------------------------------------------------------------- #
# modes
# --------------------------------------------------------------------------- #


def build_all() -> dict:
    pin = pipeline_pin()
    return {
        ENTITY_FILES: build_entities(pin),
        JOIN_FILES: build_joins(pin),
        FINGERPRINT_FILES: build_fingerprints(pin),
        AVAILABILITY_FILE: build_availability(pin),
        STUB_FILE: build_stubs(pin),
    }


def mode_generate() -> int:
    os.makedirs(rpath("contracts", "registry"), exist_ok=True)
    built = build_all()
    for rel, obj in built.items():
        out = rpath("contracts", "registry", os.path.basename(rel))
        with open(out, "wb") as fh:
            fh.write(canon_json(obj))
        size = os.path.getsize(out)
        print(f"wrote {rel} ({size:,} bytes)")
    print("generate: OK")
    return 0


def mode_verify() -> int:
    rep = Report()
    built = build_all()
    gate_registry_file(rep, ENTITY_FILES, built[ENTITY_FILES], "entities.json")
    gate_registry_file(rep, JOIN_FILES, built[JOIN_FILES], "joins.json")
    gate_registry_file(rep, FINGERPRINT_FILES, built[FINGERPRINT_FILES], "fingerprints.json")
    gate_registry_file(rep, AVAILABILITY_FILE, built[AVAILABILITY_FILE], "availability.json")
    gate_registry_file(rep, STUB_FILE, built[STUB_FILE], "stub-markers.json")
    gate_never_null(rep, committed_registry("entities.json"))
    gate_joins(rep, built[JOIN_FILES])
    gate_anchor_lint(rep, committed_registry("joins.json"))
    gate_fingerprints(rep, built[FINGERPRINT_FILES], pipeline_pin())
    gate_availability(rep, built[AVAILABILITY_FILE])
    gate_unit_semantics(rep)
    gate_selftest_mutations(rep)
    gate_docs_sync(rep, built[ENTITY_FILES])

    print(f"verify: {len(rep.oks)} gates green, {len(rep.warns)} warnings, {len(rep.fails)} failures")
    for w in rep.warns:
        print(f"  WARN  {w}")
    for f in rep.fails:
        print(f"  FAIL  {f}")
    return rep.exit_code()


def mode_self_test() -> int:
    rep = Report()
    gate_unit_semantics(rep)
    gate_selftest_mutations(rep)
    print(f"self-test: {len(rep.oks)} green, {len(rep.fails)} failures")
    for f in rep.fails:
        print(f"  FAIL  {f}")
    return rep.exit_code()


def mode_report() -> int:
    pin = pipeline_pin()
    print(f"pipeline pin: buildId {pin['build_id']} / {pin['version_label']}")
    ents = build_entities(pin)
    print(f"entity types: {len(ents['entity_types'])}")
    for name, e in ents["entity_types"].items():
        print(f"  {name:22s} rows={e['row_count']:5d} fields={len(e['fields']):3d} "
              f"class={e['header_class']} schema={e['schema_id']}")
    joins = build_joins(pin)
    ac = joins["anchor_census"]
    print(f"join families: {len(joins['families'])} edges: {ac['total_edges']} "
          f"(endpoint edges {ac['edges_with_endpoints']}, strings {ac['string_endpoints']}, "
          f"nulls {ac['null_endpoints']}, anchor-less {ac['anchorless_edges']})")
    fps = build_fingerprints(pin)
    print(f"fingerprinted artifacts: {len(fps['artifacts'])}")
    av = build_availability(pin)
    print(f"availability cells: {av['cells_total']} locales: {len(av['locales'])} "
          f"dispositions: {av['disposition_totals_excluding_book_page']}")
    stubs = build_stubs(pin)
    print(f"stub vocabulary: {len(stubs['vocabulary'])} markers; ledger entries covered: {stubs['ledger']['entries']}")
    return 0


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    cmd = argv[1] if len(argv) > 1 else "verify"
    if cmd in ("verify", "--verify"):
        return mode_verify()
    if cmd in ("generate", "--generate"):
        return mode_generate()
    if cmd in ("self-test", "--self-test"):
        return mode_self_test()
    if cmd in ("report", "--report"):
        return mode_report()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
