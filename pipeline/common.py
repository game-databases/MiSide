"""Shared helpers for the MiSide `run_all` pipeline.

Stdlib-only by design: the driver runs on any interpreter; stages that need
UnityPy/Pillow spawn the pack venv's python explicitly (child entry points in
`pipeline.stages.mono_typed_dump` and `pipeline.stages.art_export`).

Spec: docs/specs/pipeline-run_all.mdx §3-§4. Windows-first: every child
process gets absolute backslash paths via list argv (never a shell string) —
the MSYS-mangling class is retired by construction.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants pinned by the spec

DEFAULT_WORK_ROOT = r"D:\unpacked_game_data\MiSide\work"
FREE_SPACE_MIN_GB = 10  # ~10 GB headroom bar, checked at S2 and re-fired (AC-14)

# Run-varying fields exempt from byte-identity comparison (spec §3, AC-4/AC-5).
# Key = artifact path under extracted/ ("*" matches any stage report);
# value = JSON dot-paths within that artifact that may vary between runs.
VOLATILE_FIELDS = {
    "census/detect.json": ["measured_at"],
    "census/sweep-budget.json": ["measured_at", "probe_wall_time_s", "wall_time_s"],
    "census/sweep-attempts.jsonl": ["duration_s", "measured_at"],
    "census/stage-reports/<stage>.json": ["measured_at", "duration_s", "host",
                                          "free_space_bytes"],
}

# Container name families inside MiSideFull_Data (E1 §Step 4 census shape).
RE_GGM = re.compile(r"^globalgamemanagers$")
RE_GGM_ASSETS = re.compile(r"^globalgamemanagers\.assets$")
RE_RESOURCES = re.compile(r"^resources\.assets$")
RE_SHARED = re.compile(r"^sharedassets(\d+)\.assets$")
RE_LEVEL = re.compile(r"^level(\d+)$")
STREAM_SUFFIXES = (".resS", ".resource")

FAMILY_ORDER = {"globalgamemanagers": 0, "globalgamemanagers.assets": 1,
                "resources.assets": 2, "sharedassets": 3, "level": 4}


class StageFailure(Exception):
    """A stage failed: driver exits 3 naming the stage on stderr."""

    def __init__(self, stage: str, reason: str):
        super().__init__(f"{stage}: {reason}")
        self.stage = stage
        self.reason = reason


class MissingDependency(Exception):
    """Dependency outputs absent: driver exits 4 naming the missing stage."""

    def __init__(self, stage: str, dep: str):
        super().__init__(
            f"missing dependency outputs: '{dep}' is required by '{stage}' "
            f"— run the earlier stage first")
        self.stage = stage
        self.dep = dep


class UsageError(Exception):
    """Semantic CLI misuse beyond argparse's own: driver exits 2."""


# ---------------------------------------------------------------------------
# Run context

@dataclass
class RunContext:
    pack_root: Path
    game_root: Path
    work_root: Path
    keep_going: bool = False
    expect_drift: bool = False
    defaults: dict = field(default_factory=dict)

    @property
    def extracted(self) -> Path:
        return self.pack_root / "extracted"

    @property
    def data_dir(self) -> Path:
        return self.game_root / "MiSideFull_Data"

    @property
    def venv_dir(self) -> Path:
        return self.work_root / "venv"

    @property
    def venv_python(self) -> Path:
        return self.venv_dir / "Scripts" / "python.exe"

    @property
    def venv_pip(self) -> Path:
        return self.venv_dir / "Scripts" / "pip.exe"

    @property
    def tools_dir(self) -> Path:
        return self.work_root / "tools"

    @property
    def repo_root(self) -> Path:
        return self.pack_root.parent

    @property
    def requirements(self) -> Path:
        return self.pack_root / "pipeline" / "requirements.txt"

    @property
    def extraction_log(self) -> Path:
        return self.extracted / "EXTRACTION-LOG.md"

    @property
    def census_dir(self) -> Path:
        return self.extracted / "census"


def win(path) -> str:
    """Absolute backslash path string — the only form handed to child exes."""
    return str(Path(path).resolve())


# ---------------------------------------------------------------------------
# Subprocess (list argv, no shell — per-tool child-cwd pinning at call sites)

