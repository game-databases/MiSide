"""S4 mono-typed-dump — per-container typed MonoBehaviour dumps.

E1-proven CLI discipline (explorer-e1-hands-on.mdx §Step 3): the input path
is strictly argv[1] — options-first fails with `Error: Input path was empty.`
(E1 deviation 5); `--assembly-folder` typing via the S3 DummyDlls is
mandatory; dumping `resources.assets` auto-resolves dependencies, so per-
container attribution reads what the tool actually loaded, not naive
per-file math (E1 deviation 6).

Measure-first gate (R-E1-1): the smallest `levelN` is dumped alone and its
object/type mix + wall time land in census/sweep-budget.json BEFORE any
other levelN/sharedassetsN sweep; the free-space guard re-fires immediately
before the full sweep starts (AC-14).

Ledger write mode: census/sweep-attempts.jsonl is REWRITTEN IN FULL at stage
end from this run's attempts, one row per container in sweep order — never
appended (spec §2 S4). A FAIL-FAST abort rewrites it first with this run's
partial-state rows (plus an aborted stage report), so no stale COMPLETE
ledger survives beside a half-wiped output tree.
"""

import re
import sys
import time
from pathlib import Path

from pipeline import common

NAME = "mono-typed-dump"

TOOL_DIR_NAME = Path("AssetStudioModCLI")
# Cycle-guarded rebuild of upstream aelurum/AssetStudioMod 6b66ec7: stock
# 0.19.0.0 dies with STATUS_STACK_OVERFLOW on MiSide's self-referential
# MonoBehaviour types (ConsoleEditor_HierarchyCase — RCA +
# reproduction matrix in docs/research/s4-crash-investigation.mdx). The
# binary is installed once under <workroot>\tools\AssetStudioModCLI-0.19.0.1\
# (canonical dir; the stock 0.19.0.0 tree stays beside it for provenance).
# The scratch clone that produced the rebuild is never referenced here.
TOOL_VERSION_PIN = "0.19.0.1"
CANONICAL_TOOL_DIR_NAME = "AssetStudioModCLI-" + TOOL_VERSION_PIN
TOOL_ZIP_REL = Path("tools") / "AssetStudioMod" / "release" / \
    "AssetStudioModCLI_net8_portable.zip"

RECURSION_WARNING_MARK = "Recursive serializable type"

MB_DUMP_REL = Path("harvest") / "mb-dump"
ASSET_LIST_REL = Path("harvest") / "asset-list"
BUDGET_REL = Path("census") / "sweep-budget.json"
ATTEMPTS_REL = Path("census") / "sweep-attempts.jsonl"


def outputs_present(ctx) -> bool:
    return (ctx.extracted / ATTEMPTS_REL).exists() \
        and (ctx.extracted / BUDGET_REL).exists()


def _stage_tool(ctx) -> Path:
    """Resolve the pinned cycle-guarded rebuild (TOOL_VERSION_PIN).

    Order: the canonical dir under workroot tools; a legacy stock-zip
    extraction dir (accepted only because run() version-gates whatever this
    returns); last resort the repo release zip — which holds stock 0.19.0.0,
    so the gate in run() then fails with install instructions instead of a
    mid-sweep STATUS_STACK_OVERFLOW.
    """
    canonical = ctx.tools_dir / CANONICAL_TOOL_DIR_NAME
    if (canonical / "AssetStudioModCLI.exe").exists():
        return canonical
    tool_dir = ctx.tools_dir / TOOL_DIR_NAME
    found = _find_exe(tool_dir)
    if found is not None:
        return found.parent
    pinned = ctx.repo_root / TOOL_ZIP_REL
    zips = [pinned] if pinned.exists() else \
        sorted((ctx.repo_root / TOOL_ZIP_REL).parent.glob("*.zip"))
    if not zips:
        raise common.StageFailure(
            NAME, "AssetStudioModCLI %s not found: no exe under %s and no "
                  "release zip at %s" % (TOOL_VERSION_PIN, canonical, pinned))
    import zipfile
    tool_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zips[0]) as zf:
        zf.extractall(tool_dir)
    return _find_exe(tool_dir).parent


