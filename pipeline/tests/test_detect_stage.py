"""S2 detect — AC-6 fixture-tier analogue + drift guard (spec §S2).

The fixture root is synthetic, so the E1 install constants (51 files /
2,277,315,948 B / 34 locales) CANNOT be asserted here; the invariant under
test is that detect DERIVES every number from its own walk and they match
the fixture manifest exactly. Exact-constant checks live in the install
tier (test_install_smoke.py).
"""

from __future__ import annotations

import pytest

from conftest import tree_hash

pytestmark = pytest.mark.integration


def _prep(sb):
    res = sb.run("--from", "env", "--to", "detect")
    assert res.rc == 0, f"detect prep failed: {res.err}"


def test_detect_derives_fixture_totals_exactly(make_mini_root):
    sb, man = make_mini_root("detect-basic")
    _prep(sb)
    detect = sb.extracted / "census" / "detect.json"
    assert detect.exists(), "census/detect.json missing (spec §3 tree)"
    text = detect.read_text("utf-8", errors="replace")

    # Verdicts
    assert "2021.3.35f1" in text, "Unity version verdict missing"
    assert "29" in text, "metadata version 29 missing"
    assert "il2cpp" in text.lower(), "IL2CPP verdict missing"

    # Census numbers must equal the fixture's own walked truth, exactly.
    n_serialized = len(man["serialized_files"])
    n_streams = len(man["streams"])
    for label, value in [
        ("serialized count", n_serialized),
        ("serialized bytes", man["serialized_total"]),
        ("stream count", n_streams),
        ("stream bytes", man["stream_total"]),
        ("grand total", man["grand_total"]),
        ("locale dirs", len(man["languages"]["locales"])),
    ]:
        assert str(value) in text, \
            f"detect.json missing {label}={value} (must derive, not copy)"


def test_detect_records_build_id_and_version_label(make_mini_root):
    """AC-6 surface keys: buildId + VERSION label flow from the fixture
    into detect.json (install tier asserts the exact E1 constants)."""
    sb, man = make_mini_root("detect-buildid")
    _prep(sb)
    text = (sb.extracted / "census" / "detect.json").read_text("utf-8",
                                                               errors="replace")
    assert man["version_label"] in text, "VERSION label missing from detect.json"
    # Spec §S2 observation (2026-08-24): the .unity3d/Addressables absence
    # checks from the §S2 prose are NOT surfaced in detect.json by the
    # current implementation. Not an AC-6 item; flagged in COVERAGE.mdx.


def test_detect_writes_log_seed(make_mini_root):
    sb, man = make_mini_root("detect-logseed")
    assert not (sb.extracted / "EXTRACTION-LOG.md").exists()
    _prep(sb)
    log = sb.extracted / "EXTRACTION-LOG.md"
    assert log.exists(), "detect must seed EXTRACTION-LOG.md when absent"


def test_detect_rerun_without_drift_passes(full_run):
    sb, man, _ = full_run("detect-idem")
    res = sb.run("--stage", "detect")
    assert res.rc == 0, f"unchanged-inputs rerun must pass:\n{res.err}"


def test_detect_fails_fast_on_byte_drift_without_flag(make_mini_root):
    """Patch-day honesty (§S2): a silent byte change is a buildId change."""
    sb, man = make_mini_root("detect-drift")
    _prep(sb)
    container = sb.game_root / "MiSideFull_Data" / "level0"
    container.write_bytes(container.read_bytes() + b"drift-byte")
    res = sb.run("--stage", "detect")
    assert res.rc != 0, "silent census drift must FAIL-FAST without --expect-drift"


def test_detect_accepts_declared_drift(make_mini_root):
    sb, man = make_mini_root("detect-drift-ok")
    _prep(sb)
    container = sb.game_root / "MiSideFull_Data" / "level0"
    container.write_bytes(container.read_bytes() + b"drift-byte")
    res = sb.run("--stage", "detect", "--expect-drift")
    assert res.rc == 0, f"--expect-drift must let the run continue:\n{res.err}"