def run_argv(argv, cwd=None, timeout=None, env=None):
    """Run a child with a list argv (never shell-interpolated).

    env=None inherits the parent environment; a stage that must pin a
    variable into its child (e.g. S7's DOTNET_ROOT) passes a full dict.
    """
    return subprocess.run(
        [os.fspath(a) if not isinstance(a, str) else a for a in argv],
        cwd=None if cwd is None else str(cwd), timeout=timeout,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
        env=None if env is None else dict(env))


def run_tool(stage: str, argv, cwd=None, timeout=None):
    """run_argv + FAIL-FAST on non-zero exit, stderr tail in the message."""
    proc = run_argv(argv, cwd=cwd, timeout=timeout)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-15:]
        raise StageFailure(stage, "command failed (%s) rc=%s:\n%s" % (
            Path(argv[0]).name, proc.returncode, "\n".join(tail)))
    return proc


# ---------------------------------------------------------------------------
# Deterministic artifact writers (idempotency by construction, spec §2 S4)

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_json(path: Path, obj) -> None:
    write_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def write_jsonl(path: Path, rows) -> None:
    """Deterministic full rewrite — ledger artifacts are never appended to."""
    lines = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    write_text(path, lines)


def read_jsonl(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
    except OSError:
        return []


def wipe_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Small facts

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def host() -> str:
    return socket.gethostname()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_lines_split(path: Path) -> int:
    """Split-based line count (files carry no trailing newline — E1 dev 3)."""
    total = 0
    last = b"\n"
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            total += chunk.count(b"\n")
            last = chunk[-1:]
    return total + (0 if last == b"\n" else 1)


def git_head(pack_root: Path) -> str:
    try:
        proc = run_argv(["git", "rev-parse", "--short", "HEAD"], cwd=pack_root)
        if proc.returncode == 0:
            return proc.stdout.strip()
    except OSError:
        pass
    return ""


# ---------------------------------------------------------------------------
# Free-space guard (Get-Volume equivalent; re-fireable — AC-14)

def free_space_bytes(path: Path) -> int:
    drive_root = Path(os.path.splitdrive(str(Path(path).resolve()))[0] + "\\")
    if os.name == "nt":
        free = ctypes.c_ulonglong(0)
        ok = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            str(drive_root), None, None, ctypes.byref(free))
        if ok:
            return free.value
    total, used, free = shutil.disk_usage(str(drive_root))
    return free


def guard_free_space(stage: str, *paths, min_gb: int = FREE_SPACE_MIN_GB) -> dict:
    """Abort before writes when any target drive has < min_gb headroom."""
    seen = {}
    for p in paths:
        drive = os.path.splitdrive(str(Path(p).resolve()))[0]
        if drive and drive not in seen:
            seen[drive] = free_space_bytes(p)
    short = {d: b for d, b in seen.items() if b < min_gb << 30}
    if short:
        detail = ", ".join("%s %.1f GiB free" % (d, b >> 30) for d, b in sorted(short.items()))
        raise StageFailure(stage, "free-space guard: %s (need >= %d GiB)" % (detail, min_gb))
    return {d: b for d, b in seen.items()}


# ---------------------------------------------------------------------------
# Volatile-fields registry maintenance (driver-owned, spec §3)

def write_volatile_fields(ctx: RunContext) -> None:
    write_json(ctx.census_dir / "volatile-fields.json",
               {"schema": "miside.volatile-fields/1",
                "note": ("Enumerated run-varying fields exempt from byte-identity "
                         "comparison (idempotency = same data, not same clock). "
                         "'<stage>.json' matches every census/stage-reports file."),
                "fields": VOLATILE_FIELDS})


def stage_report_path(ctx: RunContext, stage: str) -> Path:
    return ctx.census_dir / "stage-reports" / ("%s.json" % stage)


def write_stage_report(ctx: RunContext, stage: str, report: dict) -> Path:
    report = {"stage": stage, "host": host(), "measured_at": utc_now_iso(), **report}
    path = stage_report_path(ctx, stage)
    write_json(path, report)
    write_volatile_fields(ctx)
    return path


# ---------------------------------------------------------------------------
# EXTRACTION-LOG.md — `pipeline-defaults` block reader/writer (spec §3)

_EVENT_RE = re.compile(r"<!-- event:([a-z0-9\-]+):([0-9a-f]{8}) -->")


