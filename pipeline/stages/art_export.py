"""S6 art-export — 2D export + MEDIA-CATALOGUE emission (no destructive moves).

Implements the toolchain.md §5 art policy table under
[DR-2026-08-18-media-scope] with the questions.md §5/§6 rulings baked in:

- The install is NEVER mutated: audio+video stay IN PLACE, catalogued with
  paths+bytes; this stage emits a *proposed* reverse-move manifest at
  directory granularity and performs no move (questions.md §5).
- Staged texture-family scope (questions.md §6): the walk/catalogue pass runs
  FIRST; each family's export-vs-catalogue scope derives from those first-pass
  row counts under the per-family rule, per family not globally, and the
  derived scope is recorded in EXTRACTION-LOG.md. No owner round-trip in P1.
- LEDGER for every unconvertible asset (named black-square policy is the
  frontend's problem; the catalogue stays complete). FAIL-FAST if catalogue
  byte sums disagree with an independent re-walk.
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

from pipeline import common

NAME = "art-export"

AUDIO_EXTS = {".ogg", ".wav", ".mp3", ".m4a"}
VIDEO_EXTS = {".ogv", ".webm", ".mp4", ".mov", ".avi", ".mkv"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga", ".tif", ".tiff"}
MODEL_EXTS = {".fbx", ".obj", ".dae", ".blend", ".glb", ".gltf"}

# Staged container-art scope (questions.md §6, A→STAGED): the scope derives
# from the FIRST-PASS ROW COUNTS (spec §2 S6), not a byte bar — export
# sprites+tex2d from the containers while the S2 census rows still fit the
# E1-measured reference shape; a patch growing either row family flips this
# family to catalogue-first with an owner-review row
# (DR-2026-08-18-media-scope: heavy classes are owner picks).
REF_CONTAINER_ROWS = 51   # E1 §Step 4: 51 SerializedFile-class containers
REF_STREAM_ROWS = 69      # E1 §Step 4: 69 .resS/.resource stream siblings

OFFLOAD_TARGET_ROOT = r"D:\game-database-media-offload"
CATALOGUE_JSONL_REL = Path("media-catalogue.jsonl")
CATALOGUE_MD_REL = Path("MEDIA-CATALOGUE.md")


def outputs_present(ctx) -> bool:
    return (ctx.extracted / CATALOGUE_JSONL_REL).exists() \
        and (ctx.extracted / CATALOGUE_MD_REL).exists()


def classify(game_root: Path, path: Path):
    """Exactly-one-family partition of a walked file, or None to ignore."""
    rel = path.relative_to(game_root)
    parts = [p.lower() for p in rel.parts]
    posix = rel.as_posix().lower()
    if len(parts) > 1 and parts[0] == "misidefull_data" and parts[1] == "gi":
        return "gi-enlighten"
    ext = path.suffix.lower()
    # Languages branch wins over the .psd bucket: the 3 source .psd live in
    # per-locale trees, so classifying them psd-other first would strand the
    # psd-source subset scan (AC-10's per-locale art includes those psds).
    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "languages":
        if ext in IMAGE_EXTS or ext == ".psd":
            return "languages-art"   # per-locale Textures + fonts-side images
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in IMAGE_EXTS:
        if len(parts) >= 2 and parts[0] == "data":
            return "custom-images"   # Data\Custom character templates et al.
        return "loose-images"
    if ext == ".psd":
        return "psd-other"
    if ext in MODEL_EXTS:
        return "models-animations-loose"
    return None


def walk_families(ctx) -> dict:
    """Single recursive walk of the game root -> per-family count/byte rows."""
    families = {}
    for root, dirs, files in os.walk(ctx.game_root):
        dirs[:] = sorted(dirs)
        for fname in sorted(files):
            p = Path(root) / fname
            fam = classify(ctx.game_root, p)
            if fam is None:
                continue
            row = families.setdefault(fam, {"count": 0, "bytes": 0,
                                            "dirs": {}, "locales": {}})
            row["count"] += 1
            try:
                size = p.stat().st_size
            except OSError:
                continue
            row["bytes"] += size
            parent = str(p.parent.relative_to(ctx.game_root))
            drow = row["dirs"].setdefault(parent, {"count": 0, "bytes": 0})
            drow["count"] += 1
            drow["bytes"] += size
            parts = p.relative_to(ctx.game_root).parts
            if fam == "languages-art" and len(parts) >= 3:
                lrow = row["locales"].setdefault(parts[2], {"count": 0, "bytes": 0})
                lrow["count"] += 1
                lrow["bytes"] += size
    return families


# --- child entry point: PNG->WebP conversion under the pack venv -------------

def _child_webp(src_str: str, dst_str: str) -> int:
    """Mirror <src> tree into <dst> as .webp; print one JSON summary line."""
    from PIL import Image

    src_root, dst_root = Path(src_str), Path(dst_str)

    def convert_one(p: Path, out: Path):
        out.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(p) as im:
            im.save(out, format="WEBP", quality=90, method=4)

    converted, failed, bytes_written = 0, [], 0
    for root, dirs, files in os.walk(src_root):
        dirs.sort()
        for fname in sorted(files):
            p = Path(root) / fname
            if p.suffix.lower() not in IMAGE_EXTS or p.suffix.lower() == ".webp":
                continue
            out = dst_root / p.relative_to(src_root).with_suffix(".webp")
            try:
                convert_one(p, out)
                converted += 1
                bytes_written += out.stat().st_size
            except Exception as exc:  # LEDGER per unconvertible asset
                failed.append({"path": p.relative_to(src_root).as_posix(),
                               "reason": str(exc)[:200]})
    print(json.dumps({"converted": converted, "bytes_written": bytes_written,
                      "failed": failed}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "webp":
        sys.exit(_child_webp(sys.argv[2], sys.argv[3]))
    sys.stderr.write("usage: python -m pipeline.stages.art_export "
                     "webp <src-root> <dst-root>\n")
    sys.exit(2)


# --- parent stage ------------------------------------------------------------

def run(ctx):
    started = time.monotonic()
    families = walk_families(ctx)

    # --- derive the staged per-family scope from first-pass rows (§6) --------
    detect = common.read_json(ctx.census_dir / "detect.json")
    totals = ((detect or {}).get("containers") or {}).get("totals") or {}
    container_rows = totals.get("serialized_count", 0)
    stream_rows = totals.get("stream_count", 0)
    container_art_scope = (
        "export" if 0 < container_rows <= REF_CONTAINER_ROWS
        and 0 < stream_rows <= REF_STREAM_ROWS else "catalogue-first")

    scopes = {
        "languages-art": "export-webp",       # §5 table row 1 (per-locale Textures)
        "custom-images": "copy-verbatim",     # loose templates copy through
        "loose-images": "copy-verbatim",
        "container-sprites-tex2d": container_art_scope,
        "audio": "catalogue-in-place",        # media carve-out, never emitted
        "video": "catalogue-in-place",
        "gi-enlighten": "catalogue-in-place",
        "psd-other": "catalogue-in-place",
        "models-animations-loose": "catalogue-first",
    }
    log_scopes = {
        "firstPassRows": {"serializedContainers": container_rows,
                          "streamSiblings": stream_rows},
        "referenceRows": {"serializedContainers": REF_CONTAINER_ROWS,
                          "streamSiblings": REF_STREAM_ROWS},
        "scopes": scopes}

    def changed(d):
        return {**d, "artExportStagedScope": log_scopes}

    if common.update_defaults(ctx, changed):
        common.append_event(ctx, "art-scope-derived", {
            k: v for k, v in log_scopes.items()})

    # --- free-space guard before export begins -------------------------------
    common.guard_free_space(NAME, ctx.extracted, ctx.work_root)

    art_root = ctx.extracted / "art"
    anomalies = []
    exported_counts = {}

    # Export/copy families -----------------------------------------------------
    lang_src = ctx.game_root / "Data" / "Languages"
    lang_dst = art_root / "localization-art"
    if families.get("languages-art", {}).get("count"):
        summary = _run_webp_child(ctx, lang_src, lang_dst)
        exported_counts["languages-art"] = summary["converted"]
        anomalies.extend({"family": "languages-art", **f} for f in summary["failed"])

    for fam, dst_name in (("custom-images", "custom"), ("loose-images", "loose")):
        copied = 0
        for rel, _row in _family_files(ctx, fam):
            src = ctx.game_root / rel
            dst = art_root / dst_name / rel
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied += 1
            except OSError as exc:
                anomalies.append({"family": fam, "path": rel.as_posix(),
                                  "reason": str(exc)[:200]})
        exported_counts[fam] = copied

    if container_art_scope == "export":
        exported_counts["container-sprites-tex2d"] = _export_container_art(
            ctx, detect, anomalies)

    # --- independent re-walk reconciliation (FAIL-FAST on disagreement) ------
    refamilies = walk_families(ctx)
    if {k: (v["count"], v["bytes"]) for k, v in refamilies.items()} != \
       {k: (v["count"], v["bytes"]) for k, v in families.items()}:
        raise common.StageFailure(NAME, "catalogue byte sums disagree with the "
                                        "re-walk — refusing to emit a wrong total")

    rows = _catalogue_rows(ctx, families, scopes, anomalies)
    common.write_jsonl(ctx.extracted / CATALOGUE_JSONL_REL, rows)
    common.write_text(ctx.extracted / CATALOGUE_MD_REL,
                      _render_catalogue_md(families, scopes, rows))
    common.write_volatile_fields(ctx)

    report = {
        "status": "ok-with-ledgered-anomalies" if anomalies else "ok",
        "staged_scope": scopes,
        "families": {k: {"count": v["count"], "bytes": v["bytes"]}
                     for k, v in sorted(families.items())},
        "exported": exported_counts,
        "anomalies": anomalies,
        "offload_proposed_target_root": OFFLOAD_TARGET_ROOT,
        "destructive_move_performed": False,
        "duration_s": round(time.monotonic() - started, 3),
    }
    common.write_stage_report(ctx, NAME, report)
    common.append_event(ctx, "art-run", {
        "scope_container_art": container_art_scope,
        "families": {k: v["count"] for k, v in sorted(families.items())},
        "anomalies": len(anomalies),
    })
    return {"families": len(families), "anomalies": len(anomalies),
            "container_scope": container_art_scope}


def _family_files(ctx, fam):
    """Yield (relative path, size) for every walked file of one family."""
    for root, dirs, files in os.walk(ctx.game_root):
        dirs.sort()
        for fname in sorted(files):
            p = Path(root) / fname
            if classify(ctx.game_root, p) == fam:
                yield p.relative_to(ctx.game_root), p.stat().st_size


def _run_webp_child(ctx, src: Path, dst: Path) -> dict:
    cmd = [common.win(ctx.venv_python), "-m", "pipeline.stages.art_export",
           "webp", common.win(src), common.win(dst)]
    proc = common.run_argv(cmd, cwd=ctx.pack_root, timeout=7200)
    if proc.returncode != 0:
        raise common.StageFailure(NAME, "WebP conversion child failed rc=%s:\n%s"
                                  % (proc.returncode, (proc.stderr or "")[-800:]))
    line = (proc.stdout or "").strip().splitlines()[-1]
    return json.loads(line)


def _assetstudio_exe(ctx) -> Path:
    """Stage the pinned CLI zip once into the workroot; return its exe."""
    import zipfile

    tool_dir = ctx.tools_dir / "AssetStudioModCLI"
    exe = tool_dir / "AssetStudioModCLI.exe"
    if exe.exists():
        return exe
    release = ctx.repo_root / "tools" / "AssetStudioMod" / "release"
    zips = sorted(release.glob("AssetStudioModCLI_net8_portable.zip")) \
        or sorted(release.glob("*.zip"))
    if not zips:
        raise common.StageFailure(NAME, "AssetStudioModCLI release zip not found at %s"
                                  % release)
    tool_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zips[0]) as zf:
        zf.extractall(tool_dir)
    nested = sorted(tool_dir.rglob("AssetStudioModCLI.exe"))
    if not nested:
        raise common.StageFailure(NAME, "AssetStudioModCLI.exe absent after unzip of %s"
                                  % zips[0].name)
    return nested[0]


def _export_container_art(ctx, detect, anomalies) -> int:
    """`-m export -t sprite,tex2d` over every container (input path FIRST)."""
    exe = _assetstudio_exe(ctx)

    dummy = ctx.extracted / "il2cpp" / "DummyDll"
    total = 0
    out_root = ctx.extracted / "art" / "container-2d"
    common.wipe_tree(out_root)
    for row in detect["containers"]["serialized"]:
        outdir = out_root / row["name"]
        common.wipe_tree(outdir)
        argv = [common.win(exe), common.win(ctx.data_dir / row["name"]),
                "-m", "export", "-t", "sprite,tex2d",
                "-o", common.win(outdir)]
        proc = common.run_argv(argv, timeout=7200)
        n = sum(1 for _ in outdir.rglob("*") if _.is_file())
        if proc.returncode != 0:
            # LEDGER per unconvertible/failed source; the catalogue stays complete.
            anomalies.append({
                "family": "container-sprites-tex2d", "container": row["name"],
                "reason": "exit %s" % proc.returncode})
        total += n
    return total


def _catalogue_rows(ctx, families, scopes, anomalies) -> list:
    """Machine catalogue rows; top-level families form a disjoint partition."""
    rows = [{"schema": "miside.media-catalogue/1"}]
    disposition = {
        "audio": "in-place-catalogued (media carve-out; never emitted into extracted/)",
        "video": "in-place-catalogued (media carve-out; never emitted into extracted/)",
        "gi-enlighten": "in-place-catalogued (R-E1-4: level3-only Enlighten cache)",
        "psd-other": "in-place-catalogued (heavy class awaiting owner pick)",
        "models-animations-loose": "catalogue-first (owner decides keep/offload)",
    }
    method = "filesystem walk of the game root (single recursive pass, art-export stage)"
    for fam in sorted(families):
        data = families[fam]
        rows.append({"family": fam, "scope": scopes.get(fam, ""),
                     "path": str(ctx.game_root), "count": data["count"],
                     "bytes": data["bytes"], "method": method,
                     "disposition": disposition.get(fam, "exported into extracted/art/")})
    # Per-directory offload PROPOSAL for the carve-out families (no move done).
    for fam in ("audio", "video"):
        for dirrel in sorted(families.get(fam, {}).get("dirs", {})):
            d = families[fam]["dirs"][dirrel]
            rows.append({"family": fam, "kind": "proposed-offload-manifest",
                         "granularity": "directory",
                         "path": "%s\\%s" % (ctx.game_root, dirrel),
                         "count": d["count"], "bytes": d["bytes"],
                         "proposed_target": "%s\\MiSide\\%s" % (OFFLOAD_TARGET_ROOT, dirrel),
                         "note": "proposal only — the live Steam install is never mutated"})
    # Subset rows (not part of the disjoint sum).
    la = families.get("languages-art", {})
    for locale in sorted(la.get("locales", {})):
        l = la["locales"][locale]
        rows.append({"family": "languages-art", "subset_of": "languages-art",
                     "locale": locale, "count": l["count"], "bytes": l["bytes"],
                     "method": method})
    psd_in_lang = 0
    psd_bytes = 0
    for rel, size in _family_files(ctx, "languages-art"):
        if rel.suffix.lower() == ".psd":
            psd_in_lang += 1
            psd_bytes += size
    if psd_in_lang:
        rows.append({"family": "psd-source", "subset_of": "languages-art",
                     "count": psd_in_lang, "bytes": psd_bytes, "method": method})
    return rows


def _render_catalogue_md(families, scopes, rows) -> str:
    lines = [
        "# MEDIA-CATALOGUE — MiSide",
        "",
        "Counts and bytes below were MEASURED by the pipeline's own walk",
        "(method recorded per row in `media-catalogue.jsonl`) — never copied",
        "from a doc ([DR-2026-08-18-media-scope], spec §8).",
        "",
        "Audio and video stay IN PLACE on the game drive: the live Steam",
        "install is never mutated, no destructive move was performed, and no",
        "pack-held media copies were created. Offload rows in the JSONL are a",
        "*proposal* awaiting the owner's pick.",
        "",
        "| Family | Count | Bytes | Scope |",
        "|---|---:|---:|---|",
    ]
    order = sorted(families, key=lambda f: (-families[f]["bytes"], f))
    for fam in order:
        lines.append("| `%s` | %s | %s | %s |" % (
            fam, families[fam]["count"], families[fam]["bytes"],
            scopes.get(fam, "")))
    lines += ["", "Per-family detail, per-directory offload proposals, and",
              "per-locale subset rows: see `media-catalogue.jsonl`.", ""]
    return "\n".join(lines)
