"""S7 decompile — ILSpy CLI batch decompile + `_structure/` graphs.

questions.md §4 ruling: the pipeline uses **ILSpy CLI** (`ilspycmd`, headless
batch project export); dnSpyEx stays interactive-only and never enters
`run_all`. Channel corrected by s6-arbiter item 2 (docs/research/
ilspycmd-acquisition.mdx): the CLI comes from the nuget dotnet-tool package,
not any upstream zip; the stage injects DOTNET_ROOT into its child env
itself — no caller-exported variables (AC-16 reproducibility).

Voice Editor (Mono sub-app) decompiles straight from its `Managed/*.dll` —
no dump step (toolchain.md §2 secondary). Structure artifacts (hierarchy +
type reference graphs from `dump.cs`) are doctrine-required and never
skipped. Per-assembly FAIL-FAST, `--keep-going` downgrades to LEDGER; the
stage report is rewritten with partial-state attempts on the abort path.
"""

import os
import re
import time
from pathlib import Path

from pipeline import common

NAME = "decompile"

# Tool pin (s6-arbiter item 2 + docs/research/ilspycmd-acquisition.mdx): the
# CLI comes from the nuget dotnet-tool package — NOT from any upstream zip
# (v11.0-rc GitHub assets are GUI-only; no CLI asset ever existed on that
# channel, which was I-4's root cause). Host-global ilspycmd stays refused
# (pin integrity). The shim is framework-dependent net10.0-only and resolves
# its runtime via DOTNET_ROOT alone (app-local layouts are ignored), so this
# stage injects it into every child env itself (_child_env) instead of
# relying on caller-exported variables.
TOOL_VERSION_PIN = "11.0.0.9335-rc"
NUPKG_NAME = "ilspycmd.11.0.0.9335-rc.nupkg"
NUPKG_SHA256 = "9e336464fb5554cf1ed1ac50bb41db2ce369ad875670b6024bc49123d063c816"
TOOL_CHANNEL = "nuget.org dotnet-tool 'ilspycmd' (--tool-path install, self-stored)"
TOOL_DIR_NAME = Path("ILSpy")  # canonical dir under <workroot>\tools\
TOOL_DIR_ALTERNATES = ("IlSpyCmd",)  # accepted: I-T1 install-record spelling
DOTNET_SDK_DIR_NAME = Path("it1-dotnet10")  # local .NET SDK 10.0.400 under workroot
INSTALL_INSTRUCTION = (
    "acquire per docs/research/ilspycmd-acquisition.mdx: extract the local "
    ".NET SDK 10 to <workroot>\\%s then run "
    "<sdk>\\dotnet.exe tool install --tool-path <workroot>\\tools\\ILSpy "
    "ilspycmd --version %s (nupkg sha256 %s)"
    % (DOTNET_SDK_DIR_NAME, TOOL_VERSION_PIN, NUPKG_SHA256))

STRUCTURE_REL = Path("decompiled") / "_structure"

DECL_RE = re.compile(
    r"^\s*(?:\[[^\]]*\]\s*)*"
    r"((?:public|private|protected|internal|static|sealed|abstract|override|"
    r"virtual|readonly|const|new|unsafe|partial|extern)\s+)*"
    r"(class|struct|interface|enum)\s+"
    r"([A-Za-z_][\w`]*)[^{:;]*"
    r"(?::\s*([^\{]+))?"
    r"\s*(?://\s*TypeDefIndex:\s*(\d+))?\s*\{?")
NAMESPACE_RE = re.compile(r"^\s*namespace\s+([\w.]+)")
IDENT_RE = re.compile(r"[A-Za-z_]\w*")

RECON_ANCHORS = [
    "GlobalLanguage.GetString", "CheckLocalization", "DialogueChanger",
    "MitaEvent", "Location1Main",
]
BODIES_CAVEAT = (
    "Decompiler method bodies are garbage-prone in call-heavy serializers "
    "(IL2CPP); take structure, get semantics from data — "
    "does-not-work/decompiler-method-bodies.md")


def outputs_present(ctx) -> bool:
    return (ctx.extracted / STRUCTURE_REL / "hierarchy.json").exists() \
        and (ctx.extracted / "decompiled" / "main").is_dir() \
        and (ctx.extracted / "decompiled" / "voice-editor").is_dir()