def _split_defaults_block(text: str):
    """Return (start_line, end_line_exclusive) of the fenced block, or None."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```") and "pipeline-defaults" in stripped:
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "```":
                    return i, j + 1
            return None
    return None


def read_defaults(ctx: RunContext):
    """Parse the ```json pipeline-defaults``` block; None when absent/broken."""
    try:
        text = ctx.extraction_log.read_text(encoding="utf-8")
    except OSError:
        return None
    span = _split_defaults_block(text)
    if span is None:
        return None
    body = "\n".join(text.split("\n")[span[0] + 1:span[1] - 1])
    try:
        return json.loads(body)
    except ValueError:
        return None


def seed_defaults(ctx: RunContext, defaults: dict) -> bool:
    """Create extracted/EXTRACTION-LOG.md with the pin block when absent."""
    if ctx.extraction_log.exists():
        return False
    header = (
        "# EXTRACTION-LOG — MiSide\n"
        "\n"
        "Pins for the `run_all` pipeline. The fenced block below is machine-read\n"
        "by the driver (`pipeline/run_all.py`); human event sections follow it.\n"
        "Discipline: tool + version + buildId pinned here, updated in the same\n"
        "commit as the entrypoint ([DR-2026-08-18-pipeline]).\n")
    block = "```json pipeline-defaults\n%s```\n" % (
        json.dumps(defaults, indent=2, ensure_ascii=False) + "\n")
    write_text(ctx.extraction_log, header + "\n" + block + "\n## Run events\n")
    return True


def update_defaults(ctx: RunContext, mutate) -> bool:
    """Apply mutate(defaults)->defaults in place; True when bytes changed.

    Upsert semantics: values are replaced, never appended as new lines, so a
    rerun over unchanged facts leaves the log byte-stable (AC-5 record dedupe).
    """
    try:
        text = ctx.extraction_log.read_text(encoding="utf-8")
    except OSError:
        return False
    span = _split_defaults_block(text)
    if span is None:
        return False
    lines = text.split("\n")
    try:
        current = json.loads("\n".join(lines[span[0] + 1:span[1] - 1]))
    except ValueError:
        return False
    updated = mutate(json.loads(json.dumps(current)))
    if updated == current:
        return False
    body = json.dumps(updated, indent=2, ensure_ascii=False)
    lines = lines[:span[0] + 1] + body.split("\n") + lines[span[1] - 1:]
    write_text(ctx.extraction_log, "\n".join(lines))
    return True


def append_event(ctx: RunContext, key: str, payload: dict) -> bool:
    """Append a dated run-event section, deduped by payload signature.

    Payload must contain no volatile values (clock, wall time, host). Same
    inputs again => same signature => no new line (AC-5).
    """
    sig = sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))[:8]
    marker = "<!-- event:%s:%s -->" % (key, sig)
    try:
        text = ctx.extraction_log.read_text(encoding="utf-8")
    except OSError:
        return False
    if marker in text or _split_defaults_block(text) is None:
        return False
    day = datetime.now(timezone.utc).date().isoformat()
    bullets = "\n".join("- `%s`: %r" % (k, v) for k, v in sorted(payload.items()))
    section = "\n## %s — %s (%s)\n%s\n%s\n" % (day, key, sig, marker, bullets)
    write_text(ctx.extraction_log, text.rstrip("\n") + "\n" + section)
    return True


# ---------------------------------------------------------------------------
# requirements.txt <-> pip freeze (stale-log defense, AC-3)

def parse_requirements(path: Path) -> dict:
    pins = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if "==" not in line:
            raise UsageError("pipeline/requirements.txt carries a non-pinned line: %r" % line)
        name, ver = line.split("==", 1)
        pins[name.strip().lower()] = ver.strip()
    return pins


def freeze_map(freeze_output: str) -> dict:
    pins = {}
    for line in freeze_output.splitlines():
        if "==" in line:
            name, ver = line.split("==", 1)
            pins[name.strip().lower()] = ver.strip()
    return pins


def stale_log_defense(ctx: RunContext) -> None:
    """Refuse to run when the LOG's pipFreeze disagrees with requirements.txt."""
    defaults = read_defaults(ctx)
    if defaults is None:
        return  # no LOG yet: S2 seeds it on first run
    pins = parse_requirements(ctx.requirements)
    logged = freeze_map("\n".join(defaults.get("pipFreeze", [])))
    if logged != pins:
        missing = sorted(set(pins) - set(logged))
        extra = sorted(set(logged) - set(pins))
        changed = sorted(k for k in set(pins) & set(logged) if pins[k] != logged[k])
        raise StageFailure(
            "env",
            "stale EXTRACTION-LOG.md pin block: pipFreeze disagrees with "
            "pipeline/requirements.txt (missing=%s extra=%s changed=%s) — update "
            "the pin block in the same commit as the entrypoint" % (
                missing or "[]", extra or "[]", changed or "[]"))
    for key in ("buildId", "versionLabel", "unity", "metadataVersion", "tools",
                "entrypointCommit"):
        if key not in defaults:
            raise StageFailure(
                "env", "stale EXTRACTION-LOG.md pin block: missing key '%s'" % key)


