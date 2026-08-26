"""S2 detect — flavor checks + container census + free-space guard + LOG pin upsert.

Patch-day step 1 of the update watch (data-acquisition.md §Update watch).
Every total is derived from this stage's own walk (spec §8) — nothing is
copied from a doc. E1's measured values appear only as warn-level reference
comparisons; the walk wins, and any disagreement is logged, never silently
absorbed.
"""

import re
import struct
import time
from pathlib import Path

from pipeline import common

NAME = "detect"

# Warn-level references from E1 / EXTRACTION-LOG pins (never hard failures).
REF_UNITY_VERSION = "2021.3.35f1"
REF_METADATA_VERSION = 29
REF_LOCALE_DIRS = 34
REF_GAME_ASSEMBLY_BYTES = 22_411_776


def outputs_present(ctx) -> bool:
    return (ctx.census_dir / "detect.json").exists()


def _read_unity_version(data_dir: Path) -> str:
    """Unity version embedded in globalgamemanagers' SerializedFile header.

    NOT the leading string: on a v22 file the head is binary header —
    leading NUL padding, then metadata size / data offset — and the ASCII
    version token sits at offset 48 (buildId 19029065; byte-measured +
    UnityPy cross-checked, docs/research/s4-crash-investigation.mdx §I-2).
    Splitting at the first NUL therefore yields "" for any such file. Scan
    the header window for the version-shaped ASCII token instead.
    """
    try:
        raw = (data_dir / "globalgamemanagers").read_bytes()[:256]
    except OSError:
        return ""
    m = re.search(rb"\d{4}\.\d+\.\d+[fpb]\d+", raw)
    return m.group(0).decode("ascii") if m else ""


def _read_metadata_version(data_dir: Path) -> int:
    meta = data_dir / "il2cpp_data" / "Metadata" / "global-metadata.dat"
    with open(meta, "rb") as fh:
        fh.seek(4)
        raw = fh.read(4)
    if len(raw) != 4:
        raise common.StageFailure(NAME, "global-metadata.dat too short to read "
                                        "the version u32 at offset 4")
    return struct.unpack("<I", raw)[0]


