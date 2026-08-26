"""S4 mono-typed-dump — AC-8 (argv order, sweep ledger, budget gate, dumps).

Stub-enforced invariants do the heavy lifting:
* input-path-first is logged per invocation -> argv-order regression;
* level*/sharedassets* invocations are refused unless sweep-budget.json
  already exists -> measure-first gate proven by a green run;
* MISIDE_STUB_FAIL_CONTAINERS drives the LEDGER-mode tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import read_jsonl

pytestmark = pytest.mark.integration


def _prep(sb):
    res = sb.run("--from", "env", "--to", "il2cpp-dump")
    assert res.rc == 0, f"prep through il2cpp-dump failed: {res.err}"


def test_resources_assets_993_typed_dumps_with_field_trees(full_run):
    sb, man, _ = full_run("harvest-resources")
    res_dir = next(d for d in (sb.extracted / "harvest" / "mb-dump").iterdir()
                   if "resources" in d.name.lower())
    dumps = list(res_dir.glob("*.txt"))
    assert len(dumps) >= 993, f"{len(dumps)} dumps from resources.assets"
    ach = res_dir / "DataAchievements.txt"
    assert ach.exists(), "DataAchievements.txt missing from resources dump"
    body = ach.read_text("utf-8", errors="replace")
    assert "int size = 26" in body, "26-entry array not visible in dump"
    assert "[25]" in body and "steamAchievement" in body
    # Non-empty field trees: tab-indented typed lines (E1 text-dump shape).
    sample = dumps[0].read_text("utf-8", errors="replace")
    assert "\n\t" in sample, f"no tab-indented field tree in {dumps[0].name}"


def test_asset_list_xml_per_container(full_run):
    """AC-8 accepts same-pass or fallback mechanism — either way the
    crosswalk must land at harvest/asset-list/<container-stem>.xml."""
    sb, man, _ = full_run("harvest-xml")
    alist = sb.extracted / "harvest" / "asset-list"
    assert alist.is_dir(), "harvest/asset-list/ missing"
    xml_names = [p.name.lower() for p in alist.rglob("*.xml")]
    assert xml_names, "no asset-list XML emitted at all"
    for container in man["serialized_files"]:
        stem = container.removesuffix(".assets").lower()
        assert any(stem in n for n in xml_names), \
            f"no asset-list XML for {container} (have {xml_names})"


def test_argv_input_path_always_first(full_run):
    """E1 deviation 5: options-first fails with 'Input path was empty.' —
    every emitted AssetStudioModCLI invocation keeps input as the FIRST
    argument (stub logs .NET args, which exclude the exe name)."""
    sb, man, _ = full_run("harvest-argv")
    calls = sb.stub_calls("assetstudio")
    assert len(calls) >= len(man["serialized_files"]), \
        f"only {len(calls)} invocations for {len(man['serialized_files'])} containers"
    container_names = {c.lower() for c in man["serialized_files"]}
    for call in calls:
        argv = call["argv"]
        assert argv, "empty invocation"
        first = Path(argv[0]).name.lower()
        assert first in container_names, \
            f"argv[0]={argv[0]!r} is not a game container — input not first: {argv}"
        assert "-m" not in argv[:1], f"options before input: {argv}"


def test_sweep_budget_written_before_level_sweep(make_mini_root):
    """R-E1-1 measure-first gate. The stub REFUSES (exit 99) any
    level*/sharedassets* work unless census/sweep-budget.json exists, so a
    successful stage proves ordering."""
    sb, man = make_mini_root("harvest-budget")
    _prep(sb)
    res = sb.run("--stage", "mono-typed-dump")
    assert res.rc == 0, (
        f"stage failed — likely budget-gate violation:\n{res.err}")
    budget = sb.extracted / "census" / "sweep-budget.json"
    assert budget.exists(), "sweep-budget.json missing after stage"


def test_all_containers_attempted_and_ledger_rows_complete(full_run):
    sb, man, _ = full_run("harvest-ledger")
    ledger = sb.extracted / "census" / "sweep-attempts.jsonl"
    assert ledger.exists()
    rows = read_jsonl(ledger)
    assert len(rows) == len(man["serialized_files"]), (
        f"{len(rows)} ledger rows != {len(man['serialized_files'])} containers "
        "(one row per container, deterministic full rewrite)")
    names = [Path(c).name.lower() for c in man["serialized_files"]]
    blob = json.dumps(rows).lower()
    for n in names:
        assert n in blob, f"ledger never mentions container {n}"
    # Per spec S4 each attempt records container, argv sha, exit, objects.
    flat0 = json.dumps(rows[0])
    assert "sha" in flat0.lower() or len(flat0) > 40, \
        f"attempt row too thin to carry argv sha/exit/objects: {rows[0]}"


def test_keep_going_downgrades_failure_to_ledger(make_mini_root):
    """Per-container FAIL-FAST default; --keep-going downgrades to LEDGER.
    The injected failure targets a sweep container (not the measure-first
    probe — a failed probe legitimately aborts since the budget can't be
    sized)."""
    sb, man = make_mini_root("harvest-keepgoing")
    _prep(sb)
    res = sb.run("--stage", "mono-typed-dump", "--keep-going",
                 env_extra={"MISIDE_STUB_FAIL_CONTAINERS": "sharedassets0"})
    assert res.rc == 0, (
        f"--keep-going must record the failure and continue:\n{res.err}")
    rows = read_jsonl(sb.extracted / "census" / "sweep-attempts.jsonl")
    failed = [r for r in rows if "sharedassets0" in json.dumps(r)]
    assert failed, "failed container absent from attempts ledger"
    assert any(int(r.get("exit_code", -1)) == 42 or r.get("failed") is True
               for r in failed), \
        f"failure exit not recorded for sharedassets0: {failed}"

    # Rerun clean: deterministic FULL REWRITE must leave no residue of the
    # old failure (never-append rule).
    res2 = sb.run("--stage", "mono-typed-dump", "--keep-going")
    assert res2.rc == 0, res2.err
    rows2 = read_jsonl(sb.extracted / "census" / "sweep-attempts.jsonl")
    assert len(rows2) == len(man["serialized_files"])
    for r in rows2:
        assert int(r.get("exit_code", -1)) == 0, \
            f"stale failure row survived rewrite: {r}"

    # And a third clean rerun reproduces the second byte-for-byte,
    # modulo the volatile fields (duration_s/measured_at vary by design —
    # spec S4: "byte-for-byte modulo the volatile fields").
    from conftest import idempotency_violations, tree_hash
    before = tree_hash(sb.extracted)
    res3 = sb.run("--stage", "mono-typed-dump", "--keep-going")
    assert res3.rc == 0, res3.err
    after = tree_hash(sb.extracted)
    ledger_rel = "census/sweep-attempts.jsonl"
    bad = idempotency_violations(
        {ledger_rel: before[ledger_rel]}, {ledger_rel: after[ledger_rel]},
        sb.extracted)
    assert not bad, f"clean rerun drifted beyond volatile fields: {bad}"


def test_default_mode_fails_fast_on_container_error(make_mini_root):
    sb, man = make_mini_root("harvest-failfast")
    _prep(sb)
    res = sb.run("--stage", "mono-typed-dump",
                 env_extra={"MISIDE_STUB_FAIL_CONTAINERS": "sharedassets0"})
    assert res.rc == 3, (
        f"default mode must FAIL-FAST with exit 3 on container error, got {res.rc}")
    assert "mono-typed-dump" in (res.err + res.out).lower(), \
        f"failed stage not named:\n{res.err}"
