# Brief CLOSURE-1 — Phase 1 closure: relink assembly + PROOF refresh + missingdata ledger

You are a fresh Closure subagent of the MiSide orchestrator. You CANNOT
spawn agents. You never run `git` commands. Write ONLY:
`C:\_reps\game-databases\MiSide\extracted\relinks\`,
`C:\_reps\game-databases\MiSide\extracted\data\missingdata.md`,
an updated `C:\_reps\game-databases\MiSide\extracted\PROOF.md`
(append a "Dataset-era reconciliation" section; keep prior content), and
your build-log block. Corpus read-only elsewhere; game root NEVER written.
KEEP DISK WRITES MINIMAL (C: critically low).

## Read

1. All SIX accepted datasets + contracts:
   `extracted/data/{characters,achievements,endings,dialogue,cartridges,documents,scenes}/`
   and `contracts/dataset-*.mdx`. Their build-log blocks
   (`docs/research/build-log.mdx`) carry every fence obligation.
2. Parked relink files: `data/*/relinks/*.jsonl` (characters ×5,
   cartridges ×6, documents ×5, scenes ×5) + dialogue's inline links.
3. `docs/specs/dataset-*.mdx` for each dataset's declared join mechanisms
   and deferral registers.

## Mission

1. **Relink assembly:** consolidate ALL parked relink files into
   `extracted/relinks/<subject>--<object>.jsonl` (canonical flat tree);
   where two datasets emitted the same relation, keep ONE authoritative
   file per the placement-authority rulings (cartridges owns pickup
   placement; characters owns identity joins) and record provenance rows;
   emit `extracted/relinks/locale_availability.jsonl` from the datasets'
   availability data (dialogue availability.csv is the seed; extend with
   per-entity locale coverage where datasets declare it).
2. **PROOF refresh:** append the dataset-era section — coverage table
   (entity counts, join edge counts, locale coverage %), reconciliation of
   every AC scoreboard, residue summary consolidated.
3. **missingdata.md:** sweep ALL `[unverified]` / stub / pending-curation
   marks across the six datasets + specs into one ledger: what's missing,
   why, unblock condition, owner-call vs derivable-later.

Byte-deterministic outputs. Final message ≤10 lines: relink file count,
edge total, missingdata entry count, any assembly conflicts found.