def run(ctx):
    started = time.monotonic()
    game_root = ctx.game_root

    # --- anchors (argument semantics): exe, *_Data, loose Data tree --------
    exe_bytes = common.require_anchor(
        NAME, game_root / "MiSideFull.exe", "MiSideFull.exe at game root")
    data_dir_bytes = common.require_anchor(
        NAME, ctx.data_dir, "MiSideFull_Data\\ at game root")
    loose_bytes = common.require_anchor(
        NAME, game_root / "Data", "loose Data\\ tree at game root")

    # --- free-space guard BEFORE any write (AC-14) --------------------------
    space = common.guard_free_space(NAME, ctx.extracted, ctx.work_root)

    warnings = []

    # --- flavor --------------------------------------------------------------
    ga = ctx.data_dir.parent / "GameAssembly.dll"
    ga_present = ga.exists()
    ga_bytes = ga.stat().st_size if ga_present else 0
    backend = "il2cpp" if ga_present else "mono"
    if not ga_present:
        warnings.append("GameAssembly.dll absent at game root: IL2CPP verdict "
                        "expected on this install; downstream il2cpp-dump will fail")
    elif ga_bytes != REF_GAME_ASSEMBLY_BYTES:
        warnings.append("GameAssembly.dll is %d B (E1 reference %d B)"
                        % (ga_bytes, REF_GAME_ASSEMBLY_BYTES))

    unity_version = _read_unity_version(ctx.data_dir)
    metadata_version = _read_metadata_version(ctx.data_dir)
    if metadata_version > 31:
        raise common.StageFailure(
            NAME,
            "metadata version %d > 31: off-the-shelf Il2CppDumper no longer applies; "
            "escalate per toolchain.md §8 P6 (Cpp2IL prerelease-21 locally)" % metadata_version)
    if unity_version != REF_UNITY_VERSION:
        warnings.append("Unity version %s differs from pinned reference %s "
                        "(patch-day signal)" % (unity_version, REF_UNITY_VERSION))
    ref_meta = (ctx.defaults or {}).get("metadataVersion", REF_METADATA_VERSION)
    if metadata_version != ref_meta:
        warnings.append("metadata version %d differs from EXTRACTION-LOG pin %s"
                        % (metadata_version, ref_meta))

    # --- loc store + Voice Editor anchors ------------------------------------
    loc_root = game_root / "Data" / "Languages"
    if not loc_root.is_dir():
        raise common.StageFailure(NAME, "missing anchor: loc store at %s "
                                        "(E1 deviation 1: store sits at game root, "
                                        "not inside *_Data)" % loc_root)
    locales = sorted(d.name for d in loc_root.iterdir() if d.is_dir())
    if len(locales) != REF_LOCALE_DIRS:
        warnings.append("%d locale dirs (E1 reference %d); a patch adding a locale "
                        "extends the surface rather than failing" % (len(locales), REF_LOCALE_DIRS))

    ve_managed = game_root / "Voice Editor" / "Miside Voice Editor_Data" / "Managed"
    ve_dlls = sorted(p.name for p in ve_managed.glob("*.dll")) if ve_managed.is_dir() else []
    if not ve_managed.is_dir():
        warnings.append("Voice Editor Mono tree absent at %s" % ve_managed)

    # --- container census (own walk; drift gate vs previous detect.json) -----
    census = common.census_data_dir(ctx.data_dir)
    prev = common.read_json(ctx.census_dir / "detect.json") if outputs_present(ctx) else None
    if prev is not None:
        prev_totals = (prev.get("containers") or {}).get("totals") or {}
        if prev_totals and prev_totals != census["totals"]:
            detail = ", ".join("%s: %s -> %s" % (k, prev_totals[k], v)
                               for k, v in census["totals"].items()
                               if prev_totals.get(k) != v)
            if not ctx.expect_drift:
                raise common.StageFailure(
                    NAME,
                    "census total deviates from the previous detect.json (%s). A silent "
                    "byte change is a buildId change — rerun with --expect-drift after "
                    "confirming the patch" % detail)
            warnings.append("census total deviates from the previous detect.json "
                            "(%s) — accepted via --expect-drift" % detail)

    build_id = common.find_build_id(game_root)
    version_label = ""
    vt = game_root / "Data" / "Version.txt"
    if vt.exists():
        version_label = vt.read_text(encoding="utf-8", errors="replace").strip().splitlines()[0] \
            if vt.read_text(encoding="utf-8", errors="replace").strip() else ""

    detect = {
        "schema": "miside.detect/1",
        "game_root": str(game_root),
        "measured_at": None,  # volatile field (see census/volatile-fields.json)
        "anchors": {
            "executable": {"present": True, "bytes": exe_bytes},
            "data_dir": {"present": True, "bytes": data_dir_bytes},
            "loose_data": {"present": True, "bytes": loose_bytes},
        },
        "flavor": {
            "engine": "unity",
            "scripting_backend": backend,
            "unity_version": unity_version,
            "metadata_version": metadata_version,
            "game_assembly": {"present": ga_present, "bytes": ga_bytes},
        },
        "version_label": version_label,
        "build_id": build_id,
        "loc_store": {"present": True, "path": "Data\\Languages",
                      "locale_dirs": len(locales), "locales": locales},
        "voice_editor": {"managed_present": ve_managed.is_dir(), "managed_dlls": ve_dlls},
        "containers": census,
        "warnings": warnings,
    }
    detect["measured_at"] = common.utc_now_iso()  # enumerated volatile field
    common.write_json(ctx.census_dir / "detect.json", detect)
    common.write_volatile_fields(ctx)

    log_pins_updated = _seed_and_update_log(ctx, detect)

    common.write_stage_report(ctx, NAME, {
        "status": "ok",
        "anchors_ok": True,
        "log_pin_block_updated": bool(log_pins_updated),
        "free_space_bytes": {d: b for d, b in sorted(space.items())},
        "flavor": detect["flavor"],
        "build_id": build_id,
        "version_label": version_label,
        "locale_dirs": len(locales),
        "voice_editor_dlls": len(ve_dlls),
        "container_totals": census["totals"],
        "other_top_level_files": len(census["other_top_level"]),
        "warnings": warnings,
        "duration_s": round(time.monotonic() - started, 3),
    })
    common.append_event(ctx, "detect-run", {
        "unity": unity_version, "metadata_version": metadata_version,
        "locales": len(locales), "build_id": build_id or "unresolved",
        **{k: v for k, v in census["totals"].items()},
    })
    return {"totals": census["totals"], "warnings": warnings}


