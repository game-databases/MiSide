"""Entrypoint surface — AC-1, AC-2, AC-3 (spec §5).

Tier F (seconds): CLI contracts only; stage-execution tests use the
synthetic mini-root. Expected-red until pipeline/run_all.py lands.
"""

from __future__ import annotations

import re

import pytest

from conftest import STAGES, tree_hash

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------- AC-1 ----

def test_list_prints_eight_stages_in_order(make_sandbox):
    sb = make_sandbox("cli-list", stages_will_run=False)
    res = sb.run("--list", root=False)
    assert res.rc == 0, f"--list exited {res.rc}: {res.err}"
    # Parse per-line: an entry is a leading (optionally numbered) stage
    # token followed by description text — immune to substrings elsewhere.
    entries = []
    for line in res.out.splitlines():
        m = re.match(r"\s*(?:\d+[.)]?\s+)?([A-Za-z0-9_-]+)\s{2,}(\S.*)?", line)
        if m and m.group(1) in STAGES:
            entries.append((m.group(1), (m.group(2) or "").strip()))
    names = [e[0] for e in entries]
    assert STAGES == names, \
        f"--list must print exactly the 8 stages in registry order; got {names}"
    for name, desc in entries:
        assert desc, f"no one-line description after '{name}'"


def test_list_touches_nothing(make_sandbox):
    sb = make_sandbox("list-no-touch", stages_will_run=False)
    before = tree_hash(sb.path)
    res = sb.run("--list", root=False)
    assert res.rc == 0
    assert tree_hash(sb.path) == before, "--list mutated the sandbox"


# ---------------------------------------------------------------- AC-2 ----

def test_help_exit_zero_and_content(make_sandbox):
    sb = make_sandbox("cli-help", stages_will_run=False)
    res = sb.run("--help", root=False)
    assert res.rc == 0, f"--help exited {res.rc}: {res.err}"
    text = res.out
    # game-root semantics: the root holds BOTH *_Data\ AND the loose Data\
    assert "*_Data" in text, "help must explain *_Data\\ anchor"
    assert "Data" in text
    # all flags
    for flag in ("--list", "--help", "--stage", "--from", "--to",
                 "--work-root"):
        assert flag in text, f"help omits {flag}"
    # all four exit codes documented
    m = re.search(r"exit codes?", text, re.IGNORECASE)
    assert m, "help omits exit-code documentation"
    tail = text[m.end():m.end() + 400]
    for code in ("0", "2", "3", "4"):
        assert re.search(rf"\b{code}\b", tail), \
            f"exit code {code} not documented near '{m.group(0)}'"


def test_unknown_flag_is_usage_error_exit_2(make_sandbox):
    sb = make_sandbox("cli-badflag", stages_will_run=False)
    res = sb.run("--definitely-not-a-flag", root=False)
    assert res.rc == 2, f"unknown flag must exit 2, got {res.rc}"


def test_bare_invocation_is_usage_error_exit_2(make_sandbox):
    sb = make_sandbox("cli-bare", stages_will_run=False)
    res = sb.run(root=False)  # no args at all: missing required game-root
    assert res.rc == 2, f"bare invocation must exit 2, got {res.rc}"


# ---------------------------------------------------------------- AC-3 ----

def test_full_run_executes_all_stages_in_order(full_run):
    sb, man, res = full_run("cli-order")
    reports = sb.extracted / "census" / "stage-reports"
    assert reports.is_dir(), "census/stage-reports/ missing after full run"
    seen = sorted(STAGES, key=lambda s: (reports / f"{s}.json").stat().st_mtime
                  if (reports / f"{s}.json").exists() else 0)
    missing = [s for s in STAGES if not (reports / f"{s}.json").exists()]
    assert not missing, f"stage reports missing for: {missing}"
    assert seen == STAGES, f"stage execution order was {seen}"


def test_failing_stage_exit_3_names_stage_and_halts_downstream(make_mini_root):
    sb, man = make_mini_root("cli-failfast")
    # Break a detect anchor: the loc store vanishes -> detect must FAIL-FAST.
    import shutil as _sh
    _sh.rmtree(sb.game_root / "Data" / "Languages")
    res = sb.run()
    assert res.rc == 3, f"failing stage must exit 3, got {res.rc}\n{res.err}"
    assert "detect" in (res.err + res.out).lower(), \
        f"failed stage not named on stderr:\n{res.err}"
    # No downstream stage ran: il2cpp/harvest outputs absent.
    assert not (sb.extracted / "il2cpp").exists(), "S3 ran despite S2 failure"
    assert not (sb.extracted / "harvest").exists(), "S4 ran despite S2 failure"


