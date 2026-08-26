"""Shared machinery for the run_all acceptance suite (spec §5, AC-1..AC-16).

Design invariants (see fixtures/README.mdx for the full contract):

* **Sandbox isolation** — every test copies the pack's ``pipeline/`` tree
  (implementation included, source unread) plus the two entrypoint shims
  into ``output/test-scratch/sbx-*`` and runs THERE. The repo's real
  ``extracted/`` is never touched; neither is the game install on A:.
* **Stub tools** — S3/S4/S7 need Il2CppDumper / AssetStudioModCLI /
  ilspycmd and S1 needs pip. Compiled-on-demand C# stubs stand in for all
  four (csc.exe from the .NET Framework ships with Windows). Stubs enforce
  spec invariants THEMSELVES (RequireAnyKey:false before spawn,
  sweep-budget-before-level-sweep) and log their argv to a side channel so
  tests can do argv-order regression without reading implementation code.
* **Blind protocol** — nothing here reads implementation source; tests
  speak only the spec's CLI/artifact language and are expected-red until
  the parallel CodeWriter lands (COVERAGE.mdx tracks which).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PACK_ROOT = TESTS_DIR.parents[1]          # .../MiSide
FIXTURES_DIR = TESTS_DIR / "fixtures"
TEMPLATES_DIR = FIXTURES_DIR / "templates"
SCRATCH_ROOT = PACK_ROOT / "output" / "test-scratch"

sys.path.insert(0, str(FIXTURES_DIR))
import builders  # noqa: E402  (synthetic fixture generators)

STAGES = ["env", "detect", "il2cpp-dump", "mono-typed-dump", "loc-jsonl",
          "art-export", "decompile", "census"]

INSTALL_ENV = "MISIDE_RUN_INSTALL_TESTS"
REAL_GAME_ROOT = Path(r"A:\SteamLibrary\steamapps\common\MiSide")

DRIVER_MISSING_MSG = (
    "pipeline/run_all.py not found in sandbox — the parallel CodeWriter has "
    "not landed yet. This suite is written to the SPEC's CLI/artifact "
    "contracts (pipeline-run_all.mdx §3/§5) and is expected-red until the "
    "implementation arrives. See pipeline/tests/COVERAGE.mdx."
)


# --------------------------------------------------------------------------
# pytest plumbing
# --------------------------------------------------------------------------

def pytest_configure(config):
    for m in ("unit", "integration", "install"):
        config.addinivalue_line("markers", f"{m}: tier marker (F/R/I per spec §6)")


def pytest_collection_modifyitems(config, items):
    # Install tier: opt-in via env AND presence of the real game root;
    # CI/default runs skip it cheaply.
    if os.environ.get(INSTALL_ENV) == "1" and REAL_GAME_ROOT.is_dir():
        return
    skip = pytest.mark.skip(reason=(
        f"install tier: set {INSTALL_ENV}=1 (and require {REAL_GAME_ROOT}) "
        "to run against the real client"))
    for item in items:
        if "install" in item.keywords:
            item.add_marker(skip)


# --------------------------------------------------------------------------
# session-scoped resources
# --------------------------------------------------------------------------

@pytest.fixture(scope="session")
def pack_root() -> Path:
    return PACK_ROOT


def _find_csc() -> Path | None:
    for frame in ("Framework64", "Framework"):
        cand = Path(rf"C:\Windows\Microsoft.NET\{frame}\v4.0.30319\csc.exe")
        if cand.exists():
            return cand
    return None


def _compile(src: Path, out: Path, csc: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(csc), "/nologo", "/warn:0", "/target:exe",
           f"/out:{out}", str(src)]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"csc failed for {src.name}:\n"
                           f"{proc.stdout.decode(errors='replace')}\n"
                           f"{proc.stderr.decode(errors='replace')}")


@pytest.fixture(scope="session")
def stubs() -> dict[str, Path]:
    """Compile the four stub exes once per session (cached by source hash)."""
    csc = _find_csc()
    if csc is None:
        pytest.skip("no csc.exe (.NET Framework 4) — cannot build stub tools; "
                    "fixture/integration tiers require them (see fixtures/README.mdx)")
    bin_root = SCRATCH_ROOT / "stubbin"
    out: dict[str, Path] = {}
    jobs = {
        "Il2CppDumper.exe": "stub_il2cpp.cs",
        "AssetStudioModCLI.exe": "stub_assetstudio.cs",
        "ilspycmd.exe": "stub_ilspy.cs",
        "pip.exe": "stub_pip.cs",
    }
    key = hashlib.sha256(
        b"".join((FIXTURES_DIR / src).read_bytes() for src in jobs.values())
    ).hexdigest()[:12]
    marker = bin_root / f".cache-{key}"
    if not marker.exists():
        if bin_root.exists():
            shutil.rmtree(bin_root, ignore_errors=True)
    for exe, src in jobs.items():
        dst = bin_root / key / src.replace(".cs", "") / exe
        if not dst.exists():
            _compile(FIXTURES_DIR / src, dst, csc)
        out[exe] = dst
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(key)
    return out


class Sandbox:
    """An isolated copy of the pack entrypoint (pipeline/ + shims) plus the
    stub-tool seams, living wholly under output/test-scratch."""

    def __init__(self, path: Path, stub_map: dict[str, Path]):
        self.path = path
        self.pipeline = path / "pipeline"
        self.game_root = path / "game-root"
        self._stubs = stub_map

    # -- locations --------------------------------------------------------
    @property
    def extracted(self) -> Path:
        return self.path / "extracted"

    @property
    def workroot(self) -> Path:
        return self.path / "work"

    @property
    def stub_log(self) -> Path:
        return self.path / "stub-log.jsonl"

    # -- construction ------------------------------------------------------
    def seed_tools(self) -> None:
        """Place stub exes at every seam the spec names: ready-made dirs in
        the workroot AND release zips in the sandbox's repo-tools layout, so
        either implementation strategy ('unzipped once' vs re-unzip) finds
        stub bytes."""
        wr = self.workroot
        il2cpp_dir = wr / "tools" / "Il2CppDumper"
        il2cpp_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self._stubs["Il2CppDumper.exe"], il2cpp_dir / "Il2CppDumper.exe")
        (il2cpp_dir / "config.json").write_text('{"RequireAnyKey": true}')  # stock; driver must flip

        for sub in ("AssetStudioModCLI", "AssetStudioModCLI_net8_portable"):
            d = wr / "tools" / sub
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._stubs["AssetStudioModCLI.exe"], d / "AssetStudioModCLI.exe")
        for sub in ("ILSpy", "ilspycmd"):
            d = wr / "tools" / sub
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._stubs["ilspycmd.exe"], d / "ilspycmd.exe")

        # Repo-side release zips (names pinned by docs/spec §S3/S4/S7).
        def zip_tool(zip_rel: str, exe_key: str, extra: dict[str, bytes] | None = None):
            zp = self.path / zip_rel
            zp.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zp, "w") as z:
                z.write(self._stubs[exe_key], exe_key)
                for name, data in (extra or {}).items():
                    z.writestr(name, data)

        zip_tool("tools/Il2CppDumper/release/Il2CppDumper-net6-win-v6.7.46.zip",
                 "Il2CppDumper.exe", {"config.json": b'{"RequireAnyKey": true}'})
        zip_tool("tools/AssetStudioMod/release/AssetStudioModCLI_net8_portable.zip",
                 "AssetStudioModCLI.exe")
        zip_tool("tools/ILSpy/release/ILSpy_windows_selfcontained_11.0.0.9335-rc-x64.zip",
                 "ilspycmd.exe")

        # The implementation resolved release zips one level above the
        # sandbox (scratch root) when no --work-root was given; mirror the
        # seam there too so either resolution finds stub bytes.
        for rel, exe_key, extra in (
            ("Il2CppDumper/release/Il2CppDumper-net6-win-v6.7.46.zip",
             "Il2CppDumper.exe", {"config.json": b'{"RequireAnyKey": true}'}),
            ("AssetStudioMod/release/AssetStudioModCLI_net8_portable.zip",
             "AssetStudioModCLI.exe", None),
            ("ILSpy/release/ILSpy_windows_selfcontained_11.0.0.9335-rc-x64.zip",
             "ilspycmd.exe", None),
        ):
            zp = SCRATCH_ROOT / "tools" / rel
            if zp.exists():
                continue
            zp.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zp, "w") as z:
                z.write(self._stubs[exe_key], exe_key)
                for name, data in (extra or {}).items():
                    z.writestr(name, data)

    def seed_venv(self) -> None:
        """Pre-stage workroot\\venv with the stub pip so S1 stays offline:
        freeze reads the sandbox's own requirements.txt (=> pin match =>
        install skipped, per spec S1 idempotency rule)."""
        scripts = self.workroot / "venv" / "Scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        (self.workroot / "venv" / "pyvenv.cfg").write_text("home = stub\nversion = 3.14\n")
        shutil.copy2(self._stubs["pip.exe"], scripts / "pip.exe")

    def seed_requirements(self) -> None:
        req = self.pipeline / "requirements.txt"
        if not req.exists():
            req.write_text(
                "# stub pins (real file arrives with the implementation)\n",
                encoding="utf-8")

    # -- invocation ---------------------------------------------------------
    def run(self, *args: str, timeout: int = 300, env_extra: dict | None = None,
            root: bool = True):
        """Run the driver. ``root=False`` omits the game-root positional
        (--help / --list forms per spec §3)."""
        driver = self.pipeline / "run_all.py"
        if not driver.exists():
            return RunResult(-99, "", DRIVER_MISSING_MSG)
        argv = [sys.executable, str(driver)]
        if root:
            argv.append(str(self.game_root))
        if "--work-root" not in args:
            argv.extend(["--work-root", str(self.workroot)])
        argv.extend(args)
        env = dict(os.environ)
        env.update({
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",  # .pyc litter is not a driver write
            "MISIDE_STUB_LOG": str(self.stub_log),
            "MISIDE_STUB_ASSETS": str(TEMPLATES_DIR),
            "MISIDE_STUB_PIP_FREEZE": str(self.pipeline / "requirements.txt"),
            "MISIDE_STUB_SWEEP_BUDGET":
                str(self.extracted / "census" / "sweep-budget.json"),
        })
        if env_extra:
            env.update(env_extra)
        proc = subprocess.run(argv, capture_output=True, cwd=self.path,
                              timeout=timeout, env=env)
        return RunResult(proc.returncode,
                         proc.stdout.decode("utf-8", errors="replace"),
                         proc.stderr.decode("utf-8", errors="replace"))

    def run_shim_cmd(self, *args: str, timeout: int = 120):
        if not (self.path / "run_all.cmd").exists():
            return RunResult(-99, "", DRIVER_MISSING_MSG + " (run_all.cmd)")
        # Absolute path: cmd's current-dir lookup is disabled under
        # NoDefaultCurrentDirectoryInExePath on some hosts.
        proc = subprocess.run(["cmd", "/c", str(self.path / "run_all.cmd"), *args],
                              capture_output=True, cwd=self.path, timeout=timeout)
        return RunResult(proc.returncode,
                         proc.stdout.decode("utf-8", errors="replace"),
                         proc.stderr.decode("utf-8", errors="replace"))

    def run_shim_sh(self, *args: str, timeout: int = 120):
        if not (self.path / "run_all").exists():
            return RunResult(-99, "", DRIVER_MISSING_MSG + " (shim `run_all`)")
        bash = shutil.which("bash") or r"C:\Program Files\Git\bin\bash.exe"
        proc = subprocess.run([bash, "./run_all", *args],
                              capture_output=True, cwd=self.path, timeout=timeout)
        return RunResult(proc.returncode,
                         proc.stdout.decode("utf-8", errors="replace"),
                         proc.stderr.decode("utf-8", errors="replace"))

    # -- inspection ----------------------------------------------------------
    def state(self, sub: str = "extracted") -> dict[str, str]:
        return tree_hash(self.path / sub)

    def stub_calls(self, tool: str) -> list[dict]:
        return [row for row in parse_stub_log(self.stub_log)
                if row.get("tool") == tool]


class RunResult:
    def __init__(self, rc: int, out: str, err: str):
        self.rc, self.out, self.err = rc, out, err

    def __repr__(self):  # pragma: no cover
        return f"<RunResult rc={self.rc} out={self.out[:120]!r} err={self.err[:200]!r}>"


@pytest.fixture()
def make_sandbox(stubs):
    def _make(name: str, *, stages_will_run: bool = True) -> Sandbox:
        if stages_will_run:
            free = shutil.disk_usage(SCRATCH_ROOT).free
            if free < 10 * 1024**3:
                pytest.skip(f"only {free / 1024**3:.1f} GiB free on scratch "
                            "volume — integration tier mirrors the 10 GiB S2 guard")
        SCRATCH_ROOT.mkdir(parents=True, exist_ok=True)
        sb_path = SCRATCH_ROOT / f"sbx-{name}"
        if sb_path.exists():
            shutil.rmtree(sb_path)
        sb_path.mkdir(parents=True)

        # Copy the implementation tree BLIND (contents never read here).
        if (PACK_ROOT / "pipeline").is_dir():
            shutil.copytree(PACK_ROOT / "pipeline", sb_path / "pipeline",
                            ignore=shutil.ignore_patterns(
                                "tests", "__pycache__", "*.pyc"))
        for shim in ("run_all.cmd", "run_all"):
            src = PACK_ROOT / shim
            if src.exists():
                shutil.copy2(src, sb_path / shim)

        sb = Sandbox(sb_path, stubs)
        sb.seed_requirements()
        if stages_will_run:
            sb.seed_tools()
            sb.seed_venv()
        return sb
    return _make


@pytest.fixture()
def make_mini_root(make_sandbox):
    """Sandbox + fully synthetic game root R + its expectation manifest."""
    def _make(name: str, *, build_languages_only: bool = False):
        sb = make_sandbox(name)
        if build_languages_only:
            man = builders.build_mini_loc(sb.game_root)
        else:
            man = builders.build_mini_root(sb.game_root)
        return sb, man
    return _make


@pytest.fixture()
def full_run(make_mini_root):
    """A completed full pipeline run against a fresh synthetic root."""
    def _make(name: str):
        sb, man = make_mini_root(name)
        res = sb.run()
        if res.rc != 0:
            pytest.fail(f"sandbox {name}: full run exited {res.rc}; "
                        f"stderr:\n{res.err[-2000:]}")
        return sb, man, res
    return _make


# --------------------------------------------------------------------------
# comparison helpers
# --------------------------------------------------------------------------

def tree_hash(root: Path) -> dict[str, str]:
    """relpath -> sha256 of content (mtimes ignored by construction)."""
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = hashlib.sha256(
                p.read_bytes()).hexdigest()
    return out


def load_volatile_tokens(extracted: Path) -> set[str]:
    """Every string appearing anywhere in census/volatile-fields.json —
    keys and values alike — lowercased. Schema-free on purpose: whatever
    field/path vocabulary the implementation enumerates counts as exempt."""
    vf = extracted / "census" / "volatile-fields.json"
    tokens: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                tokens.add(str(k).lower())
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str):
            tokens.add(node.lower())

    if vf.exists():
        try:
            walk(json.loads(vf.read_text("utf-8")))
        except json.JSONDecodeError:
            pass
    tokens.discard("")
    return tokens


def load_volatile_registry(extracted: Path) -> dict[str, set[str]]:
    """Parse census/volatile-fields.json into {path-or-pattern: {field, ...}}.
    Tolerant of shape: accepts {'fields': {...}} or a flat mapping."""
    vf = extracted / "census" / "volatile-fields.json"
    out: dict[str, set[str]] = {}
    if not vf.exists():
        return out
    try:
        data = json.loads(vf.read_text("utf-8"))
    except json.JSONDecodeError:
        return out
    table = data.get("fields", data) if isinstance(data, dict) else {}
    if not isinstance(table, dict):
        return out
    for path, fields in table.items():
        if isinstance(fields, dict):  # alternate shape: {field: desc}
            fields = list(fields)
        if isinstance(fields, list):
            out[path] = {str(f) for f in fields}
    return out


def _pattern_match(rel: str, pattern: str) -> bool:
    import re
    rx = re.escape(pattern).replace(r"\<stage\>", "[^/]+")
    return re.fullmatch(rx, rel) is not None


def _volatile_fields_for(rel: str, registry: dict[str, set[str]]) -> set[str]:
    for pattern, fields in registry.items():
        if _pattern_match(rel, pattern):
            return fields
    return set()


def _mask_json_fields(text: str, fields: set[str]):
    """Load JSON or JSONL and drop volatile-enumerated keys recursively.
    Returns None if the text is neither."""
    stripped = text.strip()
    if not stripped:
        return None

    def mask(node):
        if isinstance(node, dict):
            return {k: mask(v) for k, v in node.items() if k not in fields}
        if isinstance(node, list):
            return [mask(v) for v in node]
        return node

    try:
        if stripped[0] in "{[":
            return mask(json.loads(stripped))
        rows = [json.loads(l) for l in stripped.splitlines() if l.strip()]
        return [mask(r) for r in rows]
    except (json.JSONDecodeError, ValueError):
        return None


def idempotency_violations(before: dict[str, str], after: dict[str, str],
                           extracted: Path) -> list[str]:
    """AC-5: rerun may change nothing except the volatile fields enumerated
    in census/volatile-fields.json — plus, for census/stage-reports/*.json
    only, top-level BOOLEAN keys, which AC-5 names "stage-report run facts"
    (e.g. venv created:true→false on an idempotent rerun). Comparison is
    field-aware; anything else that changes a byte is a violation."""
    registry = load_volatile_registry(extracted)
    tokens = load_volatile_tokens(extracted)
    bad = []
    for rp in sorted(set(before) | set(after)):
        if rp not in after:
            bad.append(f"DISAPPEARED: {rp}")
            continue
        if rp not in before:
            bad.append(f"APPEARED: {rp}")
            continue
        if before[rp] == after[rp]:
            continue
        fields = set(_volatile_fields_for(rp, registry))
        is_stage_report = rp.startswith("census/stage-reports/") \
            and rp.endswith(".json")
        if fields or is_stage_report:
            old_b = (extracted / rp).read_bytes() if (extracted / rp).exists() else b""
            new_b = (extracted / rp).read_bytes()
            old_t = old_b.decode("utf-8", errors="replace")
            new_t = new_b.decode("utf-8", errors="replace")
            old_j, new_j = _mask_json_fields(old_t, fields), \
                _mask_json_fields(new_t, fields)
            if None not in (old_j, new_j):
                if is_stage_report and isinstance(old_j, dict) \
                        and isinstance(new_j, dict):
                    old_j = {k: v for k, v in old_j.items()
                             if not isinstance(v, bool)}
                    new_j = {k: v for k, v in new_j.items()
                             if not isinstance(v, bool)}
                if old_j == new_j:
                    continue
                bad.append(f"CONTENT CHANGED (beyond volatile fields): {rp}\n"
                           f"    before: {json.dumps(old_j, sort_keys=True)[:300]}\n"
                           f"    after:  {json.dumps(new_j, sort_keys=True)[:300]}")
                continue
        low = rp.lower()
        if any(t in low for t in tokens):
            continue  # whole-file exemption via path token
        bad.append(f"CONTENT CHANGED (non-volatile): {rp}")
    return bad


def parse_stub_log(log: Path) -> list[dict]:
    if not log.exists():
        return []
    rows = []
    for line in log.read_text("utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text("utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def assert_stage_subtree_unchanged(sb: Sandbox, snapshot: dict[str, str],
                                   subtree: str) -> None:
    """AC-4 helper: a --stage rerun reproduces its own subtree byte-wise,
    modulo volatile fields."""
    now = sb.state(subtree)
    bad = idempotency_violations(snapshot, now, sb.extracted)
    assert not bad, f"--stage {subtree} rerun drifted:\n" + "\n".join(bad)