def _ilspycmd(ctx) -> Path:
    """Resolve the pinned dotnet-tool shim under <workroot>\\tools\\.

    No zip fallback: the repo release-zip channel held GUI-only assets and
    could never yield a CLI (I-4), so an unzip here could only "succeed"
    with a CLI-less tree. Absence fails with the nuget instruction instead.
    """
    candidates = [ctx.tools_dir / TOOL_DIR_NAME] + [
        ctx.tools_dir / alt for alt in TOOL_DIR_ALTERNATES]
    for tool_dir in candidates:
        exe = tool_dir / "ilspycmd.exe"
        if exe.exists():
            return exe
    raise common.StageFailure(
        NAME, "pinned ilspycmd %s not found (probed %s); %s"
              % (TOOL_VERSION_PIN, ", ".join(str(d) for d in candidates),
                 INSTALL_INSTRUCTION))


def _dotnet_root(ctx):
    """Local net10 SDK home under the workroot, or None when absent —
    sandbox/stub runs carry framework-exe stubs that need no runtime."""
    sdk_dir = ctx.work_root / DOTNET_SDK_DIR_NAME
    if (sdk_dir / "dotnet.exe").is_file():
        return sdk_dir
    return None


def _child_env(ctx, dotnet_root) -> dict:
    """Child env for every ilspycmd spawn: injects
    DOTNET_ROOT=<workroot>\\it1-dotnet10 so the framework-dependent shim
    resolves its runtime with zero caller-exported variables (s6-arbiter
    I-4: option b REQUIRED — tribal-knowledge bar, AC-16)."""
    env = dict(os.environ)
    if dotnet_root is not None:
        env["DOTNET_ROOT"] = str(dotnet_root)
    return env


def _version(ctx, cmd: Path, env: dict) -> str:
    proc = common.run_argv([common.win(cmd), "--version"], timeout=120, env=env)
    out = (proc.stdout or "").strip().splitlines()
    if proc.returncode != 0 or not out:
        raise common.StageFailure(NAME, "ilspycmd --version failed rc=%s" % proc.returncode)
    ver = next((ln for ln in out if re.search(r"\d+\.\d+", ln)), out[0])
    ver = ver.strip()
    base = TOOL_VERSION_PIN.split("-", 1)[0]
    if base not in ver:
        raise common.StageFailure(
            NAME, "ilspycmd pin mismatch: measured %r, pinned %s (%s) — "
                  "host-global ilspycmd substitution is refused; %s"
                  % (ver, TOOL_VERSION_PIN, TOOL_CHANNEL, INSTALL_INSTRUCTION))
    return ver


def _decompile_assembly(ctx, cmd: Path, version: str, dll: Path, out_root: Path,
                        results, env: dict):
    stem = dll.stem
    outdir = out_root / stem
    common.wipe_tree(outdir)
    argv = [common.win(cmd), "-p", "-o", common.win(outdir), common.win(dll)]
    proc = common.run_argv(argv, timeout=1800, env=env)
    ok = proc.returncode == 0 and any(outdir.rglob("*.cs"))
    results.append({"assembly": stem, "argv_sha256":
                    common.sha256_text(" ".join(argv)),
                    "exit_code": proc.returncode, "cs_files":
                    sum(1 for _ in outdir.rglob("*.cs")) if ok else 0})
    if not ok:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-10:]
        if not ctx.keep_going:
            raise common.StageFailure(
                NAME, "decompile of %s failed rc=%s (--keep-going downgrades to "
                "ledger):\n%s" % (dll.name, proc.returncode, "\n".join(tail)))
    return argv


