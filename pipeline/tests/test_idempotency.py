"""Isolation & idempotency — AC-4, AC-5.

Idempotency means same data, not same clock: comparisons run modulo the
volatile fields enumerated in census/volatile-fields.json (schema-free
token match — whatever the implementation enumerates is exempt; anything
else that changes a byte fails).
"""

from __future__ import annotations

import json

import pytest

from conftest import (STAGES, assert_stage_subtree_unchanged, tree_hash,
                      idempotency_violations, load_volatile_tokens)

pytestmark = pytest.mark.integration


def test_volatile_fields_registry_exists(full_run):
    sb, man, _ = full_run("idem-volatile")
    vf = sb.extracted / "census" / "volatile-fields.json"
    assert vf.exists(), "driver must maintain census/volatile-fields.json"
    data = json.loads(vf.read_text("utf-8"))
    assert data is not None


def test_full_rerun_changes_no_nonenumerated_byte(full_run):
    """AC-5: consecutive double-run of the whole pipeline."""
    sb, man, _ = full_run("idem-double2")
    before = sb.state("extracted")
    log_before = (sb.extracted / "EXTRACTION-LOG.md").read_text("utf-8",
                                                                errors="replace")
    res = sb.run()
    assert res.rc == 0, f"second full run failed:\n{res.err}"
    bad = idempotency_violations(before, sb.state("extracted"), sb.extracted)
    assert not bad, "rerun drifted:\n" + "\n".join(bad[:20])

    # Record dedupe: unchanged tool set + buildId + inputs => EXTRACTION-LOG
    # gains NO new line.
    log_after = (sb.extracted / "EXTRACTION-LOG.md").read_text("utf-8",
                                                               errors="replace")
    assert len(log_after.splitlines()) <= len(log_before.splitlines()), \
        "EXTRACTION-LOG.md gained lines on an unchanged rerun"
    for line in log_before.splitlines():
        if line.strip():
            assert line in log_after.splitlines(), \
                f"EXTRACTION-LOG lost/rewrote line: {line!r}"


STAGE_SUBTREES = {
    "detect": ["census/detect.json"],
    "il2cpp-dump": ["il2cpp"],
    "mono-typed-dump": ["harvest"],
    "loc-jsonl": ["localization"],
    "art-export": ["art", "MEDIA-CATALOGUE.md", "media-catalogue.jsonl"],
    "decompile": ["decompiled"],
    "census": ["PROOF.md"],
}


def test_stage_isolation_matches_full_run_outputs(full_run):
    """AC-4: each --stage rerun reproduces byte-identical outputs (modulo
    volatile fields) to what the same stage produced inside a full run."""
    sb, man, _ = full_run("idem-isolation2")
    snapshot = sb.state("extracted")

    def slice_state(sub: str, prefixes: list[str]) -> dict[str, str]:
        return {k: v for k, v in sub.items()
                if any(k == p or k.startswith(p + "/") for p in prefixes)}

    for stage in STAGES[1:]:
        res = sb.run("--stage", stage)
        assert res.rc == 0, f"--stage {stage} failed:\n{res.err}"
        now = sb.state("extracted")
        prefixes = STAGE_SUBTREES[stage]
        bad = idempotency_violations(slice_state(snapshot, prefixes),
                                     slice_state(now, prefixes),
                                     sb.extracted)
        assert not bad, f"--stage {stage} output differs from full run:\n" \
            + "\n".join(bad)


def test_ledger_style_artifacts_deterministic(full_run):
    """S4 write mode: ledger-style artifacts are fully rewritten per run,
    never appended -> clean consecutive runs reproduce them byte-wise."""
    sb, man, _ = full_run("idem-ledgers")
    paths = [
        sb.extracted / "census" / "sweep-attempts.jsonl",
        sb.extracted / "localization" / "_ledger" / "locale-delta.jsonl",
        sb.extracted / "census" / "detect.json",
    ]
    before = {p: p.read_bytes() for p in paths if p.exists()}
    res = sb.run("--stage", "loc-jsonl")   # any cheap stage re-touches its own ledgers
    assert res.rc == 0, res.err
    res = sb.run("--stage", "mono-typed-dump")
    assert res.rc == 0, res.err
    for p, old in before.items():
        if p.exists():
            new = p.read_bytes()
            if old != new:
                tokens = load_volatile_tokens(sb.extracted)
                low = p.as_posix().lower()
                assert any(t in low for t in tokens), \
                    f"non-append drift in {p.name} on clean rerun"
