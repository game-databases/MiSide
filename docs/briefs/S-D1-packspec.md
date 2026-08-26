# Brief S-D1 — Documentator: author the MiSide pack spec (spec.md)

You are a fresh Documentator subagent launched by the MiSide orchestrator.
You CANNOT spawn other agents. You never run `git` commands. Write ONLY
`C:\_reps\game-databases\MiSide\spec.md` (plus nothing else); read-only
elsewhere except the read-only listing of the game install noted below
(NEVER write under `A:\SteamLibrary\...`).

## Read first

Canon (in full unless marked): `C:\_reps\game-databases\FRAMEWORK.md` §4
(spec template — your output MUST follow it) + §7 phases; AGENTS.md;
`_foundation/site-sections.md` (CORE/FIT rules);
`_foundation/seo-standard.md`; `_foundation/localization-architecture.md`;
`_foundation/design-standard.md`; `_foundation/domain-doctrine.md`.

Pack inputs (all verified/accepted):
- `MiSide/competitor-research.md` + `MiSide/docs/research/game-research.mdx`
  (niche analysis, version lattice, content inventory)
- `MiSide/docs/research/ui-style-scout.mdx` (dual-soul palette, motifs,
  token table — the design-direction source)
- `MiSide/toolchain.md`, `MiSide/data-acquisition.md`,
  `MiSide/docs/research/explorer-e1-hands-on.mdx` (what data exists and how
  it is extracted)

## Mission

Author `C:\_reps\game-databases\MiSide\spec.md` per the FRAMEWORK §4
template: product definition & audience; section map with CORE/FIT tags
(database, entity pages, Mita character pages as soul surfaces, owned scene
maps + per-page map modules, header search-in-place, guides, news, ending
explorer, trackers, changelog viewer, UGC — tag honestly, cut nothing
silently); page inventory; tools overview (detailed scoring happens later
in tools-plan.md — leave a stub section pointing there); locale strategy;
design direction summary referencing ui-style-scout.mdx (do NOT duplicate
its tables); data-source map (which extraction artifact feeds which
section); explicit non-goals.

## Locale reconciliation (do this concretely)

Three-way reconcile with evidence:
1. List actual client dirs: `ls "A:\SteamLibrary\steamapps\common\MiSide\Data\Languages"`
   (read-only listing allowed).
2. The 31 store-listed languages per `competitor-research.md`.
3. Pivot = en (bare paths, others `/xx/` per [DR-2026-08-20-locale-urls]).
Produce the shipped-locale table: code, client-dir name, store-listed Y/N,
notes (e.g. pt-BR vs pt-PT naming, any client-only or store-only stragglers).
Site chrome ships for every locale with full client coverage; document any
locale that fails the bar instead of silently dropping it.

## Rules

- Every claim cites its input file. No invented features. MDX-safe plain
  markdown. If FRAMEWORK §4 prescribes a different filename/location, follow
  it and say so in your final message.
- Final message ≤10 lines: deliverable path, section count, locale table
  row count, any input gaps you hit.