def _seed_and_update_log(ctx, detect):
    """Seed EXTRACTION-LOG.md when absent; otherwise upsert the ENTIRE
    machine pin block from this run's resolved facts (F-TW3 finding).

    The fenced ```json pipeline-defaults``` block is machine-owned and is
    rewritten IN PLACE from live values every run — never appended to
    (spec §2 S4 write mode; AC-5 record dedupe). A resumed run over a log
    seeded by older code therefore heals the block at S2 instead of
    finishing beside a stale pin (e.g. pre-errata AssetStudioModCLI 0.19.0.0)
    and false-failing AC-13. Human event sections below the block sit
    outside `update_defaults`' span and are never touched; keys and
    per-tool fields this stage does not own survive the merge, and a
    tool entry a later stage verified on disk keeps its live pin. The
    detect-measured-change event stays reserved for measured-scalar
    deltas — a pure pin-block heal shows in the stage report instead.
    """
    pins = sorted("%s==%s" % (k, v) for k, v in
                  common.parse_requirements(ctx.requirements).items())
    desired = {
        "buildId": detect["build_id"] or "",
        "versionLabel": detect["version_label"],
        "unity": detect["flavor"]["unity_version"],
        "metadataVersion": detect["flavor"]["metadata_version"],
        "python": "3.14",
        "tools": {
            "Il2CppDumper": {
                "version": "6.7.46",
                "artifact": "Il2CppDumper-net6-win-v6.7.46.zip"},
            "AssetStudioModCLI": {
                "version": "0.19.0.1",
                "artifact": "local rebuild of upstream aelurum/AssetStudioMod "
                            "6b66ec7 + recursive-type guard (natives from "
                            "AssetStudioModCLI_net8_portable.zip)",
                "versionSource": "assembly FileVersion"},
            "ilspycmd": {
                "version": "11.0.0.9335-rc",
                "artifact": "ILSpy_windows_selfcontained_11.0.0.9335-rc-x64.zip",
                "commandPin": "ilspycmd -p -o <outdir> <dll>",
                "verified": False},
        },
        "configDeltas": {"RequireAnyKey": False},
        "pipFreeze": pins,
        "entrypointCommit": common.git_head(ctx.pack_root),
        "references": {"dumpCsLines": 288102, "dummyDllCount": 57},
    }

    measured_keys = ("versionLabel", "unity", "metadataVersion", "buildId")
    measured_changed = False

    def mutate(d):
        # Machine-owned keys refresh from this run; a measured-empty read
        # never overwrites an existing pin (self-healing, never
        # self-degrading). Tool entries merge per field — current code pins
        # beat stale identity fields — EXCEPT an entry a later stage
        # measured and verified on disk (decompile sets verified:true):
        # that live-resolved pin outranks the seed placeholder, or every
        # full rerun would downgrade and re-refine it (AC-5 drift).
        nonlocal measured_changed
        before = tuple(d.get(k) for k in measured_keys)
        for key, value in desired.items():
            if key == "tools":
                merged = dict(d["tools"]) if isinstance(d.get("tools"), dict) else {}
                for name, entry in value.items():
                    prev = merged.get(name)
                    prev = prev if isinstance(prev, dict) else {}
                    if prev.get("verified") is True:
                        merged[name] = {**entry, **prev}
                    else:
                        merged[name] = {**prev, **entry}
                d["tools"] = merged
            elif key == "buildId":
                if detect["build_id"]:
                    d[key] = value
            elif key == "unity":
                if value:
                    d[key] = value
            else:
                d[key] = value
        measured_changed = before != tuple(d.get(k) for k in measured_keys)
        return d

    seeded = common.seed_defaults(ctx, desired)
    changed = False if seeded else common.update_defaults(ctx, mutate)
    if changed and measured_changed:
        common.append_event(ctx, "detect-measured-change", {
            "unity": detect["flavor"]["unity_version"],
            "metadata_version": detect["flavor"]["metadata_version"],
            "version_label": detect["version_label"],
            "build_id": detect["build_id"] or "unresolved",
        })
    return changed
