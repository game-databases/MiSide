# Brief D-S1 — Documentator: site scaffold & foundation spec (MiSide)

You are a fresh Documentator subagent of the MiSide orchestrator. You
CANNOT spawn agents; never run `git`. Write ONLY
`C:\_reps\game-databases\MiSide\docs\specs\site-scaffold.mdx`.

## Read first

1. `MiSide/spec.md` — FROZEN product spec (section map, page inventory,
   locale strategy, design direction).
2. `_foundation/design-standard.md` (§5 bar), `seo-standard.md`,
   `localization-architecture.md`, `site-sections.md`, FRAMEWORK §4+§8.
3. `MiSide/docs/research/ui-style-scout.mdx` — token table + motifs
   (pill chrome / VHS corruption) the kit must speak.
4. `[DR-2026-08-24-miside-pack]` §3 in `_foundation/decision-register.md`
   — shadcn/ui UPGRADED not reskinned.
5. Data contracts available to the frontend: `MiSide/contracts/*.mdx`
   (6 datasets) + `extracted/data/*/README*`.

## Mission

Author the scaffold spec that gates ALL site building:
- Stack pin (Next.js App Router; versions), rendering strategy per
  section type (static-first for SEO/AEO), repo layout under `site/`.
- **Locale architecture implementation**: pivot EN bare paths, `/xx/`
  prefixes for the other shipped locales per the spec's locale table;
  hreflang set; chrome i18n mechanism (which of the 34 ship at launch vs
  staged — justify).
- **shadcn upgrade plan**: which primitives, what each inherits stock
  (Radix behavior) vs rebuilt (visuals/motion/interactions per T2
  evidence); the token layer (`design/tokens.css`) structure consuming
  ui-style-scout's table; font-family decision procedure (identify game
  fonts from extracted artifacts — name the artifacts to inspect).
- Routing map: every page-inventory entry → route pattern; dynamic
  entity routes from contracts; search-in-place architecture
  ([DR-2026-08-22-search-is-not-a-page]).
- Map module contract: owned scene maps consuming scenes dataset +
  markers; no embeds ever.
- Non-goals for the scaffold piece itself (pages/tools come as separate
  pieces).

≥8 verifier-checkable ACs. Cite everything. Final message ≤10 lines.
