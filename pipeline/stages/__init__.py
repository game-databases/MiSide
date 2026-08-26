"""Ordered stage registry — spec §2. Tuple: (name, module, deps, description)."""

import importlib

STAGES = [
    ("env", "pipeline.stages.env", [],
     "Create the workroot venv + install pinned requirements (idempotent on pip freeze)"),
    ("detect", "pipeline.stages.detect", ["env"],
     "Flavor checks + container census + free-space guard + EXTRACTION-LOG seed"),
    ("il2cpp-dump", "pipeline.stages.il2cpp_dump", ["detect"],
     "Il2CppDumper 6.7.46 over GameAssembly.dll + global-metadata.dat -> extracted/il2cpp/"),
    ("mono-typed-dump", "pipeline.stages.mono_typed_dump", ["il2cpp-dump"],
     "Per-container typed MonoBehaviour dumps + asset-list XML + measure-first sweep budget"),
    ("loc-jsonl", "pipeline.stages.loc_jsonl", ["detect"],
     "Split-based loc parse -> per-locale JSONL + per-locale skew ledger"),
    ("art-export", "pipeline.stages.art_export", ["detect"],
     "2D export (staged scope) + MEDIA-CATALOGUE emission; no destructive moves"),
    ("decompile", "pipeline.stages.decompile", ["il2cpp-dump"],
     "ILSpy CLI batch decompile (main DummyDlls + Voice Editor Managed) + _structure/ graphs"),
    ("census", "pipeline.stages.census",
     ["detect", "il2cpp-dump", "mono-typed-dump", "loc-jsonl", "art-export", "decompile"],
     "PROOF.md generator: source inventory, coverage reconciliation, residue ledger, protocol placeholder"),
    ("logic-layer", "pipeline.stages.logic_layer", [],
     "LG1-LG4 logic-layer emitters over harvest/mb-dump + dump.cs -> extracted/data/logic/ (docs/specs/logic-layer.mdx)"),
]

_BY_NAME = {name: (module, deps, desc) for name, module, deps, desc in STAGES}


def stage_names():
    return [name for name, _module, _deps, _desc in STAGES]


def deps_of(name):
    return _BY_NAME[name][1]


def description_of(name):
    return _BY_NAME[name][2]


def load_stage(name):
    return importlib.import_module(_BY_NAME[name][0])