def _find_exe(tool_dir: Path):
    """AssetStudioModCLI.exe at the root or one level down (stock zip nests)."""
    if (tool_dir / "AssetStudioModCLI.exe").exists():
        return tool_dir / "AssetStudioModCLI.exe"
    if tool_dir.is_dir():
        nested = sorted(tool_dir.rglob("AssetStudioModCLI.exe"))
        if nested:
            return nested[0]
    return None


def _tool_version(tool_dir: Path) -> str:
    """Pin by assembly FileVersion — the zip name carries no version (E1)."""
    dll = None
    for cand in sorted(tool_dir.rglob("AssetStudioModCLI.dll")):
        dll = cand
        break
    if dll is None:
        return "unknown"
    try:
        proc = common.run_argv(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Item '%s').VersionInfo.FileVersion" % common.win(dll)],
            timeout=60)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip().splitlines()[-1].strip()
    except Exception:
        pass
    return "unknown"


def _dump_argv(exe: Path, container: Path, dummy_dll: Path, outdir: Path,
               with_asset_list_flag: bool) -> list:
    """Input path strictly FIRST; everything else after (AC-8 invariant)."""
    argv = [common.win(exe), common.win(container),
            "-m", "dump", "-t", "monoBehaviour",
            "--assembly-folder", common.win(dummy_dll)]
    if with_asset_list_flag:
        argv += ["--export-asset-list", "xml"]
    argv += ["-o", common.win(outdir)]
    return argv


def _count_dumps(outdir: Path) -> int:
    return sum(1 for _ in outdir.rglob("*.txt")) if outdir.is_dir() else 0


def _type_mix(outdir: Path, top=10):
    """Approximate filename-derived type census (E1 §Step 3 pattern)."""
    counts = {}
    for p in outdir.rglob("*.txt"):
        token = p.stem.split(" ", 1)[0]
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return [{"type": t, "count": c} for t, c in ranked]


def _loaded_containers(stdout: str, names) -> list:
    """Which containers the tool says it loaded (deviation-6 attribution).

    Segment match, not substring: `level1` must not light up because
    `level13` appears in the tool output."""
    found = {n for n in names
             if re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(n),
                          stdout)}
    return sorted(found)


def _crosswalk(ctx, container: Path, out_xml: Path) -> bool:
    """UnityPy-derived name/pathID/source crosswalk (venv child process)."""
    cmd = [common.win(ctx.venv_python), "-m", "pipeline.stages.mono_typed_dump",
           "crosswalk", common.win(container), common.win(out_xml)]
    proc = common.run_argv(cmd, cwd=ctx.pack_root, timeout=3600)
    return proc.returncode == 0 and out_xml.exists()


# --- child entry point (runs under the pack venv; UnityPy lives there) ------

def _child_crosswalk(container_str: str, out_xml_str: str) -> int:
    import xml.sax.saxutils as sx

    import UnityPy

    src, dst = Path(container_str), Path(out_xml_str)
    env = UnityPy.load(str(src))
    rows = []
    for obj in env.objects:
        try:
            name = ""
            try:
                data = obj.read(check_read=False)
                name = getattr(data, "m_Name", "") or ""
            except Exception:
                name = ""
            rows.append((obj.path_id, obj.type.name, str(name),
                         getattr(obj, "container", "") or ""))
        except Exception:
            continue
    rows.sort(key=lambda r: r[0])
    parts = ['<?xml version="1.0" encoding="utf-8"?>',
             '<assets source=%s tool="UnityPy crosswalk">' % sx.quoteattr(src.name)]
    for pid, typ, name, cont in rows:
        parts.append('  <asset path_id="%d" type="%s" name=%s container=%s/>' % (
            pid, sx.escape(typ), sx.quoteattr(name), sx.quoteattr(cont)))
    parts.append("</assets>")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    return 0


# --- parent stage ------------------------------------------------------------

