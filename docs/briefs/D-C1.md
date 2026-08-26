# Brief D-C1 — Documentator: data-contracts spec draft (MiSide contracts/)

You are the Documentator subagent of the MiSide orchestrator (PrepareTask
step 1 for the CONTRACTS piece). You CANNOT spawn agents; never run `git`;
write ONLY `C:\_reps\game-databases\MiSide\docs\specs\data-contracts.mdx`.
DISK MINIMAL.

## Goal

Draft the spec that pins ENTITY SCHEMAS in `MiSide/contracts/` so the
frontend CONSUMES, NEVER DERIVES (FRAMEWORK §7 gate; domain-doctrine).
This is the contract layer between the six ACCEPTED datasets + canonical
relinks and every Phase-3 site piece that follows.

## Read (sources of truth)

1. `extracted/data/{characters,achievements,endings,dialogue,cartridges,
   documents,scenes}/` — READMEs + emitted rows (the real shapes)
2. `extracted/relinks/` — 25 relation files / 1,159 edges +
   `locale_availability.jsonl` + `_assembly-provenance.jsonl`
3. `extracted/PROOF.md` §5 + `missingdata.md` (83 entries — stub policy)
4. `docs/specs/pipeline-run_all.mdx` §4 ledger policy (VOLATILE_FIELDS,
   deterministic rewrite) + dataset emitters' self-check contracts

## Spec must pin

1. One schema block per entity type: fields, types, nullability,
   units/coordinate frames (POI positions!), enums — derived FROM the
   emitted data (cite row counts; every claim evidence-backed)
2. Join-key registry: which relink file binds which entities, cardinality,
   and the reference-by-reference rule (B-5/B-4 precedent — no duplication)
3. Locale availability semantics for consumers (2,686 cells → per-field
   fallback chain rules; RTL aliases ru-x-prerev→ru, ar-EG→ar)
4. Versioning: fingerprint/hash rule per artifact so site builds fail
   loud on drift (ties to pipeline ledger policy)
5. Stub policy: how missingdata.md entries surface in typed contracts
   (explicit stub markers, never silent empties)
6. Directory layout + file formats under `contracts/`; AC list (S-style,
   numbered, machine-checkable); explicit NON-goals

## Constraints

- Follow FRAMEWORK §4 spec template exactly (same section skeleton as
  `docs/specs/site-scaffold.mdx`)
- Do NOT invent fields not present in emitted data; where a consumer will
  need something absent, write it as an open question for the reviewer
- ≤500 lines

Final message ≤8 lines: spec path, section map, row-count citations used,
open questions count.