def parse_dump_cs(path: Path):
    """Extract type declarations + intra-block reference edges from dump.cs."""
    types = {}
    order = []
    namespace = ""
    depth = 0
    decl_depth = None
    decl_opened = False
    current = None
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = NAMESPACE_RE.match(line)
            if m and current is None:
                namespace = m.group(1)
            dm = DECL_RE.match(line.rstrip())
            opens = line.count("{")
            closes = line.count("}")
            if dm is not None and decl_depth is None:
                kind, name, bases_raw, tdi = (dm.group(2), dm.group(3),
                                              dm.group(4), dm.group(5))
                current = {
                    "name": name, "namespace": namespace, "kind": kind,
                    "typeDefIndex": int(tdi) if tdi else None,
                    "bases": [], "references": [],
                }
                if bases_raw:
                    seen = []
                    for token in IDENT_RE.findall(bases_raw.split("<")[0]):
                        if token not in ("object",) and token not in seen:
                            seen.append(token)
                    current["bases"] = seen[:6]
                types[name] = current
                order.append(name)
                decl_depth = depth
                # dump.cs puts a type's `{` on the NEXT line (empty bodies use
                # `{}` there), so the body may not exist yet when the header
                # matches. Gate the closer on the opener (x3-vA): without it,
                # `depth <= decl_depth` held on the header line itself and
                # every body closed instantly — references stayed empty.
                decl_opened = opens > 0
            elif current is not None:
                for token in IDENT_RE.findall(line):
                    if token in types and token != current["name"] \
                            and token not in current["references"]:
                        current["references"].append(token)
            depth += opens - closes
            if current is not None and decl_depth is not None \
                    and not decl_opened and opens > 0:
                decl_opened = True
            if current is not None and decl_depth is not None \
                    and decl_opened and depth <= decl_depth:
                current = None
                decl_depth = None
                decl_opened = False
    hierarchy = {n: {"bases": types[n]["bases"],
                     "derived": sorted(k for k in types
                                       if n in types[k]["bases"])}
                 for n in order}
    references = {n: sorted(types[n]["references"]) for n in order}
    catalog = [{"name": t["name"], "namespace": t["namespace"], "kind": t["kind"],
                "typeDefIndex": t["typeDefIndex"]} for t in
               (types[n] for n in order)]
    return catalog, hierarchy, references


