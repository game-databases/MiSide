"""S8 census — PROOF.md generator (Principle two: completeness is PROVEN).

Four mandatory sections (extraction-doctrine.md):
1. Source inventory  — every source with sizes/totals AND how each was
   measured (tool + count method). Every number is derived from this stage's
   own walks or from pipeline artifacts it cites — never copied from a doc
   (spec §8).
2. Coverage reconciliation — per source: attempted vs succeeded, read from
   `census/sweep-attempts.jsonl` + stage reports; numbers must reconcile to
   the S2 census byte-for-byte.
3. Residue ledger — seeded from E1's known gaps plus anything stages ledgered.
4. Remaining theoretical surface + protocol placeholder.

FAIL-FAST on any reconciliation mismatch — a wrong total is worse than a
crashed run.
"""

import os
import time
from collections import Counter
from pathlib import Path

from pipeline import common
from pipeline.stages import art_export, loc_jsonl

NAME = "census"

PROOF_REL = Path("PROOF.md")

RESIDUE_SEEDS = [
    ("levelN dump depth", "R-E1-1",
     "Level/scene dumps were measured first (sweep-budget.json) and swept with "
     "the rest; dialogue/location/endings component coverage inside levelN "
     "dumps still needs a curation-pass read before claiming depth."),
    ("achievement unlock-state ambiguity", "R-E1-2",
     "DataAchievements `get` bools serialize unlock state into assets; "
     "defaults vs live state must be separated downstream (entity-curation)."),
    ("locale category/texture skew", "R-E1-3",
     "Per-locale category sets differ (64-76 on buildId 19029065) and texture "
     "subsets differ (JA 20 png vs EN/RU/FR 26); skew is ledgered in "
     "localization/_ledger/locale-delta.jsonl instead of asserted uniform."),
    ("GI cache level3-only", "R-E1-4",
     "Enlighten Global-Illumination precomputed data exists only for level3; "
     "catalogued in MEDIA-CATALOGUE, never chased."),
    ("cyclic typetree tails unexpanded", "I-S4",
     "AssetStudioModCLI 0.19.0.1 (cycle guard on upstream 6b66ec7) stops "
     "expanding a recursive serializable type at re-entry: inside affected "
     "dev-console components (ConsoleEditor_HierarchyCase family, "
     "dump.cs:99328) the cyclic field's nested tail is not expanded — bounded "
     "loss confined to dev-console scaffolding fields; per-run counts in the "
     "EXTRACTION-LOG 'cyclic-tail-residue' event."),
]


def _walk_tree(root: Path):
    count = 0
    total = 0
    ext_counter = Counter()
    if not root.is_dir():
        return count, total, ext_counter
    for root_dir, dirs, files in os.walk(root):
        dirs.sort()
        for fname in sorted(files):
            p = Path(root_dir) / fname
            try:
                size = p.stat().st_size
            except OSError:
                continue
            count += 1
            total += size
            ext_counter[p.suffix.lower() or "(none)"] += 1
    return count, total, ext_counter


def outputs_present(ctx) -> bool:
    return (ctx.extracted / PROOF_REL).exists()


