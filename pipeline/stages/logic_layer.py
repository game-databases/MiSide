"""logic-layer — LG1-LG4 dataset emitters (docs/specs/logic-layer.mdx).

Wraps extracted/data/logic/build/emit_logic.py (the B-LL2 builder) as a run_all
stage so the delivery gate holds: a module is done only when its pipeline stage
is registered (XC-6 precedent, carried as a spec section 4 gate).

Deps are intentionally empty: the raw layers were relocated off C:
(extracted/*/MOVED-TO.txt -> D:\\unpacked_game_data\\MiSide), so the stage
resolves the corpus itself through those pointers and fails loudly (exit 3)
when harvest/mb-dump or il2cpp/dump.cs cannot be found. The stage reads the
frozen datasets only (Law 1); AC-L1a byte-freeze and the AC-L5 drift manifest
live inside the builder.

Interim AC-L6 CI-diff: the stage report records sha256(contracts/registry/
entities.json) alongside the emitted artifacts until check_contracts.py
activation lands from D-C1.
"""

import os
import time

from pipeline import common

NAME = "logic-layer"

_PACK_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_EMITTER = os.path.join(_PACK_ROOT, "extracted", "data", "logic", "build",
                        "emit_logic.py")
_ARTIFACTS = ("flag_instances.jsonl", "effect_calls.jsonl",
              "predicate_records.jsonl", "minigame_tunables.jsonl")


def outputs_present(ctx) -> bool:
    logic_dir = os.path.join(str(ctx.extracted), "data", "logic")
    return all(os.path.isfile(os.path.join(logic_dir, a)) for a in _ARTIFACTS)


def run(ctx):
    import importlib.util

    if not os.path.isfile(_EMITTER):
        raise common.StageFailure(NAME, "emitter missing: %s" % _EMITTER)

    started = time.monotonic()
    logic_dir = os.path.join(str(ctx.extracted), "data", "logic")

    before = {a: common.sha256_file(os.path.join(logic_dir, a))
              for a in _ARTIFACTS if os.path.isfile(os.path.join(logic_dir, a))}

    spec = importlib.util.spec_from_file_location("miside_logic_emitter", _EMITTER)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:  # syntax/import failure in the builder
        raise common.StageFailure(NAME, "emitter failed to load: %r" % exc)

    corpus = mod.resolve_corpus_root(None)
    try:
        result = mod.build(corpus, quiet=True)
    except SystemExit as exc:
        raise common.StageFailure(NAME, str(exc))

    after = {a: common.sha256_file(os.path.join(logic_dir, a))
             for a in _ARTIFACTS}
    missing = [a for a in _ARTIFACTS
               if not os.path.isfile(os.path.join(logic_dir, a))]
    if missing:
        raise common.StageFailure(NAME, "emitter did not produce %s" % missing)
    changed = sorted(a for a in _ARTIFACTS if before.get(a) != after[a])

    # Interim AC-L6 CI-diff: pin the consumer-contract registry next to the data.
    entities = os.path.join(_PACK_ROOT, "contracts", "registry", "entities.json")
    entities_sha = common.sha256_file(entities) \
        if os.path.isfile(entities) else None

    common.write_stage_report(ctx, NAME, {
        "status": "ok",
        "corpus_root": corpus,
        "rows": result,
        "artifacts": {a: after[a] for a in sorted(after)},
        "artifacts_changed_this_run": changed,
        "contracts_registry_entities_json_sha256": entities_sha,
        "duration_s": round(time.monotonic() - started, 3),
    })
    return result
