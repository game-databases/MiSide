"""Install-tier smoke (I) — the ONLY tests allowed to touch the real
client root at A:\\SteamLibrary\\steamapps\\common\\MiSide\\.

Gated three ways:
  1. MISIDE_RUN_INSTALL_TESTS=1 in the environment,
  2. the real game root exists,
  3. conftest deselects the whole module otherwise (cheap CI skip).

These run against the REAL pipeline in place (no sandbox, real tools from
the pack's tools/ releases, workroot redirected to scratch). They refresh
the repo's real extracted/ — run deliberately, on NE8K, never in CI.
Runtime-budgeted per spec §6: S3+S4(resources) are seconds-class; the full
S4 sweep and S6/S7 budgets are unknown until sweep-budget.json exists —
measure-then-decide per R-E1-1.
"""

from __future__ import annotations

import os

import pytest

from conftest import REAL_GAME_ROOT

pytestmark = pytest.mark.install

BUILD_ID = "19029065"
VERSION_LABEL = "VERSION 0.93L"
UNITY = "2021.3.35f1"
METADATA_V = "29"

E1 = {
    "serialized_count": "51",
    "serialized_bytes": "583027900",
    "stream_count": "69",
    "stream_bytes": "1694288048",
    "grand_total": "2277315948",
    "locale_dirs": "34",
    "loc_files": "2210",
}


def _run_real_pipeline():
    """Full run_all against the real install (real tools, no sandbox)."""
    import subprocess
    import sys
    driver = r"C:\_reps\game-databases\MiSide\pipeline\run_all.py"
    assert os.path.exists(driver), "pipeline/run_all.py not landed"
    argv = [sys.executable, driver, str(REAL_GAME_ROOT)]
    proc = subprocess.run(argv, capture_output=True, timeout=7200)
    return proc.returncode, \
        proc.stdout.decode("utf-8", errors="replace"), \
        proc.stderr.decode("utf-8", errors="replace")


@pytest.fixture(scope="module")
def real_run():
    rc, out, err = _run_real_pipeline()
    if rc != 0:
        pytest.fail(f"real run_all exited {rc}:\n{err[-3000:]}")
    return True


@pytest.fixture(scope="module")
def real_run():
    res = _run_real_pipeline()
    if res.rc != 0:
        pytest.fail(f"real run_all exited {res.rc}:\n{res.err[-3000:]}")
    return res


def test_ac6_detect_exact_e1_totals(real_run):
    detect = r"C:\_reps\game-databases\MiSide\extracted\census\detect.json"
    text = open(detect, encoding="utf-8", errors="replace").read()
    for token in (UNITY, METADATA_V, BUILD_ID,
                  E1["serialized_count"], E1["serialized_bytes"],
                  E1["stream_count"], E1["stream_bytes"],
                  E1["grand_total"], E1["locale_dirs"]):
        assert token in text, f"detect.json missing E1-pinned value {token}"


def test_ac7_il2cpp_artifacts_and_counts(real_run):
    base = r"C:\_reps\game-databases\MiSide\extracted\il2cpp"
    dump_cs = open(os.path.join(base, "dump.cs"), encoding="utf-8",
                   errors="replace")
    lines = sum(1 for _ in dump_cs)
    assert lines >= 250_000, f"dump.cs has {lines} lines (<250k)"
    dummy = os.path.join(base, "DummyDll")
    dlls = [f for f in os.listdir(dummy) if f.lower().endswith(".dll")]
    assert len(dlls) == 57, f"{len(dlls)} DummyDlls"
    for name in ("script.json", "stringliteral.json", "il2cpp.h"):
        assert os.path.exists(os.path.join(base, name)), name


def test_ac9_localization_surface(real_run):
    loc = r"C:\_reps\game-databases\MiSide\extracted\localization"
    locales = [d for d in os.listdir(loc)
               if os.path.isdir(os.path.join(loc, d)) and not d.startswith("_")]
    assert len(locales) == int(E1["locale_dirs"]), \
        f"{len(locales)} locale dirs (a patch may legitimately add one)"
    jsonl_count = sum(
        len([f for f in files if f.endswith(".jsonl")])
        for _, _, files in os.walk(loc))
    assert jsonl_count >= int(E1["loc_files"]), \
        f"{jsonl_count} category JSONLs < {E1['loc_files']}"
    en_ach = os.path.join(loc, "English", "Achievements.jsonl")
    rows = [__import__("json").loads(l) for l in open(en_ach, encoding="utf-8")
            if l.strip()]
    assert len(rows) == 26 and rows[25]["text"] == "Pro Gamer"
    ru_first = open(os.path.join(loc, "Russian", "Achievements.jsonl"),
                    encoding="utf-8").readline()
    assert "Кислое молоко." in ru_first


def test_ac13_extraction_log_pins(real_run):
    log_path = r"C:\_reps\game-databases\MiSide\extracted\EXTRACTION-LOG.md"
    text = open(log_path, encoding="utf-8", errors="replace").read()
    # AssetStudioModCLI pinned at the 0.19.0.1 cycle-guarded rebuild
    # (spec errata; stock 0.19.0.0 dies with STATUS_STACK_OVERFLOW).
    for pin in (BUILD_ID, VERSION_LABEL, UNITY, "6.7.46", "0.19.0.1",
                "RequireAnyKey"):
        assert pin in text, f"EXTRACTION-LOG missing pin {pin}"
    assert text.count("==") >= 13, "13-line pip freeze not pinned"