def run(ctx):
    started = time.monotonic()
    detect = common.read_json(ctx.census_dir / "detect.json")
    if detect is None:
        raise common.StageFailure(NAME, "census/detect.json missing (run detect)")
    attempts = common.read_jsonl(ctx.extracted / "census" / "sweep-attempts.jsonl")
    swept = (common.stage_report_path(ctx, "mono-typed-dump")).exists()
    if swept and not attempts:
        raise common.StageFailure(
            NAME, "census/sweep-attempts.jsonl missing or empty while the sweep "
                  "stage report exists — refusing to claim coverage")

    game_root = Path(detect["game_root"])

    # --- own measurements (derive, never copy) --------------------------------
    loc_root = game_root / "Data" / "Languages"
    loc_count, loc_bytes, _ = _walk_tree(loc_root)
    txt_count = sum(1 for _ in loc_root.rglob("*.txt")) if loc_root.is_dir() else 0
    png_count = sum(1 for _ in loc_root.rglob("*.png")) if loc_root.is_dir() else 0
    psd_count = sum(1 for _ in loc_root.rglob("*.psd")) if loc_root.is_dir() else 0

    families = art_export.walk_families(ctx)
    audio = families.get("audio", {"count": 0, "bytes": 0})
    video = families.get("video", {"count": 0, "bytes": 0})
    gi = families.get("gi-enlighten", {"count": 0, "bytes": 0})
    custom = families.get("custom-images", {"count": 0, "bytes": 0})

    ve_data = next(iter((game_root / "Voice Editor").glob("*_Data")), None) \
        if (game_root / "Voice Editor").is_dir() else None
    ve_count, ve_bytes, ve_exts = _walk_tree(ve_data) if ve_data else (0, 0, {})

    # --- coverage reconciliation ------------------------------------------------
    totals = detect["containers"]["totals"]
    by_name = {a["container"]: a for a in attempts}
    succeeded_rows = [r for r in detect["containers"]["serialized"]
                      if r["name"] in by_name and not by_name[r["name"]].get("failed")]
    failed_names = [a["container"] for a in attempts if a.get("failed")]
    missing_attempts = [r["name"] for r in detect["containers"]["serialized"]
                        if r["name"] not in by_name]
    succeeded_bytes = sum(r["bytes"] for r in succeeded_rows)
    failed_bytes = sum(r["bytes"] for n in failed_names
                       for r in detect["containers"]["serialized"] if r["name"] == n)

    mismatches = []
    if len(attempts) != totals["serialized_count"]:
        mismatches.append("sweep attempts (%d) != census containers (%d)"
                          % (len(attempts), totals["serialized_count"]))
    if missing_attempts:
        mismatches.append("containers never attempted: %s" % missing_attempts)
    if succeeded_bytes + failed_bytes != totals["serialized_bytes"]:
        mismatches.append("succeeded+failed bytes (%d+%d) != census serialized "
                          "bytes (%d)" % (succeeded_bytes, failed_bytes,
                                          totals["serialized_bytes"]))

    loc_report = common.read_json(common.stage_report_path(ctx, "loc-jsonl")) or {}
    parsed = loc_report.get("categories_parsed", 0)
    anomalies = loc_report.get("anomalies", [])
    if parsed + len(anomalies) != txt_count and txt_count:
        mismatches.append("loc files parsed+anomalous (%d+%d) != walked txt (%d)"
                          % (parsed, len(anomalies), txt_count))

    if mismatches:
        raise common.StageFailure(NAME, "reconciliation mismatch:\n  - "
                                  + "\n  - ".join(mismatches))

    budget = common.read_json(ctx.census_dir / "sweep-budget.json") or {}
    catalogue_rows = common.read_jsonl(ctx.extracted / "media-catalogue.jsonl")

    proof = _render_proof(
        ctx, detect, attempts, succeeded_rows, succeeded_bytes, failed_names,
        failed_bytes, totals, loc_root, loc_count, loc_bytes, txt_count,
        png_count, psd_count, audio, video, gi, custom, ve_data, ve_count,
        ve_bytes, ve_exts, budget, catalogue_rows, len(anomalies), parsed,
        loc_jsonl.residue_seeds(loc_report))
    common.write_text(ctx.extracted / PROOF_REL, proof)
    common.write_volatile_fields(ctx)

    common.write_stage_report(ctx, NAME, {
        "status": "ok",
        "reconciliations": {
            "containers_attempted": len(attempts),
            "containers_succeeded": len(succeeded_rows),
            "containers_failed": failed_names,
            "succeeded_bytes": succeeded_bytes,
            "loc_txt_walked": txt_count,
            "loc_parsed": parsed,
            "loc_anomalous": len(anomalies),
        },
        "duration_s": round(time.monotonic() - started, 3),
    })
    return {"mismatches": 0}


# --- PROOF.md rendering -------------------------------------------------------

