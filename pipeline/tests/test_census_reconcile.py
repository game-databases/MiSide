"""S8 census / PROOF.md — AC-12 (Principle-two sections, method-per-number,
reconciliation, residue ledger, protocol placeholder)."""

from __future__ import annotations

import json

import pytest

from conftest import read_jsonl

pytestmark = pytest.mark.integration

METHOD_TOKENS = ("walk", "walked", "measured", "measurement", "census",
                 "count", "tool", "filesystem", "assetstudio",
                 "il2cppdumper", "detect")


def _window_has_method(lines: list[str], idx: int, radius: int = 4) -> bool:
    lo = max(0, idx - radius)
    hi = min(len(lines), idx + radius + 1)
    hay = "\n".join(lines[lo:hi]).lower()
    return any(t in hay for t in METHOD_TOKENS)


def test_proof_exists_with_all_four_sections(full_run):
    sb, man, _ = full_run("proof-sections")
    proof = sb.extracted / "PROOF.md"
    assert proof.exists(), "PROOF.md missing after full run"
    low = proof.read_text("utf-8", errors="replace").lower()
    for section in ("source inventory", "coverage reconciliation",
                    "residue", "protocol"):
        assert section in low, f"PROOF.md missing '{section}' section"


def test_numbers_carry_tool_and_method(full_run):
    """Every number carries tool + method (§8: totals derived from own
    walks) — checked as digit-groups appearing near a method token."""
    sb, man, _ = full_run("proof-method")
    lines = (sb.extracted / "PROOF.md").read_text("utf-8",
                                                  errors="replace").splitlines()
    for digits in (str(man["grand_total"]), str(len(man["ogg"]))):
        hits = [i for i, ln in enumerate(lines) if digits in ln]
        assert hits, f"grand total {digits} absent from PROOF.md"
        assert any(_window_has_method(lines, i) for i in hits), (
            f"number {digits} appears with no tool/method context nearby")


def test_voice_editor_content_source_row(full_run):
    """questions.md §7 ruling: Voice Editor is a PROOF content-source row
    with counts+bytes+method (probe P7)."""
    sb, man, _ = full_run("proof-voiceeditor")
    lines = (sb.extracted / "PROOF.md").read_text("utf-8",
                                                  errors="replace").splitlines()
    hits = [i for i, ln in enumerate(lines)
            if "voice editor" in ln.lower()]
    assert hits, "no Voice Editor source row in PROOF.md"
    window = "\n".join(lines[max(0, hits[0] - 3):hits[0] + 5]).lower()
    assert any(t in window for t in METHOD_TOKENS), \
        "Voice Editor row lacks counts/bytes/method context"


def test_container_totals_reconcile_to_detect_census(full_run):
    sb, man, _ = full_run("proof-reconcile")
    detect_txt = (sb.extracted / "census" / "detect.json").read_text(
        "utf-8", errors="replace")
    proof = (sb.extracted / "PROOF.md").read_text("utf-8", errors="replace")
    assert str(man["grand_total"]) in detect_txt
    assert str(man["grand_total"]) in proof, \
        "PROOF container total does not reconcile to the S2 census"

    # Attempted-vs-succeeded read from the LATEST S4 full rewrite.
    rows = read_jsonl(sb.extracted / "census" / "sweep-attempts.jsonl")
    n_containers = len(man["serialized_files"])
    assert len(rows) == n_containers, (
        f"ledger has {len(rows)} rows; census must reconcile against one "
        f"row per container ({n_containers}), never accumulated across runs")
    low = proof.lower()
    assert "attempted" in low and "succeed" in low, \
        "coverage reconciliation must speak attempted-vs-succeeded"


def test_residue_ledger_entries_seeded(full_run):
    """E1's known gaps seeded into the residue ledger — each entry pinned by
    its residue ID plus discriminating content ('gi'/'get' needles were
    substrings of 'logic'/'budget' and could never fail)."""
    sb, man, _ = full_run("proof-residue")
    lines = (sb.extracted / "PROOF.md").read_text("utf-8",
                                                  errors="replace").splitlines()
    for rid, needles in {
        "R-E1-1": ("leveln dump depth", "curation-pass"),
        "R-E1-2": ("dataachievements", "unlock state"),
        "R-E1-3": ("category sets differ", "locale-delta.jsonl"),
        "R-E1-4": ("global-illumination", "level3"),
    }.items():
        rows = [ln for ln in lines if "[%s]" % rid in ln]
        assert rows, f"residue ledger missing [{rid}] entry"
        hay = "\n".join(rows).lower()
        assert all(n in hay for n in needles), \
            f"[{rid}] row present but lost its seeded residue content"


def test_protocol_placeholder_explicitly_seeded(full_run):
    sb, man, _ = full_run("proof-protocol")
    lines = (sb.extracted / "PROOF.md").read_text("utf-8",
                                                  errors="replace").splitlines()
    hits = [i for i, ln in enumerate(lines) if "protocol" in ln.lower()]
    assert hits, "no protocol section in PROOF.md"
    window = "\n".join(lines[hits[0]:hits[0] + 6]).lower()
    assert any(t in window for t in ("placeholder", "seeded", "later piece")), \
        "protocol section must be an explicitly-seeded placeholder in P1"


def test_census_fails_fast_on_reconciliation_mismatch(full_run):
    """§S8 failure semantics: a wrong total is worse than a crashed run —
    inconsistent ledger vs stage reports must FAIL-FAST."""
    sb, man, _ = full_run("proof-mismatch")
    ledger = sb.extracted / "census" / "sweep-attempts.jsonl"
    rows = read_jsonl(ledger)[:2]  # truncate: 2 of 6 containers "attempted"
    ledger.write_text("".join(json.dumps(r) + "\n" for r in rows),
                      encoding="utf-8")
    res = sb.run("--stage", "census")
    assert res.rc != 0, (
        "census accepted attempted-vs-succeeded numbers that contradict "
        "the truncated sweep ledger — reconciliation is not real")
