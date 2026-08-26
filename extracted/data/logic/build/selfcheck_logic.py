#!/usr/bin/env python3
"""B-LL2 self-check — runs every logic-layer acceptance criterion that can run
offline (spec docs/specs/logic-layer.mdx section 8), re-measuring inputs instead
of trusting emitter _meta:

    L1a  byte-freeze      sha256 of endings/*.jsonl identical before/after emission
    L1b  row resolution   1555/1555 branch_edges resolve under key K, uniquely
    L1c  census accounting _meta totals additive over ALL persistent calls
    L2   flag census      independent walk == 384; flag_tables reconciles as projection
    L3   polarity honesty recomputes BOTH evidence_class and value against the
                          section 3 derivation table; zero "negative" rows
    L4   scoring fence    deny-list grep over extracted/data/logic/*.jsonl +
                          minigames.jsonl hash compare + rule_status gate
    L5   drift tripwire   recorded input manifest matches the live corpus
    plus  tier-A floors, DS-2 classifier reproduction over all 1,555 joined rows,
          and disk-truth spot checks (target_path_id 18198, the tier/class
          orthogonality row, the CoreSkip dead reference).

Exit code 0 iff every check passes. Stdlib only; no git, no network.
Run:  python extracted/data/logic/build/selfcheck_logic.py [--corpus-root PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
import emit_logic as E  # noqa: E402  (reuses only parsers/constants, never outputs)

REPO = E.REPO
OUT = E.OUT
DATA = E.DATA
RELINKS = E.RELINKS

FAILURES = []
PASSES = []


def check(name, ok, detail=""):
    (PASSES if ok else FAILURES).append((name, detail))
    print("%-4s %s%s" % ("PASS" if ok else "FAIL", name,
                         (" — " + detail) if detail else ""))
    return ok


def sha(path):
    return E.sha256_file(path)


def read_rows(path):
    _, rows = E.read_jsonl_data(path)
    return rows


def read_meta_and_rows(path):
    return E.read_jsonl_data(path)


# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus-root", default=None)
    args = ap.parse_args(argv)
    corpus = E.resolve_corpus_root(args.corpus_root)

    logic_dir = OUT
    f_flags = os.path.join(logic_dir, "flag_instances.jsonl")
    f_effects = os.path.join(logic_dir, "effect_calls.jsonl")
    f_preds = os.path.join(logic_dir, "predicate_records.jsonl")
    f_tunables = os.path.join(logic_dir, "minigame_tunables.jsonl")
    for p in (f_flags, f_effects, f_preds, f_tunables):
        if not os.path.isfile(p):
            raise SystemExit("FATAL: %s missing — run emit_logic.py first" % p)

    flag_meta, flags = read_meta_and_rows(f_flags)
    eff_meta, effects = read_meta_and_rows(f_effects)
    pred_meta, preds = read_meta_and_rows(f_preds)
    tune_meta, tunables = read_meta_and_rows(f_tunables)
    endings_dir = os.path.join(DATA, "endings")
    edges = read_rows(os.path.join(endings_dir, "branch_edges.jsonl"))
    nodes = {n["node_id"]: n for n in
             read_rows(os.path.join(endings_dir, "choice_nodes.jsonl"))}
    flag_tables = read_rows(os.path.join(endings_dir, "flag_tables.jsonl"))

    # --- L5: drift tripwire ---------------------------------------------------
    manifest_path = os.path.join(logic_dir, "input-manifest.json")
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    l5_diffs = []
    if manifest.get("corpus_root") != corpus:
        l5_diffs.append("corpus_root moved (%r != %r)"
                        % (manifest.get("corpus_root"), corpus))
    for rel, h in manifest["inputs"].items():
        if rel.startswith("extracted/"):
            p = os.path.join(REPO, *rel.split("/"))
        else:  # corpus-relative (raw layers live off-repo)
            p = os.path.join(corpus, *rel.split("/"))
        if not os.path.isfile(p) or sha(p) != h:
            l5_diffs.append(rel)
    check("L5 drift tripwire", not l5_diffs,
          "recorded input manifest matches the live corpus"
          if not l5_diffs else "drifted: %s" % ", ".join(l5_diffs[:5]))

    # --- L1a: byte-freeze -------------------------------------------------------
    frozen = ["endings.jsonl", "choice_nodes.jsonl", "branch_edges.jsonl",
              "flag_tables.jsonl"]
    ledger = {r["ledger"]: r for r in read_rows(os.path.join(logic_dir,
                                                             "emit-ledger.jsonl"))}
    rec = ledger.get("ac-l1a-byte-freeze", {})
    live = {f: sha(os.path.join(endings_dir, f)) for f in frozen}
    ok = all(rec.get("sha256_after_emission", {}).get(f) == live[f] for f in frozen)
    check("L1a byte-freeze", ok,
          "emitted-after hashes == live files for all four endings/*.jsonl")

    # --- L1b: row resolution under K ---------------------------------------------
    idx = {}
    ambiguous = 0
    for r in effects:
        k = (r["container"], r["event_field"], r["host_object_path_id"],
             r["option_index"], r["call_index"], r["target"]["type"],
             r["target"]["method"], r["target"]["object_path_id"],
             (r["args"]["string"], r["args"]["int"], r["args"]["float"],
              r["args"]["bool"], r["args"]["object_path_id"]))
        idx.setdefault(k, []).append(r)

    def edge_key(e):
        n = nodes[e["from_node"]]
        t, a = e["target"], e["args"]
        return (n["container"], n["event_field"], n["object_path_id"],
                e["from_option"], e["call_index"], t["type"], t["method"],
                t["object_path_id"],
                (a["string"], a["int"], a["float"], a["bool"],
                 a["object_path_id"]))

    resolved, unmatched, amb, class_mismatch = 0, [], [], []
    for e in edges:
        hits = idx.get(edge_key(e))
        if not hits:
            unmatched.append(e["edge_id"])
            continue
        if len(hits) > 1:
            amb += 1
            continue
        resolved += 1
        if hits[0]["effect_class"] != e["effect_class"]:
            class_mismatch.append((e["edge_id"], e["effect_class"],
                                   hits[0]["effect_class"]))
    check("L1b row resolution (AC)", resolved == len(edges) == 1555,
          "%d/%d edges resolve to exactly one effect_call under K"
          % (resolved, len(edges)))
    check("L1b uniqueness", not unmatched and not amb,
          "%d unmatched / %d ambiguous" % (len(unmatched), len(amb)))
    check("DS-2 classifier reproduction", not class_mismatch,
          "emitted effect_class equals the DS-2 annotation on every joined row"
          if not class_mismatch else "%d divergences e.g. %s"
          % (len(class_mismatch), class_mismatch[:3]))

    # --- L1c: census accounting -----------------------------------------------------
    ca = eff_meta["census_accounting"]
    per = ca["per_effect_class"]
    recount = {}
    for r in effects:
        recount[r["effect_class"]] = recount.get(r["effect_class"], 0) + 1
    tiers = {"A": 0, "B": 0}
    for r in effects:
        tiers[r["tier"]] += 1
    ok = (per == recount
          and ca["tier_a_count"] == tiers["A"]
          and ca["tier_b_count"] == tiers["B"]
          and sum(per.values()) == len(effects)
          and ca["tier_a_count"] + ca["tier_b_count"] == len(effects)
          and eff_meta["row_count"] == len(effects))
    check("L1c census accounting", ok,
          "per-class %s additive; tier A %d + tier B %d = %d"
          % (json.dumps(per, sort_keys=True), tiers["A"], tiers["B"], len(effects)))

    # sweep universe closes against an INDEPENDENT count (byte-grep equivalent)
    mb_root = os.path.join(corpus, "harvest", "mb-dump")
    grep_calls = 0
    for c in sorted(os.listdir(mb_root)):
        cdir = os.path.join(mb_root, c)
        for fn in os.listdir(cdir):
            if fn.endswith(".txt"):
                with open(os.path.join(cdir, fn), "rb") as fh:
                    grep_calls += fh.read().count(b"PersistentCall data")
    check("L1c sweep universe closes", grep_calls == len(effects),
          "independent PersistentCall-element count %d == emitted rows %d"
          % (grep_calls, len(effects)))
    check("internal_only pairing (F-7)",
          all((r["tier"] == "B") == r["internal_only"] for r in effects),
          "internal_only true exactly on tier-B rows")

    # --- L2: flag census ------------------------------------------------------------
    found_im, found_ed = [], []
    txt_total = 0
    for c in sorted(os.listdir(mb_root)):
        cdir = os.path.join(mb_root, c)
        for fn in os.listdir(cdir):
            if not fn.endswith(".txt"):
                continue
            txt_total += 1
            stem, pid = E.split_dump_name(fn)
            if stem == "Events_IntMemory":
                found_im.append((c, fn))
            elif stem == "Events_Data":
                found_ed.append((c, fn))
    check("L2 flag census (AC)",
          len(flags) == 384 and len(found_im) == 5 and len(found_ed) == 379,
          "rows %d == independent find %d (%d IntMemory + %d Events_Data)"
          % (len(flags), len(found_im) + len(found_ed), len(found_im),
             len(found_ed)))

    by_key = {(f["container"], f["object_path_id"]): f for f in flags}
    ft_bad = []
    for ft in flag_tables:
        hit = by_key.get((ft["container"], ft["object_path_id"]))
        if hit is None:
            ft_bad.append("missing %r" % ((ft["container"], ft["object_path_id"]),))
            continue
        got = [(b["branch_ordinal"], b["if_int"], b["persistent_calls"])
               for b in hit["memory_branches"]]
        want = [(b["branch_ordinal"], b["if_int"], b["calls"])
                for b in ft["branches"]]
        if got != want or hit["int_memory_default"] != ft["int_memory_default"]:
            ft_bad.append("projection mismatch %r" %
                          ((ft["container"], ft["object_path_id"]),))
    check("L2 flag_tables projection", len(flag_tables) == 5 and not ft_bad,
          "all 5 flag_tables rows reconcile as projections of flag_instances")

    id_rows = read_rows(os.path.join(logic_dir, "identity-ledger.jsonl"))
    unresolved_ids = [f for f in flags if f["identity_status"] == "unresolved"]
    check("L2 identity ledger absorption ban",
          len(id_rows) == sum(1 for f in flags if f["identity_status"] != "resolved"),
          "%d bare-named instances ledgered (identity_status bare-name/unresolved); "
          "%d carry no resolvable id in either space"
          % (len(id_rows), len(unresolved_ids)))

    # --- L3: polarity honesty ----------------------------------------------------------
    SITE_PREFIXES = ("harvest/mb-dump/", "il2cpp/dump.cs")

    def sites(row):
        return [p for p in row.get("evidence", [])
                if p.startswith(SITE_PREFIXES)]

    def cites(row):
        out = [p for p in row.get("evidence", [])
               if not p.startswith(SITE_PREFIXES)]
        out += [c for c in row.get("citations", []) if not c.startswith(SITE_PREFIXES)]
        return out

    GRANT = {"AchievementGet", "AchievementComplete", "ClothCompleted"}
    bad_pair, bad_value, negatives = [], [], []
    pos_static = pos_inferred = pickup_gates = windows = cloth_pos = award_pos = 0
    for r in preds:
        v, ec = r["polarity"]["value"], r["polarity"]["evidence_class"]
        kind = r["subject"]["kind"]
        xclass = r["condition"].get("expression_class")
        call = r["condition"].get("call") or {}
        if v == "negative":
            negatives.append(r["predicate_id"])
        if v is not None and ec == "fail-closed-unknown":
            bad_pair.append(r["predicate_id"])
        # mechanical derivation-table recomputation
        if call.get("method") in GRANT and sites(r) and xclass == "serialized-site":
            want_v, want_ec = "positive", "static-proven"
            award_pos += call.get("method") == "AchievementGet"
            cloth_pos += call.get("method") == "ClothCompleted"
        elif kind == "cartridge" and r["condition"].get("pickup") \
                and sites(r):
            want_v, want_ec = "positive", "static-proven"
            pickup_gates += 1
        elif kind == "safe-window":
            want_v, want_ec = "positive", "inferred"
            if not cites(r):
                bad_value.append(r["predicate_id"] + " (inferred without citation)")
            windows += 1
        elif r.get("status") == "community" and cites(r):
            # section 6 wiki-attribution family (e.g. HellVamp, [CAR-4]):
            # community-cited STRUCTURE with no proven direction -- evidence
            # class 'inferred', value null, never styled as advice
            want_v, want_ec = None, "inferred"
        elif kind in ("minigame", "save-point") or xclass in ("save-literal",):
            want_v, want_ec = None, "static-proven"
        else:
            want_v, want_ec = None, "fail-closed-unknown"
        if (v, ec) != (want_v, want_ec):
            bad_value.append("%s emitted (%r,%r) != derived (%r,%r)"
                             % (r["predicate_id"], v, ec, want_v, want_ec))
        pos_static += 1 if (v == "positive" and ec == "static-proven") else 0
        pos_inferred += 1 if (v == "positive" and ec == "inferred") else 0
    check("L3 pairing law", not bad_pair,
          "no value rides fail-closed-unknown")
    check("L3 negative reservation (zero rows)", not negatives,
          "'negative' occurs 0 times this build")
    check("L3 value derivation table", not bad_value,
          "both evidence_class and value recompute mechanically for %d rows"
          % len(preds)
          if not bad_value else "; ".join(bad_value[:4]))
    expected_pop = award_pos == 11 and cloth_pos == 2 and pickup_gates == 21 \
        and windows >= 1
    check("L3 initial population", expected_pop,
          "%d award + %d cloth + %d pickup gates + %d community window rows"
          % (award_pos, cloth_pos, pickup_gates, windows))

    # --- L4: scoring fence -----------------------------------------------------------------
    # Pinned pattern family applied to (a) minigame_tunables FIELD NAMES -- the
    # rules plane the fence exists for -- and (b) NUMERIC assertions everywhere;
    # citation-string fields are excluded by name. Bare substring hits on
    # non-numeric provenance enums ('safe-window', 'showInterface') are not
    # threshold assertions; the emit side is already conservatively stricter
    # (any deny-matching candidate field is fenced OUT of LG4 and ledgered).
    deny = re.compile(r"win|threshold|score|percent|progress\s*>=", re.I)
    CITATION_FIELDS = {"evidence", "citations", "attribution", "attribution_method",
                       "note", "question_en", "mechanism", "scoring_fence"}
    hits = []

    def walk(obj, path, names_denied):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kp = "%s.%s" % (path, k)
                if k in CITATION_FIELDS:
                    continue
                if isinstance(v, (int, float)) and not isinstance(v, bool) \
                        and deny.search(str(k)):
                    hits.append("numeric key " + kp)
                if names_denied and isinstance(k, str) and deny.search(k) \
                        and not isinstance(v, (int, float)):
                    hits.append("field name " + kp)
                walk(v, kp, names_denied)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, "%s[%d]" % (path, i), names_denied)
        elif isinstance(obj, str):
            if re.fullmatch(r"-?\d+(\.\d+)?", obj) and deny.search(path):
                hits.append("numeric-assertion " + path)

    for fn in ("flag_instances.jsonl", "effect_calls.jsonl",
               "predicate_records.jsonl", "minigame_tunables.jsonl"):
        meta, rowsx = read_meta_and_rows(os.path.join(logic_dir, fn))
        is_tun = fn == "minigame_tunables.jsonl"
        if is_tun:
            # the rules plane: its _meta (declared carriers, exclusions) audits too
            walk(meta, fn + "._meta", True)
        for i, r in enumerate(rowsx):
            walk(r, "%s[%d]" % (fn, i), is_tun)
        # NB: name-deny applies to the tunables FIELD plane and numeric
        # assertions everywhere; the other artifacts' structural labels
        # ('safe-window') are provenance enums, not threshold-shaped fields,
        # and their _metas carry emission accounting only.

    fence_ok = not hits and all(r["rule_status"] == "not-a-threshold"
                                for r in tunables) \
        and all(r["kind"] == "envelope" for r in tunables)
    mg_path = os.path.join(DATA, "cartridges", "minigames.jsonl")
    mg_sha_ok = sha(mg_path) == manifest["inputs"]["extracted/data/cartridges/"
                                                 "minigames.jsonl"]
    excl = tune_meta.get("l4_fence_exclusions", [])
    check("L4 scoring fence", fence_ok and mg_sha_ok,
          "deny-list clean across logic/*.jsonl (%d candidate fields fenced out "
          "at emit: %s); every row rule_status=not-a-threshold; minigames.jsonl "
          "sha unchanged" % (len(excl), ", ".join(
              "%s.%s" % (x["carrier_class"], x["field"]) for x in excl) or "none"))

    # --- floors + spot checks --------------------------------------------------------------
    fl = ledger.get("tier-a-floors", {})
    check("tier-A floors", fl.get("award_sites_found", 0) >= 11
          and fl.get("cloth_sites_found", 0) >= 2,
          "award %d/11, cloth %d/2 distinct dumped sites corpus-wide"
          % (fl.get("award_sites_found", 0), fl.get("cloth_sites_found", 0)))

    slap = [r for r in effects if r["args"]["string"] == "ACHI_slaphead"
            and r["file"] == "Dialogue_3DText_#12820.txt"]
    check("spot: slaphead target_path_id 18198",
          len(slap) == 1 and slap[0]["target"]["object_path_id"] == 18198
          and slap[0]["tier"] == "A" and slap[0]["subject_ids"] ==
          ["logic:achievement:achi_slaphead"],
          slap[0]["edge_id"] if slap else "row absent")
    ortho = [r for r in effects if r["container"] == "level14"
             and r["host_object_path_id"] == 3695 and r["call_index"] == 4
             and r["event_field"] == "eventClick"]
    check("spot: tier/effect_class orthogonality row",
          len(ortho) == 1 and ortho[0]["tier"] == "A"
          and ortho[0]["effect_class"] == "cosmetic"
          and ortho[0]["target"]["method"] == "StartLoad",
          "level14:ObjectInteractive:3695 call4 Scene_Load.StartLoad = tier A + "
          "cosmetic (both axes real)" if ortho else "row absent")
    core = [r for r in effects if r["target"]["type"] == "CoreSkip"
            and r["target"]["method"] == "StopWait"
            and r["container"] == "level15" and r["call_index"] == 2
            and r["file"] == "ObjectInteractive_#4662.txt"]
    check("spot: CoreSkip dead reference preserved",
          len(core) == 1 and core[0]["effect_class"] == "dead-reference"
          and core[0]["tier"] == "B" and core[0]["internal_only"],
          core[0]["edge_id"] + " (END-4 residue kept, never resolved)"
          if core else "row absent")
    twins = [f for f in flags if f["container"] == "level4"
             and f["component"] == "Events_IntMemory"]
    twin_by = {str(f["object_path_id"]): f for f in twins}
    bare_twin, suf_twin = twin_by.get("None"), twin_by.get("3327")
    check("spot: level4 IntMemory twins distinct keys",
          len(twins) == 2 and bare_twin is not None
          and bare_twin["object_path_id"] is None
          and bare_twin["identity_status"] in ("bare-name", "unresolved")
          and suf_twin is not None and suf_twin["object_path_id"] == 3327
          and suf_twin["identity_status"] == "resolved",
          "bare (%s, inventory true id %s) + #3327 (resolved) coexist as distinct "
          "keys" % (bare_twin["identity_status"],
                    bare_twin["inventory_object_path_id"]) if bare_twin else "?")
    check("spot: flag tables level4 branch shape",
          any(f["object_path_id"] == 3327
              and [(b["branch_ordinal"], b["if_int"], b["persistent_calls"])
                   for b in f["memory_branches"]] == [(0, 3, 7)]
              for f in twins),
          "#3327 carries one branch (if_int 3) with 7 persistent calls")

    # --- summary -----------------------------------------------------------------------------
    print("\n%d passed, %d failed" % (len(PASSES), len(FAILURES)))
    for name, detail in FAILURES:
        print("  FAILED: %s — %s" % (name, detail))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