def run(ctx):
    started = time.monotonic()
    dummy = ctx.extracted / "il2cpp" / "DummyDll"
    dump_cs = ctx.extracted / "il2cpp" / "dump.cs"
    if not dummy.is_dir() or not dump_cs.is_file():
        raise common.StageFailure(NAME, "il2cpp outputs missing (run il2cpp-dump)")

    # Free-space guard before the batch begins — 57 trees are unmeasured.
    common.guard_free_space(NAME, ctx.extracted, ctx.work_root)

    cmd = _ilspycmd(ctx)
    dotnet_root = _dotnet_root(ctx)
    env = _child_env(ctx, dotnet_root)
    version = _version(ctx, cmd, env)

    dec_root = ctx.extracted / "decompiled"
    main_root = dec_root / "main"
    ve_root = dec_root / "voice-editor"
    common.wipe_tree(main_root)
    common.wipe_tree(ve_root)

    results = []
    ve_count = 0

    def flush_aborted(reason: str):
        """Abort path: rewrite the stage report with partial-state attempts
        BEFORE the raise — no stale COMPLETE report may survive beside a
        half-decompiled tree."""
        common.write_stage_report(ctx, NAME, {
            "status": "aborted",
            "abort_reason": reason[:400],
            "ilspycmd_version": version,
            "ilspycmd_path": str(cmd),
            "dotnet_root": str(dotnet_root) if dotnet_root else None,
            "assemblies_attempted": len(results),
            "voice_editor_assemblies": ve_count,
            "failed_assemblies": [r["assembly"] for r in results
                                  if r["exit_code"] != 0],
            "attempts": results,
            "keep_going": ctx.keep_going,
            "duration_s": round(time.monotonic() - started, 3),
        })

    try:
        for dll in sorted(dummy.glob("*.dll")):
            _decompile_assembly(ctx, cmd, version, dll, main_root, results, env)
        ve_managed = ctx.game_root / "Voice Editor" / "Miside Voice Editor_Data" / "Managed"
        if ve_managed.is_dir():
            for dll in sorted(ve_managed.glob("*.dll")):
                _decompile_assembly(ctx, cmd, version, dll, ve_root, results, env)
                ve_count += 1
    except Exception as exc:
        # Not StageFailure alone (review c-w1-r2): a tool TimeoutExpired or
        # OSError mid-batch must land the partial-state report too, then
        # propagate unchanged — exit codes stay with the driver.
        flush_aborted(str(exc))
        raise

    # --- structure graphs (mandatory, never skipped) --------------------------
    # Same abort discipline as the batch above (build-arbiter FIX_LOOP 1):
    # wipe+parse sit AFTER the guarded batch, so a failure here (the real
    # dump.cs is met for the first time at runtime) must rewrite the stage
    # report as aborted BEFORE propagating — no COMPLETE decompile.json may
    # survive beside a torn _structure/.
    struct_root = ctx.extracted / STRUCTURE_REL
    try:
        common.wipe_tree(struct_root)
        catalog, hierarchy, references = parse_dump_cs(dump_cs)
        common.write_json(struct_root / "types.json", {
            "schema": "miside.structure/1", "source": "extracted/il2cpp/dump.cs",
            "type_count": len(catalog), "types": catalog})
        common.write_json(struct_root / "hierarchy.json", {
            "schema": "miside.structure/1", "nodes": hierarchy})
        common.write_json(struct_root / "references.json", {
            "schema": "miside.structure/1", "edges": references})
        common.write_text(struct_root / "README.md", (
            "# Code structure artifacts (doctrine Logic layer)\n\n"
            "Derived from `extracted/il2cpp/dump.cs` (%d types): `types.json`\n"
            "(catalog), `hierarchy.json` (base/derived edges), `references.json`\n"
            "(intra-block type reference edges). Raw source lives beside this in\n"
            "`decompiled/main/` (57 DummyDlls via ilspycmd %s) and\n"
            "`decompiled/voice-editor/` (Mono Managed set).\n\n%s\n"
            % (len(catalog), version, BODIES_CAVEAT)))
    except Exception as exc:
        # Not StageFailure alone, mirroring the batch path: any tool/OSError
        # mid-leg lands the partial-state report naming this leg, then
        # propagates unchanged — nothing swallowed, exit codes stay with the
        # driver.
        flush_aborted("structure-graph leg: %s" % exc)
        raise

    anchor_hits = {a: False for a in RECON_ANCHORS}
    main_texts = [_safe_read(p) for p in sorted(main_root.rglob("*.cs"))]
    for a in RECON_ANCHORS:
        anchor_hits[a] = any(a in text for text in main_texts)

    failed = [r for r in results if r["exit_code"] != 0]
    warnings = ["%s" % BODIES_CAVEAT]
    missing_anchors = [a for a, hit in anchor_hits.items() if not hit]
    if missing_anchors:
        warnings.append("recon anchors absent from the decompiled tree: %s"
                        % missing_anchors)

    common.update_defaults(ctx, lambda d: {**d, "tools": {
        **d.get("tools", {}),
        "ilspycmd": {**d.get("tools", {}).get("ilspycmd", {}),
                     "version": version,
                     "versionPin": TOOL_VERSION_PIN,
                     "channel": TOOL_CHANNEL,
                     # Replaces the wrong-channel GUI-zip artifact name (I-4).
                     "artifact": NUPKG_NAME,
                     "package_sha256": NUPKG_SHA256,
                     "toolDir": str(TOOL_DIR_NAME),
                     "runtime": "DOTNET_ROOT=<workroot>\\%s injected by the "
                                "stage" % DOTNET_SDK_DIR_NAME,
                     "commandPin": "ilspycmd -p -o <outdir> <dll>",
                     "verified": True}}})

    common.write_stage_report(ctx, NAME, {
        "status": "ok-with-ledgered-failures" if failed else "ok",
        "ilspycmd_version": version,
        "ilspycmd_path": str(cmd),
        "dotnet_root": str(dotnet_root) if dotnet_root else None,
        "main_assemblies_attempted": sum(1 for r in results),
        "voice_editor_assemblies": ve_count,
        "structure_types": len(catalog),
        "recon_anchor_hits": anchor_hits,
        "bodies_caveat": BODIES_CAVEAT,
        "keep_going": ctx.keep_going,
        "failed_assemblies": [r["assembly"] for r in failed],
        "attempts": results,
        "warnings": warnings,
        "duration_s": round(time.monotonic() - started, 3),
    })
    common.append_event(ctx, "decompile-run", {
        "assemblies": len(results), "failed": len(failed),
        "structure_types": len(catalog), "ilspycmd_version": version,
    })
    return {"assemblies": len(results), "failed": len(failed),
            "structure_types": len(catalog)}


def _safe_read(p: Path, limit=1 << 20) -> str:
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return ""
