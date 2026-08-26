"""S3 il2cpp-dump — Il2CppDumper 6.7.46 over GameAssembly.dll + metadata.

E1-proven invocation shape (explorer-e1-hands-on.mdx §Step 2), kept
byte-identical: absolute backslash paths via list argv, child cwd pinned to
the tool dir, scratch `config.json` gets `RequireAnyKey: false` applied
programmatically before EVERY run (headless shells hang on the stock
config — E1 deviation 4). FAIL-FAST on failure; the metadata-version gate
is deterministic (toolchain.md §7 pitfall 1).
"""

import json
import time
import zipfile
from pathlib import Path

from pipeline import common

NAME = "il2cpp-dump"

TOOL_SUBDIR = Path("Il2CppDumper")
TOOL_ZIP_REL = Path("tools") / "Il2CppDumper" / "release" / \
    "Il2CppDumper-net6-win-v6.7.46.zip"


def outputs_present(ctx) -> bool:
    d = ctx.extracted / "il2cpp"
    return all((d / n).is_file() for n in
               ("dump.cs", "il2cpp.h", "script.json", "stringliteral.json")) \
        and (d / "DummyDll").is_dir()


def _stage_tool(ctx) -> Path:
    tool_dir = ctx.tools_dir / TOOL_SUBDIR
    exe = tool_dir / "Il2CppDumper.exe"
    if exe.exists():
        return tool_dir
    zips = sorted((ctx.repo_root / TOOL_ZIP_REL).parent.glob("*.zip"))
    pinned = ctx.repo_root / TOOL_ZIP_REL
    if pinned.exists():
        zips = [pinned]
    if not zips:
        raise common.StageFailure(NAME, "tool release zip not found at %s" % pinned)
    tool_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zips[0]) as zf:
        zf.extractall(tool_dir)
    if not exe.exists():  # some zips nest one level deep
        nested = list(tool_dir.rglob("Il2CppDumper.exe"))
        if not nested:
            raise common.StageFailure(NAME, "Il2CppDumper.exe absent after unzip of %s"
                                      % zips[0].name)
    return tool_dir


def _apply_config_delta(ctx, tool_dir: Path) -> dict:
    """RequireAnyKey true->false in the SCRATCH copy, before every run."""
    config = tool_dir / "config.json"
    if not config.exists():
        raise common.StageFailure(NAME, "scratch config.json missing at %s "
                                        "(unzip incomplete?)" % config)
    cfg = json.loads(config.read_text(encoding="utf-8"))
    delta_applied = bool(cfg.get("RequireAnyKey"))
    cfg["RequireAnyKey"] = False
    config.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return {"require_any_key": False, "delta_applied_this_run": delta_applied}


def run(ctx):
    started = time.monotonic()
    ga = ctx.game_root / "GameAssembly.dll"
    meta = ctx.data_dir / "il2cpp_data" / "Metadata" / "global-metadata.dat"
    if not ga.exists():
        raise common.StageFailure(NAME, "missing input: %s" % ga)
    if not meta.exists():
        raise common.StageFailure(NAME, "missing input: %s" % meta)

    tool_dir = _stage_tool(ctx)
    config_state = _apply_config_delta(ctx, tool_dir)

    out = ctx.extracted / "il2cpp"
    common.wipe_tree(out)

    argv = [common.win(tool_dir / "Il2CppDumper.exe"),
            common.win(ga), common.win(meta), common.win(out)]
    proc = common.run_argv(argv, cwd=tool_dir, timeout=900)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-15:]
        raise common.StageFailure(
            NAME, "Il2CppDumper exited %s (metadata-version gate is deterministic):\n%s"
            % (proc.returncode, "\n".join(tail)))

    artifacts = {}
    for n in ("dump.cs", "il2cpp.h", "script.json", "stringliteral.json"):
        p = out / n
        if not p.is_file() or p.stat().st_size == 0:
            raise common.StageFailure(NAME, "expected artifact missing/empty: %s" % p.name)
        artifacts[n] = {"bytes": p.stat().st_size}
    dump_cs_lines = common.count_lines_split(out / "dump.cs")
    artifacts["dump.cs"]["lines"] = dump_cs_lines

    dummy = out / "DummyDll"
    dlls = sorted(p.name for p in dummy.glob("*.dll")) if dummy.is_dir() else []
    if not dlls:
        raise common.StageFailure(NAME, "DummyDll/ produced no DLLs")
    if "Assembly-CSharp.dll" not in dlls:
        raise common.StageFailure(NAME, "DummyDll/Assembly-CSharp.dll missing")

    warnings = []
    refs = (ctx.defaults or {}).get("references") or {}
    ref_lines = refs.get("dumpCsLines")
    if ref_lines and abs(dump_cs_lines - ref_lines) > 0.05 * ref_lines:
        warnings.append("dump.cs has %d lines (>5%% from EXTRACTION-LOG pin %d); "
                        "logged, never fails" % (dump_cs_lines, ref_lines))
    ref_dlls = refs.get("dummyDllCount")
    if ref_dlls and len(dlls) != ref_dlls:
        warnings.append("%d DummyDlls vs EXTRACTION-LOG reference %d"
                        % (len(dlls), ref_dlls))

    common.write_stage_report(ctx, NAME, {
        "status": "ok",
        "argv_sha256": common.sha256_text(" ".join(argv)),
        "child_cwd": str(tool_dir),
        "config": config_state,
        "artifacts": artifacts,
        "dummy_dll_count": len(dlls),
        "warnings": warnings,
        "duration_s": round(time.monotonic() - started, 3),
    })
    common.append_event(ctx, "il2cpp-dump-run", {
        "dump_cs_lines": dump_cs_lines, "dummy_dlls": len(dlls),
        "dump_cs_bytes": artifacts["dump.cs"]["bytes"],
    })
    return {"lines": dump_cs_lines, "dlls": len(dlls), "warnings": warnings}
