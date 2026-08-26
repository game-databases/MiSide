"""Provenance & hygiene — AC-13 (pins, fixture-light), AC-14 (install stays
read-only), AC-15 (git tracking split).

The free-space guard's <10 GB abort path cannot be triggered synthetically
without mocking internals; it is covered by the integration tier's own
10 GiB skip-guard parity and documented in COVERAGE.mdx as an
install-tier/manual check. Everything else here is mechanical.
"""

from __future__ import annotations

import json
import re

import pytest

from conftest import PACK_ROOT, tree_hash

pytestmark = pytest.mark.integration


def test_log_pins_block_after_full_run(full_run):
    """AC-13 fixture-light: the pin block exists, parses, and carries the
    tool versions + freeze shape. Exact install constants (buildId etc.)
    are asserted in the install tier."""
    sb, man, _ = full_run("hyg-pins")
    log = sb.extracted / "EXTRACTION-LOG.md"
    assert log.exists()
    text = log.read_text("utf-8", errors="replace")
    m = re.search(r"```json\s+pipeline-defaults(.*?)```", text, re.DOTALL)
    assert m, "no ```json pipeline-defaults block near the top of EXTRACTION-LOG.md"
    try:
        block = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        pytest.fail(f"pipeline-defaults block is not valid JSON: {e}")
    blob = json.dumps(block)
    for key in ("buildId", "versionLabel"):
        assert key in blob, f"pin block missing {key}"
    assert "6.7.46" in blob, "Il2CppDumper 6.7.46 pin missing"
    assert "0.19.0.1" in blob, \
        "AssetStudioModCLI 0.19.0.1 cycle-guarded rebuild pin missing"
    assert "RequireAnyKey" in blob, "config delta not pinned"
    # 13-line pip freeze from E1 §Step 1.
    assert blob.count("==") >= 13, \
        f"pin block carries {blob.count('==')} pins, expected >=13"


def test_install_root_never_written(full_run):
    """AC-14 half A: the pipeline writes nothing under <game-root>."""
    sb, man, _ = full_run("hyg-readonly")
    from conftest import SCRATCH_ROOT
    import shutil
    import builders
    pristine = SCRATCH_ROOT / "pristine-check"
    if pristine.exists():
        shutil.rmtree(pristine)
    builders.build_mini_root(pristine)
    assert tree_hash(sb.game_root) == tree_hash(pristine), \
        "game root diverged from pristine fixture — something wrote to it"


def test_writes_confined_to_workroot_and_extracted(make_mini_root):
    """AC-14 half B: all mutable state lives in workroot + extracted/.
    Exact pre/post snapshot around the run: any NEW or CHANGED file outside
    those two trees (harness side-channel excluded) is a driver write."""
    from conftest import tree_hash as th
    sb, man = make_mini_root("hyg-confined3")
    pre = th(sb.path)
    res = sb.run()
    assert res.rc == 0, res.err
    post = th(sb.path)

    def exempt(rel: str) -> bool:
        return (rel.startswith("extracted/") or rel.startswith("work/")
                or rel == "stub-log.jsonl")

    added = [r for r in sorted(set(post) - set(pre)) if not exempt(r)]
    changed = [r for r in sorted(set(pre) & set(post))
               if pre[r] != post[r] and not exempt(r)]
    assert not added, f"driver created files outside workroot/extracted: {added[:10]}"
    assert not changed, \
        f"driver modified files outside workroot/extracted: {changed[:10]}"


def test_gitignore_encodes_tracking_split():
    """AC-15 / questions.md §8: local-only subtrees guarded; derived
    artifacts commit normally. Static repo check — red on the il2cpp line
    until CodeWriter lands the manifest task."""
    gi = PACK_ROOT / ".gitignore"
    assert gi.exists(), "pack .gitignore missing"
    lines = [l.strip() for l in gi.read_text("utf-8").splitlines()]
    for guarded in ("extracted/harvest/", "extracted/decompiled/",
                    "extracted/art/", "extracted/media/",
                    "extracted/il2cpp/"):
        assert guarded in lines, \
            f".gitignore must guard {guarded} (local-only per ruling)"
    # Test scratch never staged either.
    assert "output/" in lines


def test_no_client_bytes_in_test_tree():
    """Brief rule: NO real client bytes anywhere under pipeline/tests/. The
    fixtures are generated; this guards against someone 'optimizing' real
    containers into fixtures later. Markers are split at the source level so
    this file cannot trip itself."""
    tests = PACK_ROOT / "pipeline" / "tests"
    banned_markers = (b"Unity" + b"FS",           # unity bundle magic
                      b"Raw " + b"Data",          # SerializedFile field tag
                      b"2021.3.35f1" + bytes([0]))  # ggm version + NUL
    offenders = []
    for p in tests.rglob("*"):
        if "__pycache__" in p.parts or not p.is_file():
            continue
        if p.stat().st_size > 1024 * 1024:
            continue
        head = p.read_bytes()[:4096]
        if any(marker in head for marker in banned_markers):
            offenders.append(p.name)
    assert not offenders, f"possible client bytes committed under tests/: {offenders}"