def run(ctx):
    started = time.monotonic()
    detect = common.read_json(ctx.census_dir / "detect.json")
    if detect is None:
        raise common.StageFailure(NAME, "census/detect.json missing (run detect first)")
    containers = common.container_order(detect["containers"]["serialized"])
    names = [r["name"] for r in containers]
    dummy = ctx.extracted / "il2cpp" / "DummyDll"
    if not dummy.is_dir():
        raise common.StageFailure(NAME, "%s missing (run il2cpp-dump first)" % dummy)

    tool_dir = _stage_tool(ctx)
    exe = _find_exe(tool_dir)
    if exe is None:
        raise common.StageFailure(NAME, "AssetStudioModCLI.exe absent in %s" % tool_dir)
    version = _tool_version(tool_dir)
    if version != TOOL_VERSION_PIN and version != "unknown":
        # "unknown" (no parsable FileVersion) is only ever a stand-in exe;
        # every real AssetStudioModCLI build carries its FileVersion, so a
        # real stock install is refused here rather than dying mid-sweep.
        raise common.StageFailure(
            NAME,
            "AssetStudioModCLI FileVersion %s != pinned %s: stock 0.19.0.0 crashes "
            "with STATUS_STACK_OVERFLOW (0xC00000FD) on MiSide's self-referential "
            "MonoBehaviour types. Install the cycle-guarded rebuild at %s "
            "(patch on upstream 6b66ec7; docs/research/s4-crash-investigation.mdx)"
            % (version, TOOL_VERSION_PIN,
               ctx.tools_dir / CANONICAL_TOOL_DIR_NAME))

    mb_root = ctx.extracted / MB_DUMP_REL
    al_root = ctx.extracted / ASSET_LIST_REL
    common.wipe_tree(mb_root)
    common.wipe_tree(al_root)

    def stem(row):
        return row["name"]

    def flush_attempts(rows):
        """Deterministic FULL rewrite from this run's attempts, sweep order."""
        rank = {name: i for i, name in enumerate(names)}
        common.write_jsonl(ctx.extracted / ATTEMPTS_REL,
                           sorted(rows, key=lambda a: rank[a["container"]]))

    def flush_aborted(rows, reason):
        """Abort path: rewrite the ledger with partial-state rows BEFORE the
        raise — no stale COMPLETE ledger may survive beside a half-wiped
        output tree (spec §2 S4)."""
        flush_attempts(rows)
        succeeded = sum(1 for a in rows if not a["failed"])
        common.write_stage_report(ctx, NAME, {
            "status": "aborted",
            "abort_reason": reason[:400],
            "containers_attempted": len(rows),
            "containers_succeeded": succeeded,
            "containers_failed": len(rows) - succeeded,
            "objects_total": sum(a["objects_dumped"] for a in rows),
            "keep_going": ctx.keep_going,
            "duration_s": round(time.monotonic() - started, 3),
        })

    # Abort coverage (review c-w1-r2): anything raised past the wipes — tool
    # TimeoutExpired, OSError mid-loop, StageFailure alike — must land the
    # partial ledger + aborted report BEFORE propagating, or the previous
    # COMPLETE ledger survives beside a half-wiped tree. Fail-fast sites
    # stage their exact rows/reason via `attempts`/`abort_reason`; every
    # other exception is described by the handler. Single flush point, then
    # bare re-raise — exit codes stay with the driver.
    attempts = []
    abort_reason = None
    try:
        # --- measure-first gate: smallest levelN alone (R-E1-1) --------------
        levels = [r for r in containers if r["family"] == "level"]
        if not levels:
            raise common.StageFailure(NAME, "no levelN containers in the census")
        probe_row = min(levels, key=lambda r: r["bytes"])

        def dump_one(row, with_flag):
            outdir = mb_root / stem(row)
            common.wipe_tree(outdir)
            argv = _dump_argv(exe, ctx.data_dir / row["name"], dummy, outdir, with_flag)
            t0 = time.monotonic()
            proc = common.run_argv(argv, timeout=7200)
            duration = round(time.monotonic() - t0, 3)
            objects = _count_dumps(outdir)
            return {
                "container": row["name"],
                "argv_sha256": common.sha256_text(" ".join(argv)),
                "exit_code": proc.returncode,
                "objects_dumped": objects,
                "recursion_warnings":
                    (proc.stdout or "").count(RECURSION_WARNING_MARK),
                "loaded": _loaded_containers(proc.stdout or "", names),
                "failed": proc.returncode != 0,
                "duration_s": duration,
                "measured_at": common.utc_now_iso(),
                "_stderr_tail": (proc.stderr or "").strip().splitlines()[-10:],
            }, outdir

        probe_attempt, probe_outdir = dump_one(probe_row, with_flag=True)
        if probe_attempt["failed"] and not ctx.keep_going:
            tail = "\n".join(probe_attempt.pop("_stderr_tail") or [])
            attempts.append(dict(probe_attempt, asset_list_emitted=False))
            abort_reason = tail
            raise common.StageFailure(
                NAME, "measure-first probe of %s exited %s:\n%s" % (
                    probe_row["name"], probe_attempt["exit_code"], tail))
        # --keep-going: a failed probe no longer aborts (I-S4 F3 hardening) —
        # it is ledgered now, the budget is written from what was measured,
        # and the probe container rejoins the sweep loop below for a retry.
        probe_retry_pending = probe_attempt["failed"]

        # --- asset-list mechanism (verify-during-build item, spec §8) --------
        # Combined-pass first: did `-m dump` tolerate --export-asset-list xml?
        emitted = sorted(mb_root.rglob("*.xml")) + sorted(al_root.glob("*.xml")) \
            + sorted(al_root.parent.glob("*.xml"))
        if emitted:
            mechanism = "cli-combined"
            (al_root / ("%s.xml" % probe_row["name"])).write_bytes(emitted[0].read_bytes())
        else:
            mechanism = "unitypy-crosswalk"
            if not _crosswalk(ctx, ctx.data_dir / probe_row["name"],
                              al_root / ("%s.xml" % probe_row["name"])):
                if not ctx.keep_going:
                    attempts.append(dict(probe_attempt, asset_list_emitted=True))
                    abort_reason = "asset-list fallback (UnityPy crosswalk) failed"
                    raise common.StageFailure(
                        NAME, "asset-list fallback (UnityPy crosswalk) failed for %s"
                        % probe_row["name"])
                # --keep-going: keep the chosen mechanism; every later
                # container's crosswalk miss is ledgered per-row by
                # settle_asset_list instead of aborting the sweep.

        def settle_asset_list(attempt, row, outdir):
            """Land the per-container crosswalk XML in harvest/asset-list/."""
            target = al_root / ("%s.xml" % row["name"])
            if attempt["failed"]:
                attempt["asset_list_emitted"] = False
            elif mechanism == "cli-combined":
                found = sorted(outdir.rglob("*.xml"))
                if found:
                    target.write_bytes(found[0].read_bytes())
                attempt["asset_list_emitted"] = bool(found)
            else:
                attempt["asset_list_emitted"] = _crosswalk(
                    ctx, ctx.data_dir / row["name"], target)

        budget = {
            "schema": "miside.sweep-budget/1",
            "probe_container": probe_row["name"],
            "probe_bytes": probe_row["bytes"],
            "probe_status": "failed" if probe_retry_pending else "ok",
            "objects_dumped": probe_attempt["objects_dumped"],
            "type_mix_top": _type_mix(probe_outdir),
            "probe_wall_time_s": probe_attempt["duration_s"],
            "measured_at": common.utc_now_iso(),
            "asset_list_mechanism": mechanism,
            "assetstudiomodcli_version": version,
            "sweep_order": names,
        }
        common.write_json(ctx.extracted / BUDGET_REL, budget)
        common.write_volatile_fields(ctx)  # budget exists before any further sweep

        # --- free-space guard re-fire immediately before the full sweep ------
        common.guard_free_space(NAME, ctx.extracted, ctx.work_root)

        probe_attempt.pop("_stderr_tail", None)
        attempts.append(dict(probe_attempt,
                             asset_list_emitted=not probe_retry_pending))
        probe_staged_idx = len(attempts) - 1
        for row in containers:
            retrying_probe = row["name"] == probe_row["name"] and probe_retry_pending
            if row["name"] == probe_row["name"] and not retrying_probe:
                continue
            attempt, outdir = dump_one(row, with_flag=(mechanism == "cli-combined"))
            tail = "\n".join(attempt.pop("_stderr_tail") or [])
            settle_asset_list(attempt, row, outdir)
            if attempt["failed"] and not ctx.keep_going:
                # Stage the row + reason; the shared handler flushes once.
                if retrying_probe:
                    attempts[probe_staged_idx] = attempt  # one row per container
                else:
                    attempts.append(attempt)
                abort_reason = "container %s exited %s" % (row["name"],
                                                           attempt["exit_code"])
                raise common.StageFailure(
                    NAME, "container %s exited %s (--keep-going downgrades to "
                    "ledger):\n%s" % (row["name"], attempt["exit_code"], tail))
            if retrying_probe:
                attempts[probe_staged_idx] = attempt  # replace the failed row
            else:
                attempts.append(attempt)

        # Deterministic FULL rewrite from this run's attempts, sweep order.
        flush_attempts(attempts)
        common.write_volatile_fields(ctx)

        succeeded = sum(1 for a in attempts if not a["failed"])
        failed = len(attempts) - succeeded
        warnings = []
        if failed:
            warnings.append("%d/%d containers failed (see sweep-attempts.jsonl)"
                            % (failed, len(attempts)))
        if probe_retry_pending:
            warnings.append(
                "measure-first probe of %s exited %s on first attempt "
                "(--keep-going: retried in-sweep, outcome in the ledger)"
                % (probe_row["name"], probe_attempt["exit_code"]))
        ref_ver = ((ctx.defaults or {}).get("tools") or {}).get("AssetStudioModCLI", {})
        if ref_ver.get("version") and version != ref_ver["version"]:
            warnings.append("AssetStudioModCLI FileVersion %s differs from "
                            "EXTRACTION-LOG pin %s" % (version, ref_ver["version"]))
            common.update_defaults(ctx, lambda d: {**d, "tools": {
                **d.get("tools", {}),
                "AssetStudioModCLI": {**d.get("tools", {}).get("AssetStudioModCLI", {}),
                                      "version": version}}})

        common.write_stage_report(ctx, NAME, {
            "status": "ok" if not failed else "ok-with-ledgered-failures",
            "containers_attempted": len(attempts),
            "containers_succeeded": succeeded,
            "containers_failed": failed,
            "objects_total": sum(a["objects_dumped"] for a in attempts),
            "asset_list_mechanism": mechanism,
            "assetstudiomodcli_version": version,
            "probe": {"container": probe_row["name"],
                      "objects": probe_attempt["objects_dumped"],
                      "type_mix_top": budget["type_mix_top"]},
            "keep_going": ctx.keep_going,
            "warnings": warnings,
            "duration_s": round(time.monotonic() - started, 3),
        })
        common.append_event(ctx, "sweep-run", {
            "attempted": len(attempts), "succeeded": succeeded,
            "objects_total": sum(a["objects_dumped"] for a in attempts),
            "mechanism": mechanism, "tool_version": version,
        })
        # Cyclic-tail residue (I-S4): the 0.19.0.1 cycle guard stops expanding
        # a recursive serializable type at re-entry — the node is emitted, the
        # cyclic nested tail inside that object is not. Bounded loss confined
        # to dev-console scaffolding fields; census S8 carries the same caveat
        # in its residue ledger so it survives to PROOF time.
        recursion_rows = [a for a in attempts if a.get("recursion_warnings")]
        common.append_event(ctx, "cyclic-tail-residue", {
            "tool_version": version,
            "behavior": ("recursive serializable type expansion truncated at "
                         "re-entry (cycle guard); nested cyclic tail not "
                         "expanded inside affected objects"),
            "containers_with_recursion_warnings": len(recursion_rows),
            "recursion_warnings_total":
                sum(a["recursion_warnings"] for a in recursion_rows),
            "objects_total": sum(a["objects_dumped"] for a in attempts),
        })
        return {"attempted": len(attempts), "succeeded": succeeded}
    except Exception as exc:
        flush_aborted(attempts, abort_reason if abort_reason is not None
                      else "%s: %s" % (type(exc).__name__, exc))
        raise


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "crosswalk":
        sys.exit(_child_crosswalk(sys.argv[2], sys.argv[3]))
    sys.stderr.write("usage: python -m pipeline.stages.mono_typed_dump "
                     "crosswalk <container> <out.xml>\n")
    sys.exit(2)