# ---------------------------------------------------------------------------
# Container census primitives (shared by S2 detect and S8 re-verification)

def classify_container(name: str):
    """Return (family, index) for SerializedFile-class names, else None."""
    if RE_GGM.match(name):
        return ("globalgamemanagers", None)
    if RE_GGM_ASSETS.match(name):
        return ("globalgamemanagers.assets", None)
    if RE_RESOURCES.match(name):
        return ("resources.assets", None)
    m = RE_SHARED.match(name)
    if m:
        return ("sharedassets", int(m.group(1)))
    m = RE_LEVEL.match(name)
    if m:
        return ("level", int(m.group(1)))
    return None


def is_stream_sibling(name: str) -> bool:
    return name.endswith(STREAM_SUFFIXES)


def census_data_dir(data_dir: Path) -> dict:
    """Walk MiSideFull_Data top level once; classify into E1's families."""
    serialized, streams, other = [], [], []
    with os.scandir(data_dir) as it:
        for entry in it:
            if not entry.is_file():
                continue
            name, size = entry.name, entry.stat().st_size
            fam = classify_container(name)
            if fam is not None:
                serialized.append({"family": fam[0], "index": fam[1],
                                   "name": name, "bytes": size})
            elif is_stream_sibling(name):
                streams.append({"name": name, "bytes": size})
            else:
                other.append({"name": name, "bytes": size})
    serialized.sort(key=lambda r: (FAMILY_ORDER[r["family"]],
                                   r["index"] if r["index"] is not None else -1,
                                   r["name"]))
    streams.sort(key=lambda r: r["name"])
    other.sort(key=lambda r: r["name"])
    ser_bytes = sum(r["bytes"] for r in serialized)
    str_bytes = sum(r["bytes"] for r in streams)
    return {
        "serialized": serialized,
        "streams": streams,
        "other_top_level": other,
        "totals": {
            "serialized_count": len(serialized),
            "serialized_bytes": ser_bytes,
            "stream_count": len(streams),
            "stream_bytes": str_bytes,
            "grand_total_bytes": ser_bytes + str_bytes,
        },
    }


def container_order(rows) -> list:
    """Sweep order: ggm, ggm.assets, resources.assets, sharedassetsN, levelN."""
    return sorted(rows, key=lambda r: (FAMILY_ORDER[r["family"]],
                                       r["index"] if r["index"] is not None else -1))


# ---------------------------------------------------------------------------
# Game-root anchors (argument semantics, spec header)

def find_build_id(game_root: Path):
    """Best-effort buildId from the sibling steamapps appmanifest (read-only)."""
    steamapps = game_root.parent.parent
    if not steamapps.is_dir():
        return None
    want = game_root.name.lower()
    acf_re = re.compile(r'"(buildid|name|installdir)"\s+"([^"]*)"')
    for acf in sorted(steamapps.glob("appmanifest_*.acf")):
        try:
            fields = dict(acf_re.findall(acf.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            continue
        if fields.get("installdir", "").lower() == want or \
                fields.get("name", "").lower() == want.replace("-", " "):
            bid = fields.get("buildid")
            if bid:
                return bid
    return None


def require_anchor(stage: str, path: Path, label: str) -> int:
    if not path.exists():
        raise StageFailure(stage, "missing anchor: %s (%s)" % (label, path))
    return path.stat().st_size if path.is_file() else 0