def test_missing_dependency_outputs_exit_4(full_run):
    sb, man, _ = full_run("cli-dep4")
    # Wipe every produced output: census needs S2..S7 outputs.
    import shutil as _sh
    _sh.rmtree(sb.extracted)
    res = sb.run("--stage", "census")
    assert res.rc == 4, f"--stage census without deps must exit 4, got {res.rc}"
    hay = (res.err + res.out).lower()
    assert any(s in hay for s in ("detect", "il2cpp")), \
        f"exit 4 must name the missing upstream stage:\n{res.err}"


def test_missing_midchain_dependency_exit_4(full_run):
    sb, man, _ = full_run("cli-dep4b")
    import shutil as _sh
    _sh.rmtree(sb.extracted)
    res = sb.run("--from", "mono-typed-dump", "--to", "census")
    assert res.rc == 4
    assert "il2cpp" in (res.err + res.out).lower(), (
        f"must name il2cpp-dump as missing dependency:\n{res.err}")


def _pin_block(sb, drop_one_pin: bool = False) -> str:
    """Craft an EXTRACTION-LOG pin block in the driver's own grammar
    (mirrored from a detect-seeded log), optionally staled by dropping a
    pip pin — the disagreement class AC-3 binds the refusal to."""
    import json as _json
    reqs = [ln.strip() for ln in
            (sb.pipeline / "requirements.txt").read_text("utf-8").splitlines()
            if "==" in ln]
    if drop_one_pin and reqs:
        reqs = reqs[:-1]
    block = {
        "buildId": "19029065",
        "versionLabel": "VERSION 0.93L",
        "unity": "2021.3.35f1",
        "metadataVersion": 29,
        "tools": {
            "Il2CppDumper": {"version": "6.7.46",
                             "artifact": "Il2CppDumper-net6-win-v6.7.46.zip"},
            "AssetStudioModCLI": {"version": "0.19.0.1",
                                  "artifact": "local cycle-guarded rebuild"},
            "ilspycmd": {"version": "11.0.0.9335"},
        },
        "configDeltas": {"RequireAnyKey": False},
        "pipFreeze": reqs,
        "entrypointCommit": "stub",
    }
    return ("# EXTRACTION-LOG\n\n```json pipeline-defaults\n"
            + _json.dumps(block, indent=2) + "\n```\n")


def test_stale_extraction_log_aborts_before_s1(make_mini_root, stubs):
    sb, man = make_mini_root("cli-stale")
    sb.extracted.mkdir(parents=True, exist_ok=True)
    (sb.extracted / "EXTRACTION-LOG.md").write_text(
        _pin_block(sb, drop_one_pin=True), encoding="utf-8")
    work_before = tree_hash(sb.workroot)
    res = sb.run()
    assert res.rc != 0, "stale pin block must abort the run"
    hay = (res.err + res.out).lower()
    assert any(k in hay for k in ("stale", "pin", "extraction-log", "mismatch",
                                  "disagree", "refus")), \
        f"abort message must name the stale-log defense:\n{res.err}"
    assert tree_hash(sb.workroot) == work_before, \
        "stale-log abort happened after S1 started writing (venv touched)"


def test_matching_log_block_lets_env_proceed(make_mini_root):
    """Control for the stale-log defense: a well-formed pin block whose pins
    agree with pipeline/requirements.txt must NOT refuse. Negotiates the
    log-block grammar between suite and implementation."""
    sb, man = make_mini_root("cli-freshlog")
    sb.extracted.mkdir(parents=True, exist_ok=True)
    (sb.extracted / "EXTRACTION-LOG.md").write_text(
        _pin_block(sb), encoding="utf-8")
    res = sb.run("--stage", "env")
    assert res.rc == 0, f"matching pins must proceed past S1:\n{res.err}"
    # Offline proof: stub pip's freeze matched => install was SKIPPED
    # (no .installed marker beside the freeze file).
    assert not (sb.pipeline / "requirements.txt.installed").exists(), \
        "S1 re-installed despite matching freeze (idempotency rule broken)"