def _render_proof(ctx, detect, attempts, succeeded_rows, succeeded_bytes,
                  failed_names, failed_bytes, totals, loc_root, loc_count,
                  loc_bytes, txt_count, png_count, psd_count, audio, video,
                  gi, custom, ve_data, ve_count, ve_bytes, ve_exts,
                  budget, catalogue_rows, loc_anomaly_count, loc_parsed,
                  loc_residue_seeds) -> str:
    method_census = ("filesystem walk of `MiSideFull_Data` top level; "
                     "name-family classification (`detect` stage)")
    method_walk = "filesystem walk of the game root (single recursive pass, `art-export` stage)"
    method_loc = "filesystem walk of `Data\\Languages` (`census` stage)"

    lines = [
        "# PROOF — MiSide extraction (P1 raw layer)",
        "",
        "Completeness is PROVEN, not claimed. Every number below carries its",
        "measurement method. Totals reconcile to the S2 census byte-for-byte;",
        "`run_all` regenerates this file deterministically.",
        "",
        "| Pin | Value |",
        "|---|---|",
        "| buildId | %s |" % (detect.get("build_id") or "(unresolved at run time)"),
        "| version label | %s |" % (detect.get("version_label") or "(absent)"),
        "| Unity | %s |" % detect["flavor"]["unity_version"],
        "| metadata version | %s |" % detect["flavor"]["metadata_version"],
        "| scripting backend | %s |" % detect["flavor"]["scripting_backend"],
        "",
        "## 1. Source inventory",
        "",
        "| Source | Count | Bytes | Measured how |",
        "|---|---:|---:|---|",
        "| SerializedFile containers | %d | %d | %s |" % (
            totals["serialized_count"], totals["serialized_bytes"], method_census),
        "| Stream siblings (.resS/.resource) | %d | %d | %s |" % (
            totals["stream_count"], totals["stream_bytes"], method_census),
        "| **Container corpus grand total** | %d files | %d B | sum of the two rows above |" % (
            totals["serialized_count"] + totals["stream_count"],
            totals["grand_total_bytes"]),
        "| Localization tree (`Data\\Languages`) | %d files / %d txt / %d png + %d psd | %d | %s |" % (
            loc_count, txt_count, png_count, psd_count, loc_bytes, method_loc),
        "| Audio (`.ogg` family et al.) | %d | %d | %s |" % (
            audio["count"], audio["bytes"], method_walk),
        "| Video | %d | %d | %s |" % (video["count"], video["bytes"], method_walk),
        "| GI Enlighten tree (`MiSideFull_Data\\GI`) | %d | %d | %s |" % (
            gi["count"], gi["bytes"], method_walk),
        "| Loose character templates (`Data\\Custom`) | %d | %d | %s |" % (
            custom["count"], custom["bytes"], method_walk),
        "| Voice Editor `*_Data` (second content source, P7) | %d | %d | filesystem walk of `%s` |" % (
            ve_count, ve_bytes, ve_data.name if ve_data else "(absent)"),
        "",
        "Voice Editor extension mix: %s." % (
            ", ".join("%s=%d" % kv for kv in sorted(ve_exts.items())) or "(none)"),
        "Full media families incl. per-locale art subsets: `MEDIA-CATALOGUE.md`",
        "+ `media-catalogue.jsonl` (%d rows)." % len(catalogue_rows),
        "",
        "## 2. Coverage reconciliation",
        "",
        "- Container sweep: attempted **%d**, succeeded **%d**, failed **%s**."
        % (len(attempts), len(succeeded_rows), failed_names or "none"),
        "- Bytes reconciled: succeeded %d + failed %s = census serialized %d B ✔"
        % (succeeded_bytes, failed_bytes, totals["serialized_bytes"]),
        "- Attribution caveat: AssetStudioModCLI auto-resolves dependencies when"
        " dumping (E1 deviation 6), so per-source attribution reads each"
        " attempt's `loaded` list in `census/sweep-attempts.jsonl`, not naive"
        " per-file math.",
        "- Localization: category files parsed + ledgered non-UTF-8 anomalies"
        " (%d + %d) reconcile to the walked `.txt` total (%d) ✔"
        % (loc_parsed, loc_anomaly_count, txt_count),
        "- Media catalogue rows reconcile to an independent re-walk of the game"
        " root (`art-export` FAIL-FASTs on any disagreement).",
        "",
        "## 3. Residue ledger",
        "",
    ]
    for title, rid, text in RESIDUE_SEEDS:
        lines.append("- **%s** [%s] — %s" % (title, rid, text))
    # Stage-ledgered residue (I-3 legacy encoding) joins the ledger here,
    # derived from the loc-jsonl stage report — never copied from a doc.
    for title, rid, text in loc_residue_seeds:
        lines.append("- **%s** [%s] — %s" % (title, rid, text))
    lines += [
        "- Audio/video offload — [DR-2026-08-18-media-scope]: catalogued in"
        " place; proposed reverse-move manifest emitted at directory"
        " granularity; no pack-held copies exist until the owner opts in.",
        "",
        "## 4. Remaining theoretical surface + protocol placeholder",
        "",
        "Seeded; filled by later pieces (spec §1 non-goals): entity-curation"
        " datasets over the typed dumps, the relink layer (pairwise join"
        " matrix, UI-link→schema map, `RELATIONS.md`, locale availability),"
        " logic-layer derivations from `decompiled/_structure/`, demo-diff"
        " pass (dropped until a demo install exists — questions.md Q2).",
        "",
        "### Protocol layer — PLACEHOLDER (explicitly seeded)",
        "",
        "Single-player title: owes either the proof of no surface or an",
        "inventory of Steam achievements/cloud saves/telemetry endpoints.",
        "Seeded empty here; a later piece owns the content.",
        "",
    ]
    return "\n".join(lines)
