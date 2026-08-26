# Brief DS-1 — Dataset Specifier: Characters & Mitas (MiSide)

You are a fresh Dataset Specifier subagent launched by the MiSide
orchestrator. You CANNOT spawn agents. You never run `git` commands. Write
ONLY `C:\_reps\game-databases\MiSide\docs\specs\dataset-characters.mdx`;
read-only elsewhere (workroot + game root readable, never writable).

## Read first

1. `MiSide/spec.md` — frozen spec: entity pages section, character/Mita
   pages as SOUL SURFACES, data-source map.
2. `MiSide/docs/research/game-research.mdx` — Mita lore/variants chapters.
3. Corpus map: `D:\unpacked_game_data\MiSide\work\extracted\` — loc JSONLs
   (`loc/<locale>/<Category>.jsonl`), decompiled trees
   (`decompiled/Assembly-CSharp/...`), census + EXTRACTION-LOG,
   `_ledger/encoding-residue.jsonl`.
4. E1 findings: `GlobalLanguage.GetString(category, lineIndex)` join
   authority; UI strings = Localization_UIText(NameFile, StringNumber).

## Mission

Author the curation SPEC for the characters/Mitas dataset:
- Proposed schema (fields, types, locale columns vs per-locale files) with
  rationale tied to actual corpus evidence — open dump.cs classes and REAL
  loc category rows to ground every field. Name the exact categories/
  classes/assets feeding each field.
- Join plan: which keys link profiles ↔ dialogue ↔ scenes ↔ achievements.
- Completeness risks + what stays `[unverified]`; missingdata marks needed.
- Curated output location + format (`extracted/data/characters.jsonl` or
  better — propose), stub-first plan where data is absent (promptForDB).
- Acceptance criteria ≥6, each independently checkable by a verifier.

## Rules

Cite file paths for EVERY claim. MDX style. Final message ≤8 lines:
schema field count, source count, top completeness risk.
